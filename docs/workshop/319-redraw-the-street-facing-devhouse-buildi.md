# Redraw the street-facing Devhouse buildings in the house look (#319, part 2 of 7 of #295)

## Context

`gamev2/tools/generate_devhouse_art.py` draws 37 `devhouse-*` sprites. Two of them stand on a street:
`devhouse-tokyo_0_0` (5x8, `Park` 10,9) and `devhouse-osaka_0_0` (3x7, `Osaka` 9,10). Both predate the house
look: a front elevation with no roof (Tokyo's tank and rail and Osaka's garden are drawn side-on above the
wall), windows lit yellow (`LIT`, `LIT_HI`), smooth green discs for plants, a `0a1627` outline, and 21 and 24
colours that are in no GuttyKreum sheet.

Outcome: the two buildings read like the pack's buildings beside them (a roof seen from above, dark glass with
a slanted glare, ragged foliage, sheet colours only, navy outline) with the same keys, sizes, anchors and door
cells. Nothing else is drawn for the street: every other `devhouse-*` sprite is placed only inside
`Devhouse*` rooms (checked in `config.json`) and belongs to #325, so it is not touched here.

## Approach

Rewrite only the section `# ---- the two houses, from the street ----` of the generator (the local `pane`,
`devhouse_tokyo`, `lattice`, `devhouse_osaka`) with the code in the appendix. It was prototyped during design
and dropped into a scratch copy of the generator: the other 35 PNGs and `config.json` came out identical, the
two buildings have 40 and 41 colours, all sheet colours, no colour over 18% of a sprite, and every pixel next
to a clear one is `172459`. Before/after pictures are on the ticket (`319-sprites-before-after.png`,
`319-park-before-after.png`, `319-osaka-before-after.png`).

- **Own palette, shared helpers.** The section gets its own block of pack colours, all named `S_*`, so no
  constant imported from `generate_hokkaido.py` or `generate_house_art.py` changes and the interior sprites
  draw exactly as before. Glass, foliage and roof tile come from `generate_sendai_art.py` (`pane`, `foliage`,
  `roof_tile`, `speck`, `LEAF`; importing it has no side effects, and it is the same on this branch and on
  `master`). `house_look.py` (#279) is only on `master` and has none of these helpers, so it is not used.
- **Roofs.** Tokyo: rows 4-43 are a flat roof seen from above, built as the 7-Eleven's is (steel coping lit
  top and left, slate panels with staggered joints), carrying the water tank, a condenser, the aerial and the
  lift's motor room with its own small roof. Osaka: rows 1-41 are the roof garden seen from above (bamboo
  fence along the back, raked gravel, stepping stones, a rock, foliage clumps with azalea), inside an eave of
  the pack's kawara (rows 42-53), and the ground floor's pent roof is the same kawara (rows 180-191).
- **Room for the roof** comes from shorter storeys, not a bigger sprite: Tokyo's five upper storeys are 35
  rows (were 39) from row 44 and the ground floor is rows 219-255; Osaka's three upper storeys are 42 rows
  (were 48) from row 54 and the ground floor still starts at row 180. Columns are unchanged, so both doors
  stay where they were: Tokyo x 99-128 (cell column 3), Osaka x 33-62 (cell column 1), each in the bottom cell.
- **Glass** is `pane()`: `2c2d51` with `4b6396` glare. What was lit becomes a room with its blind part down
  (Tokyo 3F and 6F), shoji with one screen slid open on the dark (Tokyo 5F, Osaka 4F), bars over the dark
  (Osaka 3F), dark glass doors (Tokyo) and a noren over a dark hall (Osaka). The name is dim gold `f3d890`
  on a dark board in Tokyo and dark on a wooden board in Osaka.
- **Outline** is `outline(im, NAVY)`, as the ticket says and as the home kit does on `master` (#330). The
  dark roof tone is `293038`, not the worked examples' `2b373c`, which is in no sheet (#375, #378).

The appendix is the starting point, not a constraint: tune by eye against the pack on a contact sheet, as long
as what "Data and interfaces" and the new test hold stays true.

## Changes

- `gamev2/tools/generate_devhouse_art.py`
  - Imports: add `NAVY` to the `generate_hokkaido` import; add
    `from generate_sendai_art import pane as glass, foliage, roof_tile, speck, LEAF`. Leave the
    `from generate_house_art import (...)` statement as it is (a test on `master` parses it and wants more
    than 20 names), and leave the module's other constants alone even where the street no longer uses them.
  - Replace the street section (from `def pane(` up to, not including, `SPRITES = {`) with the appendix.
    `SPRITES`, `main()` and every other builder are untouched.
  - Docstring: the `outside` entries say what is drawn now (a roof seen from above; the roof garden inside a
    tiled eave), and the paragraph on style says the two street buildings are in the house look (sheet
    colours, navy outline, dark glass) while the rest waits for #325.
- `gamev2/assets/sprites/devhouse-tokyo_0_0.png`, `devhouse-osaka_0_0.png`: rewritten by
  `python3 tools/generate_devhouse_art.py`. No other sprite and not `config.json` may change (`git status`).
- `gamev2/assets/map/world-map.png`: rebuild with `python3 tools/make_worldmap.py --pil` (the overworld
  picture is drawn from the sprites; `check_generators.py` fails on a stale one). Only this file changes.
- `gamev2/tools/tests/devhouse.test.js`: one new test (below).
- Docs: `gamev2/docs/generators-and-checks.md` (the `generate_devhouse_art.py` paragraph: the two buildings
  are in the house look, helpers from `generate_sendai_art.py`, the rest is #325);
  `gamev2/docs/landmarks-and-towns.md` ("The Devhouses of Tokyo and Osaka", `Outside` row: a flat roof seen
  from above / the roof garden seen from above inside a tiled eave). `buildings-and-street-props.md` needs
  no change (sizes, doors and places are the same).
- No map, prefab, `roomgen`, `Glows.js` or `src/` change. Rooms whose look changes: `Park` and `Osaka`.

Commit as the ticket asks: `gamev2: <what changed> (#295)`, one commit, no attribution line.

## Data and interfaces

None change. Held fixed: the 37 keys and labels; PNG sizes 320x512 and 192x448; `spriteMetadata`
`{frameCount: 1, anchorX: 32/w, anchorY: 32/h}` (0.1, 0.0625 and 1/6, 1/14), no glow entry;
`roomgen.DEVHOUSE_DOORS` (`(3, 7)` and `(1, 6)`); the prefabs `building(5, 8, door=3)` and
`building(3, 7, door=1)`; `tilePalette`.

## Tests

New test in `gamev2/tools/tests/devhouse.test.js`, named
`the two Devhouses seen from the street are in the house look: sheet colours, a navy edge, dark glass, nothing lit (#319)`.
For `devhouse-tokyo_0_0` and `devhouse-osaka_0_0` (decode with `tools/png`, as the file already does):

1. size 320x512 / 192x448; every 2x2 block from an even origin is one colour; alpha is 0 or 255;
   `spriteMetadata` is exactly `{frameCount: 1, anchorX: 32/w, anchorY: 32/h}`.
2. every opaque colour is an opaque colour of a PNG under `../art-source/GuttyKreum` whose name does not
   start with `preview` (walk the folder, as `house-art.test.js` does on `master`; keep the helper local to
   the test so the file does not depend on that one), and none is `f2c66a`, `fbe6a4`, `f9c22e`, `f0943a`
   or `e8623a`.
3. every opaque pixel with a clear 4-neighbour inside the canvas is `172459`.
4. both hold `2c2d51` and `4b6396` (the glass); no colour covers more than a quarter of the opaque pixels.
5. a roof seen from above: Tokyo's pixel at full-size (188, 62) is one of the slate tones
   `5b6c79`, `698592`, `444f5e` (the prototype has `5b6c79`); Osaka's row y = 96 holds a kawara tone
   (`2e4040` or `395050`).
6. the door cell is glass or hall, not lit: Tokyo full-size (220, 480) and Osaka (80, 432) are `2c2d51`
   or `4b6396` (the prototype has `2c2d51` at both).

Loosen 5 and 6 to whatever the final drawing has if it was tuned; keep them about the roof and the door.

Run, from `gamev2/`:

```bash
python3 tools/generate_devhouse_art.py     # "37 devhouse sprites written"; git status: the two PNGs only
python3 tools/make_worldmap.py --pil
node tools/test_game.js
python3 tools/test_blog_to_npc.py
node tools/play.js check
python3 tools/check_generators.py          # no DRIFT; generate_devhouse_art ok
python3 tools/sync_cities.py --check
node tools/browser/regress.js              # how: tools/browser/README.md
```

By eye, before and after, saved to `/work/media/`:

- `node tools/play.js render Park out.png` and `... render Osaka out.png`, cropped to the building: the roof
  reads as a roof, the door is findable, the building sits with its neighbours (Tokyo Tower's square; Don
  Takote and the blue high-rise).
- `render DevhouseTokyo1F`, `DevhouseTokyo6F`, `DevhouseOsaka1F`, `DevhouseOsaka4F`: pixel-identical before
  and after (nothing indoors moved).
- a contact sheet of the two sprites beside `seven-eleven_0_0`, `sendai-pub_0_0`, `kanazawa-chaya-a_0_0`,
  `highrise-apartment_0_0` and `machiya-black_0_0`.
- in a browser, desktop and a phone size, by day and with `?tod=night`: walk to each door in `Park` and
  `Osaka`, go in and come out; walk behind each building's top two rows.

The summary names any part that still reads flat. Known from the prototype: Tokyo's shutter and the blank
tile under its 2F windows are the plainest areas; Osaka's side fences are two pixels wide.

## Risks and open questions

- **This branch is behind `master`**, where #330 has landed: `generate_house_art.py` there repaints its own
  sprites but keeps every constant value, and the generator, its test file, `generate_sendai_art.py` and
  `generate_hokkaido.py` are the same on both, so this change is the same on either base. `master` has
  rebuilt `assets/map/world-map.png` and edited both doc files elsewhere: after a merge, rebuild the map with
  the command above rather than resolving it by hand.
- **#325 (interiors) edits the same file.** It should leave the `S_*` block and the street section alone; a
  save-time repaint there (as #330's `SWAP` does for the home kit) must skip these two keys.
- **The recipe on `master` names `0a1627` as the silhouette ink** (`docs/generators-and-checks.md`), while
  the ticket and the redrawn towns and home kit use navy `172459`. This design follows the ticket.
- **Colour count.** 40 and 41, above the recipe's 24 for an object; the pack's own buildings are in the same
  range (`highrise-apartment` 60, `machiya-black` 62), and no test caps it. Not worth merging tones for.
- **Osaka's door is no longer a lit rectangle.** It reads by the noren and the name board. If it is hard to
  find at phone size, lighten the hall's step (`S_SOOT_HI`) rather than lighting the doorway.
- **Night.** Neither sprite has a `Glows.js` entry and none is added; the fronts were only painted yellow.
  If the owner wants the houses lit at night, that is a glow entry, a separate change.

## Appendix: the street section, as prototyped

Replaces everything from `def pane(` to just before `SPRITES = {`. Coordinates are half-size pixels
(32 a cell). `R`, `H`, `V`, `P`, `oval`, `soft`, `letters`, `canvas`, `outline`, `rgb` and `INK` are the
generator's own or already imported. Rectangles, points and pixel writes only.

```python
# the pack's colours, for the two houses seen from the street
S_WALL, S_WALL_HI, S_WALL_LO, S_WALL_DK = rgb('dae2e4'), rgb('fafcfd'), rgb('bcc7cc'), rgb('a4b0b5')
S_TOWER, S_TOWER_HI, S_TOWER_LO, S_TOWER_DK = rgb('a4b0b5'), rgb('bcc7cc'), rgb('919ea4'), rgb('848295')
S_FRAME, S_FRAME_HI, S_FRAME_LO = rgb('47485d'), rgb('5f6177'), rgb('2a2636')
S_METAL, S_METAL_HI, S_METAL_LO = rgb('94a2a8'), rgb('d1e2eb'), rgb('646e86')
S_SLATE, S_SLATE_HI, S_SLATE_JOINT, S_SLATE_LO = rgb('5b6c79'), rgb('698592'), rgb('444f5e'), rgb('293038')
S_DARK, S_GLARE = rgb('2c2d51'), rgb('4b6396')
S_SHOJI, S_SHOJI_HI, S_SHOJI_LO = rgb('e4cecc'), rgb('fafcfd'), rgb('d2bab0')
S_TIMBER, S_TIMBER_HI, S_TIMBER_LO, S_TIMBER_DK = rgb('aa775f'), rgb('c18e75'), rgb('7f513b'), rgb('5a3827')
S_TIMBER_INK = rgb('3f210f')
S_POT, S_POT_HI, S_POT_LO = rgb('aa4d31'), rgb('d16b56'), rgb('8a3a22')
S_PINK, S_PINK_HI, S_PINK_LO = rgb('bb6479'), rgb('d78bc1'), rgb('83374f')
S_CLOTH, S_CLOTH_HI, S_CLOTH_LO = rgb('314b8e'), rgb('4b6396'), rgb('232449')
S_SIGN, S_BOARD_HI = rgb('f3d890'), rgb('ebbca2')
S_WASH, S_WASH_LO = rgb('588cc6'), rgb('425faa')
S_SOOT, S_SOOT_HI, S_SOOT_LO = rgb('3c3a4c'), rgb('47485d'), rgb('2a2636')
S_BAMBOO, S_BAMBOO_HI, S_BAMBOO_LO, S_BAMBOO_DK = rgb('c6aa71'), rgb('e3c587'), rgb('a7843b'), rgb('86624f')
S_REED, S_REED_LO = rgb('be9e8c'), rgb('aa775f')
S_ROCK, S_ROCK_HI, S_ROCK_LO = rgb('848295'), rgb('bcc7cc'), rgb('53596d')
S_RIDGE, S_RIDGE_HI, S_EAVE = rgb('434857'), rgb('53596d'), rgb('191c2a')


def window(d, x0, y0, x1, y1, frame=S_FRAME, step=9):
    """The pack's dark glass with its slanted glare, in a frame."""
    R(d, x0, y0, x1, y1, frame)
    glass(d, x0 + 1, y0 + 1, x1 - 1, y1 - 1, step)


def flat_roof(d, x0, y0, x1, y1):
    """A flat roof seen from above: a steel coping lit on its top and left, slate panels inside it."""
    R(d, x0, y0, x1, y1, S_METAL)
    H(d, x0, x1, y0, S_METAL_HI); V(d, x0, y0, y1, S_METAL_HI)
    H(d, x0, x1, y1, S_METAL_LO); V(d, x1, y0 + 1, y1, S_METAL_LO)
    R(d, x0 + 3, y0 + 3, x1 - 3, y1 - 3, NAVY)
    x0, y0, x1, y1 = x0 + 4, y0 + 4, x1 - 4, y1 - 4
    R(d, x0, y0, x1, y1, S_SLATE)
    for n, x in enumerate(range(x0, x1, 9)):               # panels, their joints staggered
        V(d, x, y0, y1, S_SLATE_JOINT)
        H(d, x + 1, min(x + 8, x1), y0, S_SLATE_HI)
        for y in range(y0 + 4 + n % 3 * 5, y1, 13):
            H(d, x + 1, min(x + 8, x1), y, S_SLATE_JOINT)
            if y + 1 < y1:
                H(d, x + 1, min(x + 8, x1), y + 1, S_SLATE_HI)
    R(d, x0, y1 - 1, x1, y1, S_SLATE_LO); R(d, x1 - 1, y0, x1, y1, S_SLATE_LO)


def devhouse_tokyo():
    """160x256: a flat roof seen from above, five storeys of 35 rows and a ground floor of 37."""
    im, d = canvas(5, 8)
    flat_roof(d, 1, 4, 158, 43)
    # on the roof: the water tank, a condenser, an aerial, the lift's motor room over the stair tower
    R(d, 19, 32, 44, 35, S_SLATE_LO)
    R(d, 14, 14, 40, 33, NAVY); R(d, 15, 15, 39, 32, S_METAL)
    R(d, 15, 15, 18, 32, S_METAL_HI); R(d, 34, 15, 39, 32, S_METAL_LO)
    for y in (22, 27):
        H(d, 15, 39, y, S_METAL_LO)
    oval(d, 14, 7, 40, 20, NAVY); oval(d, 15, 8, 39, 19, S_WALL_LO)
    oval(d, 17, 9, 33, 15, S_METAL_HI); R(d, 25, 12, 30, 15, S_METAL); H(d, 25, 30, 12, S_WALL_HI)
    R(d, 52, 34, 71, 35, S_SLATE_LO)
    R(d, 50, 20, 69, 33, NAVY); R(d, 51, 21, 68, 32, S_METAL); H(d, 51, 68, 21, S_METAL_HI)
    R(d, 53, 24, 62, 31, S_METAL_LO); R(d, 55, 26, 60, 29, S_FRAME); P(d, S_METAL_HI, (57, 27))
    R(d, 64, 24, 66, 25, S_DARK); R(d, 64, 28, 66, 29, S_DARK)
    R(d, 82, 25, 90, 26, S_SLATE_LO)
    R(d, 79, 22, 87, 25, S_FRAME); H(d, 79, 87, 22, S_FRAME_HI)
    V(d, 83, 1, 21, S_FRAME); H(d, 79, 87, 3, S_FRAME); H(d, 80, 86, 6, S_FRAME); H(d, 81, 85, 9, S_FRAME)
    R(d, 106, 36, 154, 38, S_SLATE_LO); R(d, 152, 10, 154, 36, S_SLATE_LO)
    R(d, 103, 1, 151, 35, NAVY)
    R(d, 104, 2, 150, 20, S_METAL); H(d, 104, 150, 2, S_METAL_HI); V(d, 104, 2, 20, S_METAL_HI)
    H(d, 104, 150, 20, S_METAL_LO); V(d, 150, 3, 20, S_METAL_LO)
    R(d, 107, 5, 147, 17, NAVY); R(d, 108, 6, 146, 16, S_SLATE_HI)
    for x in range(108, 146, 9):
        V(d, x, 6, 16, S_SLATE)
    R(d, 108, 15, 146, 16, S_SLATE); R(d, 145, 6, 146, 16, S_SLATE)
    R(d, 104, 21, 150, 34, S_TOWER); H(d, 104, 150, 21, S_TOWER_DK); H(d, 104, 150, 22, S_TOWER_LO)
    for y in (27, 33):
        H(d, 104, 150, y, S_TOWER_LO)
    V(d, 104, 23, 34, S_TOWER_HI); V(d, 150, 21, 34, S_TOWER_DK)
    R(d, 110, 24, 125, 31, S_FRAME)
    for y in range(25, 31, 2):
        H(d, 111, 124, y, S_METAL); H(d, 111, 124, y + 1, S_METAL_LO)
    R(d, 132, 23, 143, 34, S_FRAME); R(d, 133, 24, 142, 34, S_METAL); V(d, 133, 24, 34, S_METAL_HI)
    V(d, 142, 24, 34, S_METAL_LO); P(d, S_FRAME, (140, 29), (140, 30))
    # the body: pale tile, and the stair tower in grey tile up the east side
    R(d, 1, 44, 158, 255, S_WALL); R(d, 96, 44, 158, 255, S_TOWER)
    for y in range(49, 256, 6):                            # the courses of tile
        H(d, 2, 95, y, S_WALL_LO); H(d, 98, 157, y, S_TOWER_LO)
    R(d, 1, 44, 95, 45, S_WALL_DK); R(d, 96, 44, 158, 45, S_TOWER_DK)                # the coping's shade
    V(d, 1, 46, 255, S_WALL_HI); V(d, 158, 46, 255, S_TOWER_DK)
    V(d, 96, 46, 255, S_TOWER_DK); V(d, 97, 46, 255, S_TOWER_HI)
    for n in range(6, 0, -1):                              # the top floor first
        y = 44 + (6 - n) * 35
        if n < 6:                                          # the slab between floors
            R(d, 1, y, 95, y + 1, S_WALL_DK); H(d, 1, 95, y, S_WALL_HI)
            R(d, 96, y, 158, y + 1, S_TOWER_DK); H(d, 97, 158, y, S_TOWER_HI)
        if n == 1:
            break
        # the stair tower: one tall landing window a floor, and a small one beside it
        window(d, 132, y + 5, 151, y + 30, step=7)
        V(d, 141, y + 6, y + 29, S_FRAME); V(d, 142, y + 6, y + 29, S_FRAME_HI)
        for gy in (y + 13, y + 22):
            H(d, 133, 150, gy, S_FRAME)
        H(d, 131, 152, y + 31, S_TOWER_HI); H(d, 131, 152, y + 32, S_TOWER_DK)
        window(d, 104, y + 11, 120, y + 21, step=7)
        V(d, 112, y + 12, y + 20, S_FRAME)
        H(d, 103, 121, y + 22, S_TOWER_HI); H(d, 103, 121, y + 23, S_TOWER_DK)
        # the rooms: three windows over a balcony
        for i, x0 in enumerate((6, 35, 64)):
            x1, y0, y1 = x0 + 25, y + 5, y + 20
            R(d, x0, y0, x1, y1, S_FRAME)
            if n == 2:                                     # the floor that is not ours: blinds down
                R(d, x0 + 1, y0 + 1, x1 - 1, y1 - 1, S_WALL_LO)
                for by in range(y0 + 3, y1, 3):
                    H(d, x0 + 1, x1 - 1, by, S_METAL)
                H(d, x0 + 1, x1 - 1, y0 + 1, S_WALL_DK)
            elif n == 5:                                   # the tatami room: paper screens, one slid open
                R(d, x0 + 1, y0 + 1, x1 - 1, y1 - 1, S_SHOJI)
                for bx in range(x0 + 5, x1, 5):
                    V(d, bx, y0 + 1, y1 - 1, S_TIMBER)
                H(d, x0 + 1, x1 - 1, y0 + 8, S_TIMBER)
                H(d, x0 + 1, x1 - 1, y0 + 1, S_SHOJI_LO)
                if i == 1:
                    glass(d, x0 + 16, y0 + 1, x1 - 1, y1 - 1, 7)
                    V(d, x0 + 15, y0 + 1, y1 - 1, S_TIMBER_LO)
            else:
                glass(d, x0 + 1, y0 + 1, x1 - 1, y1 - 1)
                V(d, x0 + 12, y0 + 1, y1 - 1, S_FRAME); V(d, x0 + 13, y0 + 1, y1 - 1, S_FRAME_HI)
                if n == 4 and i != 1:                      # curtains half drawn
                    R(d, x0 + 1, y0 + 1, x0 + 5, y1 - 1, S_PINK); V(d, x0 + 3, y0 + 1, y1 - 1, S_PINK_LO)
                    V(d, x0 + 1, y0 + 1, y1 - 1, S_PINK_HI)
                if (n, i) in ((3, 0), (3, 1), (6, 2)):     # a roller blind part down
                    R(d, x0 + 1, y0 + 1, x1 - 1, y0 + 7, S_SHOJI); H(d, x0 + 1, x1 - 1, y0 + 8, S_SHOJI_LO)
                    V(d, x0 + 12, y0 + 1, y0 + 8, S_FRAME); V(d, x0 + 13, y0 + 1, y0 + 8, S_FRAME_HI)
            H(d, x0, x1, y0, S_FRAME_LO)
            if n == 2:
                H(d, x0 - 1, x1 + 1, y1 + 1, S_WALL_HI); H(d, x0 - 1, x1 + 1, y1 + 2, S_WALL_DK)
        if n > 2:                                          # the balcony: a rail of bars, something on it
            R(d, 4, y + 22, 92, y + 23, S_FRAME); H(d, 4, 92, y + 22, S_FRAME_HI)
            for bx in range(5, 92, 4):
                V(d, bx, y + 24, y + 30, S_FRAME)
            R(d, 4, y + 31, 92, y + 32, S_WALL_DK); H(d, 4, 92, y + 31, S_WALL_HI)
            H(d, 5, 93, y + 33, S_WALL_LO)
        if n == 6:                                         # a plant in the sun
            R(d, 11, y + 25, 17, y + 30, S_POT); H(d, 11, 17, y + 25, S_POT_HI); R(d, 16, y + 26, 17, y + 30, S_POT_LO)
            foliage(im, [(14, y + 19, 7, 6), (10, y + 21, 4, 4), (18, y + 22, 4, 3)], LEAF, 3)
        if n == 4:                                         # the washing
            H(d, 40, 68, y + 23, S_METAL_HI)
            R(d, 44, y + 24, 49, y + 30, S_WALL_HI); H(d, 44, 49, y + 30, S_WALL_LO)
            R(d, 52, y + 24, 56, y + 29, S_WASH); H(d, 52, 56, y + 29, S_WASH_LO)
            R(d, 59, y + 24, 63, y + 30, S_POT_HI); H(d, 59, 63, y + 30, S_POT)
        if n == 3:                                         # the air conditioner's box
            R(d, 69, y + 23, 85, y + 31, S_FRAME); R(d, 70, y + 24, 84, y + 30, S_METAL_HI)
            oval(d, 72, y + 25, 78, y + 30, S_METAL_LO); P(d, S_FRAME, (75, y + 27), (75, y + 28))
            H(d, 70, 84, y + 30, S_METAL); R(d, 80, y + 26, 83, y + 27, S_METAL)
    # the ground floor: a shutter that is never up, and the way in under the name
    y = 219
    R(d, 5, y + 3, 69, 253, S_FRAME); H(d, 5, 69, y + 3, S_FRAME_HI)
    R(d, 7, y + 7, 67, 252, S_METAL)
    for sy in range(y + 8, 252, 3):
        H(d, 7, 67, sy, S_METAL_LO); H(d, 7, 67, sy + 1, S_METAL_HI)
    V(d, 67, y + 7, 252, S_METAL_LO)
    R(d, 74, y + 11, 88, y + 25, S_FRAME); R(d, 75, y + 12, 87, y + 24, S_METAL_LO)               # the post boxes
    for py in range(y + 15, y + 24, 3):
        H(d, 75, 87, py, S_FRAME_LO); H(d, 75, 87, py + 1, S_ROCK)
    V(d, 81, y + 12, y + 24, S_FRAME_LO)
    R(d, 96, y + 2, 131, y + 10, S_FRAME_LO); H(d, 96, 131, y + 2, S_FRAME); H(d, 96, 131, y + 10, INK)   # the name board
    letters(d, 98, y + 4, 'DEVHOUSE', S_SIGN)
    R(d, 99, y + 11, 128, 255, S_FRAME)                      # the door: two leaves of dark glass
    glass(d, 101, y + 13, 113, 251, 7); glass(d, 115, y + 13, 126, 251, 7)
    R(d, 101, 247, 113, 251, S_FRAME_HI); R(d, 115, 247, 126, 251, S_FRAME_HI)
    R(d, 111, y + 20, 112, y + 27, S_METAL_HI); R(d, 116, y + 20, 117, y + 27, S_METAL_HI)
    R(d, 132, y + 9, 139, y + 21, S_FRAME); R(d, 133, y + 10, 138, y + 13, S_DARK)                # the intercom
    P(d, S_GLARE, (133, y + 13), (134, y + 12), (135, y + 11), (136, y + 10))
    for py in (y + 15, y + 17, y + 19):
        P(d, S_METAL_HI, (134, py), (136, py), (138, py))
    P(d, S_POT_HI, (138, y + 10))
    R(d, 1, 252, 158, 253, S_ROCK); R(d, 1, 254, 158, 255, S_ROCK_LO)                            # the kerb
    H(d, 1, 158, 252, S_WALL_DK)
    R(d, 99, 252, 128, 255, S_WALL_DK); H(d, 99, 128, 252, S_WALL_LO)
    R(d, 144, 242, 153, 251, S_POT); H(d, 144, 153, 242, S_POT_HI); R(d, 151, 243, 153, 251, S_POT_LO)   # a pot by the door
    foliage(im, [(150, 234, 7, 8), (146, 238, 4, 4), (154, 239, 4, 5), (150, 228, 5, 4)], LEAF, 5)
    outline(im, NAVY)
    return im


def kawara(im, d, x0, y0, x1, y1):
    """A band of the pack's roof tile: a ridge course, the tiles, a dark eave."""
    px = im.load()
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            px[x, y] = roof_tile(x, y - y0)
    R(d, x0, y0, x1, y0 + 2, S_RIDGE); H(d, x0, x1, y0, S_RIDGE_HI)
    R(d, x0, y1 - 1, x1, y1, S_EAVE)
    V(d, x0, y0, y1, NAVY); V(d, x1, y0, y1, NAVY)


def lattice(d, x0, y0, x1, y1, bar=S_TIMBER_LO):
    """A window behind wooden bars (koshi): the dark of the room between them."""
    R(d, x0, y0, x1, y1, S_DARK)
    for x in range(x0, x1 + 1, 3):
        V(d, x, y0, y1, bar)
    H(d, x0, x1, y0, S_TIMBER_DK); H(d, x0, x1, y1, S_TIMBER_DK)


def devhouse_osaka():
    """96x224: the roof garden seen from above inside a tiled eave, three storeys of 42 rows, the shop front."""
    im, d = canvas(3, 7)
    # the roof garden, seen from above: raked gravel inside a bamboo fence
    R(d, 1, 9, 94, 41, S_WALL)
    for y in range(20, 42):
        for x in range(3, 93):
            s = speck(x, y, 11)
            if y % 3 == 0:
                P(d, S_WALL_LO if s > 12 else S_WALL_DK, (x, y))
            elif s < 7:
                P(d, S_WALL_HI, (x, y))
            elif s > 95:
                P(d, S_WALL_DK, (x, y))
    R(d, 1, 9, 94, 18, S_BAMBOO)                             # the fence along the back
    for x in range(1, 95, 4):
        V(d, x, 11, 18, S_BAMBOO_HI); V(d, x + 3, 11, 18, S_BAMBOO_LO)
    H(d, 1, 94, 13, S_BAMBOO_DK); H(d, 1, 94, 14, S_BAMBOO_HI)
    R(d, 1, 9, 94, 10, S_TIMBER_LO); H(d, 1, 94, 9, S_TIMBER)
    H(d, 1, 94, 19, S_WALL_DK)
    for x in (1, 93):                                      # and down each side
        R(d, x, 19, x + 1, 41, S_BAMBOO_LO)
        for y in range(20, 41, 3):
            P(d, S_BAMBOO_HI, (x, y)); P(d, S_BAMBOO_DK, (x + 1, y + 1))
    for x0, y0 in ((45, 35), (40, 29), (47, 23)):          # stepping stones to the back
        soft(d, x0, y0, x0 + 7, y0 + 4, S_ROCK); H(d, x0 + 1, x0 + 6, y0, S_ROCK_HI)
        H(d, x0 + 1, x0 + 6, y0 + 4, S_ROCK_LO)
    oval(d, 62, 26, 76, 37, NAVY); oval(d, 63, 27, 75, 36, S_ROCK); oval(d, 64, 27, 72, 32, S_ROCK_HI)   # a rock
    oval(d, 66, 29, 75, 36, S_ROCK); R(d, 66, 35, 73, 36, S_ROCK_LO)
    foliage(im, [(17, 11, 14, 10), (36, 8, 9, 7), (78, 11, 13, 9), (88, 16, 5, 6)], LEAF, 21)
    foliage(im, [(13, 31, 8, 6), (22, 35, 5, 4), (84, 32, 6, 6)], LEAF, 31)
    for x, y in ((9, 29), (16, 32), (12, 34), (82, 30), (86, 34), (24, 34)):                 # azalea
        P(d, S_PINK_HI, (x, y), (x + 1, y)); P(d, S_PINK, (x, y + 1))
    kawara(im, d, 0, 42, 95, 53)                           # the eave round it
    # the body: charred boards round plaster
    R(d, 1, 54, 94, 223, S_SOOT)
    R(d, 1, 54, 94, 55, S_SOOT_LO)
    V(d, 1, 56, 223, S_SOOT_HI); V(d, 94, 54, 223, S_SOOT_LO)
    for n in (4, 3, 2):
        y = 54 + (4 - n) * 42
        R(d, 5, y + 2, 90, y + 33, S_SHOJI)                  # plaster between the posts
        R(d, 5, y + 2, 90, y + 3, S_SHOJI_LO)
        for x in range(5, 91):
            if (x + y) % 2:
                P(d, S_SHOJI_LO, (x, y + 4))
        for x in (5, 31, 64, 90):                          # the posts
            V(d, x, y + 2, y + 33, S_SOOT); V(d, x + (1 if x < 90 else -1), y + 4, y + 33, S_SHOJI_LO)
        y0, y1 = y + 7, y + 28
        if n == 4:                                         # the tatami room: paper screens, one slid open
            for x0 in (9, 35, 68):
                R(d, x0, y0, x0 + 18, y1, S_SHOJI_HI)
                for bx in range(x0 + 6, x0 + 18, 6):
                    V(d, bx, y0, y1, S_TIMBER)
                for by in range(y0 + 5, y1, 6):
                    H(d, x0, x0 + 18, by, S_TIMBER)
                H(d, x0, x0 + 18, y0 + 1, S_SHOJI_LO)
                if x0 == 35:
                    glass(d, x0, y0 + 1, x0 + 8, y1 - 1, 7); V(d, x0 + 9, y0, y1, S_TIMBER_LO)
                H(d, x0 - 1, x0 + 19, y0, S_TIMBER_DK); H(d, x0 - 1, x0 + 19, y1, S_TIMBER_DK)
                V(d, x0 - 1, y0, y1, S_TIMBER_DK); V(d, x0 + 19, y0, y1, S_TIMBER_DK)
        elif n == 3:                                       # bars, and a reed blind let down
            lattice(d, 9, y0, 27, y1); lattice(d, 35, y0, 60, y1); lattice(d, 68, y0, 86, y1)
            R(d, 68, y0, 86, y0 + 15, S_REED)
            for by in range(y0 + 1, y0 + 15, 2):
                H(d, 68, 86, by, S_REED_LO)
            H(d, 68, 86, y0 + 15, S_TIMBER_LO)
        else:                                              # glass in wooden frames
            for x0 in (9, 35, 68):
                w = 25 if x0 == 35 else 18
                window(d, x0, y0, x0 + w, y1, S_TIMBER_DK)
                V(d, x0 + w // 2, y0 + 1, y1 - 1, S_TIMBER_DK)
                H(d, x0 + 1, x0 + w - 1, y0 + 11, S_TIMBER_DK)
        R(d, 3, y + 30, 92, y + 31, S_TIMBER_DK); H(d, 3, 92, y + 30, S_TIMBER_LO)    # a rail of bars under the windows
        for bx in range(4, 92, 3):
            V(d, bx, y + 32, y + 37, S_TIMBER_DK)
        R(d, 1, y + 38, 94, y + 41, S_SOOT_LO); H(d, 1, 94, y + 38, S_SOOT_HI)       # the floor's beam
    # the ground floor: a pent roof of tiles, the name, a noren over the door, bars either side
    y = 180
    kawara(im, d, 0, y, 95, y + 11)
    R(d, 2, y + 12, 93, 223, S_TIMBER_DK); R(d, 2, y + 12, 93, y + 13, S_TIMBER_INK)
    lattice(d, 5, y + 16, 27, 216, S_TIMBER); lattice(d, 68, y + 16, 90, 216, S_TIMBER)
    R(d, 3, 217, 29, 222, S_ROCK); R(d, 66, 217, 92, 222, S_ROCK)
    H(d, 3, 29, 217, S_ROCK_HI); H(d, 66, 92, 217, S_ROCK_HI); H(d, 3, 29, 222, S_ROCK_LO); H(d, 66, 92, 222, S_ROCK_LO)
    R(d, 32, y + 12, 63, y + 20, S_TIMBER_HI); H(d, 32, 63, y + 12, S_BOARD_HI)              # the name board
    H(d, 32, 63, y + 20, S_TIMBER_LO)
    letters(d, 33, y + 14, 'DEVHOUSE', S_SOOT_LO)
    R(d, 33, y + 21, 62, 223, S_DARK)                        # the doorway: the dark of the hall
    R(d, 33, y + 21, 62, y + 22, S_TIMBER_LO)
    R(d, 33, 218, 62, 223, S_SOOT); H(d, 33, 62, 218, S_SOOT_HI)
    V(d, 47, y + 35, 217, S_TIMBER_LO); V(d, 48, y + 35, 217, S_TIMBER_DK)
    for x0 in (34, 44, 54):                                # the noren, three widths of indigo
        R(d, x0, y + 23, x0 + 8, y + 34, S_CLOTH)
        V(d, x0, y + 23, y + 34, S_CLOTH_HI); H(d, x0, x0 + 8, y + 34, S_CLOTH_LO)
        R(d, x0 + 3, y + 27, x0 + 5, y + 29, S_SHOJI); P(d, S_CLOTH, (x0 + 4, y + 28))
    outline(im, NAVY)
    return im
```
