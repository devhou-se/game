# Design: pagoda interior sprites in the house look (#335)

## Context

`gamev2/tools/generate_pagoda_art.py` draws the 31 `pagoda-in-*` sprites of the three pagoda rooms
(`PagodaMarket1`, `PagodaPark3`, `PagodaFukuoka1`). They are coherent with each other but not with the
GuttyKreum pack: their own RGB palette, a purple-black outline, gradients, and lit yellow on the lantern pane
and the candle flames. The ticket (part 6 of #293) asks for the palette, the outline and the lit yellow to be
fixed, **not new shapes**: every colour one the pack's sheets have, the outline the pack's navy, lamps the
pack's dim gold `c6a663`, keys, sizes and anchors unchanged.

This design was prototyped end to end on `origin/master` (the tool, the test and the 31 PNGs): 46 colours
over the 31 sprites, 45 of them on the sheets (the 46th is the room's void, below), `config.json` untouched,
`check_generators.py`, `test_game.js` and `play.js check` green. Before/after pictures are with the ticket.

## Approach

Follow the temple hall (#326, `generate_temple_art.py`): keep every drawing function and coordinate, replace
the palette block with pack hexes under the same constant names, and replace each colour computed in place
(a `mix()`, a literal tuple, a gradient) with a named pack colour or flat bands. Three choices differ from
the temple, each on purpose:

- **No `settle()` and no `mix()`.** After the changes below no blend is left (the temple's `settle()` would
  move 0 pixels), so `mix()` is deleted and the new unit test is the guard, not a silent snap.
- **`VOID` stays `(12, 12, 17)`**, which is not a pack colour. It is the colour of the room's own
  `office-void-autotile` tile, and ten pieces (`wall`, `wall-head`, `side`, `edge`, `base`, each `-w`/`-e`)
  are Floor tiles that paint it beside that tile. With a pack dark (`080d16`) a navy strip shows down both
  sides of every storey. Transparency is not an option (they replace the void tile on Floor) and moving them
  to another layer is map data. The test allows this one colour in those ten keys only. The pillar's floor
  gap is not beside the void, so it takes the pack dark.
- **The tool stays self-contained** (its own `rgb()`, RGB 3-tuples, `ImageDraw`), like the temple tool;
  `house_look.py` is not imported.

Reds are the pack's own red pagoda's (`red-pagoda-*`: `aa4d31`, `d16b56`, `e78d7b`), so the inside matches
the tower outside. The windows and the doorway show day and get no glow row, so at night they dim with the
room's tint like everything else; only the lantern and the candles glow, from their existing `Glows.SPRITES`
rows (checked at `?tod=night` on the prototype).

## Changes

### `gamev2/tools/generate_pagoda_art.py`

1. Replace the palette block (`INK` … `PINK, PINK_HI`, lines 48-67) with:

```python
def rgb(h):
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


# Every colour but VOID is one the GuttyKreum sheets use (art-source/GuttyKreum; pagodas.test.js checks it).
INK = rgb('1f1f3b')                      # the temple sheets' outline navy, as on the pagodas outside
VOID = (12, 12, 17)                      # office-void, the room's own tile: the dark round the tower (not a pack colour)
SHADE = rgb('080d16')                    # what a thing throws on the floor, with alpha; the dark under a floor
DAY, DAY_SH = rgb('e6d6cd'), rgb('d7d0ba')                                        # daylight at the door, and further out
WHITE, PAPER_SH = rgb('fafcfd'), rgb('be9e8c')
LAMP, LAMP_SH, LAMP_HI = rgb('c6a663'), rgb('a7843b'), rgb('f3d890')              # a pane: the pack's dim gold; its small core
FLAME, FLAME_HI = rgb('c6a663'), rgb('f3d890')
LQ, LQ_HI, LQ_DK = rgb('2a2636'), rgb('524b59'), rgb('171831')                    # black lacquer, deep shadow
VERM, VERM_HI, VERM_DK = rgb('d16b56'), rgb('e78d7b'), rgb('aa4d31')              # vermilion: the red pagodas' outside
WINE = rgb('5b283b')                                                              # the ground behind the thousand Buddhas
GOLD, GOLD_HI, GOLD_DK = rgb('c6a663'), rgb('e3c587'), rgb('a7843b')              # gilt
BOARD, BOARD_ALT, BOARD_HI, BOARD_DK = rgb('6d483b'), rgb('68422d'), rgb('85553e'), rgb('4d3326')
GRAIN = rgb('5a3827')
WOOD, WOOD_HI, WOOD_DK = rgb('5a3827'), rgb('7f513b'), rgb('3f210f')              # dark timber
CYP, CYP_HI, CYP_DK = rgb('c6aa71'), rgb('e3c587'), rgb('a7843b')                 # the pillar's bare cypress
CYP_GRAIN, CYP_FOOT = rgb('b2a168'), rgb('4d3326')
PLASTER, PLASTER_HI, PLASTER_SH = rgb('d7d0ba'), rgb('e6d6cd'), rgb('c2ac9e')
STONE, STONE_HI, STONE_DK = rgb('655d6d'), rgb('848295'), rgb('4c4754')
TILE, TILE_HI, TILE_DK = rgb('d16b56'), rgb('e78d7b'), rgb('aa4d31')              # roof tiles
BRASS, BRASS_HI, BRASS_DK = rgb('c6aa71'), rgb('e3c587'), rgb('86624c')
IRON, IRON_HI = rgb('3c3a4c'), rgb('5f6177')
SLAT, SLAT_HI = rgb('506b6b'), rgb('6c8e7f')                                      # a window's green slats
SKY, SKY_LO = rgb('bfd2db'), rgb('dae2e4')
FAR, FAR_DK, NEAR = rgb('848295'), rgb('5f6177'), rgb('8e7366')                   # the roofs through the window
PURPLE, PURPLE_DK = rgb('5c527d'), rgb('3f3651')
PINK, PINK_HI = rgb('bb6479'), rgb('ff9b92')
# a sutra chest: its wood, the light along its lid
CHESTS = ((rgb('85553e'), rgb('aa775f')), (rgb('71412a'), rgb('85553e')), (rgb('86624f'), rgb('b07c63')))
```

`GLOW` and `GLOW_HI` are gone. Delete `mix()`.

2. Colours computed in place (line numbers are the file's today; nothing else in these functions changes):

| Where | Now | Becomes |
|---|---|---|
| `shadow` (102) | `fill=(0, 0, 0, a)` | `fill=SHADE + (a,)` |
| `_boards` grain (135) | `mix(BOARD, BOARD_DK, 0.5)` | `GRAIN` |
| `_wall_head` (176), `wall_head_w` (242): rows 0-3, the dark under the floor above | `LQ_DK` | `SHADE` |
| `_edge` rows 13-31 (280) | `mix(WOOD_DK, LQ_DK, …)` gradient | `WOOD_DK if y < 17 else LQ if y < 22 else LQ_DK if y < 27 else SHADE` |
| `threshold` day (341) | `mix((236, 214, 170), (255, 248, 226), y / 31)` | `DAY_SH if y < 6 else DAY if y < 14 else WHITE` |
| `threshold` steps (343) | `(214, 190, 150)` | `PLASTER_SH` |
| `doorlight` (359) | `(255, 228, 170, round(12 + 44 * t))` | `DAY + (round(12 + 44 * t),)` |
| `_grain` (494) | `mix(CYP, CYP_DK, 0.45)` | `CYP_GRAIN` |
| `_shaft` (502) | the `mix(CYP, CYP_HI, 0.5)` column | delete the line |
| `_shaft` fade (505-508) | per-pixel `mix(pixel, LQ_DK, 0.7 * t)` over 10 rows | `for i, col in enumerate((WOOD_DK, WOOD, BRASS_DK)): d.rectangle([x0, y0 + 3 * i, x1, min(y1, y0 + 3 * i + 2)], fill=col)` (three flat steps, before the two `INK` side lines) |
| `pillar` gap (517) | `fill=VOID` | `fill=SHADE` |
| `pillar` foot (525) | `mix(CYP_DK, LQ_DK, 0.6)` | `CYP_FOOT` |
| `shumidan` bar (559) | `mix(GOLD_DK, INK, 0.4)` | `BRASS_DK` |
| `toro_hang` pane (634-636) | `box(…, GLOW_HI)` and the `mix(GLOW_HI, GLOW, …)` rows | `box(d, 9, 24, 22, 40, LAMP)`; `for y0 in (25, 37): d.rectangle([10, y0, 21, y0 + 2], fill=LAMP_SH)`; `d.rectangle([13, 29, 18, 35], fill=LAMP_HI)` (the bars are drawn over it as now) |
| `kyozo` (669, 671) | three literal chest colours; lid `mix(col, WHITE, 0.25)` | `col, hi = rnd.choice(CHESTS)`; lid `fill=hi` |
| `senbutsu` ground (691) | `(70, 24, 36)` | `WINE` |
| `senbutsu` figures (694, 697) | `rnd.choice((GOLD, GOLD, GOLD_HI, GOLD_DK))`; `mix(col, INK, 0.45)` | `col, sh = rnd.choice(((GOLD, GOLD_DK), (GOLD, GOLD_DK), (GOLD_HI, GOLD), (GOLD_DK, BRASS_DK)))`; `fill=sh` |
| `window` sky (717) | `mix(SKY, SKY_LO, …)` | `SKY if y < y0 + 12 else SKY_LO` |
| `window` roofs (718-720) | `(118, 132, 150)`, `(90, 102, 124)`, `(150, 104, 96)` | `FAR`, `FAR_DK`, `NEAR` |

Each `rnd.choice` keeps its one call per item, so the seeded scatter draws the same shapes. The flames
(`shokudai`, the two candles of `senbutsu`) need no edit: `FLAME`/`FLAME_HI` are now the dim gold and its core.

3. Docstring: after "pixel-doubled." add that the colours are the GuttyKreum sheets' only, the outline their
   navy, lamps the pack's dim gold with a small core and the night glow left to `Glows.js` (#335); `VOID` is
   the room's void tile.

`main()`, `sprites()`, `DEPTH_BIAS`, `LOOK_UP`, sizes and anchors are untouched.

### Regenerated (run `python3 tools/generate_pagoda_art.py` from `gamev2/`)

The 31 `gamev2/assets/sprites/pagoda-in-*_0_0.png`. `config.json` must come out byte-identical; if it does
not, a key, size or anchor moved and that is a bug.

### `gamev2/tools/tests/pagodas.test.js`

Add one test, modelled on `temple.test.js`' "the hall is drawn in the GuttyKreum pack's colours" (name the
file walker something other than `walk`, which this file already has):

- pack = every fully opaque colour of every PNG under `art-source/GuttyKreum`, less `000000` and `ffffff`;
- exactly 31 `pagoda-in-*` keys in `spriteMetadata`;
- every non-clear pixel of each sprite is a pack colour, or is `0c0c11` in a key matching
  `/^pagoda-in-(wall|wall-head|side|edge|base)-[we]_0_0$/`; `0c0c11` is in
  `assets/sprites/office-void-autotile_center.png` and not in the pack; a key has `0c0c11` if and only if it
  matches;
- no lit yellow: a pixel with `r >= 0xf3 && g >= 0xd0 && b < 0xc8` is `f3d890`;
- `f3d890` is at most 8% of a sprite's non-clear pixels (prototype: lantern 5.0%, candle 3.1%);
- `pagoda-in-toro-hang_0_0` and `pagoda-in-shokudai_0_0` have `f3d890`, and more `c6a663` than it;
- `1f1f3b` is in at least 25 sprites (prototype: 28).

### `gamev2/docs/landmarks-and-towns.md`

The pagoda **Art** bullet (line 1835): say the sprites are in the GuttyKreum sheets' colours only with the
navy outline `1f1f3b`, flat bands and no blends, the lantern and candles the dim gold `c6a663` with a small
`f3d890` core and the night glow left to `Glows.js`, and that the ten corner and side pieces carry the void
tile's `0c0c11` so they meet it with no seam (#335; `pagodas.test.js`).

### Not changed

`src/utils/Glows.js` (the two rows stay), `tools/generate_pagodas.py`, `config.json`, `tiled/`,
`devhouse.world`, the world map (interiors are not on it), `check_generators.py`.

## Data and interfaces

None. Same 31 keys, pixel sizes, `spriteMetadata` and `tileNames`. No map data is touched; the three pagoda
rooms look different.

## Tests

From `gamev2/`:

```bash
python3 tools/generate_pagoda_art.py --preview /tmp/before.png   # before editing, for the comparison
python3 tools/generate_pagoda_art.py && git status --short        # only the tool and 31 PNGs
python3 tools/generate_pagoda_art.py && git status --short        # a second run changes nothing
node tools/test_game.js
python3 tools/test_blog_to_npc.py
node tools/play.js check
python3 tools/check_generators.py      # no DRIFT
python3 tools/sync_cities.py --check
```

Look at: the `--preview` sheet before and after; `node tools/play.js render PagodaMarket1 out.png` (and
`PagodaFukuoka1`) before and after, checking that no strip of a different dark shows beside the storeys.
In a browser, desktop and a landscape phone (`?notitle=1&nointro=1`, `rm.switchRoomInstant('PagodaFukuoka1',
9, 25)` and a top-storey cell such as `10, 8`): by day, and at `?tod=night` that the window and the doorway
are dim and only the lantern and the candles glow. Then the browser regression
(`tools/browser/README.md`; `REGRESS_TIME_SCALE=2` in a Workshop container).

## Risks and open questions

- **Taste.** The palette is a judgement: plaster is the pack's cream (`d7d0ba`) rather than the pink-white
  of the pack's pagoda walls (`e4cecc`), which read as pink over this much wall; the reds are paler than
  today's because the pack's are. If a colour looks wrong in the before/after, swap it for another sheet
  colour; the test holds any swap to the sheets.
- **`VOID` is not a pack colour**, by design (above). The void tile itself is shared by every interior and is
  not this ticket's.
- **#331** (pagoda outdoor sprites, "every key not `pagoda-in-*`") has no keys: this tool draws only
  `pagoda-in-*`. `pagoda-in-roof` and the eaves are recoloured here; their shape (a front elevation) is left
  alone, as the ticket says no new shapes.
- This branch is 28 commits behind `master`, but every file named here, the source art and the void tile are
  the same on both, so nothing here depends on the newer commits.
