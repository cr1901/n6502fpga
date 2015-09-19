# from migen import *

from migen.fhdl.std import *

import n6502fpga.interconnect.n6502 as bus65


# Debugging unit
class LEDUnit(Module):
    def __init__(self):
        self.bus = bus65.Interface()
        self.o = Signal(8)
        
        # self.comb += [self.bus.din.eq(self.o)]
        self.sync += [If(self.bus.wen & self.bus.sel,
            self.o.eq(self.bus.dout))]
            
    def bind_outputs(self, outs, offset=0):
        self.comb += [j.eq(self.o[i]) for i, j in enumerate(outs, start=offset)]
