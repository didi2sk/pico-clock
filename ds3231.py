"""Minimálny ovládač DS3231 (čas + teplota)."""

_ADDR = 0x68


def _bcd(v):
    return (v // 10) << 4 | (v % 10)


def _dec(v):
    return (v >> 4) * 10 + (v & 0x0F)


class DS3231:
    def __init__(self, i2c):
        self.i2c = i2c

    def present(self):
        return _ADDR in self.i2c.scan()

    def get(self):
        """(rok, mesiac, deň, hodina, minúta, sekunda) — uložené ako UTC."""
        d = self.i2c.readfrom_mem(_ADDR, 0x00, 7)
        return (2000 + _dec(d[6]), _dec(d[5] & 0x1F), _dec(d[4]),
                _dec(d[2] & 0x3F), _dec(d[1]), _dec(d[0] & 0x7F))

    def set(self, y, mo, d, h, mi, s):
        self.i2c.writeto_mem(_ADDR, 0x00, bytes(
            (_bcd(s), _bcd(mi), _bcd(h), 1, _bcd(d), _bcd(mo), _bcd(y - 2000))))

    def temperature(self):
        d = self.i2c.readfrom_mem(_ADDR, 0x11, 2)
        t = d[0] - 256 if d[0] & 0x80 else d[0]
        return t + (d[1] >> 6) * 0.25
