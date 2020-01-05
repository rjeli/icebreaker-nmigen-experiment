#!/usr/bin/env python3

from nmigen import *
from nmigen.build import *
from nmigen_boards.icebreaker import ICEBreakerPlatform

class SSDigitDecoder(Elaboratable):
    def __init__(self):
        self.i_num = Signal(4)
        self.o_disp = Signal(7)
        self.lut = {
            0: 0b011_1111,
            1: 0b000_0110,
            2: 0b101_1011,
            3: 0b100_1111,
            4: 0b110_0110,
            5: 0b110_1101,
            6: 0b111_1101,
            7: 0b000_0111,
            8: 0b111_1111,
            9: 0b110_0111,
        }
    def incr(self):
        return self.i_num.eq(self.i_num+1)
    def elaborate(self, platform):
        m = Module()
        with m.Switch(self.i_num):
            for a, b in self.lut.items():
                with m.Case(a):
                    m.d.comb += self.o_disp.eq(b)
        return m

class Blinky(Elaboratable):
    def __init__(self):
        self.dd0 = SSDigitDecoder()
        self.dd1 = SSDigitDecoder()
    def elaborate(self, platform):
        m = Module()
        m.submodules.dd0 = self.dd0
        m.submodules.dd1 = self.dd1

        timer = Signal(20)
        led = platform.request('led', 0)
        btn = platform.request('button', 0)
        btn1 = platform.request('button', 1)
        dig_sel = platform.request('ss_dig_sel', 0)
        disp = platform.request('ss_disp', 0)

        # blinky led
        m.d.sync += timer.eq(timer+1)
        m.d.comb += led.o.eq(timer[-1] & ~btn)

        # debouncing?
        """
        btn1_db = Signal(20)
        with m.If(btn1.i):
            m.d.sync += btn1_db.eq(2**20)
        with m.Else
        with m.
        """

        # 7 seg
        running = Signal(1)
        # naive btn
        last_btn1 = Signal(1)
        m.d.sync += last_btn1.eq(btn1.i)
        with m.If(btn1.i & ~last_btn1):
            m.d.sync += running.eq(~running)
        # debouncing (doesnt work??)
        """
        btn1_db = Signal(range(0, 0xfffff))
        with m.If(btn1.i & (btn1_db == 0)):
            m.d.sync += [
                running.eq(~running),
                btn1_db.eq(0xfffff),
            ]
        with m.If(btn1_db > 0):
            m.d.sync += btn1_db.eq(btn1_db-1)
        """

        with m.If(running & (timer == 0)):
            with m.If(self.dd0.i_num == 9):
                m.d.sync += self.dd0.i_num.eq(0)
                with m.If(self.dd1.i_num == 9):
                    m.d.sync += self.dd1.i_num.eq(0)
                with m.Else():
                    m.d.sync += self.dd1.incr()
            with m.Else():
                m.d.sync += self.dd0.incr()
        with m.If(timer[8]):
            m.d.comb += [
                dig_sel.o.eq(0),
                disp.o.eq(self.dd1.o_disp),
            ]
        with m.Else():
            m.d.comb += [
                dig_sel.o.eq(1),
                disp.o.eq(self.dd0.o_disp),
            ]

        return m

if __name__ == '__main__':
    p = ICEBreakerPlatform()
    p.add_resources(p.break_off_pmod)
    p.add_resources([
        Resource('ss_dig_sel', 0, 
            Pins('10', dir='o', conn=('pmod', 0)),
            Attrs(IO_STANDARD='SB_LVCMOS')),
        Resource('ss_disp', 0, 
            PinsN('1 2 3 4 7 8 9', dir='o', conn=('pmod', 0)),
            Attrs(IO_STANDARD='SB_LVCMOS')),
    ])
    for r in p.resources:
        print('r:', r)
    p.build(Blinky(), do_program=False)
