# 333: Sendai's Samurai quarter pieces in the house look

Part 3 of 6 of #288. Paths are relative to `gamev2/`. A prototype of everything below was run on
`origin/master` (`eb4f0703`); its drawing code is the appendix, and its pictures are in `/work/media/`
(`333-samurai-pieces-before.png` / `-after.png`, `333-samurai-scene-before.png` / `-after.png`,
`333-samurai-scene-night-after.png`).

## Context

`tools/generate_sendai_town_art.py` draws 102 `sendai-*` sprites that no room places yet (none is in
`config.json`). Its 17 Samurai quarter pieces predate the house look (`docs/generators-and-checks.md`,
"House look: GuttyKreum"):

| Sprite (`sendai-…_0_0`) | Cells | Colours now (off the sheets) | What is wrong |
|---|---|---|---|
| `samurai-gate` | 4x3 | 20 (18) | copper roof is a front-elevation trapezoid |
| `board-fence`, `-corner-e`, `-corner-w`, `-v`, `-end`, `-wicket` | 1x2, 1x3 | 14 to 21 (12 to 19) | palette; the wicket's roof is a flat front; an ink tick across every cell of a north-south run |
| `samurai-house-a`, `-b` | 5x4, 4x4 | 43, 44 (36, 38) | thatch is a flat front; lit yellow screens and door lamp |
| `samurai-store` | 3x3 | 32 (27) | thatch is a flat front |
| `well` | 1x2 | 23 (17) | flat roof front |
| `propped-pine` | 3x3 | 12 (9) | smooth-blob foliage, a 2000px soft shadow |
| `kabuto-stand` | 2x3 | 17 (15) | palette, a soft shadow |
| `andon-lamp-post` | 1x2 | 19 (16) | lit yellow paper, a soft shadow |
| `stepping-stone-a`, `-b`, `-c` | 1x1 | 6 (6) | palette |

Outcome: the 17 are redrawn in place in the house look and in Sendai's own materials (black lacquer boards,
gilt fittings, verdigris copper, thatch, cut grey stone). Keys, sizes, anchors, door, solid and walk-through
cells and glow spots stay exactly as the tool's manifest writes them; the other 85 sprites of the tool do
not change by a pixel or a byte.

Found while designing:

- The tool reproduces all 102 committed PNGs by pixels, but `main()` saves with `im.save`, so every run
  rewrites all 102 files' bytes. `generate_kanazawa_art.save_png` (writes only when the pixels differ) fixes
  that and keeps the siblings' files out of this change.
- `lacquer_boards`, `copper_roof`, `thatch_roof`, `shingle_pent`, `mon`, `gold_band`, `lq_post`, `engawa` and
  `lit_door` are called only by these 17 pieces, so they can be redrawn in place. `ashlar`, `shoji`,
  `step_stone`, `bar`, `glyph`, `puff`, `grounded`, `blob`, `trunk` are shared with other districts (and
  `bar`, `glyph`, `puff`, `grounded` with `generate_fukuoka_town_art.py`): not touched.
- No room places these sprites, so `node tools/play.js render Sendai` shows none of them. The before and
  after pictures are the tool's own `--scenes` (`sendai_art_samurai.png`, `_night.png`) and a contact sheet.
- This branch was cut before `tools/house_look.py`, `save_png`, `tools/tests/kanazawa-art.test.js` and the
  doc's house-look section reached `master`. The implementer needs them: if `tools/house_look.py` is missing,
  `git merge origin/master` first (locally; the tool itself is the same file on both).

## Approach

Redraw in the tool, in place, to these rules (all met by the prototype):

1. **Palette**: a new `S_*` block of GuttyKreum sheet colours only (appendix). The old constants (`LQ`,
   `COPPER_P`, `THATCH*`, `PAPER`, `WARM`, …) stay: other districts use them.
2. **Roofs seen from above**: one geometry, `hip_cells` (laid out as Kanazawa's `lead_hip`: a ridge bar, a
   front slope between two hips that reach the eave's corners, hip ends that widen to the full width), under
   two skins, `copper_roof` (standing seams, gilt ridge ends and eave nails) and `thatch_roof` (combed reed,
   lap lines, a thick cut eave, a bark ridge under straddling poles). The gate, wicket and well take copper;
   the two houses and the store thatch; house-b's pent is board shingles in courses. Walls under them stay
   front faces, as the pack's own buildings are.
3. **Light from the upper left**: `block()` puts `hi` on top and west edges, `lo` on foot and east; west hip
   ends lit, east in shade; a lip or eave casts one row of shadow.
4. **Nothing lit**: paper screens are cool white (`dae2e4` on `a4b0b5` lattice), openings `2c2d51` with a
   `2a3151` head. The andon lamp's paper and the door lamps are dim gold `c6a663` with a few `f3d890` pixels
   (under 3% of a sprite). The glow spots in the manifest are unchanged: the night glow is DayNight's.
5. **Rectangles and pixels only** in the redrawn code (`d.rectangle`, `d.point`, pixel access, hand-set
   `pix()` pictures); no polygon, ellipse, arc, pieslice, chord or line, and no `grounded()` soft shadow.
   Round things (the crest, house-b's window, the helmet bowl, the crescent) are integer tests or hand-set.
6. **Ink**: `outline(im)` on every piece but the three stepping stones (flat layer, laid on gravel: a 1px
   `575f79` shadow instead). On the four tall fence pieces the ink row across the run is cleared after
   `outline` (row 16 on all four, row 49 on `-v`, as `hakata_bei` does), so stacked pieces show no tick.
7. **The pine** is a pack-look tree: `generate_sendai_art.foliage` with `NEEDLE`, and its `ground_shade`
   (alpha 90, the one translucent thing kept, as Sendai's other pack-look trees keep it).
8. **Fence geometry is kept** row for row (cap at 16, boards 24 to 51, stone 52 to 63; the north-south strip
   on columns 6 to 19, rows 17 to 48), so pieces join each other and the gate's wing walls as before.
9. **Kanazawa is avoided**: no white plaster, ochre earth, straw mats or dark-red lattice; lattices are bare
   timber, walls black boards.

What each sprite shows (the appendix is exact):

| Sprite | Picture |
|---|---|
| `samurai-gate` | copper hip roof with gilt ridge ends and eave nails; lacquer lintel, gilt ends, nail covers, the 13px crest; banded posts on stone plinths; leaves folded back; boarded wing walls on cut stone |
| `board-fence` | copper ridge, board cap, lapped black boards with battens and gilt nails, two courses of cut stone |
| `-corner-e/-w` | the same face stopped at a gilt-banded corner post; the cap strip turns north over a mitre |
| `-v` | the cap from above: stone foot sliver, two board edges with a batten and nails every 8px, copper strip with seams |
| `-end` | the strip, then the fence end-on: copper cap, board cap, banded post, stone footing |
| `-wicket` | a little copper hip roof, lintel with the 7px crest, two posts on stones, the leaf folded back |
| `samurai-house-a` | thatched hip roof; engawa of three paper screens, the third slid back on an alcove with a scroll; entry under the crest with a dim gold lamp; boarded bay with a barred window and rain tub |
| `samurai-house-b` | smaller thatched hip roof over a clerestory band and a shingle pent; boarded bay with a round paper window in a gilt rim; entry; engawa |
| `samurai-store` | thatched hip roof; black boards; plank doors with iron straps and a gilt lock; firewood end-on; straw raincoat and hat |
| `well` | copper hip roof on lacquer posts, pulley, rope, bucket, cut-stone curb with the dark of the shaft |
| `propped-pine` | leaning bark trunk, one long limb on two padded props, nine needle clumps, ground shade under the trunk |
| `kabuto-stand` | lacquer dais, four-leaf gold screen, armour chest with the crest, black cuirass laced in gold, the helmet and its great gold crescent |
| `andon-lamp-post` | banded lacquer post on a stone, dim gold paper lantern in a lacquer frame, a copper cap with a gilt finial |
| `stepping-stone-a/-b/-c` | one broad stone, two small ones, a cut slab: lit north-west edge, shaded south-east, a worn centre |

Result of the prototype: colours 16 (gate), 14 to 16 (fence family), 21, 21, 19 (houses, store), 16 (well),
12 (pine), 15 (kabuto), 14 (lamp), 5 (stones); none off the sheets; no colour on more than 47% of a sprite.

**Still read as flat** (to repeat in the implementer's summary): the three stepping stones (pale stones seen
from above, flat by design), and the wall faces of the houses and store, which stay front faces under roofs
seen from above. The north-south fence strip is a narrow band, as before.

## Changes

### `tools/generate_sendai_town_art.py`

Line numbers are the file's as it is on `master` and on this branch. Replace by function name.

- **Imports**: `foliage`, `ground_shade`, `NEEDLE` from `generate_sendai_art` and `save_png` from
  `generate_kanazawa_art`, added to the import lines the tool already has for those two modules (100, 105).
- **Palette** (after the colour block, line 132): the `S_*` block.
- **Helpers redrawn in place**: `lacquer_boards` (188, with new `block` and `pix` before it), `copper_roof`
  and `thatch_roof` (226 to 308, with new `cut_stone` and `hip_cells` before them), `shingle_pent` (311),
  `mon` (342, with `MON`). `ashlar` and `shoji` between them are left as they are.
- **Samurai section** (`gold_band` at 1128 to the end of `kabuto_stand` at 1474): replaced whole. New:
  `taper`, `paper_screen`, `entry` (replaces `lit_door`, which is deleted), `shoe_stone`, `PULLEY`, `bough`.
  `step_stone` stays verbatim (the distillery warehouse calls it).
- **`andon_lamp`** (2062), **`samurai_store`** (2368, with `LOG`), **`STEPPING` and `stepping_stone`** (2463):
  replaced.
- **`main()`**: `im.save(f'{SPR}/{key}.png')` becomes `save_png(im, f'{SPR}/{key}.png')`.
- **Words only**: in the module docstring, after "lit from the west, a 1px ink outline" add that the Samurai
  quarter is in the house look, lit from the upper left; the gate's line says "a copper hip roof seen from
  above"; house-a's "an engawa and paper screens". In `PIECES`: the gate "a verdigris copper hip roof seen
  from above with gilt ridge ends"; house-a "paper screens, one slid back on an alcove" (not "one lit") and
  "a dim gold lamp inside"; the lamp "a square paper lantern in dim gold". Every other field of the 17
  `PIECES` rows (key, builder, size, district, `door`, `solid`, `walk`, `lit`, `layer`) is unchanged, and so
  are `sheet()`, `scenes()` and `manifest()`.

### `assets/sprites/`

The 17 PNGs, rewritten by the tool. No other file may change (`git status --short assets/sprites`).

### `tools/tests/sendai-town-art.test.js` (new)

See Tests. Modelled on `tools/tests/kanazawa-art.test.js` (its `load`, `hex`, `sheets()` and `rebuild`).

### `docs/generators-and-checks.md`

One paragraph at the end of "House look: GuttyKreum", after Kanazawa's: the 17 Samurai quarter pieces of
`tools/generate_sendai_town_art.py` (#333, part of #288) are drawn by it, their roofs hipped and seen from
above in copper and thatch (`hip_cells`), and held to it by `tools/tests/sendai-town-art.test.js`; the tool
saves with `save_png`, so a rerun leaves unchanged sprites' files alone.

## Data and interfaces

None. No `config.json`, prefab, Tiled or `devhouse.world` change; rooms touched: none. The tool's
`--manifest` output is the same for all 102 sprites apart from the three reworded descriptions.
`copper_roof`, `thatch_roof`, `shingle_pent` and `engawa` change signature; they have no caller outside the
17 pieces.

## Tests

`tools/tests/sendai-town-art.test.js`, test names starting `sendai town art:` and ending `(#333)`. `QUARTER`
maps the 17 keys to their cells; `FENCE` is `sendai-board-fence`. Coordinates below are in drawn (32px a
cell) pixels; the PNG's are doubled.

1. **Sizes**: each PNG is cells x 64, every pixel a 2x2 block, alpha 0 or 255 (`propped-pine` may also have
   alpha 90, and only as `2a3151`).
2. **Colours**: opaque pixels are sheet colours only; at most 16 for the 1x1, 1x2 and 1x3 pieces and 24 for
   the gate, houses, store, pine and kabuto stand; none on more than half the opaque pixels; none of `f6dc8c`,
   `f2c66a`, `f9c22e`, `2b373c`, `000000`; `f3d890` under 3%.
3. **Silhouette**: every opaque pixel with a clear (alpha 0) 4-neighbour inside the canvas is `0a1627`,
   except in the three stepping stones, and on rows 17 (`-v`, `-end`, both corners) and 48 (`-v`) of the tall
   fence pieces, where the run carries on into the next piece.
4. **Fence joins**: columns 0 to 13, rows 48 to 95 of `-corner-e` equal columns 0 to 13, rows 16 to 63 of the
   straight piece; columns 16 to 31 likewise for `-corner-w`; the straight piece's columns 0 to 15 equal its
   columns 16 to 31; `-v`'s rows 17 to 32 equal its rows 33 to 48; rows 16 to 46 of `-end` and of both corners
   equal `-v`'s; row 16 of all four and row 49 of `-v` are clear.
5. **Rectangles and pixels only**: the source of `block`, `pix`, `lacquer_boards`, `cut_stone`, `hip_cells`,
   `copper_roof`, `thatch_roof`, `shingle_pent`, `mon`, `gold_band`, `lq_post`, `taper`, `samurai_gate`,
   `fence`, `paper_screen`, `engawa`, `entry`, `shoe_stone`, `samurai_house`, `well`, `bough`, `propped_pine`,
   `kabuto_stand`, `andon_lamp`, `samurai_store`, `stepping_stone` (cut as the Kanazawa test cuts a builder)
   has none of `.polygon(`, `.ellipse(`, `.arc(`, `.pieslice(`, `.chord(`, `.line(`, `grounded(`.
6. **Map data pinned** (skips without Pillow): a `python3 -c` snippet imports the tool and prints, for the
   `PIECES` rows whose district is `SQ`, the size and the `door`, `solid`, `walk`, `lit`, `layer` of each; the
   test compares it with a literal table of today's values (exactly 17 keys):

   | Key | Size | Data |
   |---|---|---|
   | `samurai-gate` | 4x3 | solid `[[0,2],[3,2]]`, walk `[[1,2],[2,2]]` |
   | `board-fence` | 1x2 | solid `[[0,1]]` |
   | `-corner-e`, `-corner-w`, `-v`, `-end` | 1x3 | solid `[[0,2]]` |
   | `-wicket` | 1x2 | walk `[[0,1]]` |
   | `samurai-house-a` | 5x4 | door `[[2,3]]`, solid rows 2 to 3 of 5 columns, lit `[[0.6,2.9,WARM,0.9],[2.25,2.75,WARM,0.5]]` |
   | `samurai-house-b` | 4x4 | door `[[1,3]]`, solid rows 2 to 3 of 4 columns, lit `[[1.35,2.85,WARM,0.5],[2.75,3.0,WARM,0.9]]` |
   | `samurai-store` | 3x3 | door `[[1,2]]`, solid rows 1 to 2 of 3 columns |
   | `well`, `andon-lamp-post` | 1x2 | solid `[[0,1]]` |
   | `propped-pine` | 3x3 | solid `[[0,2],[2,2]]`, walk `[[1,2]]` |
   | `kabuto-stand` | 2x3 | solid row 2 of 2 columns, lit `[[1.0,1.6,GILT,1.1,0.4]]` |
   | `stepping-stone-a/-b/-c` | 1x1 | layer `flat`, walk `[[0,0]]` |

   Take the literal values (and `WARM_HEX`, `GILT_HEX` as strings) from the snippet's output on the
   untouched tool.
7. **The tool draws what is committed** (skips without Pillow): the Kanazawa test's rebuild snippet with
   `generate_sendai_town_art`, over every key of `SPRITES` (all 102: this is the guard that the helper edits
   moved no Station, Arcade, Downtown, Distillery, Bay or ground sprite; it took 0.5s in the prototype).

The implementer, in order (from `gamev2/`):

```bash
mkdir -p /tmp/333/before
python3 tools/generate_sendai_town_art.py --sheet /tmp/333/before/sheet.png --scenes /tmp/333/before/scenes \
    --manifest /tmp/333/before/manifest.json
git checkout -- assets/sprites                        # the untouched tool rewrites all 102 files' bytes
# ... edit the tool ...
python3 tools/generate_sendai_town_art.py --sheet /tmp/333/sheet.png --scenes /tmp/333/scenes \
    --manifest /tmp/333/manifest.json
git status --short assets/sprites                     # exactly the 17
python3 tools/house_look.py --sheet /tmp/333/contact.png --scale 2 assets/sprites/sendai-samurai-*.png \
    assets/sprites/sendai-board-fence*.png assets/sprites/sendai-well_0_0.png \
    assets/sprites/sendai-propped-pine_0_0.png assets/sprites/sendai-kabuto-stand_0_0.png \
    assets/sprites/sendai-andon-lamp-post_0_0.png assets/sprites/sendai-stepping-stone-*.png
node tools/play.js render Sendai /tmp/333/sendai.png  # unchanged: no room places these
node tools/test_game.js && python3 tools/test_blog_to_npc.py && node tools/play.js check \
    && python3 tools/check_generators.py && python3 tools/sync_cities.py --check
```

- The two manifests are equal once `description` is dropped from each sprite (17 keys of district
  `Samurai quarter`, same sizes, doors, solid, walk-through, glow, halo, layer).
- The scenes `sendai_art_station`, `_downtown`, `_distillery`, `_bay` and their nights are pixel-equal before
  and after.
- Look at `/tmp/333/scenes/sendai_art_samurai.png` and `_night.png` beside the before ones, and at the
  contact sheet beside a done model (`sendai-earthen-wall_0_0.png`, `fukuoka-kushida-hall_0_0.png`). The
  result should match `/work/media/333-samurai-pieces-after.png`. Save before and after to `/work/media/` and
  name in the summary the pieces that still read as flat (list above).
- The browser regression (`tools/browser/regress.js`) cannot see these sprites: run it as the house rule
  asks, or say it was not run and why.
- Commit as `gamev2: … (#333)`; rooms touched: none.

## Risks and open questions

- **Sibling tickets edit the same file** (#336 station, deck, arcade; #342 ground; #343, #344, #345): expect
  textual conflicts at the import lines, the palette block and `main()`'s save line, none in the drawing
  code. Whoever lands second keeps both. Test 7 then fails for anyone whose helper edit moves a Samurai piece.
- **A free north end of a north-south run has no closing ink row** once row 16 is cleared (Fukuoka has a
  `-top` piece for that; the ticket fixes Sendai's keys at 17). It is the pack's copper strip against grass;
  a `-top` piece would be a later ticket when a room needs one.
- **Night**: the houses' glow spots stay where the lit screens were, so DayNight glows over paper that is no
  longer drawn lit (see `333-samurai-scene-night-after.png`). That is the house look's rule for every window.
- **Close tones**: thatch `c6aa71` sits near gilt `c6a663` (they never touch: lacquer or timber is between);
  lacquer's darkest `080d16` sits near the ink `0a1627` (both are the pack's); paper shares the stone ramp.
- **The tool is not in `check_generators.ART_TOOLS`**; test 7 is the guard, as `kanazawa-art.test.js` is for
  its tool.
- No open question for the owner.

## Appendix: the prototype's drawing code

Spliced into the tool as marked (line numbers of the untouched file), this draws the 17 sprites of
`/work/media/333-samurai-pieces-after.png` and leaves the other 85 alone. It uses what the tool already
imports (`rgb`, `canvas`, `outline`, `CLEAR`, `h3`, `WHITE`, `ASH_DK`, `ASH_LO`).

```python
# ====================================================================================================
# with the imports (or added to the two existing import lines for these modules)
# ====================================================================================================
from generate_sendai_art import foliage, ground_shade, NEEDLE                                       # noqa: E402
from generate_kanazawa_art import save_png                                                        # noqa: E402


# ====================================================================================================
# after the colour block (line 132)
# ====================================================================================================
# The Samurai quarter is in the house look (docs/generators-and-checks.md): GuttyKreum's sheet colours only (#333)
S_LQ, S_LQ_HI, S_LQ_EDGE, S_LQ_LO = rgb('1b1e2a'), rgb('2a2636'), rgb('413f53'), rgb('080d16')   # black lacquer
S_CU_HI, S_CU, S_CU_LO, S_CU_DK = rgb('93c297'), rgb('6c8e7f'), rgb('506b6b'), rgb('395050')     # verdigris copper
S_GILT_HI, S_GILT, S_GILT_LO, S_GILT_DK = rgb('f3d890'), rgb('c6a663'), rgb('a7843b'), rgb('86624f')
S_TH_HI, S_TH, S_TH_LO, S_TH_DK = rgb('c6aa71'), rgb('b2a168'), rgb('928372'), rgb('716555')     # thatch
S_ST_HI, S_ST, S_ST_LO, S_ST_DK = rgb('dae2e4'), rgb('a4b0b5'), rgb('848295'), rgb('575f79')     # cut grey stone
S_WD_HI, S_WD, S_WD_LO = rgb('a68777'), rgb('7f513b'), rgb('594b45')                              # bare timber, bark
S_DARK, S_DARK_LO, S_RED, S_WORN = rgb('2c2d51'), rgb('2a3151'), rgb('aa4d31'), rgb('bcc7cc')


# ====================================================================================================
# in place of lacquer_boards (188 to 201)
# ====================================================================================================
def block(d, x0, y0, x1, y1, base, hi=None, lo=None):
    """A box lit from the upper left: `hi` along its top and west edge, `lo`
    along its foot and east edge (`lo` wins the corners)."""
    d.rectangle([x0, y0, x1, y1], fill=base)
    if hi:
        d.rectangle([x0, y0, x1, y0], fill=hi); d.rectangle([x0, y0, x0, y1], fill=hi)
    if lo:
        d.rectangle([x0, y1, x1, y1], fill=lo); d.rectangle([x1, y0, x1, y1], fill=lo)


def pix(d, rows, x, y, tones):
    """A hand-set picture: one character a pixel, '.' clear, every other
    character a key of `tones`."""
    for gy, row in enumerate(rows):
        for gx, ch in enumerate(row):
            if ch != '.':
                d.point((x + gx, y + gy), fill=tones[ch])


def lacquer_boards(d, x0, y0, x1, y1, batten=8, off=3, studs=False):
    """Shitami-ita in black lacquer: lapped boards 4px deep, each with a lit
    upper arris and the shadow of its lap, under thin battens lit down their
    west side; `studs` are gilt nails."""
    for y in range(y0, y1 + 1):
        k = (y - y0) % 4
        d.rectangle([x0, y, x1, y], fill=S_LQ_HI if k == 0 else (S_LQ_LO if k == 3 else S_LQ))
    for x in range(x0, x1 + 1):
        if (x - off) % batten == 0:
            d.rectangle([x, y0, x, y1], fill=S_LQ_EDGE)
            if x + 1 <= x1:
                d.rectangle([x + 1, y0, x + 1, y1], fill=S_LQ_LO)
            if studs:
                d.point((x, y0 + 2), fill=S_GILT_HI); d.point((x, y1 - 2), fill=S_GILT)


# ====================================================================================================
# new, before copper_roof (ashlar above it is untouched)
# ====================================================================================================
def cut_stone(d, x0, y0, x1, y1, ch=6, bw=16, seed=0):
    """Cut grey stone in the house look, laid as ashlar is (period 32 in x, so a
    run joins): each block lit along its top and west edge, shaded along its
    foot, a dark joint under and east of it."""
    for y in range(y0, y1 + 1):
        j, yy = (y - y0) // ch, (y - y0) % ch
        for x in range(x0, x1 + 1):
            u = (x + j * (bw // 2) + seed * 5) % 32 % bw
            if yy == ch - 1 or u == bw - 1:
                c = S_ST_DK
            elif yy == 0 or u == 0:
                c = S_ST_HI
            elif yy == ch - 2:
                c = S_ST_LO
            else:
                c = S_ST
            d.point((x, y), fill=c)


# ====================================================================================================
# in place of copper_roof and thatch_roof (226 to 308)
# ====================================================================================================
def hip_cells(x0, x1, top, eave, run, side_rows):
    """A hipped roof seen from above, a pixel at a time, laid out as Kanazawa's
    lead_hip is: the front slope falls from `top` to `eave` between two hips
    that start `run` in from either end and reach the eave's corners; outside
    them the hip ends widen to the full width in `side_rows` rows. Yields
    (x, y, part, n): part 'w' / 'e' is a hip end (n pixels in from its outer
    edge), 'hw' / 'he' a hip (n is -1, 0, 1 across it, west to east), 'f' the
    front slope (n pixels west of the east hip)."""
    for y in range(top, eave + 1):
        hip = (y - top) * run // (eave - top)
        side = min(run, (y - top) * run // side_rows)
        hw, he, ow, oe = x0 + run - hip, x1 - run + hip, x0 + run - side, x1 - run + side
        for x in range(ow, oe + 1):
            if x < hw - 1:
                yield x, y, 'w', x - ow
            elif x > he + 1:
                yield x, y, 'e', oe - x
            elif x <= hw + 1:
                yield x, y, 'hw', x - hw
            elif x >= he - 1:
                yield x, y, 'he', x - he
            else:
                yield x, y, 'f', he - 2 - x


def copper_roof(d, x0, x1, top, eave, run, side_rows, gilt=True, seam=6):
    """A verdigris copper hip roof seen from above: sheet copper with standing
    seams that run down each slope (upright on the front slope, level on the
    hip ends), the west hip end lit and the east in shade, an eave lip of 3
    rows under `eave`, a ridge bar in the 4 rows above `top`; with `gilt`,
    gilded ridge ends and a gilt nail at each seam along the eave."""
    for x, y, part, n in hip_cells(x0, x1, top, eave, run, side_rows):
        if part == 'w':
            c = S_CU if (y - top) % seam == seam - 1 else S_CU_HI
        elif part == 'e':
            c = S_CU_DK if (y - top) % seam == seam - 1 else S_CU_LO
        elif part == 'hw':
            c = S_CU_DK if n == 1 else S_CU_HI
        elif part == 'he':
            c = S_CU_HI if n == -1 else S_CU_DK
        elif y == top:
            c = S_CU_LO                                           # the ridge bar's shadow
        elif n < 8:                                               # the slope's east end turns from the light
            c = S_CU_DK if (x - x0) % seam == 3 else S_CU_LO
        else:
            c = S_CU_LO if (x - x0) % seam == 3 else S_CU
        d.point((x, y), fill=c)
    d.rectangle([x0, eave + 1, x1, eave + 1], fill=S_CU_HI)
    d.rectangle([x0, eave + 2, x1, eave + 2], fill=S_CU_LO)
    d.rectangle([x0, eave + 3, x1, eave + 3], fill=S_CU_DK)
    a, b = x0 + run - 2, x1 - run + 2
    d.rectangle([a, top - 4, b, top - 1], fill=S_CU_LO)
    d.rectangle([a, top - 4, b, top - 4], fill=S_CU_HI)
    d.rectangle([a, top - 1, b, top - 1], fill=S_CU_DK)
    for x in range(a + 3, b - 1, seam):
        d.rectangle([x, top - 3, x, top - 2], fill=S_CU_DK)
    if gilt:
        for x in range(x0 + 3, x1, seam):
            d.point((x, eave + 2), fill=S_GILT)
        for cx in (a - 4, b - 1):
            block(d, cx, top - 6, cx + 5, top, S_GILT, S_GILT_HI, S_GILT_LO)


def thatch_roof(d, x0, x1, top, eave, run, side_rows):
    """A thatched hip roof seen from above: combed reed laid in layers (a shadow
    line where one laps the next: every 8 rows down the front slope, every 8
    columns out along the hip ends), the hips soft, the west end lit and the
    east in shade, a thick cut eave of 5 rows under `eave`, a bark ridge in the
    7 rows down to `top` held by straddling poles."""
    for x, y, part, n in hip_cells(x0, x1, top, eave, run, side_rows):
        if part in ('w', 'e'):
            reed = n % 8 == 0 or h3(x // 3, y, 5) < 22            # the reeds run out to the end's own eave
            c = (S_TH if reed else S_TH_HI) if part == 'w' else (S_TH_DK if reed else S_TH_LO)
        elif part == 'hw':
            c = S_TH_HI
        elif part == 'he':
            c = S_TH_DK
        else:
            k = h3(x, (y - top) // 3, 5)
            lap = (y - top) % 8 == 7 or y == top
            if n < 10 or (n < 12 and (x + y) % 2):                # the slope's east end turns from the light
                c = S_TH_DK if lap else (S_TH if k < 24 else S_TH_LO)
            else:
                c = S_TH_LO if lap or k > 228 else (S_TH_HI if k < 30 else S_TH)
        d.point((x, y), fill=c)
    d.rectangle([x0, eave + 1, x1, eave + 1], fill=S_TH_LO)       # the eave's cut edge, in its own shade
    d.rectangle([x0, eave + 2, x1, eave + 4], fill=S_TH_DK)
    for x in range(x0 + x0 % 2, x1 + 1, 2):
        d.rectangle([x, eave + 2, x, eave + 4], fill=S_TH_LO if x % 6 else S_TH)
    d.rectangle([x0, eave + 5, x1, eave + 5], fill=S_WD_LO)
    a, b = x0 + run, x1 - run
    d.rectangle([a - 3, top - 6, b + 3, top], fill=S_WD)
    d.rectangle([a - 3, top - 6, b + 3, top - 6], fill=S_WD_HI)
    d.rectangle([a - 3, top, b + 3, top], fill=S_WD_LO)
    n = max(3, (b - a) // 16)
    for i in range(n + 1):                                        # the straddling poles
        x = a + (2 * i * (b - a) + n) // (2 * n)
        d.rectangle([x - 1, top - 9, x + 1, top + 3], fill=S_TH_HI)
        d.rectangle([x + 1, top - 9, x + 1, top + 3], fill=S_TH_LO)


# ====================================================================================================
# in place of shingle_pent (311 to 327; shoji below it is untouched)
# ====================================================================================================
def shingle_pent(d, y0, y1, x0, x1):
    """A pent roof of weathered board shingles seen from above, 3px proud of
    x0..x1 either side: thin courses 3 rows deep, each lit along its head and
    dark where the next laps it, the joints staggered."""
    for y in range(y0, y1 + 1):
        k, course = (y - y0) % 3, (y - y0) // 3
        for x in range(x0 - 3, x1 + 4):
            if k == 2 or (k == 1 and (x + course * 2) % 5 == 0):
                c = S_WD_LO
            else:
                c = S_WD_HI if k == 0 else S_WD
            d.point((x, y), fill=c)
    d.rectangle([x0 - 3, y1 + 1, x1 + 3, y1 + 1], fill=S_WD_LO)
    d.rectangle([x0 - 3, y1 + 2, x1 + 3, y1 + 2], fill=S_LQ_LO)


# ====================================================================================================
# in place of mon (342 to 348)
# ====================================================================================================
MON = {3: ['..hhg..', '.hkkkg.', 'hkkkkkg', 'gkckckl', 'gkccckl', '.gkkkl.', '..gll..'],
       6: ['....hhhhg....', '..hhkkkkkgg..', '.hkkkkkkkkkg.', '.hkkkkkkkkkg.', 'hkkkkkkkkkkkg',
           'hkkckkkkkckkg', 'gkkckkkkkckkl', 'gkkcckkkcckkl', 'gkkkccccckkkl', '.gkkkccckkkl.',
           '.gkkkkkkkkkl.', '..ggkkkkkll..', '....gglll....']}


def mon(d, cx, cy, r=6):
    """The quarter's invented crest, hand-set at r 3 or 6: a crescent, horns up,
    in a gold ring lit from the upper left. Not a real mon."""
    pix(d, MON[r], cx - r, cy - r, {'h': S_GILT_HI, 'g': S_GILT, 'l': S_GILT_LO, 'c': S_GILT_HI, 'k': S_LQ_LO})


# ====================================================================================================
# in place of gold_band .. kabuto_stand (1128 to 1474; step_stone is the old one, verbatim)
# ====================================================================================================
def gold_band(d, x0, y, x1, h=2):
    d.rectangle([x0, y, x1, y + h - 1], fill=S_GILT)
    d.point((x0, y), fill=S_GILT_HI)
    if h > 1:
        d.rectangle([x0, y + h - 1, x1, y + h - 1], fill=S_GILT_LO)


def lq_post(d, x0, y0, x1, y1, bands=True):
    """A black-lacquer post lit down its west arris, with gilt bands if asked."""
    d.rectangle([x0, y0, x1, y1], fill=S_LQ)
    d.rectangle([x0, y0, x0, y1], fill=S_LQ_EDGE)
    d.rectangle([x1, y0, x1, y1], fill=S_LQ_LO)
    if x1 - x0 >= 4:
        d.rectangle([x0 + 1, y0, x0 + 1, y1], fill=S_LQ_HI)
    if bands:
        gold_band(d, x0, y0 + 2, x1, 2)
        gold_band(d, x0, y1 - 5, x1, 3)


def taper(d, y0, y1, top, bottom, fill):
    """Rows y0..y1 whose ends run straight from `top` (x0, x1) to `bottom`."""
    n = max(1, y1 - y0)
    for y in range(y0, y1 + 1):
        t = y - y0
        d.rectangle([top[0] + (bottom[0] - top[0]) * t // n, y, top[1] + (bottom[1] - top[1]) * t // n, y], fill=fill)


def samurai_gate():
    im, d = canvas(4, 3)                 # 128 x 96
    copper_roof(d, 1, 126, 12, 33, 13, 8)
    d.rectangle([8, 37, 119, 37], fill=S_LQ_LO)                   # the eave's shadow
    # the lintel: lacquer, gilded ends, the mon
    block(d, 8, 38, 119, 49, S_LQ, S_LQ_EDGE, S_LQ_LO)
    d.rectangle([9, 39, 118, 39], fill=S_LQ_HI)
    for x0 in (8, 114):
        block(d, x0, 38, x0 + 5, 49, S_GILT, S_GILT_HI, S_GILT_LO)
    for x in range(22, 108, 8):                                   # gilt nail covers
        if abs(x - 62) > 10:
            d.rectangle([x, 42, x + 1, 44], fill=S_GILT); d.point((x, 42), fill=S_GILT_HI)
            d.point((x + 1, 45), fill=S_LQ_LO)
    mon(d, 64, 43, 6)
    # the wing walls: a little copper cap, black boards, cut stone
    for x0, x1 in ((2, 13), (114, 125)):
        d.rectangle([x0, 51, x1, 53], fill=S_CU); d.rectangle([x0, 51, x1, 51], fill=S_CU_HI)
        d.rectangle([x0, 54, x1, 54], fill=S_CU_DK)
        lacquer_boards(d, x0, 55, x1, 83, batten=6, off=x0 + 2)
        cut_stone(d, x0, 84, x1, 91, ch=4, bw=8)
    # the posts and the leaves folded back
    for x0 in (14, 104):
        lq_post(d, x0, 50, x0 + 9, 88)
        block(d, x0 - 1, 88, x0 + 10, 92, S_ST, S_ST_HI, S_ST_DK)
    for x0 in (24, 97):
        block(d, x0, 51, x0 + 6, 89, S_LQ_HI, S_LQ_EDGE if x0 == 24 else None, S_LQ_LO)
        for y in range(56, 88, 8):
            d.point((x0 + 2, y), fill=S_GILT); d.point((x0 + 4, y), fill=S_GILT_LO)
        gold_band(d, x0, 68, x0 + 6, 2)
    d.rectangle([31, 50, 96, 52], fill=S_LQ_LO)                   # the shadow under the lintel
    outline(im)
    return im


def fence(kind):
    """One piece of the black board fence. `h` (1x2) runs east-west: a copper
    ridge on a board cap, lapped black boards with battens and gilt nails, on
    two courses of cut stone; `wicket` (1x2) is a roofed side gate, walked
    through. The rest are 1x3, because a fence running NORTH-SOUTH is seen
    end-on: all that shows of it is its cap from above, a narrow copper strip
    between two board edges, a cell and a half up the map from where it
    stands (the fence is as tall as the east-west run). `v` is a length of
    that strip; `end` is the same with the fence's south end under it - the
    copper cap, the board cap, a gilt-banded post, the stone footing, drawn to
    the east-west run's own heights; `corner-e` / `corner-w` end an east-west
    run where the fence turns north: the face stops at a corner post and the
    cap turns up the map over a mitre (`v` goes in the cells above)."""
    tall = kind in ('v', 'end', 'corner-e', 'corner-w')
    im, d = canvas(1, 3 if tall else 2)  # 32 x 96 or 32 x 64
    oy = 32 if tall else 0

    def cap_h(x0, x1, y=oy + 16):
        d.rectangle([x0, y, x1, y], fill=S_CU_HI); d.rectangle([x0, y + 1, x1, y + 1], fill=S_CU)
        for x in range(x0 - x0 % 8, x1 + 1, 8):                   # a seam in the copper every 8px
            if x >= x0:
                d.point((x, y + 1), fill=S_CU_DK)
        d.rectangle([x0, y + 2, x1, y + 6], fill=S_LQ_HI)         # the board cap
        d.rectangle([x0, y + 2, x1, y + 2], fill=S_LQ_EDGE)
        d.rectangle([x0, y + 6, x1, y + 7], fill=S_LQ_LO)         # its foot and its shadow on the boards

    def face(x0, x1):
        lacquer_boards(d, x0, oy + 24, x1, oy + 51, studs=True)
        cut_stone(d, x0, oy + 52, x1, oy + 63)

    # a north-south run from the south and a little west: the stone foot, the boards' lit laps, the copper cap
    STRIP = ((6, S_ST_HI), (7, S_ST), (8, S_LQ_EDGE), (9, S_LQ), (10, S_LQ_LO), (11, S_LQ_EDGE), (12, S_LQ),
             (13, S_LQ_LO), (14, S_CU_HI), (15, S_CU), (16, S_CU), (17, S_CU_LO), (18, S_CU_DK), (19, S_LQ_LO))

    def cap_v(y0, y1):
        for y in range(y0, y1 + 1):
            for x, c in STRIP:
                d.point((x, y), fill=c)
            if y % 8 == 3:                                        # a batten, a gilt nail at each lap
                d.rectangle([8, y, 13, y], fill=S_LQ_HI)
                d.point((9, y), fill=S_GILT_HI); d.point((12, y), fill=S_GILT)
            elif y % 8 == 4:
                d.rectangle([8, y, 13, y], fill=S_LQ_LO)
            if y % 8 == 7:                                        # a seam in the copper
                d.rectangle([14, y, 18, y], fill=S_CU_DK)
            if y % 16 == 15:                                      # a joint in the stone
                d.rectangle([6, y, 7, y], fill=S_ST_DK)

    if kind == 'h':
        cap_h(0, 31); face(0, 31)
    elif kind == 'v':
        cap_v(17, 48)
    elif kind == 'end':
        cap_v(17, 47)
        cap_h(6, 20, 48)                                          # the fence end-on: its copper cap, its board cap
        lq_post(d, 8, 56, 18, 83)
        cut_stone(d, 6, 84, 20, 95, bw=8, seed=2)
        d.rectangle([6, 84, 6, 95], fill=S_ST_HI); d.rectangle([20, 84, 20, 95], fill=S_ST_DK)
    elif kind in ('corner-e', 'corner-w'):
        east = kind == 'corner-e'
        fx0, fx1 = (0, 19) if east else (6, 31)
        cap_v(17, 47)                                             # the run going north
        cap_h(0 if east else 5, 20 if east else 31)               # its copper turns along the east-west cap
        face(fx0, fx1)
        px = fx1 - 5 if east else fx0
        lq_post(d, px, oy + 24, px + 5, oy + 51)                  # the corner post
        d.point((14, 47), fill=S_CU_DK); d.point((15, 48), fill=S_CU_DK)         # the mitre in the copper
    elif kind == 'wicket':
        copper_roof(d, 0, 31, 8, 14, 6, 4, gilt=False)
        d.rectangle([0, 18, 31, 18], fill=S_LQ_LO)                # the eave's shadow
        block(d, 0, 19, 31, 24, S_LQ, S_LQ_EDGE, S_LQ_LO)
        mon(d, 15, 21, 3)
        for x0 in (0, 27):
            lq_post(d, x0, 25, x0 + 4, 60)
            block(d, x0, 60, x0 + 4, 63, S_ST, S_ST_HI, S_ST_DK)
        block(d, 5, 25, 8, 61, S_LQ_HI, S_LQ_EDGE, S_LQ_LO)       # the leaf, folded back
        d.point((6, 34), fill=S_GILT); d.point((6, 44), fill=S_GILT); d.point((6, 54), fill=S_GILT_LO)
    outline(im)
    if tall:                                                      # no ink across a run: pieces stack seamlessly
        px = im.load()
        for x in range(32):
            px[x, 16] = CLEAR
            if kind == 'v':
                px[x, 49] = CLEAR
    return im


def paper_screen(d, x0, y0, x1, y1, cw=5, chh=6):
    """A paper screen in the house look, never lit: a lacquer frame, a lattice,
    cool white paper with the head rail's shadow along its top."""
    d.rectangle([x0, y0, x1, y1], fill=S_LQ)
    d.rectangle([x0 + 1, y0 + 1, x1 - 1, y1 - 1], fill=S_ST_HI)
    for x in range(x0 + 1 + cw, x1, cw + 1):
        d.rectangle([x, y0 + 1, x, y1 - 1], fill=S_ST)
    for y in range(y0 + 1 + chh, y1, chh + 1):
        d.rectangle([x0 + 1, y, x1 - 1, y], fill=S_ST)
    d.rectangle([x0 + 1, y0 + 1, x1 - 1, y0 + 1], fill=S_ST_LO)


def engawa(d, x0, x1, y0, y1, open_at=None):
    """A veranda: paper screens behind a timber deck on short posts and stones.
    y0 is the screens' head, y1 the ground; screen `open_at` is slid back on an
    alcove with a scroll."""
    deck = y1 - 12
    n = max(1, (x1 - x0 + 1) // 13)
    for i in range(n):
        a, b = x0 + i * (x1 - x0 + 1) // n, x0 + (i + 1) * (x1 - x0 + 1) // n - 1
        if i == open_at:                                          # the room: an alcove, a scroll, tatami
            d.rectangle([a, y0, b, deck - 1], fill=S_DARK); d.rectangle([a, y0, b, y0 + 1], fill=S_DARK_LO)
            d.rectangle([a + 4, y0 + 4, b - 4, deck - 8], fill=S_ST_HI)
            d.rectangle([a + 4, y0 + 4, b - 4, y0 + 4], fill=S_GILT_LO)
            d.rectangle([a + 4, deck - 8, b - 4, deck - 8], fill=S_GILT_LO)
            for k in range(6):                                    # a brush stroke
                d.rectangle([a + 6 + k, y0 + 8 + k * 2, a + 6 + k, y0 + 9 + k * 2], fill=S_LQ)
            d.rectangle([a + 1, deck - 4, b - 1, deck - 1], fill=S_TH)
            d.rectangle([a + 1, deck - 4, b - 1, deck - 4], fill=S_TH_HI)
        else:
            paper_screen(d, a, y0, b, deck - 1)
    d.rectangle([x0, y0 - 3, x1, y0 - 1], fill=S_LQ); d.rectangle([x0, y0 - 3, x1, y0 - 3], fill=S_LQ_EDGE)
    d.rectangle([x0 - 1, deck, x1 + 1, deck + 3], fill=S_WD)      # the deck, its boards end-on
    d.rectangle([x0 - 1, deck, x1 + 1, deck], fill=S_WD_HI)
    for x in range(x0, x1 + 1, 4):
        d.rectangle([x, deck + 1, x, deck + 3], fill=S_WD_LO)
    d.rectangle([x0 - 1, deck + 4, x1 + 1, deck + 4], fill=S_WD_LO)
    d.rectangle([x0, deck + 5, x1, y1], fill=S_LQ_LO)             # under the floor
    for x in range(x0 + 3, x1 - 2, 14):
        d.rectangle([x, deck + 5, x + 2, y1 - 3], fill=S_WD_LO)
        d.rectangle([x - 1, y1 - 2, x + 3, y1], fill=S_ST); d.rectangle([x - 1, y1 - 2, x + 3, y1 - 2], fill=S_ST_HI)


def entry(d, x0, y0, x1, y1):
    """The way in: one lattice leaf slid back on the dark of the entry (a step
    up into the house, a lamp in dim gold inside), the other closed, under a
    gilt-nailed head."""
    d.rectangle([x0, y0, x1, y1], fill=S_LQ)
    m = (x0 + x1) // 2
    d.rectangle([x0 + 1, y0 + 7, m, y1], fill=S_DARK)             # the open half
    d.rectangle([x0 + 1, y0 + 7, m, y0 + 8], fill=S_DARK_LO)
    d.rectangle([x0 + 3, y1 - 12, m - 2, y1 - 6], fill=S_WD)      # a step up into the house
    d.rectangle([x0 + 3, y1 - 12, m - 2, y1 - 12], fill=S_WD_HI)
    d.rectangle([x0 + 3, y1 - 6, m - 2, y1 - 6], fill=S_WD_LO)
    d.rectangle([x0 + 4, y0 + 13, x0 + 6, y0 + 17], fill=S_GILT)  # the lamp
    d.point((x0 + 5, y0 + 14), fill=S_GILT_HI); d.rectangle([x0 + 4, y0 + 17, x0 + 6, y0 + 17], fill=S_GILT_LO)
    d.rectangle([m + 1, y0 + 7, x1 - 1, y1], fill=S_WD_LO)        # the closed leaf: a timber lattice
    for x in range(m + 2, x1 - 1, 2):
        d.rectangle([x, y0 + 8, x, y1 - 1], fill=S_WD)
    for y in (y0 + 16, y0 + 28):
        d.rectangle([m + 1, y, x1 - 1, y], fill=S_WD_LO)
    d.rectangle([x0, y0, x1, y0 + 6], fill=S_LQ_HI); d.rectangle([x0, y0, x1, y0], fill=S_LQ_EDGE)
    for x in range(x0 + 3, x1 - 1, 5):
        d.point((x, y0 + 3), fill=S_GILT)
    d.rectangle([x0, y0 + 6, x1, y0 + 6], fill=S_GILT_LO)


def step_stone(d, x0, x1, y):
    """The shoe stone before a door: one long pale slab, standing proud."""
    d.rectangle([x0, y, x1, y + 4], fill=rgb('c9ccd4'))
    d.line([(x0, y), (x1, y)], fill=WHITE); d.line([(x0, y + 4), (x1, y + 4)], fill=ASH_DK)
    d.line([(x0, y), (x0, y + 3)], fill=WHITE); d.line([(x1, y + 1), (x1, y + 4)], fill=ASH_LO)


def shoe_stone(d, x0, x1, y):
    """step_stone in the house look: the long slab before a door."""
    block(d, x0, y, x1, y + 4, S_ST, S_ST_HI, S_ST_DK)
    d.rectangle([x0 + 1, y + 3, x1 - 1, y + 3], fill=S_ST_LO)


def samurai_house(variant):
    if variant == 'a':
        im, d = canvas(5, 4)             # 160 x 128: thatch over an engawa, the door, a boarded bay
        thatch_roof(d, 3, 156, 16, 62, 43, 20)
        d.rectangle([8, 68, 151, 120], fill=S_LQ_LO)
        engawa(d, 12, 61, 74, 120, open_at=2)
        entry(d, 66, 72, 93, 116)
        mon(d, 79, 75, 3)
        lacquer_boards(d, 99, 69, 148, 113, studs=True)
        d.rectangle([108, 78, 139, 97], fill=S_LQ_LO)             # a barred window, gilt-framed
        d.rectangle([109, 79, 138, 96], fill=S_DARK); d.rectangle([109, 79, 138, 80], fill=S_DARK_LO)
        for x in range(111, 138, 4):
            d.rectangle([x, 79, x + 1, 96], fill=S_WD_LO); d.rectangle([x, 79, x, 96], fill=S_WD)
        d.rectangle([107, 77, 140, 77], fill=S_GILT); d.rectangle([107, 98, 140, 98], fill=S_GILT_LO)
        cut_stone(d, 98, 114, 149, 120, ch=7, bw=16)
        block(d, 138, 104, 147, 119, S_WD, S_WD_HI, S_WD_LO)      # a rain tub, a dipper on it
        d.rectangle([139, 108, 146, 108], fill=S_WD_LO); d.rectangle([139, 115, 146, 115], fill=S_WD_LO)
        d.rectangle([139, 102, 146, 103], fill=S_DARK); d.rectangle([141, 102, 145, 102], fill=S_WD_HI)
        for x in (8, 62, 95, 149):
            lq_post(d, x, 68, x + 2, 120, bands=False)
        block(d, 6, 121, 153, 123, S_ST_LO, S_ST, S_ST_DK)
        shoe_stone(d, 66, 93, 118)
    else:
        im, d = canvas(4, 4)             # 128 x 128: thatch above, a shingle pent over door and engawa
        thatch_roof(d, 5, 122, 16, 50, 31, 14)
        d.rectangle([8, 56, 119, 61], fill=S_LQ)                  # the wall between the two roofs
        d.rectangle([8, 56, 119, 56], fill=S_LQ_LO)
        for x in range(12, 118, 10):
            d.rectangle([x, 57, x + 5, 60], fill=S_ST_HI); d.rectangle([x, 57, x + 5, 57], fill=S_ST_LO)
        shingle_pent(d, 62, 73, 6, 121)
        d.rectangle([8, 76, 119, 120], fill=S_LQ_LO)
        lacquer_boards(d, 9, 77, 35, 113, studs=True)
        for y in range(84, 101):                                  # a round paper window in a gilt rim
            for x in range(14, 31):
                r2 = (x - 22) ** 2 + (y - 92) ** 2
                if r2 <= 72:
                    c = S_ST_HI if r2 <= 50 else (S_GILT_HI if x + y < 108 else (S_GILT_LO if x + y > 120 else S_GILT))
                    d.point((x, y), fill=S_ST if r2 <= 50 and (x in (18, 22, 26) or y == 92) else c)
        cut_stone(d, 9, 114, 36, 120, ch=7, bw=16)
        entry(d, 39, 78, 60, 116)
        engawa(d, 65, 118, 81, 120)
        for x in (6, 36, 61, 119):
            lq_post(d, x, 76, x + 2, 120, bands=False)
        block(d, 4, 121, 123, 123, S_ST_LO, S_ST, S_ST_DK)
        shoe_stone(d, 39, 60, 118)
    outline(im)
    return im


PULLEY = ['.oooo.', 'ohhhoo', 'ohllol', 'oollol', 'oooool', '.llll.']


def well():
    im, d = canvas(1, 2)                 # 32 x 64
    copper_roof(d, 2, 29, 6, 12, 6, 4, gilt=False)
    d.rectangle([4, 16, 27, 16], fill=S_LQ_LO)                    # the eave's shadow
    for x0 in (5, 24):                                            # the posts
        lq_post(d, x0, 17, x0 + 2, 47, bands=False)
    block(d, 4, 17, 27, 19, S_LQ, S_LQ_EDGE, S_LQ_LO)             # the beam the pulley hangs from
    pix(d, PULLEY, 13, 20, {'o': S_WD, 'h': S_WD_HI, 'l': S_WD_LO})
    d.rectangle([13, 26, 13, 44], fill=S_WD_HI); d.rectangle([18, 26, 18, 33], fill=S_WD_HI)   # the rope
    block(d, 16, 33, 21, 39, S_WD, S_WD_HI, S_WD_LO)              # the bucket
    d.rectangle([17, 36, 20, 36], fill=S_WD_LO)
    # the stone curb: a square of cut blocks, the dark of the shaft
    block(d, 3, 42, 28, 47, S_ST_HI, None, S_ST_LO)
    d.rectangle([7, 43, 24, 46], fill=S_DARK)
    d.rectangle([7, 43, 24, 43], fill=S_ST_DK)
    cut_stone(d, 3, 48, 28, 59, ch=6, bw=13, seed=1)
    d.rectangle([3, 48, 3, 59], fill=S_ST_HI); d.rectangle([28, 48, 28, 59], fill=S_ST_DK)
    d.rectangle([2, 60, 29, 61], fill=S_ST_LO); d.rectangle([2, 61, 29, 61], fill=S_ST_DK)
    for x, y in ((5, 58), (9, 59), (25, 57)):                     # moss at its foot
        d.point((x, y), fill=S_CU)
    outline(im)
    return im


def bough(d, x0, y0, x1, y1, w=3):
    """A pine bough a pixel at a time, `w` thick: lit along its top or west
    side, dark along its foot or east side."""
    steps = max(abs(x1 - x0), abs(y1 - y0))
    flat = abs(x1 - x0) >= abs(y1 - y0)
    for n in range(steps + 1):
        x, y = x0 + (x1 - x0) * n // steps, y0 + (y1 - y0) * n // steps
        if flat:
            d.rectangle([x, y, x, y + w - 1], fill=S_WD)
            d.point((x, y), fill=S_WD_HI); d.point((x, y + w - 1), fill=S_WD_LO)
        else:
            d.rectangle([x, y, x + w - 1, y], fill=S_WD)
            d.point((x, y), fill=S_WD_HI); d.point((x + w - 1, y), fill=S_WD_LO)


def propped_pine():
    im, d = canvas(3, 3)                 # 96 x 96
    ground_shade(d, 22, 88, 16)
    # the trunk leans east; one long limb runs out level and is carried on props
    bough(d, 17, 92, 19, 76, 7); bough(d, 19, 76, 27, 62, 7); bough(d, 27, 62, 28, 48, 6); bough(d, 28, 48, 22, 36, 5)
    bough(d, 30, 60, 46, 56, 5); bough(d, 46, 56, 66, 58, 5); bough(d, 66, 58, 90, 54, 4)
    bough(d, 30, 50, 40, 40, 3); bough(d, 40, 40, 52, 35, 3)
    bough(d, 25, 40, 14, 34, 3)
    for x, top in ((68, 62), (84, 59)):                           # the props: a post and a padded crutch
        block(d, x, top, x + 2, 92, S_WD, None, None)
        d.rectangle([x, top, x, 92], fill=S_WD_HI); d.rectangle([x + 2, top, x + 2, 92], fill=S_WD_LO)
        d.rectangle([x - 3, top - 1, x + 5, top + 1], fill=S_WD_LO); d.rectangle([x - 3, top - 1, x + 5, top - 1], fill=S_WD)
        d.rectangle([x - 1, top - 3, x + 3, top - 2], fill=S_TH_HI)   # straw rope padding
        d.rectangle([x - 2, 92, x + 4, 92], fill=S_ST_LO)
    foliage(im, [(12, 32, 12, 6), (24, 24, 15, 8), (44, 18, 14, 7), (56, 30, 12, 6), (30, 12, 11, 6),
                 (48, 49, 12, 6), (66, 50, 11, 5), (85, 47, 9, 5), (66, 41, 10, 5)], NEEDLE, 4)
    outline(im)
    return im


def kabuto_stand():
    im, d = canvas(2, 3)                 # 64 x 96
    # ---- a low dais and a folding screen in gold leaf behind ---------------------
    block(d, 4, 84, 59, 90, S_LQ, S_LQ_EDGE, S_LQ_LO)
    gold_band(d, 4, 86, 59, 2)
    block(d, 2, 91, 61, 93, S_ST, S_ST_HI, S_ST_DK)
    for i in range(4):                                            # four leaves of the screen, zig-zag
        x0, top = 6 + i * 13, 30 + (2 if i % 2 else 0)
        leaf, line, hi = (S_GILT_LO, S_GILT_DK, S_GILT) if i % 2 else (S_GILT, S_GILT_LO, S_GILT_HI)
        d.rectangle([x0, top, x0 + 12, 83], fill=S_LQ)
        d.rectangle([x0 + 1, top + 1, x0 + 11, 82], fill=leaf)
        for y in range(top + 9, 82, 9):                           # the squares of leaf
            d.rectangle([x0 + 1, y, x0 + 11, y], fill=line)
        d.rectangle([x0 + 6, top + 1, x0 + 6, 82], fill=line)
        d.rectangle([x0 + 1, top + 1, x0 + 11, top + 1], fill=hi)
    for k in range(9):                                            # a painted pine bough on the leaves
        d.point((10 + k, 62 - k), fill=S_CU_DK); d.point((45 + k, 66 - k), fill=S_CU_DK)
    for x, y in ((12, 57), (15, 54), (17, 51), (48, 60), (51, 57)):
        d.rectangle([x, y, x + 2, y + 1], fill=S_CU_LO)
    # ---- the armour chest ------------------------------------------------------------
    block(d, 19, 68, 44, 83, S_LQ, S_LQ_EDGE, S_LQ_LO)
    d.rectangle([20, 69, 43, 69], fill=S_LQ_HI)
    gold_band(d, 19, 71, 44, 1); gold_band(d, 19, 80, 44, 1)
    mon(d, 32, 76, 3)
    # ---- the cuirass: black plates laced in gold, shoulder guards, a skirt -------
    taper(d, 46, 62, (24, 39), (22, 41), S_LQ_HI)
    for y in range(48, 62, 3):
        d.rectangle([24, y, 39, y], fill=S_GILT if y % 2 else S_GILT_LO)
    taper(d, 46, 62, (24, 24), (22, 22), S_LQ_EDGE)
    d.rectangle([31, 46, 32, 62], fill=S_LQ_LO)
    for x0 in (16, 41):                                           # sode
        d.rectangle([x0, 45, x0 + 6, 58], fill=S_LQ)
        for y in range(47, 58, 3):
            d.rectangle([x0, y, x0 + 6, y], fill=S_GILT)
        d.rectangle([x0, 45, x0, 58], fill=S_LQ_EDGE); d.rectangle([x0 + 6, 45, x0 + 6, 58], fill=S_LQ_LO)
    for x0 in (22, 27, 32, 37):                                   # kusazuri tassets
        d.rectangle([x0, 62, x0 + 3, 67], fill=S_LQ)
        d.rectangle([x0, 64, x0 + 3, 64], fill=S_GILT); d.rectangle([x0, 66, x0 + 3, 66], fill=S_RED)
    # ---- the helmet: a black bowl, a flared neck guard, the mask, the crescent ----
    taper(d, 38, 44, (24, 39), (21, 42), S_LQ)                    # the shikoro
    d.rectangle([22, 42, 41, 42], fill=S_GILT); d.rectangle([23, 40, 40, 40], fill=S_GILT_LO)
    d.rectangle([27, 38, 36, 45], fill=S_LQ_HI)                   # the menpo: a dark iron half-mask
    d.rectangle([27, 38, 27, 45], fill=S_LQ_EDGE)
    d.rectangle([28, 40, 30, 40], fill=S_LQ_LO); d.rectangle([33, 40, 35, 40], fill=S_LQ_LO)
    d.point((31, 41), fill=S_LQ_EDGE); d.rectangle([32, 42, 32, 43], fill=S_LQ_EDGE)        # its nose
    d.rectangle([28, 45, 35, 45], fill=S_RED)                     # the cord under the chin
    for y in range(26, 36):                                       # the bowl
        for x in range(24, 40):
            if (2 * x - 63) ** 2 * 81 + (y - 35) ** 2 * 256 <= 256 * 81:
                rib = (x - 26) % 3 == 0 and y > 27
                d.point((x, y), fill=(S_LQ_EDGE if x < 31 else S_LQ_LO) if rib else S_LQ)
    d.rectangle([24, 35, 39, 37], fill=S_LQ_HI); d.rectangle([24, 35, 39, 35], fill=S_GILT)  # the peak
    # the crescent: one great thin moon of gold, its horns up, the east one longer
    moon = set()
    for y in range(4, 36):
        for x in range(8, 58):
            outer = ((x - 33) * 19) ** 2 + ((y - 14) * 23) ** 2 <= (23 * 19) ** 2
            inner = ((2 * x - 69) * 39) ** 2 + ((2 * y - 19) * 44) ** 2 <= (44 * 39) ** 2
            if outer and not inner and not (x < 14 and y < 14):
                moon.add((x, y))
    for x, y in sorted(moon):
        lit = (x - 1, y) not in moon and x < 33
        d.point((x, y), fill=S_GILT_HI if lit else (S_GILT if x < 46 else S_GILT_LO))
    block(d, 30, 31, 34, 34, S_GILT, None, S_GILT_LO); d.point((30, 31), fill=S_GILT_HI)   # its socket on the peak
    outline(im)
    return im


# ====================================================================================================
# in place of andon_lamp (2062 to 2084)
# ====================================================================================================
def andon_lamp():
    """The samurai quarter's lamp: a slim black-lacquer post with gilt bands
    carrying a square paper lantern, its paper dim gold, under a little copper
    cap seen from above."""
    im, d = canvas(1, 2)                 # 32 x 64
    block(d, 10, 58, 21, 61, S_ST, S_ST_HI, S_ST_DK)
    lq_post(d, 14, 27, 17, 58, bands=False)
    gold_band(d, 14, 30, 17, 2); gold_band(d, 14, 52, 17, 2)
    d.rectangle([8, 25, 23, 26], fill=S_LQ); d.rectangle([8, 25, 23, 25], fill=S_GILT_LO)   # the lantern's shelf
    d.rectangle([9, 10, 22, 24], fill=S_LQ)                       # its frame
    d.rectangle([10, 11, 21, 23], fill=S_GILT)                    # the paper, lit dim
    d.rectangle([10, 21, 21, 23], fill=S_GILT_LO)
    d.rectangle([12, 13, 13, 15], fill=S_GILT_HI); d.rectangle([18, 13, 19, 15], fill=S_GILT_HI)
    d.rectangle([15, 11, 16, 23], fill=S_LQ); d.rectangle([10, 17, 21, 17], fill=S_LQ)
    d.rectangle([9, 10, 9, 24], fill=S_LQ_EDGE); d.rectangle([22, 10, 22, 24], fill=S_LQ_LO)
    for y in range(4, 10):                                        # the copper cap: its west face lit, its east in shade
        w = 3 + (y - 4) * 2 - (y - 4) // 3
        for x in range(15 - w, 17 + w):
            c = S_CU_DK if y == 9 else (S_CU_HI if x < 15 - (y - 4) else (S_CU_LO if x > 16 + (y - 4) else S_CU))
            d.point((x, y), fill=c)
    block(d, 15, 1, 16, 3, S_GILT, None, S_GILT_LO); d.point((15, 1), fill=S_GILT_HI)
    outline(im)
    return im


# ====================================================================================================
# in place of samurai_store (2368 to 2400)
# ====================================================================================================
LOG = ['.hhh.', 'hhooo', 'hoxol', 'hoool', '.lll.']


def samurai_store():
    """A thatched outbuilding for a house court, 3x3: black boards, wide plank
    doors with iron straps, firewood stacked under the eave, a straw raincoat."""
    im, d = canvas(3, 3)                 # 96 x 96
    thatch_roof(d, 3, 92, 14, 40, 25, 12)
    d.rectangle([7, 46, 88, 88], fill=S_LQ_LO)
    lacquer_boards(d, 8, 47, 87, 83, studs=True)
    cut_stone(d, 7, 84, 88, 89, ch=6, bw=16)
    d.rectangle([33, 50, 62, 88], fill=S_LQ)                      # the doors (cell 1)
    for x0 in (34, 48):
        d.rectangle([x0, 52, x0 + 13, 88], fill=S_WD)
        d.rectangle([x0, 52, x0, 88], fill=S_WD_HI); d.rectangle([x0 + 13, 52, x0 + 13, 88], fill=S_WD_LO)
        for x in range(x0 + 3, x0 + 13, 4):
            d.rectangle([x, 52, x, 88], fill=S_WD_LO)
        for y in (58, 80):                                        # iron straps, gilt nails
            d.rectangle([x0, y, x0 + 13, y + 1], fill=S_LQ_HI); d.rectangle([x0, y, x0 + 13, y], fill=S_LQ_EDGE)
            d.point((x0 + 2, y), fill=S_GILT); d.point((x0 + 11, y), fill=S_GILT)
    block(d, 46, 68, 49, 72, S_GILT, None, S_GILT_LO); d.point((46, 68), fill=S_GILT_HI)   # the lock
    d.rectangle([33, 50, 62, 51], fill=S_LQ_HI); d.rectangle([33, 50, 62, 50], fill=S_GILT_LO)
    for row in range(3):                                          # firewood, stacked end-on (cell 0)
        for i in range(5 - row % 2):
            pix(d, LOG, 9 + i * 5 + (row % 2) * 2, 83 - row * 5, {'o': S_WD, 'h': S_WD_HI, 'l': S_WD_LO, 'x': S_WD_LO})
    taper(d, 56, 76, (70, 80), (66, 84), S_TH)                    # a straw raincoat on a peg (cell 2)
    for x in range(67, 84, 2):
        d.rectangle([x, 62 + x % 4, x, 76 + x % 3], fill=S_TH_LO)
    taper(d, 56, 76, (70, 70), (66, 66), S_TH_HI)
    d.rectangle([73, 53, 77, 56], fill=S_TH_DK)
    for y, x0, x1, c in ((49, 73, 77, S_TH_HI), (50, 71, 79, S_TH_HI), (51, 69, 81, S_TH), (52, 68, 82, S_TH),
                         (53, 68, 82, S_TH_LO), (54, 70, 80, S_TH_DK)):               # and its hat
        d.rectangle([x0, y, x1, y], fill=c)
    for x in (7, 31, 62, 86):
        lq_post(d, x, 46, x + 2, 88, bands=False)
    shoe_stone(d, 36, 59, 88)
    block(d, 5, 90, 90, 92, S_ST_LO, S_ST, S_ST_DK)
    outline(im)
    return im


# ====================================================================================================
# in place of STEPPING and stepping_stone (2463 to 2488)
# ====================================================================================================
# each stepping stone: its top row, then (x0, x1) a row
STEPPING = {'a': [(5, [(12, 19), (10, 22), (8, 24), (7, 25), (6, 26), (6, 26), (5, 27), (5, 27), (5, 27), (5, 27),
                       (6, 27), (6, 27), (6, 26), (7, 26), (7, 25), (8, 25), (9, 24), (10, 22), (12, 20)])],
            'b': [(4, [(8, 12), (6, 13), (4, 14), (3, 15), (3, 15), (3, 16), (4, 16), (4, 15), (5, 15), (6, 14),
                       (7, 12)]),
                  (16, [(20, 24), (18, 26), (17, 27), (16, 28), (16, 28), (16, 29), (16, 29), (17, 28), (17, 28),
                        (18, 27), (19, 26), (21, 24)])],
            'c': [(9, [(4, 27)] * 13)]}


def stepping_stone(variant):
    """Stepping stones to lay ON the gravel (flat, see-through round them, so
    no ink line): -a one broad stone, -b two smaller ones, -c a cut slab. Each
    is lit along its north and west arris, shaded along its south and east,
    worn pale in the middle, with its shadow on the gravel."""
    im, d = canvas(1, 1)                 # 32 x 32
    stones = [{(x, y0 + i) for i, (a, b) in enumerate(rows) for x in range(a, b + 1)}
              for y0, rows in STEPPING[variant]]
    for stone in stones:
        for x, y in sorted(stone):
            d.point((x + 1, y + 2), fill=S_ST_DK)
    for stone in stones:
        for x, y in sorted(stone):
            if (x, y - 1) not in stone or (x - 1, y) not in stone:
                c = S_ST_HI
            elif (x, y + 1) not in stone or (x + 1, y) not in stone:
                c = S_ST_LO
            elif all((x + dx, y + dy) in stone for dx, dy in ((-4, 0), (4, 0), (0, -4), (0, 4))):
                c = S_WORN
            else:
                c = S_ST
            d.point((x, y), fill=c)
    return im
```
