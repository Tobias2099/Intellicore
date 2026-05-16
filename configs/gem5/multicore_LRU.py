import os

import m5
from m5.objects import *

class L1ICache(Cache):
  size = "32KiB"
  assoc = 2
  tag_latency = 2
  data_latency = 2
  response_latency = 2
  mshrs = 4
  tgts_per_mshr = 20
  replacement_policy = LRURP()

class L1DCache(Cache):
  size = "32KiB"
  assoc = 2
  tag_latency = 2
  data_latency = 2
  response_latency = 2
  mshrs = 4
  tgts_per_mshr = 20
  replacement_policy = LRURP()

class L2Cache(Cache):
  size = "512KiB"
  assoc = 8
  tag_latency = 20
  data_latency = 20
  response_latency = 20
  mshrs = 20
  tgts_per_mshr = 12
  replacement_policy = LRURP()

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

system.mem_ctrl = MemCtrl()
system.mem_ctrl.dram = DDR3_1600_8x8()
system.mem_ctrl.dram.range = system.mem_ranges[0]
system.mem_ctrl.port = system.membus.mem_side_ports

num_cores = 4
system.cpu = [X86TimingSimpleCPU(cpu_id=i) for i in range(num_cores)]

for cpu in system.cpu:
  cpu.icache = L1ICache()
  cpu.dcache = L1DCache()

  cpu.icache.cpu_side = cpu.icache_port
  cpu.dcache.cpu_side = cpu.dcache_port

  cpu.icache.mem_side = system.l2bus.cpu_side_ports
  cpu.dcache.mem_side = system.l2bus.cpu_side_ports

  cpu.createInterruptController()
  cpu.interrupts[0].pio = system.membus.mem_side_ports
  cpu.interrupts[0].int_requestor = system.membus.cpu_side_ports
  cpu.interrupts[0].int_responder = system.membus.mem_side_ports

system.system_port = system.membus.cpu_side_ports

gem5_root = os.environ.get("GEM5_ROOT", "/opt/gem5")
binary = os.path.join(gem5_root, "tests/test-progs/hello/bin/x86/linux/hello")

system.workload = SEWorkload.init_compatible(binary)

for cpu_id, cpu in enumerate(system.cpu):
  process = Process(pid=100 + cpu_id)
  process.cmd = [binary]
  cpu.workload = process
  cpu.createThreads()

root = Root(full_system=False, system=system)
m5.instantiate()

print("Beginning multicore LRU simulation!")
exit_event = m5.simulate()
print("Exiting @ tick {} because {}".format(m5.curTick(), exit_event.getCause()))
