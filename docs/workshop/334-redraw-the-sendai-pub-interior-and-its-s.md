# Design: the Sendai pub interior and its shared frame in the house look (#334, part 5 of 7 of #295)

## Context

`gamev2/tools/generate_pub_art.py` draws the 21 `pub-in-*` sprites of `PubSendai1` and exports the frame
(`wall_side`, `wall_front`, `threshold`, `doorlight`), the helpers and the colour constants that five other
art tools import: `generate_distillery_art.py`, `generate_mall_art.py`, `generate_tower_deck_art.py`,
`generate_wheel_art.py` and `generate_flinders_art.py`. None of its colours is a GuttyKreum colour: the
outline is `INK=(38,43,68)`, shadows are black, the lamps and the daylight at the door are lit yellow
(`GLOW`, `GLOW_HI`, `(255,236,176)`), the back bar is a pale mirror, bottle highlights are made with `mix()`.

Outcome: the same 21 keys at the same sizes, anchors and depth bias, in the same shapes, with every pixel a
colour the GuttyKreum sheets use, outlines in the pack's navy, dark glass behind the bottles, and nothing
lit (a lamp is `c6a663`; night light stays in `src/utils/Glows.js`). The exported names keep their names
and take the same pack values, and the rooms that import them are regenerated. No map, config or placement
change.

A design-stage prototype settled the values below (images on the ticket: `334-pub-before-after.png`,
`334-pub-sprites-before-after.png`, `334-pub-browser-day/-night-before-after.png`,
`334-frame-<Room>-before-after.png` for the four other rooms). It is not in the repository; this document
is what it drew. With it applied, all 21 PNGs hold 46 colours, all in the sheets, `config.json` is
byte-identical, `node tools/test_game.js` and `python3 tools/check_generators.py` pass.

## Approach

**Substitute colours in place; change no shape.** Replace the palette block with pack hexes under the same
names, replace every inline RGB literal with a named pack colour, and remove the three things that cannot
be a pack colour by construction: the black shadow, the two gradients at the door, and `mix()` on bottles.
`ImageDraw` does not anti-alias, so no clean-up pass is needed.

**Change the exported constants' values, and regenerate the importers in the same commit.** The ticket and
#337 both expect this ("it must run after the pub part has changed those constants on master"). The
alternative, pub-only names with the exports frozen at their old values, leaves the shared frame non-pack
and every importer's ticket to undo it. The importers' pictures move a little and in the right direction
(navy outlines, dim-gold lamps, the new door light: see the four `334-frame-*` images); their own colours
remain their tickets' work (#337, #315, #321, #296; #309 for Flinders).

**Do not use #279's `house_look.py`** (not on master; the ticket owner says it is not needed) and do not
edit any importer's source.

## Changes

### `gamev2/tools/generate_pub_art.py`

1. **Palette block** (replaces lines 45-61, `INK` to `BOTTLES`). Names used by importers are unchanged.

```python
def rgb(h):
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


# Every colour is one the GuttyKreum sheets use (art-source/GuttyKreum; pub.test.js holds the pub to it).
INK = rgb('172459')                      # the pack's navy: every outline
VOID = rgb('080d16')
SHADE = rgb('2a3151')                    # what a thing throws on the floor, with alpha
WHITE, CREAM, CREAM_SH = rgb('fafcfd'), rgb('e4cecc'), rgb('d7b6ab')
DAY = (WHITE, rgb('ffe2e0'), CREAM)      # daylight at a door, palest first
GLOW, GLOW_HI = rgb('c6a663'), rgb('f3d890')                          # a lamp: the pack's dim gold, its core
WOOD, WOOD_HI, WOOD_DK = rgb('71412a'), rgb('85553e'), rgb('4d3326')  # mahogany
TOP, TOP_HI, TOP_DK = rgb('85553e'), rgb('b07c63'), rgb('68422d')     # a polished counter top
BOARD, BOARD_ALT, BOARD_HI, BOARD_DK = rgb('4d3326'), rgb('5a3827'), rgb('68422d'), rgb('2a2636')
GREEN, GREEN_HI, GREEN_DK = rgb('395050'), rgb('4a6262'), rgb('2e4040')   # the wallpaper
GREEN_GLINT = rgb('6c8e7f')
BRASS, BRASS_HI, BRASS_DK = rgb('c6a663'), rgb('f3d890'), rgb('a7843b')
LEATHER, LEATHER_HI, LEATHER_DK = rgb('aa4d31'), rgb('d16b56'), rgb('8a3a22')
STEEL, STEEL_HI, STEEL_DK = rgb('a4b0b5'), rgb('d1e2eb'), rgb('656e92')
MIRROR, MIRROR_HI = rgb('2c2d51'), rgb('4b6396')    # the back bar's glass: dark, a slanted glare
BEER, BEER_DK, FOAM = rgb('c6a663'), rgb('a7843b'), rgb('fafcfd')
SLATE, SLATE_HI = rgb('2e4040'), rgb('4a6262')
BLACK, BLACK_HI = rgb('1b1e2a'), rgb('47485d')
GRASS, GRASS_HI, DIRT, DIRT_DK = rgb('678e57'), rgb('83af6f'), rgb('b07c63'), rgb('86624f')
RED, LEAF, BLUE, BLUE_DK, ORANGE, PINK = rgb('d16b56'), rgb('508582'), rgb('4b6396'), rgb('314b8e'), rgb('ce6a42'), rgb('bb6479')
MAT, MAT_HI, ICE, SKY, SKIN = rgb('2a2636'), rgb('47485d'), rgb('d1e2eb'), rgb('bbe9ff'), rgb('f6a583')
# a bottle: its glass, the light down its side, its label
BOTTLES = [(LEAF, rgb('93c297'), CREAM), (GLOW, GLOW_HI, WHITE), (rgb('904a37'), RED, CREAM), (BLUE, rgb('588cc6'), CREAM),
           (CREAM, WHITE, CREAM_SH), (rgb('7f513b'), rgb('aa775f'), CREAM), (PINK, rgb('d78bc1'), CREAM)]
```

2. **Helpers.**
   - `shadow(d, x0, y0, x1, y1, a=90)` fills `SHADE + (a,)` (was black, 70). The pub's own four calls
     (stool, table, chair, chalkboard: drop their `70`/`60` argument) use the default.
   - `bottle(d, x, foot, h, col, hi=None, label=None)`: first line
     `hi, label = hi or mix(col, WHITE, 0.45), label or mix(col, CREAM, 0.7)`, then draw with `hi` and
     `label`. The distillery's four-argument calls keep working unchanged; the pub passes all three.
   - `new`, `box`, `text`, `latin`, `mix`, `bar`, `post`, `pint`, `register`: unchanged.

3. **Frame** (shapes and cells unchanged; `wall_side` and `wall_front` need no edit).
   - `threshold`: replace the 32-line gradient with three flat bands:
     `d.rectangle([0, 0, 31, 31], fill=DAY[0])`, `d.rectangle([0, 0, 31, 3], fill=DAY[2])`,
     `d.rectangle([0, 4, 31, 9], fill=DAY[1])`.
   - `doorlight`: replace the per-row alpha gradient with four flat steps of `CREAM` (the steps #309 uses):
     `for y0, y1, inset, a in ((28, 47, 9, 28), (48, 67, 6, 56), (68, 83, 3, 84), (84, 95, 0, 112)):`
     `d.rectangle([inset, y0, 63 - inset, y1], fill=CREAM + (a,))`.

4. **Inline literals in the pub's sprites** (every remaining `(r, g, b)` tuple and `mix()` in a sprite
   function; after this, no colour literal and no `mix()` is left below the frame section):

   | Sprite | Was | Becomes |
   |---|---|---|
   | wall-print | sky, field, hill, tree literals | `SKY`, `GRASS_HI`, `GREEN_GLINT`, `LEAF` |
   | wall-backbar | `rnd.choice(BOTTLES)` | `*rnd.choice(BOTTLES)` |
   | wall-backbar optics | `col = BOTTLES[...]`, two `mix()` | `col, hi, label = BOTTLES[...]`; use `hi`, `label` |
   | wall-tv | frame highlight and score-box outline `(70,74,96)` | `BLACK_HI` |
   | wall-tv | outfield wall; crowd colours; the line under the crowd | `BLUE_DK`; `(RED, CREAM, GLOW, rgb('588cc6'))`; `GLOW` |
   | wall-tv | skin; fielders' caps and the score mark `(150,30,50)` | `SKIN`; `LEATHER_DK` |
   | wall-tv | batter and runner `(60,70,130), (40,50,100)` | `BLUE, BLUE_DK` |
   | wall-tv | the glass line `mix(GRASS, WHITE, .5)`; the power light | `rgb('93c297')` both |
   | wall-darts | red and green rings, bull; the three darts | `RED`, `GRASS`; `RED`, `BRASS`, `BLUE` |
   | bar | mat and its dots; ice | `MAT`, `MAT_HI`; `ICE` |
   | bar | tap handles `(red, CREAM, green)` and `(col, orange, navy)` | `(RED, CREAM, GRASS)`, `(col, ORANGE, BLUE_DK)` |
   | bar | till display; nuts; towel | `rgb('93c297')`; `DIRT`; `RED` |
   | table | crisps packet | `BLUE` |
   | booth | table shadow `(0,0,0,60)` | `SHADE + (90,)` |
   | chalkboard | pink chalk | `rgb('ff9b92')` |
   | lamp-hang | shade glint `(120,170,130)` | `GREEN_GLINT` |
   | lamp-hang | bulb `fill=GLOW_HI, outline=GLOW` | `d.ellipse([10, 46, 21, 52], fill=GLOW, outline=BRASS_DK)` then `d.rectangle([13, 48, 16, 49], fill=GLOW_HI)` |

5. **Docstring**: say the sprites are in the house look (pack colours, navy outline, nothing lit), and
   correct the list of importers to the five tools above (it names two).

### Regenerated art (no hand edits)

From `gamev2/`, in this order (the wheel tool imports the tower deck's):

```bash
python3 tools/generate_pub_art.py
python3 tools/generate_distillery_art.py
python3 tools/generate_mall_art.py
python3 tools/generate_tower_deck_art.py
python3 tools/generate_wheel_art.py
python3 tools/generate_flinders_art.py
```

Commit exactly what these rewrite. On today's master that is, under `assets/sprites/`: all 21 `pub-in-*`;
15 `distillery-in-*`; 15 `mall-in-*`; 18 `deck-in-*`; 12 `flinders-in-*`; and six ride pictures
(`view-dotonbori-far`, `-near`, `view-fukuoka-far`, `-near`, `view-gondola`, `view-lift`). `config.json`,
`tiled/`, `assets/map` and `devhouse.world` must come out unchanged (`git status` shows only those PNGs
and the files below); anything else changed is a mistake to find, not to commit. If master has moved and
an importer no longer takes the constants (#309 makes Flinders import only `C, new, text, latin,
register`), that tool rewrites nothing and nothing of its is committed.

### `gamev2/tools/tests/pub.test.js`

Add one test, "the pub is drawn in the house look: pack colours only, navy outlines, dark glass behind the
bottles, nothing lit, at the sizes the room places it by (#334)", decoding each
`assets/sprites/pub-in-<piece>_0_0.png` with `tools/png` (as `konbini.test.js` does):

- Sizes in px: `bar` 448x128; `booth`, `doorlight`, `wall-darts` 128x192; `wall-backbar` 448x192;
  `wall-tv` 256x192; `wall-panel`, `wall-print` 64x192; `chalkboard`, `lamp-hang` 64x128; `table` 128x64;
  `floor-a`, `floor-b`, `side-w`, `side-e`, `wall-front`, `threshold-w`, `threshold-e`, `stool`,
  `chair-w`, `chair-e` 64x64.
- Every pixel with alpha > 0 has its RGB in this set (the tool's palette, as `flinders.test.js` does in
  #309): `080d16 172459 1b1e2a 2a2636 2a3151 2c2d51 2e4040 314b8e 395050 47485d 4a6262 4b6396 4d3326 508582
  588cc6 5a3827 656e92 678e57 68422d 6c8e7f 71412a 7f513b 83af6f 85553e 8a3a22 904a37 93c297 a4b0b5 a7843b
  aa4d31 aa775f b07c63 bb6479 bbe9ff c6a663 ce6a42 d16b56 d1e2eb d78bc1 d7b6ab e4cecc f3d890 f6a583 fafcfd
  ff9b92 ffe2e0`.
- A pixel with 0 < alpha < 255 is `2a3151` at 90 (a shadow), except in `doorlight`, which is only `e4cecc`
  at 28, 56, 84 or 112 and has no opaque pixel.
- Every sprite but `floor-a`, `floor-b` and `doorlight` has `172459` pixels.
- `wall-backbar` has more than 10000 px of `2c2d51` and some `4b6396`.
- `lamp-hang` has `c6a663` and fewer `f3d890` than `c6a663` (208 and 32 in the prototype).

### `gamev2/docs/landmarks-and-towns.md`

"The Sendai pub", the **Art** bullet: add that the sprites are in the house look (pack colours, navy
outline, unlit lamps in `c6a663`, held by `pub.test.js`), that the exported constants are pack colours, and
name all five importing tools in place of "the distillery's and Canal City's".

## Data and interfaces

None. No key, size, anchor, depth bias, door cell, palette index, map or config change. Python interface:
`bottle` gains two optional arguments; `shadow`'s default alpha is 90; new names `rgb`, `SHADE`, `DAY`,
`GREEN_GLINT`, `BLACK_HI`, `RED`, `LEAF`, `BLUE`, `BLUE_DK`, `ORANGE`, `PINK`, `MAT`, `MAT_HI`, `ICE`,
`SKY`, `SKIN`; `BOTTLES` holds triples. No map data is touched; rooms that look different: `PubSendai1`,
`DistillerySendai1`, `MallFukuoka1`, `DeckFukuoka1`, `FlindersSanFranbourne1`, and the lift and wheel rides.

## Tests

From `gamev2/`:

```bash
node tools/test_game.js
python3 tools/test_blog_to_npc.py
node tools/play.js check
python3 tools/check_generators.py     # no DRIFT; generate_ads and extract_city are skip (no macOS font)
python3 tools/sync_cities.py --check
```

- Before editing, render each of the five rooms (`node tools/play.js render <Room> out.png`) and
  `python3 tools/generate_pub_art.py --preview`, outside the repository; render again after; look at each
  pair and attach them (`/work/media/`).
- Browser regression `tools/browser/regress.js` (`tools/browser/README.md`; `REGRESS_TIME_SCALE=2` in the
  container). `playwright-core` 1.65.1 on `NODE_PATH` found no Chromium of its version here; the global
  `playwright` did. Run `npx playwright install chromium` once if the launch fails.
- Play it: walk into the pub from Sendai on desktop and a phone size, by day and with `?tod=night`; look at
  screenshots. At night the lamp, back bar and screen glows come from `Glows.js` (rows unchanged) and no
  sprite pixel is lit. Look at the distillery and the tower deck at night too (their lamps use `GLOW`).
- Commit as `gamev2: <what changed> (#295)`, one commit: tool, regenerated PNGs, test, doc.

## Risks and open questions

- **PNG conflicts with sibling branches.** #309 (merge stage) replaces every `flinders-in-*`; #315 (mall)
  and #321 (tower deck) are in design; #296 will redraw the wheel. Whichever lands second conflicts on
  binary PNGs. The fix is mechanical: take the merged tools and rerun the six commands above. If #309 is
  on the branch's base when implementing, Flinders does not drift at all.
- **The importers are half-converted until their tickets**: navy outlines and pack lamps beside their own
  non-pack colours. Looked at in all four rooms; nothing reads wrong. #337 can start once this is merged.
- **Taste calls made in the prototype**, cheap to change in the palette block: the floor is darker than
  before (`4d3326`/`5a3827`; `5a3827`/`68422d` blended with the furniture, `55423b`/`594b45` read grey);
  the leather is the brick red of the pub's outside (`aa4d31`: the pack has no crimson); the back bar is
  dark glass, not a pale mirror; the door light is cream steps (white read grey on dark boards; Flinders'
  own, in #309, is white on pale terrazzo).
- `Glows.js` calls the back bar's glass "mirrors" in a comment; left alone.
