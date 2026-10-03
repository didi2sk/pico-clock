"""Ovládač LED matice 8x24 (2x SM16106 stĺpce + SM5166P dekodér riadkov).

POZOR: poradie bitov, polarita OE a adresovanie riadkov NIE SÚ overené na
hardvéri. Ak je obraz zrkadlený/prevrátený, uprav DISPLAY_* v config.py
(MIRROR_X, FLIP_Y, ROW_ACTIVE_LOW) alebo porovnaj s demom z wiki Waveshare.
"""
import _thread
import time
from machine import Pin

import config
from canvas import W, H, Canvas


class Display(Canvas):
    def __init__(self):
        super().__init__()
        self.sdi = Pin(config.PIN_SDI, Pin.OUT, value=0)
        self.clk = Pin(config.PIN_CLK, Pin.OUT, value=0)
        self.le = Pin(config.PIN_LE, Pin.OUT, value=0)
        self.oe = Pin(config.PIN_OE, Pin.OUT, value=1)  # 1 = zhasnuté
        self.addr = [Pin(p, Pin.OUT, value=0) for p in config.PIN_ROW_ADDR]
        self.brightness = 8  # 1..15
        self._front = [0] * H
        self._run = False

    def show(self):
        self._front = list(self.buf)

    def start(self):
        self._run = True
        _thread.start_new_thread(self._refresh, ())

    def stop(self):
        self._run = False

    def _shift(self, row):
        sdi, clk = self.sdi, self.clk
        rng = range(W) if config.MIRROR_X else range(W - 1, -1, -1)
        for i in rng:
            sdi.value((row >> i) & 1)
            clk.value(1)
            clk.value(0)

    def _refresh(self):
        rows = range(H - 1, -1, -1) if config.FLIP_Y else range(H)
        while self._run:
            frame = self._front
            on = self.brightness * 40  # us
            for r in rows:
                self._shift(frame[r])
                self.oe.value(1)
                for b, pin in enumerate(self.addr):
                    pin.value((r >> b) & 1)
                self.le.value(1)
                self.le.value(0)
                self.oe.value(0)
                time.sleep_us(on)
                self.oe.value(1)
                time.sleep_us(640 - on)
