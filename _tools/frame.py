"""Draws assets/home/frame-twinstick.png, the pixel border around the
Twinstick Arcade card in the catalogue.

The sprite is a 9-slice for CSS border-image: 8 px corners, 16 px edge
segments that tile, transparent centre.

    +--------+----------------+--------+
    | corner |  edge (tiles)  | corner |   8 px
    +--------+----------------+--------+
    |  edge  |  transparent   |  edge  |  16 px
    +--------+----------------+--------+
    | corner |  edge (tiles)  | corner |   8 px
    +--------+----------------+--------+

Run from the repo root: python3 _tools/frame.py
"""

from PIL import Image

OUT = 'assets/home/frame-twinstick.png'

SLICE = 8
SEGMENT = 16
SIZE = 2 * SLICE + SEGMENT

# Twinstick Arcade greens, matching the --ta-* custom properties in css/home.css.
DARK = (0x0F, 0x38, 0x0F, 255)
MID = (0x30, 0x62, 0x30, 255)
EDGE = (0x5E, 0x88, 0x1F, 255)
LIT = (0x8B, 0xAC, 0x0F, 255)
GLOW = (0xC4, 0xE3, 0x3A, 255)
CLEAR = (0, 0, 0, 0)

# Marquee lights along each edge: 2 px lit every 8 px, on rings 3-4.
LIGHT_PERIOD = 8
LIGHT_ON = (3, 4)
LIGHT_RINGS = (3, 4)

# Corner bolt: a 4x4 square, outlined, at 2-5 px into each corner.
BOLT_LO = 2
BOLT_HI = 5


def ring_colour(depth, lit_side):
    """Colour of one ring, outside in:

        0    outline
        1    bevel (lit top/left, shaded bottom/right)
        2-5  frame body
        6    inner bevel
        7    inner outline against the card
    """
    if depth in (0, 7):
        return DARK
    if depth == 1:
        return LIT if lit_side else EDGE
    if depth == 6:
        return EDGE
    return MID


def bolt(cx, cy):
    """Colour of a corner pixel if it is part of the bolt, else None."""
    if not (BOLT_LO <= cx <= BOLT_HI and BOLT_LO <= cy <= BOLT_HI):
        return None
    if cx in (BOLT_LO, BOLT_HI) or cy in (BOLT_LO, BOLT_HI):
        return DARK
    return GLOW


def pixel(x, y):
    far_x = SIZE - 1 - x
    far_y = SIZE - 1 - y
    depth = min(x, y, far_x, far_y)

    # Centre stays clear so the card shows through.
    if depth >= SLICE:
        return CLEAR

    # Corners get a bolt over the mitred rings.
    in_corner_x = x < SLICE or far_x < SLICE
    in_corner_y = y < SLICE or far_y < SLICE
    if in_corner_x and in_corner_y:
        found = bolt(min(x, far_x), min(y, far_y))
        if found:
            return found

    # Along-edge coordinate, so lights run the length of every side.
    along = x if depth in (y, far_y) else y
    edge_seg = SLICE <= along < SLICE + SEGMENT
    light = (along - SLICE) % LIGHT_PERIOD in LIGHT_ON
    if edge_seg and depth in LIGHT_RINGS and light:
        return GLOW

    return ring_colour(depth, depth in (x, y))


def main():
    img = Image.new('RGBA', (SIZE, SIZE))
    for y in range(SIZE):
        for x in range(SIZE):
            img.putpixel((x, y), pixel(x, y))
    img.save(OUT)


if __name__ == '__main__':
    main()
