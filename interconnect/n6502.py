from migen import *
from migen.fhdl import verilog

from operator import and_

# All active high for now
# Note that an ASIC 6502 makes heavy use of active-low (RWB, NMIB, RESB, IRQB, RDYB)
_layout = [
    ("adr", 16, DIR_M_TO_S),
    ("din", 8, DIR_S_TO_M),
    ("dout", 8, DIR_M_TO_S),
    ("wen", 1, DIR_M_TO_S),
    ("irq", 1, DIR_S_TO_M),
    ("nmi", 1, DIR_S_TO_M),
    ("rdy", 1, DIR_S_TO_M),
    ("sel", 1, DIR_M_TO_S),
    ("rst", 1, DIR_S_TO_M)
]

class Interface(Record):
    def __init__(self):
        Record.__init__(self, _layout)

# class DirectBus(Module):
#     def __init__(self, cpu, sys_bus):
        

# Connects din, dout, addr, wen, and sel.
# nmi, irq, rdy, and rst srcs/sinks are handled by SysCon.
class SharedBus(Module):
    def __init__(self, cpu, peripherals):
        for n, (p, _) in enumerate(peripherals):
            self.comb += [cpu.connect(p, leave_out = {"nmi", "irq", "rdy", "sel", "din", "rst"})]
        
        # sel
        self.submodules.decoder = AddressDecoder(cpu.adr, peripherals)
        
        # din
        psel_r = dict((1 << n, cpu.din.eq(p.din)) for n, (p, _) in enumerate(peripherals))
        self.comb += [Case(self.decoder.reg_sel, psel_r)]

            
# Peripherals receive the sel signal immediately. However, din to the CPU will
# not change until the next posedge.
class AddressDecoder(Module):
    def __init__(self, addr_bus, devices):
        num_devices = len(devices)
        self.reg_sel = Signal(num_devices)
        self.comb_sel = Signal(num_devices)
        
        
        for i, (dev, fcn) in enumerate(devices):
            self.comb += [self.comb_sel[i].eq(fcn(addr_bus))]
            self.comb += [dev.sel.eq(self.comb_sel[i])]
        
        self.sync += [self.reg_sel.eq(self.comb_sel)]


# TODO- Maskable IRQs, turn srcs into Record?
class SysCon(Module):
    # (RST, RDY, IRQ, NMI) = range(4)
    def __init__(self, clk_domain="sys"):
        self.gates = Record(layout_partial(_layout, "irq", "nmi", "rdy", "rst"))
        self.irq_src = []
        self.nmi_src = []
        self.rdy_src = []
        self.rst_src = []
        self.rst_sink = []
        self.clk_domain = clk_domain

    ###

    def add_rst_src(self, sigs):
        self.rst_src.append(sigs)
    
    # Two levels of reset- full SoC reset and 6502 subsystem reset.
    # TODO- Make more elegant with multiple clock domains?    
    def add_rst_sink(self, sigs):
         self.rst_sink.append(sigs)    
    
    def add_rdy_src(self, sigs):
        self.rdy_src.append(sigs)
    
    def add_irq_src(self, sigs):
        self.irq_src.append(sigs)
    
    def add_nmi_src(self, sigs):
        self.nmi_src.append(sigs)
    
    def do_finalize(self):
        for sink in self.rst_sink:
            self.comb += [sink.eq(self.gates.rst)]
        
        self.add_rst_src(~ResetSignal(self.clk_domain))
        for gate, srcs, default_state in zip(self.gates.iter_flat(),
            # FIXME- Order sensitive
            [self.irq_src, self.nmi_src, self.rdy_src, self.rst_src],
            [False, False, True, False]):
            if not srcs:
                if default_state:
                    self.comb += [gate[0].eq(1)]
                else:
                    self.comb += [gate[0].eq(0)]
            else:
                if default_state:
                    self.comb += [gate[0].eq(reduce(and_, srcs))]
                else:
                    self.comb += [gate[0].eq(~reduce(and_, srcs))]



# Modified from Migen's old wishbone module. All 6502s use an 8-bit external bus.
class SRAM(Module):
    def __init__(self, mem_or_size, read_only=None, init=None, bus=None):
        if bus is None:
            bus = Interface()
        self.bus = bus
        bus_data_width = flen(self.bus.dout)
        if isinstance(mem_or_size, Memory):
            self.mem = mem_or_size
        else:
            self.mem = Memory(bus_data_width, mem_or_size, init=init)
        if read_only is None:
            if hasattr(self.mem, "bus_read_only"):
                read_only = self.mem.bus_read_only
            else:
                read_only = False

        ###

        # memory
        port = self.mem.get_port(write_capable=not read_only, we_granularity=8)
        self.specials += self.mem, port
        # generate write enable signal
        if not read_only:
            self.comb += [port.we.eq(self.bus.wen & self.bus.sel)]
        # address and data
        self.comb += [
            port.adr.eq(self.bus.adr[:flen(port.adr)]),
            self.bus.din.eq(port.dat_r)
        ]
        if not read_only:
            self.comb += port.dat_w.eq(self.bus.dout)

