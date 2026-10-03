"""Hardvérovo nezávislé kreslenie na 24x8 maticu (testovateľné aj na PC)."""

W = 24
H = 8

# 5x7 font, stĺpce zľava doprava, bit0 = horný riadok
FONT = {
    "0": (0x3E, 0x51, 0x49, 0x45, 0x3E),
    "1": (0x00, 0x42, 0x7F, 0x40, 0x00),
    "2": (0x42, 0x61, 0x51, 0x49, 0x46),
    "3": (0x21, 0x41, 0x45, 0x4B, 0x31),
    "4": (0x18, 0x14, 0x12, 0x7F, 0x10),
    "5": (0x27, 0x45, 0x45, 0x45, 0x39),
    "6": (0x3C, 0x4A, 0x49, 0x49, 0x30),
    "7": (0x01, 0x71, 0x09, 0x05, 0x03),
    "8": (0x36, 0x49, 0x49, 0x49, 0x36),
    "9": (0x06, 0x49, 0x49, 0x29, 0x1E),
    "-": (0x08, 0x08, 0x08, 0x08, 0x08),
    "C": (0x3E, 0x41, 0x41, 0x41, 0x22),
    "?": (0x02, 0x01, 0x51, 0x09, 0x06),
    " ": (0x00, 0x00, 0x00, 0x00, 0x00),
}
COLON = (0x14,)  # 1 stĺpec, dve bodky


class Canvas:
    def __init__(self):
        self.buf = [0] * H  # každý riadok = 24-bitové číslo, bit (W-1-x) = stĺpec x

    def clear(self):
        self.buf = [0] * H

    def _col(self, x, bits):
        if not 0 <= x < W:
            return
        mask = 1 << (W - 1 - x)
        for y in range(H - 1):
            if bits & (1 << y):
                self.buf[y] |= mask

    def glyph(self, x, cols):
        for i, c in enumerate(cols):
            self._col(x + i, c)
        return x + len(cols)

    def text(self, s, x=None):
        """Vykreslí text (5px znaky, 1px medzera); bez x ho vycentruje."""
        s = str(s)
        width = len(s) * 6 - 1
        if x is None:
            x = (W - width) // 2
        for ch in s:
            x = self.glyph(x, FONT.get(ch, FONT["?"])) + 1
        return x

    def time(self, hh, mm, colon=True):
        """HH:MM presne na 24 stĺpcov."""
        x = 0
        x = self.glyph(x, FONT[str(hh // 10)]) + 1
        x = self.glyph(x, FONT[str(hh % 10)]) + 1
        if colon:
            self.glyph(x, COLON)
        x += 1
        x = self.glyph(x, FONT[str(mm // 10)]) + 1
        self.glyph(x, FONT[str(mm % 10)])

    def ascii(self):
        return "\n".join(
            "".join("#" if row & (1 << (W - 1 - x)) else "." for x in range(W))
            for row in self.buf
        )
