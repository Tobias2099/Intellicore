import sys
import argparse
import m5
import m5.objects as m5obj
from m5.objects import *

# parse CLI args passed via gem5 invocation
parser = argparse.ArgumentParser()
parser.add_argument("--repl", choices=["LRU", "LFU", "MRU"], default="LRU",
          help="Replacement policy: LRU, LFU, or MRU")
parser.add_argument("--mode", choices=["sequential", "stride", "random"],
          default="sequential", help="Memory access pattern")
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

# instantiate the selected replacement policy for use as default
policy = ReplClass()

class L1ICache(Cache):
  size = "32KiB"
  assoc = 2
  tag_latency = 2
  data_latency = 2
  response_latency = 2
  mshrs = 4
  tgts_per_mshr = 20
  replacement_policy = policy

class L1DCache(Cache):
  size = "32KiB"
  assoc = 2
  tag_latency = 2
  data_latency = 2
  response_latency = 2
  mshrs = 4
  tgts_per_mshr = 20
  replacement_policy = policy

class L2Cache(Cache):
  size = "512KiB"
  assoc = 8
  tag_latency = 20
  data_latency = 20
  response_latency = 20
  mshrs = 20
  tgts_per_mshr = 12
  replacement_policy = policy

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

modes = ["sequential", "stride", "random"]
selected_mode = args.mode
benchmark_size = "1048576" # 2^20 elements, ~4 MiB total size

for cpu_id, cpu in enumerate(system.cpu):
  process = Process(pid=100 + cpu_id)
  process.cmd = [binary, selected_mode, benchmark_size]
  cpu.workload = process
  cpu.createThreads()

root = Root(full_system=False, system=system)
m5.instantiate()

print("Beginning multicore LRU simulation!")
exit_event = m5.simulate()
print("Exiting @ tick {} because {}".format(m5.curTick(), exit_event.getCause()))
