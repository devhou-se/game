# Design: the konbini interior kit in the house look (#340, part 7 of 7 of #295)

## Context

`gamev2/tools/generate_konbini_art.py` draws the 26 `konbini-*` sprites that furnish the 14 `Konbini*`
rooms (#221). It imports its colours from `generate_station_art.py` and adds its own; none of the 47
colours it puts on screen is a GuttyKreum colour except by accident. The outline is the station's
`INK=(38,43,68)`, the clerk is outlined in black, and four things are lit yellow: the strip under the
fascia, the steamer, the hot-snack case (`WARM=(255,232,170)`) and every price label (`YELLOW`). The
cooler that stands beside the chillers (`office-fridge_0_0`, #313) and the store on the street
(`seven-eleven_0_0`) are already in the house look, so today the kit does not match either.

Outcome: the same 26 keys, sizes, anchors, shapes and seeded stock, with every pixel a colour the
GuttyKreum sheets use, outlines in the pack's navy, dark glass, nothing lit, and the three stripes and the
7 in the street store's colours. No map, config, room or placement change.

A design-stage prototype settled the values below (images on the ticket: `340-design-kit-before-after.png`,
`340-design-KonbiniMarket3-before-after.png`, `340-design-KonbiniSapporo1-before-after.png`,
`340-design-browser-night.png`). It is not in the repository; this document is what it drew. With it
applied the 26 PNGs hold 42 colours, all in the sheets; `config.json` is byte-identical;
`konbini.test.js` (with the new case) and `check_generators.py` pass; a konbini at `?tod=night` is
pixel-identical to `?tod=day`.

## Approach

**Substitute colours in place; change no shape** (the ticket: "the palette, the outline and removing lit
yellow, not new shapes"; the same method as the pub, #334). Every drawing call, coordinate, seed and the
`SPRITES` table stay. `ImageDraw` does not anti-alias, so `ellipse`, `polygon` and `arc` stay too.

**The kit owns its palette.** It stops importing colours from `generate_station_art.py` and defines them
itself under the same names, importing only plumbing (`C`, `new`, `text`, `latin`). The station file is
not edited (it is #327's), and whichever of #327 and this lands first, neither moves the other's pixels.
`box` is redefined locally because the station's has its own `INK` bound as the default outline.

**Match the neighbours.** Outline `172459` and the white and steel of the cooler; the stripes
`e78d7b` / `508582` / `aa4d31` that `konbini.test.js` pins on the street store. `0a1627` replaces black for
the clerk (the cast's dark outline) and the machines' bays.

**Nothing lit.** Gold is the pack's unlit `c6a663`, with `e3c587` (the cooler's `GOLD_HI`) as the inside of
the two warmers and the trim line; `f3d890` is not used. Glass is the look's dark `2c2d51` with the
slanted `4b6396` glare.

All five `konbini-front*` / `konbini-side-*` sprites are recoloured here: #298 has not landed.

## Changes

### 1. `gamev2/tools/generate_konbini_art.py`

Replace the `from generate_station_art import (...)` statement and the palette block (lines 43-56) with:

```python
from generate_station_art import C, new, text, latin
from house_look import rgb

# The palette: every colour one the GuttyKreum sheets use (docs/generators-and-checks.md, "House look"),
# the stripes, whites and steel those of the store on the street and the cooler beside the chillers
# (tools/generate_seven_eleven_art.py, tools/generate_cooler_art.py). Nothing is lit: gold is the pack's unlit gold.
INK, NIGHT = rgb('172459'), rgb('0a1627')                    # the pack's navy, every outline; its ink, the clerk's
WHITE, OFFWHITE = rgb('fafcfd'), rgb('dae2e4')
STEEL_LIGHT, STEEL, STEEL_DARK = rgb('bfd2db'), rgb('94a2a8'), rgb('575c6d')
SLATE, SLATE_DARK = rgb('5b6c79'), rgb('444f5e')
CREAM, CREAM_SHADE = rgb('e6d6cd'), rgb('d2bab0')
ORANGE, ORANGE_DARK = rgb('e78d7b'), rgb('d16b56')          # the three stripes, as on the street
GREEN, GREEN_DARK, GREEN_DEEP = rgb('508582'), rgb('4a6262'), rgb('395050')
RED, RED_DARK = rgb('aa4d31'), rgb('8a3a22')
GOLD_LIGHT, GOLD = rgb('e3c587'), rgb('c6a663')
BLUE, BLUE_DARK, CYAN = rgb('425faa'), rgb('314b8e'), rgb('7db9fa')
LED_GREEN = rgb('93c297')
VINYL_A, VINYL_B, VINYL_JOINT, VINYL_LIGHT = rgb('e1e9eb'), rgb('dae2e4'), rgb('bcc7cc'), rgb('fafcfd')
GLASS, GLASS_DARK, GLARE, GLARE_LIGHT = rgb('2c2d51'), rgb('2a3151'), rgb('4b6396'), rgb('8689a6')
DARK, SHADOW = rgb('1f1f3b'), rgb('47485d')
BREAD, BREAD_DARK, BREAD_LIGHT = rgb('bb8971'), rgb('85553e'), rgb('ebbca2')
BROWN, BROWN_DARK, TAN = rgb('68422d'), rgb('4d3326'), rgb('be9e8c')
PINK, PURPLE, LEAF = rgb('bb6479'), rgb('8f72b6'), rgb('83af6f')
SKIN, HAIR, MOUTH = rgb('ebbca2'), rgb('4d3326'), rgb('d16b56')
BASKET, BASKET_LIGHT, BASKET_DARK = rgb('ce6a42'), rgb('f6a583'), rgb('aa4d31')
STOCK = [RED, GOLD, CYAN, GREEN, ORANGE, BLUE, PINK, PURPLE, LEAF, WHITE]


def box(d, x0, y0, x1, y1, fill, outline=INK):
    """A filled rectangle with the navy outline; corners inclusive."""
    d.rectangle([x0, y0, x1, y1], fill=fill, outline=outline)
```

(`house_look.rgb` returns `(r, g, b, 255)`. The station's `YELLOW_DARK`, imported but never used, is
dropped; `YELLOW`, `WARM`, `WARM_DARK`, `LIT`, `BLACK` and `TEAL` no longer exist.)

Then, in the body, only these edits. Every other line is unchanged and takes its new colour by name.

| Old | New | Where |
|---|---|---|
| `WARM_DARK` | `GOLD` | the hot-snack case's two lines |
| `WARM` | `GOLD_LIGHT` | `paint_wall` row 26, the steamer's inside, the hot-snack case's inside, the chiller's line at y 9 |
| `YELLOW` | `GOLD` | every use (prices, labels, packs, tubs, covers, coin box, food, the `not in (YELLOW, WHITE)` tests) |
| `LIT` | `OFFWHITE` | the chiller's inside; the white umbrella, in `umbrella()` and on the `daily` gondola's top |
| `fill=WHITE` / `fill=LIT` | `fill=GLARE_LIGHT` / `fill=GLARE` | `freezer()` only: the two slanted lines of "the light on the glass" |
| `BLACK` | `NIGHT` | `CLERK_INK['A']` |
| `TEAL` | `LEAF` | `magazines()` `covers` (and `STOCK`, above) |
| `(64, 94, 58)` | `GREEN_DEEP` | the mat's ribs |
| `(196, 160, 96)` | `TAN` | `wall_tobacco()` `packs` |
| `(16, 18, 30)` | `NIGHT` | the bays in `coffee()` and `water()` |
| `fill=(RED)` | `fill=RED` | `coffee()` |
| `ORANGE`, `ORANGE_DARK`, `(240, 150, 100)` | `BASKET`, `BASKET_DARK`, `BASKET_LIGHT` | `baskets()` only (five lines) |
| `SLATE + (255,)` | `SLATE` | the `--preview` sheet in `main()` |

Docstring: replace "in the station interior's palette and with its helpers
(tools/generate_station_art.py)" with: in the house look (docs/generators-and-checks.md, "House look:
GuttyKreum") — its own palette of sheet colours, the pack's navy outline, dark glass, nothing lit — on the
station interior's canvas and text helpers (tools/generate_station_art.py). In `chiller()`'s docstring and
comment drop "lit" / "and its light"; in `clerk()`'s, "black outline" becomes "dark outline"; in
`paint_wall()`'s, "a lit strip" becomes "a gold trim".

`SPRITES`, `main()` (apart from the preview line), `CLERK`, `GOODS`, the seeds and all coordinates are
untouched.

### 2. Regenerated art

From `gamev2/`: `python3 tools/generate_konbini_art.py`. It must change exactly the 26
`assets/sprites/konbini-*_0_0.png` and leave `config.json` byte-identical (`git status` shows nothing else).
No room generator, `config_to_tiled.py` or `make_worldmap.py` run is needed: no key, size or placement
changes and interiors are not on the world map (the prototype's `check_generators.py` was all `ok`).

### 3. `gamev2/tools/tests/konbini.test.js`

Add one case after the kit's size/anchor case (which stays as it is, as does the #89 street-store case):
`'the konbini kit is drawn in the house look: its own pack palette, the navy outline, doubled pixels, nothing lit, the store's three stripes (#340)'`.

- `PALETTE`, the 42 hexes: `172459 0a1627 fafcfd dae2e4 e1e9eb bcc7cc bfd2db 94a2a8 575c6d 444f5e e6d6cd
  d2bab0 e78d7b d16b56 508582 4a6262 395050 aa4d31 8a3a22 e3c587 c6a663 425faa 314b8e 7db9fa 93c297 2c2d51
  2a3151 4b6396 8689a6 1f1f3b 47485d bb8971 85553e ebbca2 68422d 4d3326 be9e8c bb6479 8f72b6 83af6f ce6a42
  f6a583`.
- Every `PALETTE` colour is an opaque colour of a PNG under `art-source/GuttyKreum` (not `preview*`): the
  walker of `izakaya.test.js` / `house-look.test.js`.
- For each of the 26 kit sprites (the file's `kit` list): every 2x2 block from even coordinates is one
  value; alpha is 0 or 255; no opaque colour outside `PALETTE`.
- Over the whole kit every `PALETTE` colour is used (so the list cannot rot), and `f3d890`, `ffffff`,
  `000000` are not.
- Pixel (0,0) of `konbini-wall`, `-chiller-a`, `-gondola-snacks`, `-freezer` and pixel (127,0) of
  `-counter-w` is `172459`.
- `konbini-wall`, `-wall-clock`, `-wall-tobacco`, `-counter-w`, `-counter-e` and `-atm` each contain
  `e78d7b`, `508582` and `aa4d31`.

The case must fail on master's sprites (it does: `konbini-atm_0_0: colours outside the kit's palette`).

### 4. Docs

- `gamev2/docs/generators-and-checks.md`, the `tools/generate_konbini_art.py` paragraph (line 363): add
  that it is drawn in the house look with its own palette of sheet colours (navy outline, dark glass, gold
  only as the unlit `c6a663` / `e3c587`), takes only its canvas and text helpers from
  `generate_station_art.py`, and that `konbini.test.js` holds it to that palette.
- `gamev2/docs/landmarks-and-towns.md` line 848: after "(procedural, needs Pillow, in
  `check_generators.py`" add ", in the house look".

## Data and interfaces

None. `config.json` (`spriteMetadata`, `tileNames`, `tilePalette`, rooms), `tiled/`, `devhouse.world`,
`generate_konbinis.py`, `generate_station_art.py`, `Interactions.js` and `Glows.js` are unchanged. No rooms
are rebuilt. The tool gains an import of `tools/house_look.py` and loses its dependence on the station
tool's colours.

## Tests

From `gamev2/`:

```bash
python3 tools/generate_konbini_art.py --preview /tmp/kit.png   # same 26 keys and sizes printed
node tools/test_game.js
python3 tools/test_blog_to_npc.py
node tools/play.js check
python3 tools/check_generators.py      # no DRIFT
python3 tools/sync_cities.py --check
```

Look at, before and after: `node tools/play.js render KonbiniMarket3 out.png` (four coolers, three
chillers, ATM, three gondolas) and `KonbiniSapporo1` (freezer, copier, coffee, the mirrored counter); the
kit must sit with the cooler with no seam in outline or steel.

Browser (`tools/browser/README.md`; `REGRESS_TIME_SCALE=2` in the container): run `regress.js` (its
`konbini-enter` / `-shop` / `-exit` checks need no change) and look at `regress_konbini.png`. Then play one
store on desktop and at 390x844 with touch, at `?tod=day` and `?tod=night`: inside, the two must look the
same (interiors are not graded and `Glows.js` has no `konbini-*` entry) with no lit pixel; outside, the
street store's door at night is unchanged.

Commit: `gamev2: <what changed> (#340)`, as the sibling parts were landed under their own ticket numbers
(the ticket text says `(#295)`, the parent).

## Risks and open questions

- **Taste calls the owner may want changed, each a one-line edit of the palette block** (and of the test's
  list): the counter and cabinet tops in `e6d6cd` (the pack's `e4cecc` cream read pink beside the white
  wall; `e6d6cd` is a rare sheet colour); the warmers' inside in `e3c587` (unlit, but the palest gold
  here: `c6a663` is the stricter choice); screens in `7db9fa` / `93c297` (blue and green, not yellow);
  the floor in the cooler's cool whites `e1e9eb` / `dae2e4` instead of the old warm grey; the shopfront
  strip and the freezer lid as dark glass, where they were pale blue.
- **#298** redraws the five `konbini-front*` / `-side-*` sprites in this same file. Whichever lands second
  rebases the tool and reruns it; the PNG conflicts are resolved by the rerun.
- **#327** will change the station constants. After this change the kit no longer reads them, so the two
  are independent; if #327 renames `new`, `text` or `latin`, this import follows.
- **Pillow**: `ellipse`, `polygon`, `arc` and slanted `line` differ between Pillow versions; the pin in
  `tools/requirements-art.txt` (11.3.0, what the prototype used) is what `check_generators.py` holds.
- The branch was 28 commits behind `origin/master` when the design started and was fast-forwarded to it
  (`house_look.py` and the sibling redraws were missing); nothing else was merged.
