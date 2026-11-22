#!/usr/bin/env python3
"""news-image-20261122 — deterministic front-page renderer.

Renders ONE 1024x1024 PNG summing up Sunday 22 November 2026 world news
as a newspaper front page: masthead + date, two big event panels (COP31
Antalya, Russia's war spilling into Poland and the Baltic), and a
three-item supporting strip (Wall Street crash, GTA 6, G20 Johannesburg).

Facts verified against ~/workspace/makefun-news-image-20261122/NEWS-22NOV.md
(research cutoff Sun 22 Nov ~07:15-08:00 WIB). Honesty rules baked in:
- COP31 deal was NOT yet approved at cutoff; approval session set for
  Sunday 06:00 GMT. Headline says "CLOSE TO DEAL ... EXPECTED SUNDAY",
  never "deal agreed".
- Market and GTA 6 figures are Friday 20 Nov closes / launch figures,
  dated "FRI" in the strip.
- Only corroborated numbers are printed (CNBC/Reuters market set;
  official Take-Two GTA 6 figures). Conflicting figures (weekly %,
  Sensor Tower $2.36bn estimate, "80 drones shot down" claim) are excluded.

Python 3.12/3.13 stdlib only, no network, no clock, no randomness —
running it twice produces byte-identical output. Writes to
$MAKEFUN_OUTPUT_DIR/entry.png (or /output/entry.png when unset).
"""

import math
import os
import struct
import zlib

W, H = 1024, 1024

PAPER = (251, 247, 238)
INK = (17, 17, 17)
WHITE = (255, 255, 255)
RED = (185, 28, 28)
DARKRED = (127, 29, 29)
BLUE = (30, 58, 138)
GREEN = (27, 94, 32)
DARKGREEN = (20, 70, 24)
ORANGE = (217, 119, 6)
GREY = (96, 96, 96)

# 5x7 bitmap font, hand-written in this session. Each glyph is 7 rows;
# each row is a 5-bit integer, most-significant bit = leftmost pixel.
FONT = {
    "A": (14, 17, 17, 31, 17, 17, 17),
    "B": (30, 17, 17, 30, 17, 17, 30),
    "C": (14, 17, 16, 16, 16, 17, 14),
    "D": (30, 17, 17, 17, 17, 17, 30),
    "E": (31, 16, 16, 30, 16, 16, 31),
    "F": (31, 16, 16, 30, 16, 16, 16),
    "G": (14, 17, 16, 23, 17, 17, 15),
    "H": (17, 17, 17, 31, 17, 17, 17),
    "I": (14, 4, 4, 4, 4, 4, 14),
    "J": (7, 2, 2, 2, 2, 18, 12),
    "K": (17, 18, 20, 24, 20, 18, 17),
    "L": (16, 16, 16, 16, 16, 16, 31),
    "M": (17, 27, 21, 21, 17, 17, 17),
    "N": (17, 25, 21, 19, 17, 17, 17),
    "O": (14, 17, 17, 17, 17, 17, 14),
    "P": (30, 17, 17, 30, 16, 16, 16),
    "Q": (14, 17, 17, 17, 21, 18, 13),
    "R": (30, 17, 17, 30, 20, 18, 17),
    "S": (15, 16, 16, 14, 1, 1, 30),
    "T": (31, 4, 4, 4, 4, 4, 4),
    "U": (17, 17, 17, 17, 17, 17, 14),
    "V": (17, 17, 17, 17, 17, 10, 4),
    "W": (17, 17, 17, 21, 21, 21, 10),
    "X": (17, 17, 10, 4, 10, 17, 17),
    "Y": (17, 17, 10, 4, 4, 4, 4),
    "Z": (31, 1, 2, 4, 8, 16, 31),
    "0": (14, 17, 19, 21, 25, 17, 14),
    "1": (4, 12, 4, 4, 4, 4, 14),
    "2": (14, 17, 1, 6, 8, 16, 31),
    "3": (31, 2, 4, 2, 1, 17, 14),
    "4": (2, 6, 10, 18, 31, 2, 2),
    "5": (31, 16, 30, 1, 1, 17, 14),
    "6": (6, 8, 16, 30, 17, 17, 14),
    "7": (31, 1, 2, 4, 8, 8, 8),
    "8": (14, 17, 17, 14, 17, 17, 14),
    "9": (14, 17, 17, 15, 1, 2, 12),
    " ": (0, 0, 0, 0, 0, 0, 0),
    ".": (0, 0, 0, 0, 0, 12, 12),
    ",": (0, 0, 0, 0, 12, 4, 8),
    ":": (0, 12, 12, 0, 12, 12, 0),
    ";": (0, 12, 12, 0, 12, 4, 8),
    "'": (4, 4, 8, 0, 0, 0, 0),
    "-": (0, 0, 0, 14, 0, 0, 0),
    "!": (4, 4, 4, 4, 4, 0, 4),
    "?": (14, 17, 1, 2, 4, 0, 4),
    "%": (25, 26, 2, 4, 8, 22, 19),
    "$": (4, 15, 20, 14, 5, 30, 4),
    "&": (12, 18, 20, 8, 21, 18, 13),
    "/": (1, 2, 2, 4, 8, 8, 16),
    "(": (2, 4, 8, 8, 8, 4, 2),
    ")": (8, 4, 2, 2, 2, 4, 8),
    "+": (0, 4, 4, 14, 4, 4, 0),
    "=": (0, 0, 14, 0, 14, 0, 0),
    '"': (10, 10, 0, 0, 0, 0, 0),
    "°": (6, 9, 9, 6, 0, 0, 0),
}


def text_width(s, scale):
    return len(s) * 6 * scale


def wrap_text(s, scale, max_w):
    """Greedy word wrap. Returns a list of lines, each <= max_w pixels."""
    lines = []
    for paragraph in s.split("\n"):
        words = paragraph.split(" ")
        cur = ""
        for word in words:
            trial = word if not cur else cur + " " + word
            if text_width(trial, scale) <= max_w or not cur:
                cur = trial
            else:
                lines.append(cur)
                cur = word
        if cur:
            lines.append(cur)
    return lines


class Canvas:
    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.buf = bytearray(w * h * 3)
        self.fill_rect(0, 0, w, h, bg)

    def px(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.buf[i] = color[0]
            self.buf[i + 1] = color[1]
            self.buf[i + 2] = color[2]

    def fill_rect(self, x, y, w, h, color):
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(self.w, x + w)
        y1 = min(self.h, y + h)
        for yy in range(y0, y1):
            base = (yy * self.w + x0) * 3
            for xx in range(x0, x1):
                i = base + (xx - x0) * 3
                self.buf[i] = color[0]
                self.buf[i + 1] = color[1]
                self.buf[i + 2] = color[2]

    def hline(self, x, y, w, color, t=1):
        self.fill_rect(x, y, w, t, color)

    def vline(self, x, y, h, color, t=1):
        self.fill_rect(x, y, t, h, color)

    def line(self, x0, y0, x1, y1, color, t=1):
        """Thick line via DDA, drawing t x t blocks along the path."""
        dx = x1 - x0
        dy = y1 - y0
        steps = max(abs(dx), abs(dy), 1)
        half = t // 2
        for s in range(steps + 1):
            x = x0 + round(dx * s / steps)
            y = y0 + round(dy * s / steps)
            self.fill_rect(x - half, y - half, t, t, color)

    def circle(self, cx, cy, r, color, t=2):
        """Midpoint circle outline."""
        x = 0
        y = r
        d = 1 - r
        half = t // 2
        while x <= y:
            for sx, sy in ((x, y), (y, x), (-x, y), (-y, x),
                           (x, -y), (y, -x), (-x, -y), (-y, -x)):
                self.fill_rect(cx + sx - half, cy + sy - half, t, t, color)
            x += 1
            if d < 0:
                d += 2 * x + 1
            else:
                y -= 1
                d += 2 * (x - y) + 1

    def fill_circle(self, cx, cy, r, color):
        """Filled disc, scanline by scanline (integer sqrt, deterministic)."""
        for dy in range(-r, r + 1):
            half = math.isqrt(r * r - dy * dy)
            self.fill_rect(cx - half, cy + dy, 2 * half + 1, 1, color)

    def text(self, x, y, s, scale, color):
        for ci, ch in enumerate(s):
            glyph = FONT.get(ch, FONT[" "])
            ox = x + ci * 6 * scale
            for row in range(7):
                bits = glyph[row]
                for col in range(5):
                    if bits & (1 << (4 - col)):
                        self.fill_rect(ox + col * scale, y + row * scale,
                                       scale, scale, color)

    def text_centered(self, cx, y, s, scale, color):
        self.text(cx - text_width(s, scale) // 2, y, s, scale, color)

    def wrapped(self, x, y, s, scale, color, max_w, leading):
        """Draw wrapped text; returns y just past the last line."""
        for line in wrap_text(s, scale, max_w):
            self.text(x, y, line, scale, color)
            y += 7 * scale + leading
        return y


def draw_panel(cv, x, y, w, h, accent, dark, kicker, headline_lines,
               sub, body, graphic):
    """One front-page panel: kicker bar, headline, rule, dek, body, graphic.

    Vertical budget (relative to panel top y, h=520):
    kicker bar 3..43, headline from 56 (4 lines x 39 = 156, ends 212),
    rule 218, dek from 232 (2 lines x 26 = 52, ends 284),
    body from 296 (scale 2, 17 px/line; 5 lines end 381, 7 end 415),
    graphic band 424..517. Body is capped by construction: both bodies
    wrap to <= 7 lines at 37 chars/line, so text never reaches the band.
    """
    cv.fill_rect(x, y, w, h, WHITE)
    cv.fill_rect(x, y, w, 3, INK)
    cv.fill_rect(x, y + h - 3, w, 3, INK)
    cv.fill_rect(x, y, 3, h, INK)
    cv.fill_rect(x + w - 3, y, 3, h, INK)
    # Kicker bar with white text.
    cv.fill_rect(x + 3, y + 3, w - 6, 40, accent)
    cv.text_centered(x + w // 2, y + 12, kicker, 3, WHITE)
    cy = y + 56
    for line in headline_lines:
        cv.text(x + 16, cy, line, 5, INK)
        cy += 7 * 5 + 4
    cv.hline(x + 16, cy + 6, w - 32, accent, 3)
    cy += 20
    cy = cv.wrapped(x + 16, cy, sub, 3, dark, w - 32, 5)
    cy += 12
    cy = cv.wrapped(x + 16, cy, body, 2, INK, w - 32, 3)
    graphic(cv, x, y, w, h)


def thermometer_graphic(cv, x, y, w, h):
    """Thermometer rising past the 1.5C mark — the COP31 story in one glyph.

    Band: y+h-96 .. y+h-3. Tube top y+h-96, bulb centre y+h-36 (r=26).
    """
    cx = x + w // 2 - 46
    top = y + h - 96
    bot = y + h - 44
    bulb_cy = y + h - 36
    # Tube: ink shell, white bore, red mercury rising past the 1.5C tick.
    cv.fill_rect(cx - 12, top, 24, bot - top, INK)
    cv.fill_rect(cx - 9, top + 2, 18, bot - top - 2, WHITE)
    cv.fill_rect(cx - 9, top + 16, 18, bot - top - 16, RED)
    # Bulb.
    cv.fill_circle(cx, bulb_cy, 26, RED)
    cv.circle(cx, bulb_cy, 26, INK, 2)
    # 1.5C tick line and label, level with the top of the mercury.
    cv.hline(cx + 12, top + 16, 18, INK, 2)
    cv.text(cx + 34, top + 8, "1.5°C", 3, RED)
    cv.text(cx + 34, top + 34, "GOAL", 2, INK)
    cv.text(cx + 34, top + 50, "MISSED", 2, INK)


def ship_graphic(cv, x, y, w, h):
    """Starburst over Poland (left) + burning cargo ship Sparta II (right).

    Band: y+h-96 .. y+h-3. Burst centre (x+88, y+h-62), spokes r=32;
    ship hull y+h-52..y+h-36, flames above it, waterline y+h-34.
    """
    # Starburst = missile impacts in Poland.
    bx, by = x + 88, y + h - 62
    for k in range(8):
        ang = math.pi * k / 4.0
        ex = bx + round(32 * math.cos(ang))
        ey = by + round(32 * math.sin(ang))
        cv.line(bx, by, ex, ey, RED, 3)
    cv.fill_circle(bx, by, 6, RED)
    cv.text_centered(bx, y + h - 28, "POLAND", 2, RED)
    # Ship Sparta II, ablaze.
    hx = x + 290
    hull_top = y + h - 52
    cv.fill_rect(hx, hull_top, 150, 16, INK)
    cv.vline(hx + 75, hull_top - 28, 28, INK, 3)
    for fx in (hx + 40, hx + 110):
        # Outer red flame triangle, inner orange flame triangle.
        cv.line(fx - 10, hull_top, fx, hull_top - 30, RED, 3)
        cv.line(fx, hull_top - 30, fx + 10, hull_top, RED, 3)
        cv.line(fx - 5, hull_top, fx, hull_top - 18, ORANGE, 3)
        cv.line(fx, hull_top - 18, fx + 5, hull_top, ORANGE, 3)
    cv.hline(hx - 4, y + h - 34, 158, BLUE, 2)
    cv.text_centered(hx + 75, y + h - 28, "SPARTA II", 2, INK)


def render():
    cv = Canvas(W, H, PAPER)

    # Masthead.
    cv.text_centered(W // 2, 28, "THE WORLD TODAY", 8, INK)
    cv.hline(24, 96, W - 48, INK, 4)
    cv.text_centered(W // 2, 108, "SUNDAY 22 NOVEMBER 2026", 4, RED)
    cv.text_centered(
        W // 2, 146,
        "THE DAY'S BIGGEST STORIES - AS REPORTED ON 22 NOVEMBER 2026",
        2, INK)
    cv.hline(24, 170, W - 48, INK, 4)

    # Panel 1 — COP31 Antalya (verified: Reuters dateline Nov 22).
    # Deal NOT approved at research cutoff; approval session Sunday
    # 06:00 GMT. Headline says CLOSE TO DEAL / EXPECTED SUNDAY.
    draw_panel(
        cv, 24, 182, 476, 520, GREEN, DARKGREEN,
        "CLIMATE - COP31 ANTALYA",
        ["COP31 CLOSE", "TO DEAL", "EXPECTED", "SUNDAY"],
        "APPROVAL VOTE SET FOR 06:00 GMT SUNDAY",
        "NEARLY 200 NATIONS IN ANTALYA AFTER 2 DAYS OVERTIME. "
        "DRAFT IS THE FIRST TO ADMIT THE 1.5C GOAL IS MISSED. "
        "A $120BN ADAPTATION TARGET WAS CUT. "
        "THE US IS ABSENT FOR A 2ND YEAR.",
        thermometer_graphic)

    # Panel 2 — Russia's war spills over (verified: Reuters/AP, 20-21 Nov).
    draw_panel(
        cv, 524, 182, 476, 520, RED, DARKRED,
        "WAR - POLAND AND BALTIC",
        ["MISSILES IN", "POLAND,", "SHIP ABLAZE", "IN BALTIC"],
        "NATO: WE WILL DEFEND EVERY INCH OF POLAND",
        "FRI: 2 MISSILES AND A DRONE FELL IN POLAND AS 400+ DRONES "
        "AND 110+ MISSILES HIT UKRAINE. SAT: RUTTE IN WARSAW VOWED "
        "NATO WILL DEFEND EVERY INCH. 2 DRONES HIT THE RUSSIAN SHIP "
        "SPARTA II - 16 CREW EVACUATED AS IT BURNED INTO FINNISH "
        "WATERS.",
        ship_graphic)

    # Supporting strip.
    cv.text_centered(W // 2, 718, "ALSO IN THE NEWS", 3, INK)
    cv.hline(24, 746, W - 48, INK, 2)
    cols = [
        (24, RED, "WALL ST - FRI",
         "S&P 6,910.39 -3.7%. NASDAQ 22,617.73 -5.28% WIPES OUT ALL "
         "2026 GAINS. DOW 48,147.33 -1.93%. NVIDIA -14%."),
        (352, BLUE, "GTA 6 - FRI",
         "GTA 6 MAKES $3.79BN IN ONE DAY - THE BIGGEST ENTERTAINMENT "
         "LAUNCH EVER. 32.5M COPIES SOLD."),
        (680, GREEN, "G20 - SUNDAY",
         "G20 OPENS IN JOHANNESBURG - THE FIRST G20 IN AFRICA. "
         "THE US IS NOT ATTENDING."),
    ]
    for i, (cx0, accent, label, body) in enumerate(cols):
        if i:
            cv.vline(cx0 - 16, 760, 150, INK, 2)
        cv.text(cx0, 760, label, 3, accent)
        cv.hline(cx0, 788, 312, accent, 2)
        cv.wrapped(cx0, 802, body, 2, INK, 312, 3)

    # Footer.
    cv.hline(24, 936, W - 48, INK, 2)
    cv.text_centered(W // 2, 950, "SUNDAY 22 NOVEMBER 2026 - THE WORLD TODAY",
                     2, INK)
    return cv


def write_png(path, cv):
    raw = b"".join(
        b"\x00" + bytes(cv.buf[y * cv.w * 3:(y + 1) * cv.w * 3])
        for y in range(cv.h))

    def chunk(tag, data):
        out = struct.pack(">I", len(data)) + tag + data
        return out + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    ihdr = struct.pack(">IIBBBBB", cv.w, cv.h, 8, 2, 0, 0, 0)
    png = (b"\x89PNG\r\n\x1a\n"
           + chunk(b"IHDR", ihdr)
           + chunk(b"IDAT", zlib.compress(raw, 9))
           + chunk(b"IEND", b""))
    with open(path, "wb") as f:
        f.write(png)
    return len(png)


def main():
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, "entry.png")
    size = write_png(path, render())
    print("wrote %s (%d bytes)" % (path, size))


if __name__ == "__main__":
    main()
