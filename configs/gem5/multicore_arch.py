import sys
import argparse
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

binary = "/workspace/benchmarks/bin/memory_patterns"

system.workload = SEWorkload.init_compatible(binary)

modes = ["sequential", "stride", "random", "hotcold"]
selected_mode = args.mode
benchmark_size = "1048576" # 2^20 elements, ~4 MiB total size
thread_count = str(args.threads)

process = Process(pid=100)
process.cmd = [binary, selected_mode, benchmark_size, thread_count]

for cpu in system.cpu:
  cpu.workload = process
  cpu.createThreads()

root = Root(full_system=False, system=system)
m5.instantiate()

print("Beginning multicore LRU simulation!")
exit_event = m5.simulate()
print("Exiting @ tick {} because {}".format(m5.curTick(), exit_event.getCause()))
