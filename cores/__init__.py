# from migen import *

from migen.fhdl.std import *
import n6502fpga.interconnect.n6502 as bus65

class Core(Module):
    src_dir = ""
    src_files = ""

class Arlet(Core):
    Core.src_dir = "./cores/verilog-6502"
    def __init__(self, clk_domain="sys"):
        self.bus = bus65.Interface()

        self.clk_domain = clk_domain
        self.specials.iface = Instance("cpu", name="n6502",
            i_clk=ClockSignal(clk_domain),
            i_reset=self.bus.rst,
            o_AB=self.bus.adr,
            i_DI=self.bus.din,
            o_DO=self.bus.dout,
            o_WE=self.bus.wen,
            i_IRQ=self.bus.irq,
            i_NMI=self.bus.nmi,
            i_RDY=self.bus.rdy)

