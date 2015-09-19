from migen import *

import n6502fpga.interconnect.n6502 as bus65

class GPIO(Module):
    def __init__(self):
        self.bus = bus65.Interface()
        self.iobufs = [TSTriple() for i in range(8)]
        # self.inouts = inouts
        self.inp = Signal(8)
        self.outp = Signal(8)
        self.oe = Signal(8)
        
        # self.submodules.regsel = Decoder(4)
        
        ###

        for i in range(8):
           self.comb += [self.inp[i].eq(self.iobufs[i].i)]
           self.comb += [self.iobufs[i].o.eq(self.outp[i])]
           self.comb += [self.iobufs[i].oe.eq(self.oe[i])]
           # self.specials += [self.iobufs[i].get_tristate(self.inouts[i])]
        
        regarray_r = Array([self.oe, self.inp])
        regarray_w = Array([self.oe, self.outp])
        
        regsel_r = dict((i, self.bus.din.eq(regarray_r[i])) for i in range(2))
        regsel_w = dict((i, regarray_w[i].eq(self.bus.dout)) for i in range(2))
        
        # Address decoding mux will ensure that only one output drives CPU's
        # din. In an ASIC design, reads would be tristated when chip
        # isn't chosen for reads.
        self.comb += [Case(self.bus.adr[0], regsel_r)]
        self.sync += [If(self.bus.wen & self.bus.sel,
            Case(self.bus.adr[0], regsel_w))]
        # self.sync += [If(self.bus.sel & 
        
    def bind_iobufs(self, inouts, offset=0):
        self.specials += [self.iobufs[i].get_tristate(j) for i, j in enumerate(inouts, start=offset)]
