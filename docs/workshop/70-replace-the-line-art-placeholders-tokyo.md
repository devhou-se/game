# 70 — Better placeholders for Tokyo Tower, Tokyo Station and Tsutenkaku

## Context

Three landmarks are white line art and clash with the GuttyKreum pixel art around them:
`assets/sprites/tokyo-tower_0_0.png` (with `tokyo-tower-feet.png`, its bottom three rows),
`tokyo-station_0_0.png` (both ported from Godot, no generator) and `tsutenkaku_0_0.png` (drawn by
`tools/generate_tsutenkaku.py`). The real art is still wanted from the team. The owner's decision
(2026-11-28): put in a better placeholder for now; **the issue stays open and goes back to
`needs-art`**, waiting on the owner.

Outcome: the three PNGs are redrawn by code as shaded pixel art in the house style (the style of the
Sapporo TV Tower and the Akarenga hall), at the same pixel sizes, so nothing in the map, the config or
the game's code changes. All paths below are under `gamev2/`.

## Approach

**Same keys, same sizes, pictures only.** The sprites keep their keys, sizes (cells of 64 px) and
`spriteMetadata`; `config.json`, `tiled/`, the prefabs and `devhouse.world` stay byte-identical. Rooms
that look different, none of whose data is touched: Palace, Park, Osaka.

**Tsutenkaku: use the drawing that already exists.** `tools/generate_osaka_art.py` has `tsutenkaku()`,
a shaded 8x13 tower drawn on the placeholder's own silhouette (open steel lattice, copper roofs,
glazed deck, the OSAKA neon band, a lamp on the mast). `generate_tsutenkaku.py` saves that picture as
`tsutenkaku_0_0.png` instead of its line art. Checked while designing: importing the function has no
side effects, the archway cells stay open, and the lamp on the mast still ends below the avenue's kerb
(#181). Pointing the prefab at `osaka-tsutenkaku_0_0` instead would be a palette, prefab and Osaka map
change, and Osaka's rebuild (#219) owns that.

**Tokyo Tower and Tokyo Station: one new art tool, `tools/generate_tokyo_art.py`**, written like
`generate_sapporo_art.py`: draw at half size (32 px a cell) with the helpers and palette of
`generate_hokkaido.py` / `generate_sapporo_art.py`, lit from the left, 1 px `INK` outline, then double
with `Image.NEAREST`. `tv_tower()` (generate_hokkaido) is the model for the tower, `akarenga()`
(generate_sapporo_art, without its snow) for the station. It writes PNGs only: the keys are already
registered.

The pictures are judged by eye. The geometry below is where to start; the **hard rules** (each has a
test) are what keeps the unchanged map honest, and today's line art already meets them.

### Tokyo Tower — `tokyo-tower_0_0`, 8x15 cells, half size 256x480, axis x = 127/128

Orange-and-white open lattice (see-through between the members, as `tv_tower()` builds its `L` mask),
banded like the real tower: alternate bands about 22 px tall of vermilion (`RED`, `RED_HI` on left
edges, `RED_DK` on right edges, `RED_LO`) and white (`WHITE` / `CREAM_LO`).

| Part | Half-size px |
|---|---|
| Antenna | x 127..128, y 2..31, banded, a red lamp on top |
| Upper shaft (lattice) | y 32..215, 16 px wide at the top widening to x 96..159; a small white upper observatory about x 112..143, y 112..127 |
| Main observatory | a white two-storey box with two `GLASS` window bands, about x 84..171, y 216..263 |
| Legs (lattice) | y 264..413, the outer edges curving out from x 96..159 to x 27..228, a round-headed arch open between them from about y 330 |
| Foot Town | a low grey glazed building under the arch, about x 56..199, y 368..415: the body of the solid row |
| Front feet | each front leg carries on from the corner at y 414 to a concrete footing at about x 8..27 (right: x 228..247), y 464..475 |

Hard rules:
- 512x960. `tokyo-tower-feet.png` is `tower.crop((0, 768, 512, 960))` of the doubled picture, saved by
  the same run (Park's copy of the feet; the stitched city drops it, `?stitch=0` shows it).
- The cells of rows 13 and 14 that have no collider in Palace (row 13 columns 2..5, row 14 columns
  1..6: you walk between the feet) are each more than half transparent.

Not tested, but keep to it: what stands on the ground is over the solid cells (row 12 columns 1..6,
row 13 columns 0..1 and 6..7, row 14 columns 0 and 7), give or take the few pixels today's art
overhangs.

### Tokyo Station — `tokyo-station_0_0`, 41x8 cells, half size 1312x256, axis x = 655/656

A long three-storey red-brick front (`brick()`, `BRICK*`) with cream stone bands and quoins, a slate
mansard roof (`SLATE*`, `tiles()`), round-headed windows on the top storey (`arched()`), panes below.

| Part | Half-size px |
|---|---|
| Wings | x 8..1303; roof ridge at y 67, roof to about y 103, cornice, brick wall to the ground line at y 207 |
| End turrets | columns 0 and 40, pointed slate caps, top no higher than y 31 |
| Domed pavilions | columns 4..6 and 34..36 (centres x 176 and 1136): a brick block standing forward to about y 247, an octagonal drum, a slate dome with a finial up to y 0 |
| Centre block | columns 18..22: a brick gable (peak near y 4 at the axis) with one large arched window; ground line y 207 |
| Porch and door | a stone porch x 624..687 from about y 176 to y 255; the doorway (`glass_door()` or a dark arch) fills cell (20,7): x 640..671, y 224..255 |

Hard rules:
- 2624x512.
- Rows 0 and 1 (full-size y < 128) are transparent outside columns 0, 4..6, 18..22, 34..36 and 40:
  Palace's passing train runs on the row behind the roof and has to show (#63).
- The forecourt stays clear: cells (16..18, 7) and (22..24, 7) are fully transparent. Palace's shrub
  gardens (columns 17..18 and 22..23, rows 6..7), lamp posts and a vending machine stand there, inside
  the station's footprint, and show only because the sprite is clear. Beside the porch nothing should
  come below the ground line in row 6 either, so the gardens' upper halves show too.
- Cell (20,7), the one door cell (Palace 27,9), is drawn: more than half opaque.

## Changes

- **`tools/generate_tokyo_art.py`** (new): `tower()`, `station()`, `build()` returning
  `{'tokyo-tower_0_0', 'tokyo-tower-feet', 'tokyo-station_0_0'}` as doubled images, `main()` saving
  them to `assets/sprites/` and printing their sizes; `--sheet out.png` for a contact sheet as the other
  art tools have. No `config.json` write. Docstring: what it draws, that these are placeholders until
  the team's art arrives (#70), the hard rules above, how to run it. Do not use the identifiers other
  tests reserve for their own tools (`PALACE_`, `TEMPLE_`, `SHRINE_`, `PAGODA_`, `DEVHOUSE_`).
- **`tools/generate_tsutenkaku.py`**: delete the line-art drawing; `from generate_osaka_art import
  tsutenkaku`, double it, save. Keep the registration block exactly as it is (same size, so the same
  metadata and `tileNames` value, and `config.json` is rewritten unchanged). Update the docstring.
- **`tools/generate_osaka_art.py`**: only the docstring of `tsutenkaku()`: `generate_tsutenkaku.py`
  now saves this drawing as the landmark.
- **`tools/check_generators.py`**: `ART_TOOLS += ['generate_tokyo_art']  # Tokyo Tower and Tokyo
  Station, placeholders until the real art (issue #70)`.
- **`assets/sprites/tokyo-tower_0_0.png`, `tokyo-tower-feet.png`, `tokyo-station_0_0.png`,
  `tsutenkaku_0_0.png`**: regenerated by the two tools.
- **`tools/tests/landmark-placeholders.test.js`** (new): see Tests.
- **Docs**: `docs/landmarks-and-towns.md`, the three table rows: "shaded placeholder drawn by
  `tools/generate_tokyo_art.py` (`generate_tsutenkaku.py`); the team's art is still wanted (#70)", and
  the forecourt and train rules in one sentence under the table. `docs/generators-and-checks.md`: add
  `_tokyo_art` to the list of art tools. `tools/generate_osaka.py` docstring: no longer "line-art
  placeholder".
- **Not changed**: `assets/map/world-map.png`. Nothing moved, the game no longer shows that picture
  (#211) and no check compares it with the sprites; rebuilding it here would only collide with the town
  tickets that do rebuild it. The next rebuild picks the new art up.

## Data and interfaces

None. `config.json` (palette, `spriteMetadata`, `tileNames`, `game.lookUp`, `cities.TokyoCity.drop`),
`tiled/`, the prefabs and the game's code are untouched; `git diff --stat` shows only the files above.

## Tests

New `tools/tests/landmark-placeholders.test.js` (PNG decoding with `tools/png`, as other tests do):
- the four PNGs are 512x960, 512x192, 2624x512 and 512x832, and each `spriteMetadata` anchor is
  still `32 / width`, `32 / height` to four places;
- `tokyo-tower-feet.png` equals the bottom 192 rows of `tokyo-tower_0_0.png`, pixel for pixel;
- none is line art: each has at least 12 distinct opaque colours;
- the tower's hard rule, with the open cells taken from Palace's `Colliders` layer in
  `tiled/palace.tmj` (tower at columns 8..15, rows 6..20), and Tsutenkaku's archway mouth, cells
  (3,12) and (4,12): each more than half transparent;
- the station's three hard rules;
- `check_generators.py` lists `generate_tokyo_art`.

Run, from `gamev2/`, with a Python that has the pinned Pillow
(`pip install -r tools/requirements-art.txt` in a venv):

```bash
node tools/test_game.js
python3 tools/test_blog_to_npc.py
node tools/play.js check
<venv>/bin/python tools/check_generators.py     # the art tools must not be listed as `skip`
python3 tools/sync_cities.py --check
node tools/play.js render Palace /work/media/palace.png   # and Park, Osaka: look at them
REGRESS_TIME_SCALE=2 node tools/browser/regress.js        # tools/browser/README.md
```

Then play it in a browser (`python3 -m http.server`, `?notitle=1&nointro=1`), desktop and a phone size
(844x390 and 390x844), by day and with `?tod=night`, screenshots to `/work/media/` and looked at.
`window.game.scene.keys.GameScene.roomManager` places the player: `rm.resolve(room, x, y)` then
`rm.switchRoomInstant(r.room, r.x, r.y)`. Stand at Palace (27,12) for the station, Palace (12,21) for
the tower, Osaka (25,42) for Tsutenkaku, and with real keys:
- walk between the tower's feet and behind its legs (it fades, the player is not lost);
- walk through Tsutenkaku's archway;
- enter the station by its door, (27,10) going up, and come back out;
- wait for a train to pass behind the station's roof;
- `?stitch=0`, Park (12,4): the feet alone.

The "before" pictures are in `/work/media/70-before-*.png`.

## Risks and open questions

- **Looks are a judgement.** A test cannot say the art is good: the implementer must look at the
  renders and screenshots beside the neighbouring buildings and redraw until the three read as that
  landmark at a glance. They remain placeholders.
- **The tower stands in front of the station's west dome** (map composition, unchanged): its antenna
  and upper shaft are drawn over the pavilion at columns 4..6. Keep the antenna thin and check the
  pair in the Palace render; moving either is map work and not this ticket.
- **The station's solid footprint is deeper than its picture**: rows 8 and 9 of Palace under the wings
  are solid and show bare paving, today and after this change (the ground line stays where it is so
  the forecourt gardens keep showing). Reported separately; do not change colliders here.
- **Pillow versions.** Check on the pinned Pillow; use the primitives the other art tools use so that
  11.2 and newer agree, as `docs/generators-and-checks.md` asks.
- **Two files hold one Tsutenkaku** (`tsutenkaku_0_0`, `osaka-tsutenkaku_0_0`) until Osaka's rebuild
  settles on one; a later change to `tsutenkaku()` makes `check_generators.py` ask for the landmark to
  be regenerated, which is the intent.
- **The ticket is not finished by this change**: it must stay open and return to `needs-art`. Say so in
  the summary; Workshop and the owner do the labels.
- No open question blocks the work.
