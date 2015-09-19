from migen import *
# from migen.fhdl import verilog
from migen.build.platforms import mercury as my_plat # Your platform here
from migen.build.generic_platform import ConstraintError, Pins

import n6502fpga.interconnect.n6502 as bus65
from n6502fpga.cores import Arlet
from n6502fpga.peripheral.gpio import GPIO
from n6502fpga.peripheral.led import LEDUnit


class n6502SoC(Module):
    # Limitation: BSS must come first, though this mostly makes sense thanks
    # to zero page and page one stack.
    def __init__(self, ROM_contents=None, bss_size=0x2000, data_size=0x2000):
        self.submodules.core = Arlet()
        
        if ROM_contents:
            with open(ROM_contents, "rb") as fp:
                bytes = b"\x00"*bss_size+fp.read()
                self.specials.cpu_mem = Memory(8, len(bytes), init=bytes)
        else:
            self.specials.cpu_mem = Memory(8, bss_size + data_size)
        
        self.submodules.mem = bus65.SRAM(self.cpu_mem)
        self.submodules.led = LEDUnit()
        self.submodules.gpio = GPIO()
        self.submodules.syscon = bus65.SysCon()
        self.submodules.adr_decode = bus65.SharedBus(self.core.bus,
             [(self.mem.bus, lambda a : a[8:16] != 0xFE),
             (self.led.bus, lambda a : ((a[8:16] == 0xFE) & (a[4:8] == 0))),
             (self.gpio.bus, lambda a : ((a[8:16] == 0xFE) & (a[4:8] == 1)))])
        
        # self.clock_domains.cd_sys = ClockDomain()
        
        ###
        
        # Move to do finalize?
        for rst_sink in [self.core.bus.rst,
            self.gpio.bus.rst,
            self.led.bus.rst]:
                self.syscon.add_rst_sink(rst_sink)
        
        # OR with peripheral rst?
        self.comb += [self.core.bus.connect(self.syscon.gates, leave_out={"adr",
            "din", "dout", "wen", "sel", "rst"})]
        # self.comb += [self.core.bus.rdy.eq(self.syscon.gates.rdy)]
        # self.comb += [self.core.bus.irq.eq(self.syscon.gates.irq)]
        # self.comb += [self.core.bus.nmi.eq(self.syscon.gates.nmi)]


if __name__ == "__main__":
    # Synthesis
    plat = my_plat.Platform()

    try:
        leds = [plat.request("user_led", i) for i in range(2)]
    except ConstraintError:
        plat.add_extension(my_plat.leds)
    finally:
        leds = [plat.request("user_led", i) for i in range(2)]
        
    try:
        serial = plat.request("serial")
    except ConstraintError:
        plat.add_extension(my_plat.serial)
    finally:
        serial = plat.request("serial")
    
    # Some boards provide gpio as a signal of width > 1. We need an array
    # of single-width GPIOs to vary direction individually.
    try:
        gpio = [plat.request("gpio", i) for i in range(8)]
    except ConstraintError:
        # TODO: Query preferred connector on a board basis?
        gpios = (("gpio", i, Pins("GPIO:" + str(i))) for i in range(8))
        plat.add_extension(gpios)
    finally:
        gpio = [plat.request("gpio", i) for i in range(8)]
        
    # TODO: Assume platforms have a clock :). But which speed?
    # clk50 = plat.request("clk50")
    m = n6502SoC(ROM_contents="./firmware/test_prog.bin")
    # m.comb += [m.cd_sys.clk.eq(clk50)]
    m.led.bind_outputs(leds) # Requires list due to Cat limitations
    m.gpio.bind_iobufs(gpio) # Same
    plat.add_source_dir(m.core.src_dir)
    plat.build(m, source=True, run=True, build_dir="build", build_name="n6502SoC")
    
    # TODO: Provide option to manually generate Verilog code for not-yet-
    # supported platforms in Migen. Use each module's bind function to create
    # the signals.
    # with open("n6502SoC.v", "w") as fp:
    #     # m = n6502SoC(ROM_contents="test_prog.bin")
    #     m = n6502SoC()
    #     fp.write(str(verilog.convert(m, ios={m.io_pads})))
    
    # TODO: Port to new simulator when ready?
    # from migen.sim.generic import run_simulation, Simulator, TopLevel
    # from migen.sim.icarus import Runner
    # with Simulator(m,
    #     TopLevel(vcd_name="n6502.vcd", cd_name="sys", clk_period=20, dut_type="N6502TB", dut_name="dut"),
    #     Runner(keep_files=True, extra_files=["./cores/verilog-6502/cpu.v", "./cores/verilog-6502/ALU.v"], options=["-DSIM"]),
    #     display_run=False) as s:
    #         s.run(300)
    
