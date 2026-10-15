"""8x8 pixel-art icons for the Sense HAT LED matrix."""

from __future__ import annotations

Pixel = tuple[int, int, int]

_PALETTE: dict[str, Pixel] = {
    ".": (0, 0, 0),        # off
    "G": (90, 90, 90),     # machine body
    "D": (40, 40, 40),     # spout
    "L": (0, 200, 0),      # power LED
    "W": (220, 220, 220),  # cup
    "B": (110, 55, 15),    # coffee
    "S": (120, 120, 120),  # steam
    "R": (200, 0, 0),      # error
    "Y": (220, 170, 0),    # warning
}

TEXT_WHITE: Pixel = (200, 200, 200)
TEXT_COFFEE: Pixel = (230, 120, 30)
TEXT_RED: Pixel = _PALETTE["R"]
TEXT_YELLOW: Pixel = _PALETTE["Y"]


def _icon(*rows: str) -> list[Pixel]:
    if len(rows) != 8 or any(len(r) != 8 for r in rows):
        raise ValueError("An icon must be 8 rows of 8 characters")
    return [_PALETTE[c] for row in rows for c in row]


BLANK = _icon(*["........"] * 8)

_MACHINE_ROWS = (
    "GGGGGGGG",
    "GLGGGGGG",
    "GGGDDGGG",
    "G..DD..G",
    "G.WWWW.G",
    "G.WWWW.G",
    "G..WW..G",
    "GGGGGGGG",
)
MACHINE = _icon(*_MACHINE_ROWS)
MACHINE_LED_OFF = _icon(*(row.replace("L", "G") for row in _MACHINE_ROWS))

_CUP_ROWS = (
    ".WWWWW..",
    ".WBBBWW.",
    ".WBBBW.W",
    "..WWW.W.",
)
CUP_STEAM_1 = _icon(
    "..S..S..",
    ".S..S...",
    "..S..S..",
    "........",
    *_CUP_ROWS,
)
CUP_STEAM_2 = _icon(
    ".S..S...",
    "..S..S..",
    ".S..S...",
    "........",
    *_CUP_ROWS,
)

ERROR = _icon(
    "R......R",
    ".R....R.",
    "..R..R..",
    "...RR...",
    "...RR...",
    "..R..R..",
    ".R....R.",
    "R......R",
)

WARNING = _icon(
    "...YY...",
    "...YY...",
    "...YY...",
    "...YY...",
    "...YY...",
    "........",
    "...YY...",
    "...YY...",
)
