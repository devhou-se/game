# Sendai town art: the six ground families in the house look (#342)

## Context

`gamev2/tools/generate_sendai_town_art.py` draws six ground families, nine autotile roles each, as
`gamev2/assets/sprites/sendai-<family>-autotile_<role>.png` (54 files, 1x1 cell, 64px, layer `ground`):
plaza, jozenji, arcade-floor, samurai-lane, brick-yard, boardwalk. They were drawn before the house look
was written down ("House look: GuttyKreum" in `gamev2/docs/generators-and-checks.md` on `master`) and miss
it: none of their colours is one the GuttyKreum sheets use, slabs and kerbs are lit from no one side, and
kerbs are flat bands. This ticket redraws them; names, roles, sizes and the manifest's `tile_families`
entries do not change.

Facts found while designing:

- **No room uses the six families.** They are in no `config.json` palette, map or prefab (they wait for
  Sendai's rebuild, #219). Nothing a player sees changes, no map is re-seeded and the world map is not
  rebuilt. The "render of a room that uses each family" is the tool's own `--scenes` previews (station:
  plaza; downtown: arcade floor and jozenji; samurai: lane; distillery: brick yard; bay: boardwalk) and
  its `--sheet`.
- The tool reproduces every committed `sendai-*` PNG today (Pillow 11.3.0), so after the change exactly 54
  PNGs differ.
- `generate_sendai_town_art` is **not** in `check_generators.py`'s `ART_TOOLS`, so that check neither
  catches nor reports drift in these files: "no unexpected DRIFT" is shown by `git status` after a rerun.
- `generate_fukuoka_town_art.py` imports `family` from this tool (and is checked on `master`), and
  `red_bridge()` / `red_bridge_head()` (#345's pieces) read the block's `PLANK`.

## Approach

Replace the six texture functions, six kerb functions and their colour constants in the "Ground families"
block (from `PAVERS = ...` to just above `def ground(fam):`) with the block below, which was prototyped
against the real tool. Each family keeps its material, pattern and periods, so every `FAMILIES`
description stays true word for word. What changes, per the look:

- **Sheet colours only**, as named constants in the block (the worked example is Fukuoka's station plaza,
  `generate_fukuoka_town_art.py`). Sendai's own: cut grey stone for the kerbs (`dae2e4 bcc7cc a4b0b5`),
  gilt leaves (`f3d890 c6a663 a7843b`), verdigris moss (`506b6b`), the pack's paving creams and its red
  ramp for brick and russet, dark steel (`848295 5f6177 47485d`) for the lane's kerb stones.
- **Lit from the upper left**: each slab, paver, tile, brick and plank takes a light top row / left column
  and a darker bottom row / right column (`_lit`, or the same by hand where the piece is on a fixed grid).
- **No flat fill**: faces alternate tones by piece, with speckle or grain; the gravel is four rake rows
  (ridge, face, shadow, trough).
- **One dither edge**: every kerb is a lit lip, a jointed face and exactly one dithered row where its
  shadow falls on the floor. Dither is used nowhere else.

`_edge()`, `family()`, `ground()`, the kerb widths (4, 3, 4, 3, 3, 3), `STEPPING` / `stepping_stone`
(#333's) and `FAMILIES` are not touched. `house_look.py` is not imported: the block needs no ink outline
or ramp helper, and the tool already defines its colours as hex.

Prototype result (all colours on the sheets; share = the commonest colour's part of a tile):

| family | colours | share | reads |
|---|---|---|---|
| plaza | 12 | 0.23 | slabs in bands, clear |
| jozenji | 14 | 0.34 | pavers; pinker than the old tan (the pack has no tan stone) |
| arcade floor | 7 | 0.27 | **flattest**: polished tile is two near creams; look again |
| samurai lane | 8 | 0.29 | **still quiet** by design (raked gravel); rake lines now visible |
| brick yard | 12 | 0.33 | strong; matches the brick buildings |
| boardwalk | 8 | 0.39 | planks; now the pier's brown rather than tan |

The implementer starts from this block, looks at the renders and may retune tones or thresholds, but keeps
the rules above and the tests below. The summary must say which families still read as flat.

## Changes

### `gamev2/tools/generate_sendai_town_art.py`

Edit in place, keeping the order (jozenji, lane, `STEPPING` + `stepping_stone` between `lane_tex` and
`lane_kerb`, yard, board, plaza, arcade). Remove the old `PAVERS`, `YARD`, `PLAZA` and any other constant
only the old functions used; **keep the `PLANK = (...)` line exactly** (the red bridge reads it). `math`
and `h3` are already imported.

```python
# The six grounds in the house look (docs/generators-and-checks.md, "House look: GuttyKreum"): every
# colour is one the GuttyKreum sheets use, each slab, paver, tile, brick and plank is lit from the upper
# left, no face is one colour from edge to edge, and each kerb ends in one dithered row of its shadow.
GRANITE_HI, GRANITE, GRANITE_LO, GRANITE_JOINT = rgb('dae2e4'), rgb('bcc7cc'), rgb('a4b0b5'), rgb('949bb2')


def _lit(gap, x, y, face, hi, lo):
    """Light from the upper left on a jointed floor: a piece's top row and left column (the pixels
    just below or right of a joint) take `hi`, its bottom row and right column `lo`."""
    if gap(x + 1, y) or gap(x, y + 1):
        return lo
    if gap(x - 1, y) or gap(x, y - 1):
        return hi
    return face


def _stone_kerb(m, along, shadow):
    """A pale granite kerb, 4 wide: a lit lip, a face jointed every 16, its far edge, then one
    dithered row of shadow (`shadow` is the two tones of the floor it falls on)."""
    if m == 3:
        return shadow[along % 2]
    if m == 0:
        return GRANITE_HI
    if along % 16 == 15:
        return GRANITE_JOINT
    return GRANITE if m == 1 else GRANITE_LO


PAVERS = (rgb('c2ac9e'), rgb('b3aaa0'), rgb('c2ac9e'), rgb('be9e8c'))
PAVER_HI, PAVER_LO, PAVER_JOINT = rgb('d2bab0'), rgb('a68777'), rgb('8e7366')
LEAF, LEAF_HI, LEAF_RUS, LEAF_LO = rgb('c6a663'), rgb('f3d890'), rgb('ce6a42'), rgb('a7843b')


def _paver_gap(x, y):
    return y % 4 == 3 or (x + (y // 4 % 2) * 4) % 8 == 7


def jozenji_tex(x, y):
    """Warm stone pavers in running bond (8 x 4, period 32), each lit on its top row and left
    column, with keyaki leaves fallen on them in gilt and russet."""
    if _paver_gap(x, y):
        return PAVER_JOINT
    if h3(x, y, 31) < 5 or h3(x - 1, y, 31) < 5:
        return LEAF if h3(x, y, 2) % 3 else LEAF_HI               # keyaki leaves, fallen
    if h3(x, y, 47) < 4:
        return LEAF_RUS
    if h3(x, y, 53) < 2:
        return LEAF_LO
    j = y // 4
    u = x + (j % 2) * 4
    return _lit(_paver_gap, x, y, PAVERS[(u // 8 * 3 + j * 5) % 4], PAVER_HI, PAVER_LO)


def jozenji_kerb(m, along):
    return _stone_kerb(m, along, (PAVER_JOINT, PAVER_LO))


RAKE_HI, RAKE_LO = rgb('b0b5d7'), rgb('868da9')
GRAVEL, GRIT_HI, GRIT_LO = rgb('a2a3bd'), rgb('adb2c2'), rgb('949bb2')


def lane_tex(x, y):
    """Plain raked gravel: fine cool-grey grit, the rake's lines running with the lane in a slow
    wave (period 32, so cells join): a lit ridge, the face, its shadow, the trough."""
    k = h3(x, y, 17)
    rake = (y + round(1.5 * math.sin(x * math.pi / 16))) % 4
    if rake == 0:
        return GRIT_HI if k > 200 else RAKE_HI                    # the ridge, lit
    if rake == 2:
        return GRAVEL if k > 200 else RAKE_LO                     # its shadow
    if rake == 3:
        return GRIT_LO if k > 215 else GRIT_HI                    # the trough
    return GRIT_HI if k < 20 else (GRIT_LO if k > 232 else GRAVEL)


# STEPPING and stepping_stone() stay here, unchanged

KERB_DK = (rgb('848295'), rgb('5f6177'), rgb('47485d'))


def lane_kerb(m, along):
    """Dark kerb stones of uneven length: a lit top, a face, and one dithered row of shadow."""
    if m == 2:
        return KERB_DK[2] if along % 2 else RAKE_LO
    if along % 11 == 10:
        return KERB_DK[2]
    return KERB_DK[m]


YARD = (rgb('aa4d31'), rgb('904a37'), rgb('aa4d31'), rgb('8a3a22'))
YARD_HI, YARD_LO, YARD_JOINT = rgb('d16b56'), rgb('8a3a22'), rgb('5a3827')
SOOT_BRICK, SOOT_HI, MOSS = rgb('594b45'), rgb('6d574e'), rgb('506b6b')


def yard_tex(x, y):
    """Worn brick laid lengthwise north-south (4 x 8, columns staggered), the top of each brick lit."""
    col = x // 4
    v = y + (col % 2) * 4
    if x % 4 == 3 or v % 8 == 7:
        return MOSS if h3(x, y, 9) < 16 else YARD_JOINT           # moss in the joints
    if h3(col * 7 + 3, (v // 8) * 5 + col * 3, 12) < 7:
        return SOOT_HI if v % 8 == 0 else SOOT_BRICK              # a brick blackened by soot
    c = YARD[(col * 3 + (v // 8) * 5) % 4]
    if v % 8 == 0:
        return YARD_HI if c != YARD_LO else YARD[0]
    return c


def yard_kerb(m, along):
    return _stone_kerb(m, along, (YARD_JOINT, YARD_LO))


PLANK = (rgb('b08a68'), rgb('a57f5f'), rgb('ba9572'), rgb('ad8766'))    # the red bridge's planks (unchanged line)
BOARD = (rgb('b07c63'), rgb('aa775f'), rgb('bb8971'), rgb('b07c63'))
BOARD_HI, BOARD_LO, BOARD_GAP, BOARD_BUTT = rgb('c18e75'), rgb('85553e'), rgb('5a3827'), rgb('68422d')
BOARD_GRAIN, NAIL = rgb('86624f'), rgb('2a2636')


def board_tex(x, y):
    """Planks 8 wide running north-south, butt joints staggered by column, nailed at each end."""
    col = x // 8
    v = y + col * 13
    if x % 8 == 7:
        return BOARD_GAP
    if v % 32 == 31:
        return BOARD_BUTT
    if v % 32 in (2, 28) and x % 8 in (1, 5):
        return NAIL                                               # nail heads
    if x % 8 == 0 or v % 32 == 0:
        return BOARD_HI
    if x % 8 == 6:
        return BOARD_LO
    if h3(x, y // 3, 21) < 20:
        return BOARD_GRAIN                                        # the grain
    return BOARD[(col * 3 + v // 32) % 4]


def board_kerb(m, along):
    """The edge beam: a lit top, a face bolted every 8, one dithered row of its shadow."""
    if m == 1 and along % 8 == 4:
        return NAIL
    if m == 2:
        return BOARD_GAP if along % 2 else BOARD_BUTT
    return (BOARD[2], BOARD_LO)[m]


SLAB = (rgb('e6d6cd'), rgb('d2bab0'))
SLAB_HI, SLAB_LO, SLAB_JOINT = rgb('fafcfd'), rgb('c2ac9e'), rgb('ac9f96')
BAND = (rgb('c69f96'), rgb('bb8971'))
BAND_JOINT = rgb('a68777')


def plaza_tex(x, y):
    """The station plaza: big pale stone slabs (14 x 14, two tones) set in a grid of terracotta
    brick bands (a band down the west and along the north of every cell)."""
    x, y = x % 32, y % 32
    bx, by = x < 4, y < 4
    if bx or by:
        if bx and by:
            return BAND_JOINT if (x in (0, 3) or y in (0, 3)) else BAND[1]
        along, across = (y, x) if bx else (x, y)
        if across in (0, 3):
            return SLAB_JOINT
        if along % 8 == 7:
            return BAND_JOINT
        return BAND[0] if across == 1 else BAND[1]
    sx, sy = (x - 4) % 14, (y - 4) % 14
    if sx == 13 or sy == 13:
        return SLAB_JOINT
    if sx == 12 or sy == 12:
        return SLAB_LO
    if sx == 0 or sy == 0:
        return SLAB_HI
    k = h3(x, y, 23)
    return SLAB_LO if k < 8 else (SLAB_HI if k > 244 else SLAB[((x - 4) // 14 + (y - 4) // 14) % 2])


def plaza_kerb(m, along):
    if m == 2:
        return GRANITE_JOINT if along % 2 else SLAB_JOINT
    if m == 0:
        return GRANITE_HI
    return GRANITE_LO if along % 16 == 15 else GRANITE


TILE = (rgb('e4cecc'), rgb('e6d6cd'))
TILE_HI, TILE_JOINT = rgb('fafcfd'), rgb('d7b6ab')
RUSSET_HI, RUSSET, RUSSET_LO = rgb('d16b56'), rgb('aa4d31'), rgb('8a3a22')


def arcade_tex(x, y):
    """The arcade's floor: polished cream tiles (8 x 8) with a russet diamond at every second
    crossing and a long reflection of the roof's light."""
    tx, ty = x % 8, y % 8
    dx, dy = min(x % 16, 16 - x % 16), min(y % 16, 16 - y % 16)
    if dx + dy <= 2:
        if dx + dy < 2:
            return RUSSET
        return RUSSET_HI if (x + 8) % 16 + (y + 8) % 16 <= 16 else RUSSET_LO
    if tx == 0 or ty == 0:
        return TILE_JOINT
    if tx == 1 or ty == 1:
        return TILE_HI
    if (x % 32) in (12, 13) and ty not in (2, 7):
        return TILE_HI                                            # the skylight, mirrored in the polish
    return TILE[(x // 8 + y // 8) % 2]


def arcade_kerb(m, along):
    if m == 2:
        return RUSSET_LO if along % 2 else TILE_JOINT
    if along % 8 == 7:
        return RUSSET_LO
    return (RUSSET_HI, RUSSET)[m]
```

Every `tex(x, y)` must stay 32-periodic in both axes (that is what joins cells); the prototype's are.
Nothing else in the file changes: not the header docstring, `FAMILIES`, `SPRITES`, `scenes()` or `sheet()`.

### `gamev2/assets/sprites/sendai-{plaza,jozenji,arcade-floor,samurai-lane,brick-yard,boardwalk}-autotile_<role>.png`

The 54 files, rewritten by `python3 tools/generate_sendai_town_art.py` (from `gamev2/`). No other file
under `assets/` may change; if `sendai-red-bridge*` changes, `PLANK` was edited.

### `gamev2/tools/tests/sendai-ground.test.js` (new)

See Tests. A new file, so it does not collide with the siblings' edits to `sendai.test.js`.

## Data and interfaces

None. No `config.json`, map, prefab, palette or `devhouse.world` change; sprite keys, sizes, layer and
the `--manifest` output are byte-identical (checked on the prototype). `family(role, tex, kerb, kw)` and
`_edge()` keep their signatures and behaviour for Fukuoka's tool.

## Tests

New unit tests in `gamev2/tools/tests/sendai-ground.test.js` (shape of `module.exports = ({ test, assert,
fs, path, GV2 }) => {...}`, PNGs read with `tools/png` `decode`), over the six families x nine roles with
kerb widths `{plaza: 3, jozenji: 4, 'arcade-floor': 3, 'samurai-lane': 3, 'brick-yard': 4, boardwalk: 3}`
(drawn pixels; twice that in the file):

1. *files*: all 54 exist, are 64x64, fully opaque, and every 2x2 block is one colour (pixel-doubled).
2. *look*: every colour is an opaque colour of a PNG under `art-source/GuttyKreum` (walk it, skipping
   files named `preview*`: the same set `house-look.test.js` builds on `master`); at most 16 colours a
   tile; no colour on more than half a tile.
3. *joins*: each role equals the `center` tile everywhere outside its kerb (the strip `2 * kw` px deep on
   the sides its name has); each corner's two kerb arms, outside the corner square, equal the kerb of the
   matching `edge-n|s` and `edge-e|w` tile over the same pixels.

The prototype passes all three; the committed art fails 2 (no sheet colours), which shows the test bites.

Run, from `gamev2/`:

```bash
python3 tools/generate_sendai_town_art.py --sheet /tmp/before/sheet.png --scenes /tmp/before   # before editing; git status stays clean
python3 tools/generate_sendai_town_art.py --sheet /tmp/after/sheet.png --scenes /tmp/after     # after; run twice: the second run changes nothing
git status --short        # only the tool, the new test and the 54 sendai-*-autotile_* PNGs
node tools/test_game.js; python3 tools/test_blog_to_npc.py; node tools/play.js check
python3 tools/check_generators.py; python3 tools/sync_cities.py --check
node tools/browser/regress.js                        # tools/browser/README.md; expected unchanged: no room uses the families
```

Look at before and after: the five day scenes (`sendai_art_<district>.png`), one `_night` scene, and the
sheet's 3x3 patch of each family at 2x or more. Check at every kerb that edges and corners continue and
that no seam shows between cells in the body. Save before/after pairs to `/work/media/` and say in the
summary which families still read as flat (expect the lane and the arcade floor to be the candidates).
The design's own pairs are `342-families-before-after.png`, `342-families-after-zoom.png` and
`342-scene-<district>-before-after.png`.

## Risks and open questions

- **The branch is behind `master`**: `house_look.py`, `house-look.test.js` and the "House look" docs
  section are not on it. The design depends on none of them; the look's rules used here are restated above.
- **Same file, other tickets** (#333, #336, #343, #344, #345): keep the diff inside the ground block and
  leave `stepping_stone` and `PLANK` alone, so merges stay textual.
- **Not covered by `check_generators.py`** (see Context). Not added here: five sibling tickets rewrite
  other sprites of the same tool at the same time. Reported as noticed work.
- **Hue**: the sheets have no tan or beige stone, so jozenji and the plaza turn from tan to the pack's
  pinker creams and the boardwalk from tan to the pier's brown. This is the look, not a slip; if the
  owner wants the old warmth back it has to come from sheet colours (`d7d0ba`, `b3aaa0`, `8d8883`).
- **Still flat?** The lane is low-contrast by its description ("plain ... gravel") and the arcade floor is
  polished tile; if either still reads flat after tuning, say so rather than adding noise or more dither.
