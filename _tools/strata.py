"""Generate the footer's top border: the ground under the hero's street.

Writes assets/home/strata.png, a seamless tile that repeats along the top
edge of the footer. Its first rows dither out of the page colour, its last
rows dither into the footer ink, so the page reads as a cut through the
ground: street on top (hero), subgrade at the bottom (footer).

    page   ..............   paper
    sand   .:.:.:.:.:.:.:   dither in, lit top, speckles
    gravel oOo.oO.Oo.oOoo   pebbles
    clay   ==============   streaks
    ink    :.:.:.:.:.:.:.   dither out, footer colour

Run from the repo root: python3 _tools/strata.py
"""

import random

from PIL import Image

OUT = 'assets/home/strata.png'

# Page background above the footer and the footer background itself.
PAPER = (0xF5, 0xF8, 0xFB, 255)
INK = (0x0E, 0x22, 0x36, 255)

STRATA_W = 32
STRATA_H = 24

# Same seed every run, so the tile only changes when this file does.
SEED = 7

# Share of sand pixels speckled with grit, and of gravel pixels that start a pebble.
SPECKLE = 0.12
PEBBLE = 0.35


def rgb(hex_code):
    return tuple(int(hex_code[i:i + 2], 16) for i in (1, 3, 5)) + (255,)


SAND_HI = rgb('#F0D2B0')
SAND = rgb('#E5B98C')
GRIT = rgb('#C69769')
EDGE = rgb('#5A4636')
GRAVEL = rgb('#7D8FA6')
PEBBLE_HI = rgb('#B9C8D8')
PEBBLE_LO = rgb('#4A6178')
CLAY = rgb('#33485C')
STREAK = rgb('#26405A')


def strata_row(y, x, rng):
    """Colour of one pixel, top to bottom:

        0-1    sand dithers out of the page (mirror of the street's last rows)
        2      sand, lit top
        3-6    sand with grit speckles
        7      outline
        8-12   gravel bed (pebbles drawn on top later)
        13     outline
        14-19  clay, streak every other row offset
        20-21  clay dithers into the footer ink
        22-23  ink
    """
    if y == 0:
        return SAND if x % 4 == 1 else PAPER
    if y == 1:
        return SAND if x % 2 == 0 else PAPER
    if y == 2:
        return SAND_HI
    if y <= 6:
        return GRIT if rng.random() < SPECKLE else SAND
    if y in (7, 13):
        return EDGE
    if y <= 12:
        return GRAVEL
    if y <= 19:
        return STREAK if y % 2 == 0 and (x + y) % 6 < 3 else CLAY
    if y == 20:
        return INK if x % 2 == 0 else CLAY
    if y == 21:
        return CLAY if x % 4 == 3 else INK
    return INK


def pebbles(img, rng):
    """Two-pixel pebbles across the gravel bed: lit left, shaded right.
    Wraps at the tile edge so the repeat stays seamless."""
    for y in range(8, 13):
        for x in range(0, STRATA_W, 2):
            if rng.random() >= PEBBLE:
                continue

            shift = rng.randint(0, 1)
            img.putpixel(((x + shift) % STRATA_W, y), PEBBLE_HI)
            img.putpixel(((x + shift + 1) % STRATA_W, y), PEBBLE_LO)


def render():
    rng = random.Random(SEED)
    img = Image.new('RGBA', (STRATA_W, STRATA_H))

    for y in range(STRATA_H):
        for x in range(STRATA_W):
            img.putpixel((x, y), strata_row(y, x, rng))

    pebbles(img, rng)
    return img


def main():
    render().save(OUT)


if __name__ == '__main__':
    main()
