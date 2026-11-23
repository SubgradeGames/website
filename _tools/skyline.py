"""Generate the hero skyline: three seamless parallax layers per time of day,
with translucent cloud bands between them.

Writes assets/home/city-{day,dusk,night}-{1,2,3}.png (1 = far, 3 = near)
and assets/home/cloud-{day,dusk,night}-{1,2}.png (1 = behind mid, 2 = behind near),
plus assets/home/street-{day,dusk,night}.png, the strip the city stands on.
Each tile wraps horizontally; buildings crossing the right edge reappear on
the left. Same seed per layer, so day/dusk/night share one geometry.

    far   ..|..|||.|...||..   tall, hazy, sparse lights
    cloud     ~~~    ~~~~~
    mid   .||.|#|..||.|T|..   crane (T) and setbacks
    cloud   ~~~~~     ~~~
    near  |||.||||.|||.|||.   short, dark, brightest lights

Run from the repo root: python3 _tools/skyline.py
"""

import random
from dataclasses import dataclass
from enum import Enum

from PIL import Image

OUT = 'assets/home/city-{sky}-{layer}.png'
CLOUD_OUT = 'assets/home/cloud-{sky}-{layer}.png'
STREET_OUT = 'assets/home/street-{sky}.png'

# Page background below the hero; the street's bottom dither fades into it.
PAPER = (0xF5, 0xF8, 0xFB, 255)
STREET_W = 32

# Rows of solid ground under every layer, hidden below the hero edge so the
# pointer parallax never lifts a gap into view.
GROUND = 4


class Roof(Enum):
    FLAT = 'flat'
    SETBACK = 'setback'
    ANTENNA = 'antenna'
    SPIRE = 'spire'
    CRANE = 'crane'


@dataclass
class Layer:
    index: int
    width: int
    height: int
    min_w: int
    max_w: int
    min_h: int
    max_h: int
    seed: int


@dataclass
class Palette:
    body: tuple
    edge: tuple
    dark: tuple
    lit: tuple
    lit_odds: float
    beacon: tuple | None


LAYERS = [
    Layer(1, 160, 48 + GROUND, 6, 14, 16, 44, 11),
    Layer(2, 192, 34 + GROUND, 7, 16, 10, 30, 23),
    Layer(3, 224, 20 + GROUND, 8, 18, 6, 16, 37),
]


@dataclass
class CloudBand:
    index: int
    width: int
    height: int
    count: int
    seed: int


@dataclass
class CloudPalette:
    top: tuple
    body: tuple
    shade: tuple


# Wider than the city tiles so cloud and building repeats rarely line up.
CLOUD_BANDS = [
    CloudBand(1, 256, 24, 5, 51),
    CloudBand(2, 288, 18, 5, 67),
]


def rgb(hex_code, alpha=255):
    return tuple(int(hex_code[i:i + 2], 16) for i in (1, 3, 5)) + (alpha,)


# Clouds are partly see-through: buildings behind them show as haze.
# Example: day body alpha 90 of 255, about 35% opaque.
CLOUD_PALETTES = {
    'day': CloudPalette(rgb('#FFFFFF', 130), rgb('#F2F8FF', 90), rgb('#BFDDF8', 70)),
    'dusk': CloudPalette(rgb('#F2A98F', 120), rgb('#A882C0', 85), rgb('#6E5A9E', 65)),
    'night': CloudPalette(rgb('#6075B5', 110), rgb('#40528C', 80), rgb('#2C3C72', 60)),
}


# Far layers sit closer to the sky colour (haze); near layers darkest.
PALETTES = {
    'day': [
        Palette(rgb('#4FA6F2'), rgb('#6DB7F6'), rgb('#3F98EA'), rgb('#7FC0F7'), 0.0, None),
        Palette(rgb('#1F6CC7'), rgb('#3A86DA'), rgb('#1A5DAF'), rgb('#5FA0FF'), 0.0, None),
        Palette(rgb('#123F86'), rgb('#22579F'), rgb('#0E3472'), rgb('#2F5BE0'), 0.0, None),
    ],
    'dusk': [
        Palette(rgb('#4A3F8A'), rgb('#5E519E'), rgb('#40367C'), rgb('#C99A6E'), 0.12, rgb('#E86A6A')),
        Palette(rgb('#221F55'), rgb('#332D6E'), rgb('#1C1A4A'), rgb('#E5B98C'), 0.22, rgb('#FF5A5A')),
        Palette(rgb('#14133A'), rgb('#211F52'), rgb('#100F30'), rgb('#FFC46B'), 0.3, rgb('#FF5A5A')),
    ],
    'night': [
        Palette(rgb('#1A2858'), rgb('#22336A'), rgb('#16234D'), rgb('#B8955A'), 0.25, rgb('#C84848')),
        Palette(rgb('#16234F'), rgb('#1F2F66'), rgb('#121D45'), rgb('#E8BE6E'), 0.32, rgb('#FF5A5A')),
        Palette(rgb('#0A1130'), rgb('#141E48'), rgb('#080E28'), rgb('#FFD27A'), 0.4, rgb('#FF5A5A')),
    ],
}


def plan(layer):
    """Lay buildings left to right until the tile is full. Returns dicts."""
    rng = random.Random(layer.seed)
    buildings = []
    x = 0
    crane_done = layer.index != 2

    while x < layer.width:
        w = rng.randint(layer.min_w, layer.max_w)
        h = rng.randint(layer.min_h, layer.max_h)
        roof = rng.choice([Roof.FLAT, Roof.FLAT, Roof.SETBACK, Roof.ANTENNA, Roof.SPIRE])

        # One crane per tile on the mid layer: the city is still being built.
        if not crane_done and x > layer.width // 3:
            roof = Roof.CRANE
            crane_done = True

        buildings.append({'x': x, 'w': w, 'h': h, 'roof': roof, 'seed': rng.random()})
        x += w + rng.choice([0, 0, 1, 2])

    return buildings


def put(img, x, y, colour):
    """Set one art pixel, wrapping x so the tile repeats seamlessly."""
    w, h = img.size
    if y < 0 or y >= h:
        return
    img.putpixel((x % w, y), colour)


def block(img, x, top, w, bottom, pal):
    """Building body: lit left edge, dark right edge."""
    for col in range(w):
        colour = pal.edge if col == 0 else pal.dark if col == w - 1 else pal.body
        for y in range(top, bottom):
            put(img, x + col, y, colour)


def windows(img, x, top, w, bottom, pal, rng):
    """Window grid: one pixel per window, every 2nd column, every 3rd row."""
    for y in range(top + 2, bottom - GROUND - 1, 3):
        for col in range(2, w - 2, 2):
            lit = rng.random() < pal.lit_odds
            put(img, x + col, y, pal.lit if lit else pal.edge)


def crane(img, x, top, w, pal):
    """Tower crane on an unfinished roof: mast, jib, counter-jib, hook."""
    mast = x + w // 2
    peak = max(top - 16, 0)

    for y in range(peak, top):
        put(img, mast, y, pal.edge)
        put(img, mast + 1, y, pal.dark if y % 2 else pal.edge)

    for col in range(-6, 14):
        put(img, mast + col, peak + 1, pal.edge)

    for col in range(-6, -2):
        put(img, mast + col, peak + 2, pal.dark)

    for y in range(peak + 2, peak + 8):
        put(img, mast + 11, y, pal.dark)

    put(img, mast + 11, peak + 8, pal.edge)
    put(img, mast + 12, peak + 8, pal.edge)

    if pal.beacon:
        put(img, mast, peak - 1, pal.beacon)


def roof(img, b, top, pal):
    """Rooftop detail above the body."""
    x, w = b['x'], b['w']
    kind = b['roof']

    if kind == Roof.SETBACK:
        inset = max(w // 4, 1)
        block(img, x + inset, top - 4, w - 2 * inset, top, pal)
        return

    if kind == Roof.ANTENNA:
        mast = x + w // 2
        for y in range(top - 6, top):
            put(img, mast, y, pal.edge)
        if pal.beacon:
            put(img, mast, top - 7, pal.beacon)
        return

    # Tiered crown: up to 3 tiers, 2 rows each, 1 pixel narrower per side,
    # topped with a needle. Example (w=8): ..||.. / .||||. / ||||||
    if kind == Roof.SPIRE:
        tiers = min(3, (w - 2) // 2)
        for tier in range(tiers):
            inset = tier + 1
            block(img, x + inset, top - 2 * (tier + 1), w - 2 * inset, top - 2 * tier, pal)
        needle = x + w // 2
        crown = top - 2 * tiers
        for y in range(crown - 4, crown):
            put(img, needle, y, pal.edge)
        return

    if kind == Roof.CRANE:
        crane(img, x, top, w, pal)


def render(layer, pal):
    img = Image.new('RGBA', (layer.width, layer.height), (0, 0, 0, 0))

    for b in plan(layer):
        rng = random.Random(b['seed'])
        top = layer.height - GROUND - b['h']
        block(img, b['x'], top, b['w'], layer.height, pal)
        windows(img, b['x'], top, b['w'], layer.height, pal, rng)
        roof(img, b, top, pal)

    # Ground strip under the whole tile.
    for x in range(layer.width):
        for y in range(layer.height - GROUND, layer.height):
            put(img, x, y, pal.dark)

    return img


def cloud_mask(band):
    """Pixels covered by clouds. Each cloud is a row of overlapping puffs
    (circles) cut flat at a shared base. Example: ( )( )(  ) -> one cloud."""
    rng = random.Random(band.seed)
    mask = set()
    step = band.width // band.count

    for n in range(band.count):
        x = n * step + rng.randint(0, step // 3)
        base = band.height - 1 - rng.randint(0, 3)
        puffs = rng.randint(2, 4)

        for _ in range(puffs):
            r = rng.randint(4, 9)
            cx = x + r
            cy = base - rng.randint(0, 2)
            x += r + rng.randint(0, 2)

            for dy in range(-r, 1):
                for dx in range(-r, r + 1):
                    if dx * dx + dy * dy > r * r:
                        continue
                    if cy + dy < 0 or cy + dy > base:
                        continue
                    mask.add(((cx + dx) % band.width, cy + dy))

    return mask


def render_cloud(band, pal):
    """Top edge lit, bottom two rows shaded, body in between."""
    img = Image.new('RGBA', (band.width, band.height), (0, 0, 0, 0))
    mask = cloud_mask(band)

    for x, y in mask:
        if (x, y - 1) not in mask:
            colour = pal.top
        elif (x, y + 2) not in mask:
            colour = pal.shade
        else:
            colour = pal.body
        img.putpixel((x, y), colour)

    return img


@dataclass
class StreetPalette:
    outline: tuple
    walk_hi: tuple
    walk: tuple
    seam: tuple
    curb_hi: tuple
    curb: tuple
    lane: tuple
    lane_line: tuple
    road: tuple
    yellow: tuple


STREET_PALETTES = {
    'day': StreetPalette(rgb('#0B1440'), rgb('#DCE6F0'), rgb('#B9C8D8'), rgb('#8EA2B8'),
                         rgb('#E7EFF7'), rgb('#7D8FA6'), rgb('#4BAA5E'), rgb('#E7EFF7'),
                         rgb('#2B3550'), rgb('#F2C94C')),
    'dusk': StreetPalette(rgb('#0B1440'), rgb('#8E86B4'), rgb('#6F6896'), rgb('#514A7A'),
                          rgb('#A59CC8'), rgb('#4A4475'), rgb('#3E7A5A'), rgb('#A59CC8'),
                          rgb('#1C1A3A'), rgb('#D9B04A')),
    'night': StreetPalette(rgb('#0B1440'), rgb('#4A5788'), rgb('#36426F'), rgb('#26315A'),
                           rgb('#56649A'), rgb('#232D55'), rgb('#24553F'), rgb('#56649A'),
                           rgb('#0E1430'), rgb('#B8955A')),
}

STREET_H = 25


def street_row(pal, y, x):
    """Colour of one street pixel, top to bottom:

        0      outline
        1-4    sidewalk (lit top row, slab seam every 8 px)
        5-6    curb (lit top, shaded face)
        7      gutter outline
        8-12   bike lane, green paint
        13     lane edge line
        14-18  road lane
        19-21  double yellow centre line (yellow, road, yellow)
        22     road
        23-24  road dithers into the page
    """
    if y in (0, 7):
        return pal.outline
    if y == 1:
        return pal.walk_hi
    if y <= 4:
        return pal.seam if x % 8 == 7 else pal.walk
    if y == 5:
        return pal.curb_hi
    if y == 6:
        return pal.curb
    if y <= 12:
        return pal.lane
    if y == 13:
        return pal.lane_line
    if y in (19, 21):
        return pal.yellow
    if y <= 22:
        return pal.road
    if y == 23:
        return pal.road if x % 2 == 0 else PAPER
    return pal.road if x % 4 == 1 else PAPER


def render_street(pal):
    img = Image.new('RGBA', (STREET_W, STREET_H))
    for y in range(STREET_H):
        for x in range(STREET_W):
            img.putpixel((x, y), street_row(pal, y, x))
    return img


def main():
    for sky, pal in STREET_PALETTES.items():
        render_street(pal).save(STREET_OUT.format(sky=sky))

    for sky, palettes in PALETTES.items():
        for layer, pal in zip(LAYERS, palettes):
            render(layer, pal).save(OUT.format(sky=sky, layer=layer.index))

    for sky, pal in CLOUD_PALETTES.items():
        for band in CLOUD_BANDS:
            render_cloud(band, pal).save(CLOUD_OUT.format(sky=sky, layer=band.index))


if __name__ == '__main__':
    main()
