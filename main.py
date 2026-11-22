#!/usr/bin/env python3
"""Render a newspaper front page summing up world news on Sunday 22 Nov 2026.

One 1024x1024 PNG, Pillow only, fully deterministic: no randomness, no
timestamps, no network, fixed fonts and positions, so repeated runs produce
byte-identical output.

Usage:  python3 main.py
Output: entry.png in $MAKEFUN_OUTPUT_DIR if set, else ./output/entry.png
"""

import math
import os

from PIL import Image, ImageDraw, ImageFont

W, H = 1024, 1024
BG = (255, 255, 255)
INK = (17, 17, 17)
GREY = (90, 90, 90)
RED = (178, 34, 34)
BLUE = (30, 70, 140)
LIGHT = (238, 238, 238)

FONT_DIR = "/usr/share/fonts/truetype/dejavu"


def load_font(name, size):
    """Load a DejaVu font; fall back to Pillow's default bitmap font."""
    path = os.path.join(FONT_DIR, name)
    try:
        return ImageFont.truetype(path, size)
    except (OSError, IOError):
        return ImageFont.load_default()


def serif_bold(size):
    return load_font("DejaVuSerif-Bold.ttf", size)


def sans(size):
    return load_font("DejaVuSans.ttf", size)


def sans_bold(size):
    return load_font("DejaVuSans-Bold.ttf", size)


def wrap(draw, text, font, max_width):
    """Greedy word wrap; returns a list of lines that fit max_width."""
    words = text.split()
    lines, current = [], ""
    for word in words:
        trial = (current + " " + word).strip()
        if draw.textlength(trial, font=font) <= max_width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def draw_centered(draw, cx, y, text, font, fill=INK):
    """Draw text centered on cx; returns the y just below the text."""
    width = draw.textlength(text, font=font)
    draw.text((cx - width / 2, y), text, font=font, fill=fill)
    return y + font.size + 4


def draw_wrapped(draw, x, y, text, font, max_width, fill=INK, leading=6):
    """Draw wrapped text starting at (x, y); returns y below the last line."""
    for line in wrap(draw, text, font, max_width):
        draw.text((x, y), line, font=font, fill=fill)
        y += font.size + leading
    return y


def draw_thermometer(draw, x, y, w, h):
    """Simple thermometer graphic: bulb + tube, mercury rising high."""
    tube_w = 26
    bulb_r = 34
    cx = x + w // 2
    tube_top = y + 10
    tube_bottom = y + h - bulb_r - 6
    # Tube outline.
    draw.rounded_rectangle(
        [cx - tube_w // 2, tube_top, cx + tube_w // 2, tube_bottom + 10],
        radius=13, outline=INK, width=3, fill=(255, 255, 255),
    )
    # Mercury column (filled to near the top: the 1.5C goal is missed).
    mercury_top = tube_top + 14
    draw.rectangle(
        [cx - tube_w // 2 + 5, mercury_top, cx + tube_w // 2 - 5, tube_bottom + 6],
        fill=RED,
    )
    # Bulb.
    draw.ellipse(
        [cx - bulb_r, tube_bottom - 6, cx + bulb_r, tube_bottom - 6 + 2 * bulb_r],
        outline=INK, width=3, fill=RED,
    )
    # Tick marks beside the tube.
    for i in range(5):
        ty = tube_top + 12 + i * ((tube_bottom - tube_top - 24) // 4)
        draw.line([cx + tube_w // 2 + 6, ty, cx + tube_w // 2 + 18, ty],
                  fill=INK, width=2)
    # "1.5C" label under the bulb.
    label = "1.5C"
    font = sans_bold(22)
    draw.text((cx - draw.textlength(label, font=font) / 2,
               tube_bottom + 2 * bulb_r + 4),
              label, font=font, fill=RED)


def draw_starburst(draw, cx, cy, r_outer, r_inner, spikes=12, fill=(255, 180, 0)):
    """Jagged starburst (missile impact flash)."""
    points = []
    for i in range(spikes * 2):
        angle = math.pi * i / spikes - math.pi / 2
        r = r_outer if i % 2 == 0 else r_inner
        points.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
    draw.polygon(points, fill=fill, outline=INK)


def draw_ship(draw, x, y, w, h):
    """Small cargo ship with flames above its deck."""
    hull_top = y + h // 2
    # Hull.
    draw.polygon(
        [(x, hull_top), (x + w, hull_top), (x + w - 18, hull_top + 34),
         (x + 18, hull_top + 34)],
        fill=BLUE, outline=INK,
    )
    # Containers.
    draw.rectangle([x + 22, hull_top - 26, x + 58, hull_top - 2],
                   fill=(200, 60, 60), outline=INK)
    draw.rectangle([x + 64, hull_top - 26, x + 100, hull_top - 2],
                   fill=(60, 160, 90), outline=INK)
    # Bridge.
    draw.rectangle([x + w - 46, hull_top - 44, x + w - 12, hull_top - 2],
                   fill=(240, 240, 240), outline=INK)
    # Flames.
    flame_cx = x + 40
    draw_starburst(draw, flame_cx, hull_top - 46, 26, 12, spikes=8,
                   fill=(255, 120, 0))
    draw_starburst(draw, flame_cx + 34, hull_top - 40, 20, 9, spikes=8,
                   fill=(255, 200, 0))
    # Water line.
    draw.line([x - 6, hull_top + 44, x + w + 6, hull_top + 44],
              fill=BLUE, width=3)


def render():
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)

    # ---- Masthead -------------------------------------------------------
    draw_centered(draw, W // 2, 18, "THE WORLD TODAY", serif_bold(80))
    draw_centered(draw, W // 2, 128, "SUNDAY 22 NOVEMBER 2026", sans_bold(30))
    draw.line([40, 178, W - 40, 178], fill=INK, width=4)
    draw.line([40, 186, W - 40, 186], fill=INK, width=2)

    # ---- Main stories: two panels --------------------------------------
    panel_y = 206
    panel_h = 470
    left = (36, 36 + 456)
    right = (532, 532 + 456)

    for (px0, px1) in (left, right):
        draw.rectangle([px0, panel_y, px1, panel_y + panel_h],
                       outline=INK, width=2)

    # ---- Panel 1: COP31 -------------------------------------------------
    x0, x1 = left
    inner = x0 + 18
    inner_w = x1 - x0 - 36
    y = panel_y + 14
    y = draw_wrapped(draw, inner, y, "COP31  •  ANTALYA, TURKEY",
                     sans_bold(20), inner_w, fill=RED)
    y += 6
    y = draw_wrapped(draw, inner, y, "COP31 CLOSE TO DEAL EXPECTED SUNDAY",
                     serif_bold(40), inner_w, fill=INK, leading=4)
    y += 8
    y = draw_wrapped(draw, inner, y,
                     "~200 countries in Antalya, Turkey  •  1.5C goal "
                     "declared missed  •  USD 120bn adaptation target dropped",
                     sans(20), inner_w, fill=GREY, leading=4)
    draw_thermometer(draw, inner, y + 4, inner_w, 120)

    # ---- Panel 2: Poland + Baltic ---------------------------------------
    x0, x1 = right
    inner = x0 + 18
    inner_w = x1 - x0 - 36
    y = panel_y + 14
    y = draw_wrapped(draw, inner, y, "WAR IN EUROPE  •  NATO",
                     sans_bold(20), inner_w, fill=RED)
    y += 6
    y = draw_wrapped(draw, inner, y, "MISSILES IN POLAND, SHIP ABLAZE IN BALTIC",
                     serif_bold(38), inner_w, fill=INK, leading=4)
    y += 8
    y = draw_wrapped(draw, inner, y,
                     '2 missiles + 1 drone down in Poland, Fri 20 Nov  •  '
                     'NATO: "every inch" defended  •  Russian cargo ship '
                     "Sparta II hit by 2 drones, 16 crew evacuated",
                     sans(20), inner_w, fill=GREY, leading=4)
    draw_starburst(draw, inner + 70, y + 52, 44, 20, fill=(255, 180, 0))
    draw_ship(draw, inner + 150, y + 4, 240, 110)

    # ---- Bottom strip: three short items --------------------------------
    strip_y = panel_y + panel_h + 22
    strip_h = H - strip_y - 52
    col_w = (W - 72 - 2 * 16) // 3
    items = [
        ("WALL STREET CRASH", "FRI",
         "Nasdaq -5.3%, S&P in correction, Nvidia -14%",
         "S&P -3.7%, Dow -1.9% — 7th straight losing session"),
        ("GTA 6", "FRI",
         "$3.79bn day one — biggest entertainment launch ever",
         "32.5m units sold pre-release, a record"),
        ("G20 OPENS", "SUN",
         "Johannesburg, first in Africa, no US at the table",
         "22–23 Nov, hosted by President Ramaphosa"),
    ]
    for i, (title, tag, body, detail) in enumerate(items):
        cx0 = 36 + i * (col_w + 16)
        cx1 = cx0 + col_w
        draw.rectangle([cx0, strip_y, cx1, strip_y + strip_h],
                       outline=INK, width=2, fill=LIGHT)
        y = strip_y + 12
        # Day tag, top right of the column.
        tag_font = sans_bold(20)
        tag_w = draw.textlength(tag, font=tag_font)
        draw.text((cx1 - 14 - tag_w, y), tag, font=tag_font, fill=RED)
        y = draw_wrapped(draw, cx0 + 14, y, title, sans_bold(26),
                         col_w - 28 - tag_w - 8, fill=INK, leading=2)
        y += 6
        y = draw_wrapped(draw, cx0 + 14, y, body, sans(22),
                         col_w - 28, fill=INK, leading=4)
        y += 4
        draw_wrapped(draw, cx0 + 14, y, detail, sans(19),
                     col_w - 28, fill=GREY, leading=4)

    # ---- Sources footer ---------------------------------------------------
    draw_centered(draw, W // 2, H - 34,
                  "Sources: Reuters  •  AP  •  BBC  •  CNBC  •  Take-Two",
                  sans(18), fill=GREY)

    return img


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR") or os.path.join(".", "output")
    os.makedirs(out_dir, exist_ok=True)
    img = render()
    img.save(os.path.join(out_dir, "entry.png"), format="PNG")


if __name__ == "__main__":
    main()
