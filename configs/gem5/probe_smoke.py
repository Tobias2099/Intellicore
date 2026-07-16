import os

import m5
from m5.objects import *


gem5_root = os.environ.get(
    "GEM5_ROOT",
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "gem5")),
)

traffic_config = os.path.join(
    gem5_root, "tests", "gem5", "memory", "tgen-simple-mem.cfg"
)

try:
    cpu = TrafficGen(config_file=traffic_config)
except NameError:
    m5.fatal("TrafficGen requires protobuf support")

system = System(
    cpu=cpu,
    physmem=SimpleMemory(),
    membus=IOXBar(width=16),
    clk_domain=SrcClockDomain(clock="1GHz", voltage_domain=VoltageDomain()),
)

system.monitor = CommMonitor()
system.monitor.intellicore_probe_smoke = IntellicoreProbeSmoke()

system.cpu.port = system.monitor.cpu_side_port
system.monitor.mem_side_port = system.membus.cpu_side_ports
system.system_port = system.membus.cpu_side_ports
system.physmem.port = system.membus.mem_side_ports

root = Root(full_system=False, system=system)
root.system.mem_mode = "timing"

m5.instantiate()
exit_event = m5.simulate(100000000000)
exit_cause = exit_event.getCause()
m5.stats.dump()
print(f"Intellicore probe smoke test completed: {exit_cause}")
if exit_cause != "simulate() limit reached":
    exit(1)
