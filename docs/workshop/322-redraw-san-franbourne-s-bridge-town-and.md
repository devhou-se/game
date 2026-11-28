# Design: San Franbourne's bridge, town and landmark sprites in the house look (#322, part 3 of 5 of #292)

## Context

`gamev2/tools/generate_sanfranbourne_art.py` draws every `sfb-*` sprite. Sixteen of them are this
ticket's: `sfb-clocks-station`, `sfb-bridge-tower`, `sfb-bridge-cable-w/-e`, `sfb-rowers`,
`sfb-lady-a..d`, `sfb-mural-a..c`, `sfb-coffee`, `sfb-crates`, `sfb-pyramid`, `sfb-spire`. They were drawn
before the house look (`docs/generators-and-checks.md`, "House look: GuttyKreum"): most of their colours
are not in the GuttyKreum sheets (the bridge's orange, the station's mustard and copper, the ladies'
pastels, the bluestone), the glass is pale blue, the spire's doors and the coffee hatch are lit amber, the
roofs are seen from the front, and the shapes are ellipses, arcs and polygons with one flat fill each.

Outcome: the same 16 keys at the same sizes and anchors, redrawn in the house look: sheet colours only,
ink silhouette, light from the upper left, roofs seen from above, dark glass with a slanted glare, gold
only as the pack's unlit `c6a663`. Only the room `SanFranbourne` places them. San Franbourne is not
Japanese: the station, the bridge, the painted ladies, the lane and the two towers stay what they are;
only the drawing changes. None of the sixteen has foliage.

A design-stage prototype drew all 16 and was rendered in the room (images on the ticket:
`322-sprites-before-and-prototype.png`, and `322-room-<part>-before-and-prototype.png` for the station,
the ladies and lane, the towers and the bridge). It is not in the repository; the specification below is
what it drew.

## Approach

**Rewrite the builders in place**: `clocks_station`, `bridge_tower`, `bridge_cable`, `rowers`, `LADIES`,
`lady`, `lane_wall`, `mural`, `coffee`, `crates`, `pyramid`, `spire` (lines 120-497 today), and leave the
rest of the file alone: `river_tiles`, part 2's sprites (#328, `wheels` to `rock`), the airport sprites
and the plane pictures (#332), `font`, `label`, `box`, `main()`, `SPRITES`, `FLAT`, `LOOK_UP`. Three
tickets edit this file, so keep the diff in one block: this part's palette and helpers go in one new
section directly above `clocks_station()` (where `clock()` is today), palette names prefixed `T_` (town).
#328 prefixes its own `P_`; the prefixes differ on purpose, so a later definition cannot silently change
the other part's colours. `R` and `cast` below are #328's too: if #328 has landed, use its two and do not
define them again.

**Shared helpers.** `tools/house_look.py` (#279, on `master`, not on this branch) holds none of the six
helpers the ticket names, and nothing in it is needed. Import `pane, speck` from `generate_sendai_art`
(no side effects on import; if #328's import line is there, add to it). Not used, on purpose: `foliage`
(nothing leafy here), `roof_tile` (kawara: no Japanese roof here), `repaint` (these are redrawn, not
recoloured), `generate_fukuoka_art.flat_roof` (paints `2b373c`, not a sheet colour: #375, #378) and
`glaze` (keys on `4b6396`, the glare `pane()` has just drawn).

**Drawing rules**

- Draw at half size on `canvas(cw, ch)` as now. Every colour is a constant from the table below.
- Rectangles, points and per-pixel integer maths only: no `ellipse`, `arc`, `polygon`, slanted `line`,
  no floats (today the spire uses `t ** 2.4`, the dome and the fanlight `math.sin`). Slants are `seg`,
  curves are `arc_w` and `math.isqrt`, so the output is the same on any Pillow.
- Silhouette: `outline(im)`, ink `0a1627`, as now. Lines inside take the darkest tone of the family they
  cross. A piece painted on the wall (a mural panel, the hatch, the crates by the hatch) is boxed in ink
  by hand, since the wall pieces fill their canvas and `outline` finds no edge.
- Light from the upper left: lit top row and left column, shaded bottom row and right columns; an eave,
  a cornice or a band casts one row of shadow on what is under it. No face is one flat colour: brick is
  coursed, boards are lined, steel is plated, copper is gored.
- Glass is `pane()`; a window too small for it is `2c2d51` with a `2a3151` head row and a `4b6396` point.
  Nothing is lit: handles, finials, dials' bars and the spire's hoops and canopy are `c6a663` with
  `f3d890` / `a7843b`.
- Ground shade is `2a3151` at alpha 90, painted after the outline and only on pixels still clear (`cast`).
- **Flat in function stays flat in drawing**: the two cable rails (they tile down the deck on
  Non-Collidables; no outline) and the lane wall (a wall face; the murals are paint on it). The
  implementer's summary should name these, and the rowers and crates (one cell high), as still flat.

**Palette** (56 colours, every one in the `art-source/GuttyKreum` sheets; checked against all of them)

| Role | Colours (light to dark) |
|---|---|
| ink; inner navy | `0a1627`; `172459` |
| `T_STEEL`: white, steel, stone steps | `fafcfd`, `dae2e4`, `a4b0b5`, `848295`, `575f79`, `47485d`, `2a2636` |
| `T_MUSTARD`: station brick, gold | `f3d890`, `e3c587` (brick), `c6a663` (joint; unlit gold), `a7843b`, `86624f` |
| `T_MAROON`: bands, arch, brick footing | `aa4d31`, `904a37` (base), `5b283b` |
| `T_COPPER`: dome, awning, chalk board | `b1dfdc`, `93c297`, `508582`, `4a6262`, `395050` |
| `T_SLATE`: roofs seen from above | `698592`, `5b6c79` (base), `444f5e` |
| `T_STONE`: bluestone | `78768a`, `5f6177` (base), `47485d` |
| `T_ORANGE`: the bridge, milk crates | `db785c`, `c66347` (base), `aa4d31`, `8a3a22` |
| `T_WOOD` | `be9e8c`, `bb8971`, `86624f`, `7f513b`, `594b45` |
| `T_CREAM`: poster, cup sign | `e4cecc`, `be9e8c`, `8e7366` |
| glass | `2c2d51`, head `2a3151`, glare `4b6396` |
| `T_BLUE` | `bbe9ff`, `8ec2fa`, `7db9fa`, `588cc6`, `425faa`, `314b8e` |
| `T_PINK`; skin | `ffe2e0`, `ff9b92`, `e78d7b`, `bb6479`; skin `ffe2e0`, shade `d7b6ab` |
| red (oar blades, rainbow) | `e78d7b`, `d16b56`, `aa4d31` |
| purple; teal; lady d's greens | `8f72b6`, `3c396d`; `508582`, `3f827f`, `395050`; `6c8e7f`, `506b6b` |
| translucent | shade `2a3151` a90 |

## Changes

### `gamev2/tools/generate_sanfranbourne_art.py`

Coordinates are half-size pixels (32 a cell), inclusive, and are the prototype's: move a pixel where the
render asks for it, but keep each canvas, what each cell covers, and the rules above. Update the module
docstring (these sprites are in the house look; the import from `generate_sendai_art`). Delete `clock()`
and the constants only these builders used: `ORANGE*`, `MUSTARD_HI`, `MUSTARD_LO`, `COPPER*`,
`BLUESTONE*`, `PINK`, `MINT`, `SKYBLUE`, `LEMON`. Keep `MUSTARD`, `MAROON`, `TRAM*`, `BROWN*`, `SKIN`,
`LED`, `CARPET*` and every imported name another part still uses (grep before dropping one).

Helpers (new, in this part's section):

```python
def R(d, x0, y0, x1, y1, c): d.rectangle([x0, y0, x1, y1], fill=c)     # never called with an empty span

def seg(d, x0, y0, x1, y1, c, w=1):            # a slanted line a point at a time, w px wide along x
    n = max(abs(x1 - x0), abs(y1 - y0), 1)
    for i in range(n + 1):
        x, y = x0 + ((x1 - x0) * i * 2 + n) // (2 * n), y0 + ((y1 - y0) * i * 2 + n) // (2 * n)
        d.rectangle([x, y, x + w - 1, y], fill=c)

def arc_w(rx, ry, t):                          # half-width of an ellipse t rows from its centre line
    return math.isqrt(rx * rx * (ry * ry - t * t)) // ry
def orb(d, cx, cy, r, c):                      # a disc by rows: half-width min(r, isqrt(r*r - t*t + r))
def cast(im, boxes):                           # T_SHADE on the pixels of each box still clear (after outline)
def pixmap(d, x0, y0, rows, colours):          # rows of characters; a point for each one in `colours`

def courses(d, x0, y0, x1, y1, base, joint, hi=None, ch=6, cw=12):
    # fill `base`; a `joint` row at the foot of each full course of `ch` rows; perpend columns every
    # `cw` from x0 + cw - 1, shifted cw // 2 on odd courses; with `hi`, a lit point right of each
    # perpend on the course's top row
def arch_pane(d, x0, y0, x1, y1, surround, step=7):
    # pane(), then the top three rows' corners (3, 2, 1 px each side) back to `surround`
def band(d, x0, x1, y, shade):                 # 4 maroon rows: aa4d31, 904a37, 904a37, 5b283b; then a `shade` row
```

A rounded shape skips a row whose half-width is 0 (start one row lower, as the arches below do).

- **`clocks_station`** (12x7). Brick is `courses(…, e3c587, c6a663)`; its shade is `a7843b`, its lit
  edge `f3d890`.
  - *Wings.* Roof seen from above, y 80-103, x 4-379: slate `5b6c79`, hipped ends
    (`inset = max(0, (91 - y) * 10 // 12)` each side), a rib every 6 px from y 84 (`4a6262` point, `698592`
    point right of it above y 100), a steel ridge cap x 14-369, y 80-82 (`a4b0b5` row, `848295`), eave rows
    101-103 `4a6262`. Wall y 104-213: eave shade rows 104-105, two lit columns at x 4-5, three shaded
    at 377-379, `band` at y 126, 168, 206. Windows at x 14, 36, 58, 80, 102, 124, 256, 278, 300 and
    y0 134, 176: a 1 px `fafcfd` frame, `arch_pane(x, y0, x+11, y0+26)`, a 2 px `dae2e4` mullion from
    y0+2, a `dae2e4` right jamb, a sill x-2..x+13 on rows y0+27 (`fafcfd`) and y0+28 (`dae2e4`), a shade
    row y0+29. Plinth y 214-221 `848295`, lit top row, two dark rows.
  - *Pavilion.* Flat roof seen from above x 144-239, y 53-61 (slate, lit row, two `4a6262` rows); white
    cornice x 140-243, y 62-65 over the wall x 142-241, y 66-213; `band` at 84, 126, 206; corner piers
    x 142-151 and 232-241 `f3d890` with a `c6a663` line every 8 rows from 73 and a shaded right column;
    the pavilion's shade on the east wing, x 242-244 (`a7843b` on the wall, `4a6262` on the roof).
    Archivolt: maroon rows y 97-143, half-width `arc_w(34, 47, 143 - y)` about x 191/192, lit left edge
    and top row, dark right edge; jambs x 158-225 down to y 213. Fanlight: rows y 103-143, half-width
    `arc_w(29, 41, 143 - y)`: `2c2d51`, a `2a3151` head (every pixel with no glass above it), glare where
    `(x + y) % 9 == 0`; seven `c6a663` mullions by `seg` from (191 or 192, 143) by
    (-26,-10) (-21,-25) (-11,-35) (0,-40) (11,-35) (21,-25) (26,-10); a `c6a663` half-disc hub r 7. Transom
    y 144-146 in brick; recess x 163-220, y 147-213 `5b283b`.
  - *The clocks.* A board (160,148)-(223,166) `395050`, lit top and left `508582`, ink bottom and right;
    nine dials (`orb` r 2 `fafcfd`, ink centre, one ink hand point) at cx `165 + i*6 + (i//3)*2`, cy 156,
    a 3 px `c6a663` bar under each at y 162. Three doors at x 166, 184, 202 (15 wide, y 170-213): `594b45`
    frame and centre stile, `7f513b` leaves, `pane(x+1, 172, x+13, 190, 7)`, two panels, two `c6a663`
    handle points. The door cells (sprite cells (5,6), (6,6): x 160-223) must stay doors. Steps x 154-229,
    y 214-217 and x 150-233, y 218-221 in steel.
  - *Dome.* White drum x 160-223, y 48-58 with seven 4x7 dark windows; rim x 157-226, y 45-47; lantern
    x 187-196, y 3-11; `c6a663` finial x 191-192, y 0-2. The copper, eight gores lit from the west:

    ```python
    for y in range(11, 45):
        w = arc_w(34, 34, 44 - y)
        for x in range(192 - w, 192 + w):
            r = (2 * x - 383) * 50 // w     # 508582 r < -90, 93c297 < -34, 508582 < 34, 4a6262 < 90, else 395050
        for f in (-90, -67, -34, 0, 34, 67, 90):                         # the ribs, 395050
            d.point((191 + (f > 0) + (w * abs(f) // 100) * (1 if f > 0 else -1), y), fill=CO[4])
    ```
  - *Clock tower.* x 330-368, y 44-213 in courses, lit two columns, shaded three, `band` at 84, 126, 168,
    206, its shade on the wing at x 369-371, plinth as the wings'. Clock at (349, 63): `orb` r 13
    `a7843b`, r 12 ink, r 11 `fafcfd`, the lower right (`x + t > 9`) `dae2e4`, twelve ink tick points at
    radius 9, hands by `seg` to (349,55) and (355,66). Copper cap y 16-41, half-width `(y-16)*23//25`
    about x 349/350: west `93c297`, east `508582`, every fourth row one tone darker; eave x 325-374,
    y 42-43; `c6a663` finial x 349-350, y 6-15 with a 4x3 knob. Three maroon-framed
    `pane(343, y0+1, 355, y0+19, 7)` at y0 96, 138, 178 with maroon cross bars.
  - `outline`; `cast` row 223, x 3-380.
- **`bridge_tower`** (6x7). Two legs, x0 = 5 and 167, each four tiers stepping in as they rise:
  `(y0, inset)` = (150,0) (84,2) (30,4) (6,6), from `x0+inset` to `x0+19-inset`, down to y 213: `c66347`,
  a 1 px `db785c` left column and top row, three `aa4d31` right columns. A fluted panel x0+8..x0+11,
  y 34-209 `aa4d31` with an `8a3a22` left column and a `db785c` rivet point at x0+10 every 12 rows from 40;
  plate-joint rows 6 below each rivet on the two lower tiers only, inset by the tier, so nothing pokes
  past the silhouette. Saddle x0+6..x0+13, y 3-5. Steel pier x0-3..x0+22, y 214-221. Three portal beams
  x 17-174 at (y0, h) = (14,12) (56,10) (98,12): lit top row, two `aa4d31` bottom rows, a stepped panel
  every 16 px from x 26 (12 wide, `aa4d31` with `8a3a22` top and left, an inner `c66347` with a lit
  bottom lip); one `8a3a22` shadow row on each leg under each beam. Main cables from (10,6) and (181,6)
  outward, 11 points each, `y = 6 + i*3 + t*t*26//81` for the two cables `i`, two rows each. `outline`;
  `cast` row 223 under each pier. The solid cells stay (0,6) and (5,6): the piers; the deck between is clear.
- **`bridge_cable(side)`** (1x1, no outline). Rail at x = 2 (w) or 27 (e): ink columns x-1 and x+3, then
  `db785c`, `c66347`, `aa4d31` columns; a 5x4 post at y 4 and y 20 (inked above and below, lit top row,
  dark bottom row, two steel bolt points). Shade `2a3151` a90 on the three clear columns east of the
  rail and every other row of a fourth, inside the cell. Rows tile (posts 16 apart).
- **`rowers`** (4x1). Hull by rows y 14-20, x spans (18,110) (12,116) (8,120) (6,123) (8,120) (12,116)
  (18,110): `fafcfd` (y < 16), `dae2e4` (< 19), `a4b0b5`; cockpit rows 16 `848295` and 17 `575f79`,
  x 20-108. Four rowers at x 30, 50, 70, 90, oars alternately down and up: a 2 px oar by `seg`
  (`bb8971`, `594b45`), a 5x3 blade (`d16b56`, lit row `e78d7b`, dark row `aa4d31`), a 6x7 singlet
  alternately gold (`c6a663`, `f3d890`, `a7843b`) and navy (`314b8e`, `425faa`, `172459`), a 4x4 head
  `ffe2e0` with a `d7b6ab` right column, `594b45` hair. Two wake points. `outline`.
- **`LADIES`, `lady(kind, step)`** (3x5; steps 0, 5, 10, 15 as now). Each look is
  (body hi, body, board line, deep shade, trim, trim lit, door, door shade):

  ```python
  'a': ('bbe9ff', '8ec2fa', '588cc6', '425faa', '172459', '314b8e', 'aa4d31', '8a3a22'),
  'b': ('fafcfd', 'f3d890', 'e3c587', 'c6a663', '904a37', 'aa4d31', '508582', '395050'),
  'c': ('ffe2e0', 'ff9b92', 'e78d7b', 'bb6479', '3c396d', '8f72b6', '172459', '0a1627'),
  'd': ('b1dfdc', '93c297', '6c8e7f', '508582', '395050', '506b6b', '904a37', '5b283b'),
  ```
  `base = 157 - step`. Footing `courses(d, 4, base, 91, 157, 904a37, 5b283b, None, 4, 8)`, its top row
  `aa4d31` when `step`. Wall x 6-89, y 62..base-1 in the body colour, a board line every 5 rows from 72,
  eave shade rows 67-68 (deep), two lit columns, three shaded. The roof is seen from above, two shingled
  planes behind a gable at a slope of 1:

  ```python
  for x in range(2, 94):
      dx = 47 - x if x <= 47 else x - 48
      yg = 20 + dx                                   # the gable's edge in this column
      for y in range(yg - 12, yg):                   # the roof: west plane 698592/5b6c79, east 5b6c79/444f5e
          k = y - (yg - 12)
          joint = k % 4 == 3 or (x + (0 if (k // 4) % 2 else 2)) % 4 == 0      # the darker of the pair
      # top point (yg - 12): a4b0b5 on the west plane, 5b6c79 on the east
      for y in range(yg, 62):                        # the gable: fish-scale boards, `board` on `body`
          k = y - 22; o = 2 if (k // 4) % 2 else 0
          scale = (k % 4 == 3 and (x + o) % 4 != 1) or (k % 4 == 2 and (x + o) % 4 == 1)
      # then the bargeboard: fafcfd rows yg..yg+2, a trim point at yg+3, a deep point at yg+4
  ```
  Ridge cap x 47-48, y 8-22 (`fafcfd`, `a4b0b5`); `c6a663` finial x 47-48, y 3-7; a brick stack on the
  east plane x 66-73, y 22-37 under a steel cap x 65-74, y 20-22. Sunburst: `fafcfd` rows y 51-60,
  half-width `arc_w(11, 10, 60 - y)` about x 47/48, six trim-lit rays by `seg` from (47 or 48, 60) by
  (-9,-2) (-7,-6) (-3,-8) (3,-8) (7,-6) (9,-2), a trim hub. Cornice x 2-93, y 61-66: white rows, a
  `dae2e4` row, two trim rows, white dentils every 6. Bay x 10-46, y 72..base-6, white with a `dae2e4`
  right edge, under a slate cap x 9-47, y 69-72; two storeys (y0 76 and 110; skip one that would not
  clear the foot) of three `pane(x, y0, x+8, y0+22, 7)` at x 13, 24, 35 with a white sash bar at y0+11
  and a trim panel band y0+24..y0+27; board lines every 3 rows from 141 on the bay's foot. Window over
  the door: `pane(63, 75, 77, 91, 7)` in a white frame x 61-79, y 73-93 with cross bars and a sill. Porch
  roof seen from above x 55-85, y 97-102 (slate, lit row, white lip), a trim row, white posts at x 57-58
  and 82-83; door x 62-78, y 106..base-10 with `pane(64, 108, 75, 120, 7)`, a panel and a `c6a663` knob at
  (76,123); three steel steps widening 2 px each down from base-9. `outline`. The silhouette's top is
  12 rows higher than today's and gains the stack: it stays inside the canvas and the cells it is solid on.
- **`lane_wall(d, w=96)`**. `5f6177`; courses of 8 rows from y 5 with a `47485d` joint row, perpends every
  14 (offset 7 on odd courses), each block's top row lit `78768a`, a `47485d` scratch on the block where
  `speck(x, y, 3) < 30`. Coping seen from above, rows 0-3 `848295` (row 0 `a4b0b5`, a joint every 24),
  its shadow row 4 `2a2636`; foot rows 61-63 `47485d`.
- **`mural(kind)`** (3x2, on `lane_wall`).
  - *a*: an inked panel (6,10)-(52,56) `3f827f`, the wall's course lines showing through as `395050`, lit
    top row `508582`. A head in profile: rows y 14-50, half-width `arc_w(15, 18, y - 32)` about x 29/30,
    toned by `s = (x-29)*30 + (y-32)*45`: `ffe2e0` (< -560), `ff9b92` (< 420), `e78d7b`; a stepped nose
    x 42-50, y 28-37; eye, brow, mouth; a navy cap by row spans over the crown. A tag at x 58-88: three
    2 px zigzags by `seg` at y 20, 29, 38 (`f3d890`, `e78d7b`, `fafcfd`, each with a darker second row).
  - *b*: four inked bubble letters at x = 6 + i*22, 19 wide, y 14-46, corners inset (4, 2, 1, 1):
    gold, blue, pink, green (`f3d890`, `7db9fa`, `ff9b92`, `93c297`), the lower part from y 39 one tone
    darker with a dithered row at 38, three shaded right columns, a bluestone slot, a highlight, a drip.
  - *c*: five 3 px rainbow bands `y = 45 + i*3 - x*14//95` across the wall (`d16b56`, `f3d890`, `93c297`,
    `7db9fa`, `8f72b6`) over a `47485d` shadow row; an inked cream paste-up (68,12)-(88,38) with a navy
    picture and three text rows, one corner peeling; a white stencilled bird by
    `pixmap(d, 14, 14, BIRD, {'W': fafcfd, 'S': dae2e4, 'K': ink, 'G': c6a663})`:

    ```python
    BIRD = (
        '..........WWW.....................', '.........WWWWW....................',
        '........WWWWWWW...................', '........WWWWWWWW..................',
        '.........WWWWWWWW.................', '..........WWWWWWWW......WWWW......',
        '...........WWWWWWWW...WWWWWWW.....', 'W...........WWWWWWWWWWWWWWKWWW....',
        'WWW..........WWWWWWWWWWWWWWWWWGG..', '.WWWW......WWWWWWWWWWWWWWWWWWW....',
        '..WWWWWWWWWWWWWWWWWWWWWWWWWW......', '...WWWWWWWWWWWWWWWWWWWWWWW........',
        '....WWWWWWWWSSSSSSSWWWWW..........', '..WWWWWW......SSSSSSSSW...........',
        '.WWW............SSSSSSSS..........', 'W.................SSSSSSS.........',
        '....................SSSSS.........', '......................SSS.........',
    )
    ```
- **`coffee`** (3x2, on `lane_wall`). An inked hatch (30,16)-(66,44), dark inside (`2a2636`, not lit): a
  counter y 34-43, a steel espresso machine (34,24)-(48,40) lit top and left, three white cups; a wood
  shelf x 26-70, y 44-47. Awning seen from above x 23-73, y 5-13: stripes 6 wide, `508582` and `fafcfd`
  on rows 5-9, `395050` and `dae2e4` on rows 10-13, a scalloped edge on row 14, inked. A chalk board
  (6,18)-(24,50): wood frame, `395050` slate, five chalk rows (the first `f3d890`). A hanging cup sign:
  `orb` r 8 ink, r 7 `e4cecc` with its lower right `be9e8c`, a wood cup. Two stacked milk crates
  (74,38)-(92,57) in the bridge's orange, inked.
- **`crates`** (1x1). Two crates seen from above, orange at x 1 and blue at x 21 (`7db9fa`, `425faa`,
  `314b8e`, `172459`): the open top y 15-18 (lit rim, dark inside), the front y 19-28 with two hand
  holes. Between them a round table top by rows (y 7-11, x 10-22, `bb8971`, lit upper left, shaded lower
  right) on a `594b45` leg and foot, two white cups. `outline`; `cast` rows 30-31.
- **`pyramid`** (4x12). Centre x 64, `half(y) = 1 + (y - 40) * 43 // 280`. Spire x 64, y 4-40 with a
  `d16b56` point at y 3. Shaft, every pixel of rows 40-321:

  ```python
  floor = (y - 40) % 6; lit = x < cx
  win = floor in (2, 3) and (x - cx) % 5 != 0 and y > 70
  # win: 2a3151 on floor 2; on floor 3, 4b6396 if lit and (x + y // 6 * 2) % 11 == 0, else 2c2d51
  # wall: lit fafcfd (dae2e4 on floor 4); shaded a4b0b5 (848295 on floor 4)
  # then the edges: x = cx - w fafcfd, cx + w 575f79, cx 848295
  ```
  Two wings, 5 px outside each edge, y 120-249 (west `fafcfd`, `dae2e4`…, `a4b0b5`; east `a4b0b5`…,
  `575f79`; a joint every 12 rows) under a 2-row cap. Base y 325-379: `pane(14, 325, 113, 379, 13)`, and
  over it columns every 16 px from x 14 leaning by `o = (379 - y) * 8 // 55`: a white one 4 px wide at
  `x + o`, a grey one at `x + 13 - o`. Canopy x 12-115, y 318-324; doors x 48-79, y 350-379 with two
  `pane` leaves and `c6a663` handles; plinth y 380-381. `outline`; `cast` row 383.
- **`spire`** (4x11). Centre x 64. Hall: flat roof seen from above x 6-121, y 268-287 (slate, a rib
  every 12, dark eave rows); wall `courses(d, 10, 288, 117, 347, 5f6177, 47485d, 78768a, 8, 14)`, shade
  under the roof, lit left, shaded right, a dark foot from y 341; steel-framed
  `pane(x, 296, x+7, 330, 7)` at x 16..100 step 12, none from 50 to 68; doors x 49-78, y 304-347 with two
  `pane` leaves and `c6a663` handles under a canopy x 45-82, y 299-303 in `c6a663` (lit row `f3d890`,
  dark row `a7843b`): no amber. Mast x 64, y 4-150, a `d16b56` point on top. The lattice is open work:

  ```python
  def half(y):                                  # thin, then flaring to the roof (y 90-280)
      u = y - 90
      return 2 + 50 * u * u * math.isqrt(u * 190) // (190 * 190 * 190)
  # 13 ribs on every row: x = cx + (half(y) * abs(i) // 6) * sign(i) + (1 if i > 0 else 0), i = -6..6;
  #   fafcfd for i <= 0, dae2e4 for i < 4, a4b0b5
  # hoops every 14 rows from y 110, x = -w..w+1, sag = 3 * isqrt(w*w - x*x) // w:
  #   the far half at y - sag in 848295; the near half at y + sag in f3d890 (x < -w//3), c6a663 (x < w//2), a7843b
  ```
  `outline`; `cast` rows 349-350.

### Generated files (from `gamev2/`)

1. `python3 tools/generate_sanfranbourne_art.py` rewrites the 16 `assets/sprites/sfb-*.png` of this part.
   Every other PNG it writes and `config.json` must come out unchanged (`git status`): a diff there means
   a size or anchor moved, or another part's sprite was touched.
2. `python3 tools/make_worldmap.py --pil` and commit `assets/map/world-map.png` (and `world-map.json` if
   it changes; `check_generators.py` fails on a stale map).
3. Do not rerun `generate_sanfranbourne.py`, `generate_airports.py` or `config_to_tiled.py`.

### `gamev2/tools/tests/airports.test.js`

One new test, decoding with `tools/png.js` as the file's other pixel tests do:

- the 16 sprites have today's sizes: station 768x448, bridge tower 384x448, cables 64x64, rowers 256x64,
  ladies 192x320, murals and coffee 192x128, crates 64x64, pyramid 256x768, spire 256x704;
- every pixel with alpha > 0 has an RGB from the table above, listed in the test as a set of hexes (so
  no `f9c22e`, `ffaa28`, `fff4c8`, `000000`), and at most 24 opaque colours a sprite (prototype: 7 to 24);
- alpha is 255 everywhere except `2a3151` at 90;
- glass is dark and gold is dim: the station, each lady, the pyramid and the spire have `2c2d51` and
  `4b6396` (at least 20000 and 3000 in the station, 4000 and 600 in a lady, 15000 and 1000 in the
  pyramid, 6000 and 1000 in the spire; prototype: 25528/3996, 4820/812, 17296/1380, 7408/1216), and the
  station and the spire have `c6a663`.

### `gamev2/docs/landmarks-and-towns.md`

In San Franbourne's **Art** bullet, add one sentence: the bridge, the station, the painted ladies, the
lane and the two towers are in the house look (`generate_sendai_art`'s `pane`; roofs from above, dark
glass, unlit gold), and the cable rails and the lane wall are drawn flat on purpose.

## Data and interfaces

None. Keys, sizes, anchors, `tileNames`, the `tilePalette`, `FLAT`, `LOOK_UP`, placements, solid cells
and the `clocks` rule in `Interactions.js` are unchanged. Rooms touched: none (art only; `SanFranbourne`
shows it, and the world map picture is rebuilt).

## Tests

From `gamev2/`:

1. Before editing: `node tools/play.js render SanFranbourne /work/media/322-before.png`; after: the same to
   `322-after.png`, and `python3 tools/generate_sanfranbourne_art.py --preview <outside the repo>.png`.
   Look at both. The summary says which sprites still read as flat.
2. `node tools/test_game.js`, `python3 tools/test_blog_to_npc.py`, `node tools/play.js check`,
   `python3 tools/check_generators.py` (no DRIFT; `generate_sanfranbourne_art`, `generate_sanfranbourne`
   and the world map all `ok`), `python3 tools/sync_cities.py --check`.
3. Browser regression per `tools/browser/README.md`. Then play it at desktop and a phone size, day and
   `?tod=night` (no window, door or lamp of these sprites may look lit): walk in at the station's doors
   and bump the clocks, cross the bridge between the towers' legs and under the lowest beam, walk the
   ladies' row and behind their roofs, the lane past the murals and the hatch, and up to both towers
   (the look-up view). Screenshots to `/work/media/`. If the regression cannot run, say so.
4. Commit: `gamev2: <what changed> (#292)`.

## Risks and open questions

- **"Outline in the pack's navy"** is read as the recipe's ink `0a1627`, which these sprites and the rest
  of the file already use; inner lines are the family's darkest tone. Two approved redraws (the Fukuoka
  yatai, the Flinders design) outline in `172459`. If the owner wants that here it is one argument,
  `outline(im, NAVY)`, but it should then be the same in #328 and #332.
- **Same file as #328 and #332.** Either order works; whoever lands second rebases, keeps one `R` and
  one `cast`, reruns the tool and `make_worldmap.py --pil` (the map PNG conflicts as a binary:
  regenerate, do not merge). This branch is behind `master`; nothing here needs what it lacks.
- **The station is paler and the bridge duller.** The sheets have no saturated yellow or orange: the
  brick is `e3c587` jointed in `c6a663` (sandstone more than mustard; the ramp of the Flinders concourse,
  `generate_flinders_art.MUSTARD*` on `master`, one tone lighter for daylight) and the bridge is
  `c66347`, the strongest red-orange there is. Both were looked at in the room and read as what they
  are; they are the two biggest changes on screen.
- **The ladies' roofs are new shape**: planes seen from above behind the gable, and a chimney. The
  canvas, anchor and solid cells do not change, but look at the row from the street behind it.
- **Murals stay paint.** They are redrawn (new shapes, three tones each, inked), but a mural is flat by
  nature; the bluestone under them carries the shading.
- `2b373c` in `generate_sendai_art` / `generate_fukuoka_art` roofs (#375, #378) does not reach these
  sprites: neither `roof_tile` nor `flat_roof` is called.
