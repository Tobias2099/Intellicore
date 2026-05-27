import sys
import argparse
import os
import shlex
import m5
import m5.objects as m5obj
from m5.objects import *

# parse CLI args passed via gem5 invocation
parser = argparse.ArgumentParser()
parser.add_argument("--repl", choices=["LRU", "LFU", "MRU"], default="LRU",
          help="Replacement policy: LRU, LFU, or MRU")
parser.add_argument("--mode", choices=["sequential", "stride", "random", "hotcold"],
          default="sequential", help="Memory access pattern")
parser.add_argument("--prefetch", choices=["none", "stride", "tagged", "delta"],
          default="delta", help="Prefetcher: none, stride, tagged, delta")
parser.add_argument("--threads", type=int, default=4,
          help="Worker threads spawned by the memory_patterns process")
parser.add_argument("--benchmark", choices=["synthetic", "parsec"], default="synthetic",
          help="Benchmark family to run")
parser.add_argument("--parsec-workload", default="blackscholes",
          help="PARSEC workload name when --benchmark=parsec")
parser.add_argument("--parsec-input", default="simsmall",
          help="PARSEC input size when --benchmark=parsec")
args, unknown = parser.parse_known_args()

# Map CLI name to the gem5 replacement-policy SimObject constructor name
_repl_map = {
  "LRU": "LRURP",
  "LFU": "LFURP",
  "MRU": "MRURP",
}

try:
  repl_class_name = _repl_map[args.repl]
  ReplClass = getattr(m5obj, repl_class_name)
except Exception:
  raise SystemExit(f"Replacement policy class for {args.repl} not found in m5.objects")

# Do not instantiate a replacement-policy at module import time (can
# trigger SimObject construction ordering issues). We'll instantiate
# per-cache below after caches are created.
# policy = ReplClass()

# Map prefetch CLI to gem5 prefetcher classes
_pf_map = {
  "none": None,
  "stride": "StridePrefetcher",
  "tagged": "TaggedPrefetcher",
  "delta": "DeltaCorrelatingPrefetcher",
}

pf_choice = args.prefetch
if pf_choice == "none":
  PrefClass = None
else:
  pf_class_name = _pf_map.get(pf_choice)
  if pf_class_name and hasattr(m5obj, pf_class_name):
    PrefClass = getattr(m5obj, pf_class_name)
  else:
    PrefClass = None

class L1ICache(Cache):
  size = "32KiB"
  assoc = 2
  tag_latency = 2
  data_latency = 2
  response_latency = 2
  mshrs = 4
  tgts_per_mshr = 20
  replacement_policy = NULL

class L1DCache(Cache):
  size = "32KiB"
  assoc = 2
  tag_latency = 2
  data_latency = 2
  response_latency = 2
  mshrs = 4
  tgts_per_mshr = 20
  replacement_policy = NULL

class L2Cache(Cache):
  size = "512KiB"
  assoc = 8
  tag_latency = 20
  data_latency = 20
  response_latency = 20
  mshrs = 20
  tgts_per_mshr = 12
  replacement_policy = NULL

system = System()

system.clk_domain = SrcClockDomain()
system.clk_domain.clock = "1GHz"
system.clk_domain.voltage_domain = VoltageDomain()

system.mem_mode = "timing"
system.mem_ranges = [AddrRange("512MB")]

system.l2bus = L2XBar()
system.membus = SystemXBar()

system.l2cache = L2Cache()
system.l2cache.cpu_side = system.l2bus.mem_side_ports
system.l2cache.mem_side = system.membus.cpu_side_ports

# give the shared L2 its own replacement-policy instance
system.l2cache.replacement_policy = ReplClass()

system.mem_ctrl = MemCtrl()
system.mem_ctrl.dram = DDR3_1600_8x8()
system.mem_ctrl.dram.range = system.mem_ranges[0]
system.mem_ctrl.port = system.membus.mem_side_ports

num_cores = 4
system.cpu = [X86TimingSimpleCPU(cpu_id=i) for i in range(num_cores)]

for cpu in system.cpu:
  cpu.icache = L1ICache()
  cpu.dcache = L1DCache()

  # assign a fresh replacement-policy instance to each cache
  cpu.icache.replacement_policy = ReplClass()
  cpu.dcache.replacement_policy = ReplClass()

  # attach prefetcher instance if requested
  if PrefClass is not None:
    try:
      cpu.icache.prefetcher = PrefClass()
    except Exception:
      # some cache implementations expect a different attribute name or
      # do not support prefetcher assignment; ignore if not supported
      pass
    try:
      cpu.dcache.prefetcher = PrefClass()
    except Exception:
      pass

  cpu.icache.cpu_side = cpu.icache_port
  cpu.dcache.cpu_side = cpu.dcache_port

  cpu.icache.mem_side = system.l2bus.cpu_side_ports
  cpu.dcache.mem_side = system.l2bus.cpu_side_ports

  cpu.createInterruptController()
  cpu.interrupts[0].pio = system.membus.mem_side_ports
  cpu.interrupts[0].int_requestor = system.membus.cpu_side_ports
  cpu.interrupts[0].int_responder = system.membus.mem_side_ports

system.system_port = system.membus.cpu_side_ports

def synthetic_command():
  binary = "/workspace/benchmarks/bin/memory_patterns"
  modes = ["sequential", "stride", "random", "hotcold"]
  selected_mode = args.mode
  benchmark_size = "1048576" # 2^20 elements, ~4 MiB total size
  thread_count = str(args.threads)
  return binary, [binary, selected_mode, benchmark_size, thread_count], None, []


PARSEC_WORKLOADS = {
    "blackscholes": {
      "run_exec": "bin/blackscholes",
      "inputs": {
        "simsmall": "${NTHREADS} in_4K.txt prices.txt",
        "simmedium": "${NTHREADS} in_16K.txt prices.txt",
        "simlarge": "${NTHREADS} in_64K.txt prices.txt",
      },
    },
    "bodytrack": {
      "run_exec": "bin/bodytrack",
      "inputs": {
        "simsmall": "sequenceB_1 4 1 1000 5 0 ${NTHREADS}",
        "simmedium": "sequenceB_2 4 2 2000 5 0 ${NTHREADS}",
        "simlarge": "sequenceB_4 4 4 4000 5 0 ${NTHREADS}",
      },
    },
    "canneal": {
      "run_exec": "bin/canneal",
      "inputs": {
        "simsmall": "${NTHREADS} 10000 2000 100000.nets 32",
        "simmedium": "${NTHREADS} 15000 2000 200000.nets 64",
        "simlarge": "${NTHREADS} 15000 2000 400000.nets 128",
      },
    },
    "dedup": {
      "run_exec": "bin/dedup",
      "inputs": {
        "simsmall": "-c -p -v -t ${NTHREADS} -i media.dat -o output.dat.ddp",
        "simmedium": "-c -p -v -t ${NTHREADS} -i media.dat -o output.dat.ddp",
        "simlarge": "-c -p -v -t ${NTHREADS} -i media.dat -o output.dat.ddp",
      },
    },
    "facesim": {
      "run_exec": "bin/facesim",
      "inputs": {
        "simsmall": "-timing -threads ${NTHREADS}",
        "simmedium": "-timing -threads ${NTHREADS}",
        "simlarge": "-timing -threads ${NTHREADS}",
      },
    },
    "ferret": {
      "run_exec": "bin/ferret",
      "inputs": {
        "simsmall": "corel lsh queries 10 20 ${NTHREADS} output.txt",
        "simmedium": "corel lsh queries 10 20 ${NTHREADS} output.txt",
        "simlarge": "corel lsh queries 10 20 ${NTHREADS} output.txt",
      },
    },
    "fluidanimate": {
      "run_exec": "bin/fluidanimate",
      "inputs": {
        "simsmall": "${NTHREADS} 5 in_35K.fluid out.fluid",
        "simmedium": "${NTHREADS} 5 in_100K.fluid out.fluid",
        "simlarge": "${NTHREADS} 5 in_300K.fluid out.fluid",
      },
    },
    "freqmine": {
      "run_exec": "bin/freqmine",
      "env": {"OMP_NUM_THREADS": "${NTHREADS}"},
      "inputs": {
        "simsmall": "kosarak_250k.dat 220",
        "simmedium": "kosarak_500k.dat 410",
        "simlarge": "kosarak_990k.dat 790",
      },
    },
    "streamcluster": {
      "run_exec": "bin/streamcluster",
      "needs_input_dir": False,
      "inputs": {
        "simsmall": "10 20 32 4096 4096 1000 none output.txt ${NTHREADS}",
        "simmedium": "10 20 64 8192 8192 1000 none output.txt ${NTHREADS}",
        "simlarge": "10 20 128 16384 16384 1000 none output.txt ${NTHREADS}",
      },
    },
    "swaptions": {
      "run_exec": "bin/swaptions",
      "needs_input_dir": False,
      "inputs": {
        "simsmall": "-ns 16 -sm 10000 -nt ${NTHREADS}",
        "simmedium": "-ns 32 -sm 20000 -nt ${NTHREADS}",
        "simlarge": "-ns 64 -sm 40000 -nt ${NTHREADS}",
      },
    },
    "x264": {
      "run_exec": "bin/x264",
      "inputs": {
        "simsmall": "--quiet --qp 20 --partitions b8x8,i4x4 --ref 5 --direct auto --b-pyramid --weightb --mixed-refs --no-fast-pskip --me umh --subme 7 --analyse b8x8,i4x4 --threads ${NTHREADS} -o eledream.264 eledream_640x360_8.y4m",
        "simmedium": "--quiet --qp 20 --partitions b8x8,i4x4 --ref 5 --direct auto --b-pyramid --weightb --mixed-refs --no-fast-pskip --me umh --subme 7 --analyse b8x8,i4x4 --threads ${NTHREADS} -o eledream.264 eledream_640x360_32.y4m",
        "simlarge": "--quiet --qp 20 --partitions b8x8,i4x4 --ref 5 --direct auto --b-pyramid --weightb --mixed-refs --no-fast-pskip --me umh --subme 7 --analyse b8x8,i4x4 --threads ${NTHREADS} -o eledream.264 eledream_640x360_128.y4m",
      },
    },
}


def expand_parsec_value(value):
  return value.replace("${NTHREADS}", str(args.threads))


def parsec_command():
  workload_name = args.parsec_workload
  input_name = args.parsec_input

  workload = PARSEC_WORKLOADS.get(workload_name)
  if workload is None:
    supported = ", ".join(sorted(PARSEC_WORKLOADS))
    raise SystemExit(f"Unsupported PARSEC workload: {workload_name}. Supported: {supported}")

  run_args = workload["inputs"].get(input_name)
  if run_args is None:
    supported_inputs = ", ".join(sorted(workload["inputs"]))
    raise SystemExit(
      f"Unsupported PARSEC input '{input_name}' for {workload_name}. "
      f"Supported: {supported_inputs}"
    )

  # build.sh copies PARSEC's run_exec binary into a stable workload-named alias.
  binary = f"/workspace/benchmarks/parsec/bin/{workload_name}"
  if not os.path.exists(binary):
    raise SystemExit(
      "PARSEC binary not found: {}\n"
      "Prepare it first with benchmarks/parsec/setup_parsec.py.".format(binary)
    )

  runtime_lib = "/workspace/benchmarks/parsec/lib/libhooks.so.0"
  if not os.path.exists(runtime_lib):
    raise SystemExit(
      "PARSEC runtime library not found: {}\n"
      "Run benchmarks/parsec/setup_parsec.py to copy libhooks into the workspace.".format(runtime_lib)
    )

  cwd = f"/workspace/benchmarks/parsec/inputs/{input_name}/{workload_name}"
  if workload.get("needs_input_dir", True) and not os.path.isdir(cwd):
    raise SystemExit(
      "PARSEC input directory not found: {}\n"
      "Prepare it first with benchmarks/parsec/setup_parsec.py.".format(cwd)
    )
  if not workload.get("needs_input_dir", True):
    cwd = "/tmp"

  command_args = shlex.split(expand_parsec_value(run_args))
  env = ["LD_LIBRARY_PATH=/workspace/benchmarks/parsec/lib"]
  for key, value in workload.get("env", {}).items():
    env.append(f"{key}={expand_parsec_value(value)}")

  print(f"PARSEC workload: {workload_name}/{input_name}")
  print(f"PARSEC run_exec: {workload['run_exec']}")
  print(f"PARSEC cwd: {cwd}")
  print(f"PARSEC command: {' '.join([binary] + command_args)}")

  return binary, [binary] + command_args, cwd, env


if args.benchmark == "parsec":
  binary, command, process_cwd, process_env = parsec_command()
else:
  binary, command, process_cwd, process_env = synthetic_command()

system.workload = SEWorkload.init_compatible(binary)

process = Process(pid=100)
process.cmd = command
if process_cwd:
  process.cwd = process_cwd
if process_env:
  process.env = process_env

for cpu in system.cpu:
  cpu.workload = process
  cpu.createThreads()

root = Root(full_system=False, system=system)
m5.instantiate()

print("Beginning multicore LRU simulation!")
exit_event = m5.simulate()
print("Exiting @ tick {} because {}".format(m5.curTick(), exit_event.getCause()))
