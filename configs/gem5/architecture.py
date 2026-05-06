#!/usr/bin/env python3
"""
IntelliCore gem5 Baseline Architecture Configuration

This is the baseline simulation architecture for IntelliCore, designed for
iterative development towards a multi-core, multi-level cache hierarchy with
RL agent-driven cache eviction prediction and prefetching strategies.

Current configuration:
  - Single x86 timing-accurate CPU
  - 512MB system memory
  - Basic I/D cache hierarchy
  - Simple interconnect

Future extensions:
  - Multiple CPU cores with cache coherence protocols
  - L2 and L3 caches with configurable hierarchy
  - RL agent integration for cache eviction decisions
  - RL agent integration for prefetching predictions
  - Configurable memory systems (DDR3/DDR4/DDR5)
  - Network-on-Chip (NoC) support

For more information on gem5 architecture configuration, see:
https://www.gem5.org/documentation/learning_gem5/part1/
"""

import m5
from m5.objects import *


def create_system():
    """Create and return the baseline system configuration."""
    
    system = System()
    
    # Clock and power domain
    system.clk_domain = SrcClockDomain()
    system.clk_domain.clock = '1GHz'
    system.clk_domain.voltage_domain = VoltageDomain()
    
    # Memory configuration
    system.mem_mode = 'timing'
    system.mem_ranges = [AddrRange('512MB')]
    
    # CPU configuration
    system.cpu = X86TimingSimpleCPU()
    
    # System interconnect
    system.membus = SystemXBar()
    
    # CPU cache ports
    system.cpu.icache_port = system.membus.cpu_side_ports
    system.cpu.dcache_port = system.membus.cpu_side_ports
    
    # Interrupt controller
    system.cpu.createInterruptController()
    system.cpu.interrupts[0].pio = system.membus.mem_side_ports
    system.cpu.interrupts[0].int_requestor = system.membus.cpu_side_ports
    system.cpu.interrupts[0].int_responder = system.membus.mem_side_ports
    system.system_port = system.membus.cpu_side_ports
    
    # Memory controller and DRAM
    system.mem_ctrl = MemCtrl()
    system.mem_ctrl.dram = DDR3_1600_8x8()
    system.mem_ctrl.dram.range = system.mem_ranges[0]
    system.mem_ctrl.port = system.membus.mem_side_ports
    
    return system


def create_workload(system, binary_path):
    """Set up the workload for the given system.
    
    Args:
        system: The gem5 System object
        binary_path: Path to the binary to run (e.g., 'tests/test-progs/hello/bin/x86/linux/hello')
    """
    system.workload = SEWorkload.init_compatible(binary_path)
    process = Process()
    process.cmd = [binary_path]
    system.cpu.workload = process
    system.cpu.createThreads()


if __name__ == 'm5.defines':
    build_env['CONF_DIR'] = os.path.dirname(__file__)

if __name__ == '__main__':
    # Create the system
    system = create_system()
    
    # Set up the workload
    binary = 'tests/test-progs/hello/bin/x86/linux/hello'
    create_workload(system, binary)
    
    # Create the root and instantiate
    root = Root(full_system=False, system=system)
    m5.instantiate()
    
    # Run the simulation
    print("Beginning simulation!")
    exit_event = m5.simulate()
    print('Exiting @ tick {} because {}'.format(m5.curTick(), exit_event.getCause()))
