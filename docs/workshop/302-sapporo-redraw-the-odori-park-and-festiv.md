# Sapporo: the Odori park and festival sprites in the house look (#302, part 1 of #289)

## Context

Nine sprites drawn by `gamev2/tools/generate_sapporo_art.py` furnish Odori Park (and one, the lantern post,
the ramen alley): the two festival tents, the fountain, the three snow sculptures, the lamp, the bench and the
lantern post. They predate the house look (the GuttyKreum pack's look, as in `generate_seven_eleven_art.py`,
Sendai's pub and trees, Canal City): their snow is three off-pack whites, the tents are a flat front-on
triangle of stripes, the lamp is a bright yellow-white globe, the gold is `f9c22e`, the outline is `0a1627`.

Outcome: the same nine keys at the same sizes and anchors, redrawn so that every colour is one the pack
uses, snow is shaded in the pack's blues, the tents have a roof seen from above, the lamp is dim gold
(`c6a663`), and the outline is the pack's near-black (`080d16`). Nothing on the map moves.

Not in this ticket: `generate_hokkaido.py` and the shared snow tiles (#285), every other function of
`generate_sapporo_art.py` (#305), pack art. #279's recipe module is not on master (checked: no "house look"
helper exists), so this uses the helpers in `generate_sendai_art.py`. If #279 has landed when this is built,
take `repaint`, the ink and the lamp gold from its module instead; nothing else changes.

A rough prototype of this design, old above new, is with the ticket's media (`302-direction-prototype.png`,
with the before renders `302-before-*.png`); it may not be on the implementer's disk.

## Approach

Keep every silhouette, footprint and placed detail (boards, counters, kana, the seat rows) and change how the
pieces are finished, plus three redraws where a recolour is not enough (the tent roof, the lamp, the bench).

1. **One finisher for the nine**, in place of `outline(im)` at the end of each builder: shade the snow, swap
   every off-pack colour, ink with `P_INK`. The shared helpers the nine call (`snow_cap`, `drift`, `lantern`,
   `tanuki_face`, the `SNOW*` / `AMBER` / `DARK` / `WARM` constants) are imported by seven other tools and by
   #305's sprites, so they are **not edited**: the builders go on drawing in the old colours and the finisher
   repaints the finished image (Fukuoka's `PACK_SWAP` does the same).
2. **Snow is a ramp and a lit form**, not white with a grey line: `form()` maps the old snow tones onto the
   pack ramp and makes the rim facing the light (up, left) one step lighter and the rim turned from it one
   step darker. Clean bands, no dither and no grain (the pack has neither; both were tried and read as noise).
3. **The tent roof is a ridge tent seen from above**, like the pack's awnings: back slope, ridge, front
   slope, eave, valance, each a tone darker, stripes running front to back. A four-sided tent with radial
   stripes was tried and is too busy at this size.

New drawing uses rectangles and points with integer maths only. Existing ellipses, arcs and chords in the
sculptures and the fountain stay (the check pins Pillow 11.3.0).

## Changes

### `gamev2/tools/generate_sapporo_art.py`

**A new block directly above the `# Odori Park` banner** (line ~976; keeping it there keeps #305's edits
apart). No other import or constant in the file changes.

```python
from generate_sendai_art import repaint, P_INK        # noqa: E402   (draws nothing on import)

# The house look for Odori's pieces: the pack's colours, light to dark
O_SNOW = [rgb(c) for c in ('fafcfd', 'ecfaff', 'd1e2eb', 'b7c3e3', '99a1ca', '8085b1')]
O_SNOW_OLD = {SNOW: 1, SNOW_LO: 3, SNOW_SH: 4, SNOW_DK: 5}      # d1e2eb is only reached by a lit rim
O_STONE = [rgb(c) for c in ('d1e2eb', 'bcc7cc', '94a2a8', '848295', '47485d')]
O_STONE_OLD = {STONE: 1, STONE_LO: 3, STONE_DK: 4}
O_ICE = [rgb(c) for c in ('ecfaff', 'bbe9ff', '8ec2fa', '588cc6')]
O_ICE_OLD = {ICE_HI: 0, ICE: 1, ICE_LO: 2}                      # the ICE line (now above odori_fountain) moves up here
O_IRON_HI, O_IRON, O_IRON_LO = rgb('6c8e7f'), rgb('4a6262'), rgb('2e4040')
O_GOLD = [rgb(c) for c in ('f3d890', 'c6a663', 'a7843b', '7f513b')]
O_BLUE = [rgb(c) for c in ('588cc6', '425faa', '314b8e', '172459')]
O_SWAP = {rgb(a): rgb(b) for a, b in (
    ('ffffff', 'fafcfd'), ('0a1627', '080d16'),
    ('f9c22e', 'c6a663'), ('f6dc8c', 'c6a663'), ('fde38a', 'f3d890'), ('c98f1c', 'a7843b'),
    ('3a5fb0', '425faa'), ('2a2330', '1b1e2a'), ('5a3b34', '5a3827'), ('d2a58c', 'be9e8c'), ('89af78', '83af6f'),
    ('f0669e', 'd78bc1'), ('f3cfe6', 'ffe2e0'), ('66dcea', '76cae3'), ('c8f2f6', 'ecfaff'), ('f8efcf', 'f3d890'))}


def form(im, ramp, old):
    """A flat fill becomes a lit form: the `old` colours go onto `ramp`, one step lighter on the rim that
    faces the light (up, left), one darker on the rim turned from it. Call before the outline."""
    px = im.load(); W, H = im.size
    idx = {(x, y): old[px[x, y]] for y in range(H) for x in range(W) if px[x, y] in old}
    bare = lambda x, y: not (0 <= x < W and 0 <= y < H) or px[x, y][3] == 0
    for (x, y), i in idx.items():
        if bare(x - 1, y) or bare(x, y - 1): i = max(0, i - 1)
        elif bare(x + 1, y) or bare(x, y + 1): i = min(len(ramp) - 1, i + 1)
        px[x, y] = ramp[i]


def odori_finish(im, snow=O_SNOW_OLD):
    form(im, O_SNOW, snow); repaint(im, O_SWAP); outline(im, P_INK)
    return im
```

Every builder below ends `return odori_finish(im)` where it now has `outline(im); return im`.

| Builder | What changes (drawn pixels, before doubling) |
|---|---|
| `snow_castle`, `snow_tanuki`, `snow_bear` (with `snow_block`, `snow_roof`) | Drawing unchanged. Finish with `odori_finish(im, {**O_SNOW_OLD, WHITE: 0})`, so the carved highlights stay the lightest tone: body `ecfaff`, joints and shaded ends `b7c3e3`, carved windows and gate `99a1ca` / `8085b1`, lit rims `fafcfd`. The castle's rope and the bear's salmon come through `O_SWAP`. |
| `stall(kind)` | `STALLS` gives each kind a four-tone stripe ramp (`corn`: `O_GOLD`, `drinks`: `O_BLUE`) and its cloth (`RED`, `O_BLUE[1]`). The triangle tent (rows 8-30), valance and peak snow go. **Roof**, x 3..92: back slope rows 6-12, ridge row 13, front slope rows 14-27, eave rows 28-31, valance rows 32-34 plus row 35 where `x % 7 in (2, 3, 4)` (scallops). Tone `t` = 0 back slope and ridge, 1 front slope, 2 eave, 3 valance; `+1` (to at most 3) where `x > 83 + (y - 6) // 6`, the end turned from the light. Stripe where `(x + 4) // 7 % 2`: stripe ramp `[t]`, else `O_SNOW[t]`. The ridge row is `O_SNOW[0]` from x 3 to 82. **Snow on the roof** with `snow_cap`: along the ridge (x 30..66, y 9, depth 4) and in the two back corners (x 3..21 and 70..92, y 4, depth 3), each with one row of `SNOW_SH` under it. **Inside**: the dark fill starts at row 36 (was 34) and its rows 36-38 are `P_INK`, the roof's shade; poles start at row 36. Board, bulb, counter, goods, cloth and drifts stay where they are (the night glow spot in `Glows.SPRITES` is on the inside at cell (1.5, 1.6)); their colours come through `O_SWAP`. |
| `odori_fountain` | Geometry unchanged. Before `odori_finish`: `form(im, O_STONE, O_STONE_OLD)` and `form(im, O_ICE, O_ICE_OLD)`, so the wall, bowls and stem get a lit left rim and a dark right one and the ice a shaded edge. Lights in the ice come through `O_SWAP`: cores `d78bc1` / `76cae3` / `c6a663`, no bright yellow. |
| `odori_lamp` | Redrawn at the same places. Post, collars, foot, cup and cap in `O_IRON` (lit left / top edge `O_IRON_HI`, right column `O_IRON_LO`). Globe: a 16 px disc at rows 5-20 centred x 16, by half-widths `(4, 6, 7, 7, 8, 8, 8, 8, 8, 8, 8, 8, 7, 7, 6, 4)` (row r: x 16-hw .. 15+hw); with `u = x - 16`, `v = r - 8`: `f3d890` where `(u+3)² + (v+3)² <= 10`, `a7843b` where `u + v >= 7` or (`u² + v² >= 44` and `u + v > 0`), else `c6a663`; one `fafcfd` glint at (12, 9). No `ellipse`. Snow cap and drift as now. The globe stays in the top cell (the night halo is by key and cell). |
| `odori_bench` | Same places: slats and seat in `O_IRON` (top row `O_IRON_HI`, bottom row and the right 4 px of each slat `O_IRON_LO`), end frames `1b1e2a` with a `47485d` lit edge, rows 23-24 under the seat `1b1e2a`, and on rows 25-26 between the legs (x 11..52) a toothed band of `b7c3e3` (row 25 every x, row 26 every other x): the seat's shade on the snow. Seat stays rows 19-22 (`Seats.js` poses the sitter by it). |
| `lantern_post` | Drawing unchanged; `odori_finish` shades its cap and drift, turns the paper `fafcfd` and the lantern caps and outline `080d16`. `lantern()` itself is not edited. |

Also in this file: the module docstring's Odori lines and the `PIECES` descriptions say what is now drawn
("a dim gold globe on a green iron post", "striped ridge tents seen from above"); `scenes()`'s Odori block adds
`s.put('odori-lamp-post_0_0', x, 9)` for x in (0, 11, 17) and `s.put('odori-bench_0_0', x, 12)` for x in
(9, 13), so the preview shows all of the park's pieces. `PIECES` keys, sizes, `solid` and `glow` do not change.

### Generated files

- `gamev2/assets/sprites/`: the nine PNGs (`snow-sculpture-castle|tanuki|bear_0_0`,
  `snowfest-stall-corn|drinks_0_0`, `odori-fountain_0_0`, `odori-lamp-post_0_0`, `odori-bench_0_0`,
  `ramen-alley-lanterns_0_0`). The tool rewrites all 63 of its PNGs with different bytes and the same
  pixels: `git checkout` the other 54 so the commit holds nine (and #305 does not conflict on them).
- `gamev2/assets/map/world-map.png` (and `.json` if it changes): `python3 tools/make_worldmap.py --pil`,
  in its own commit after the art, as 3dc4f0a0 did. `check_generators.py` fails on a stale map.
- `gamev2/config.json`, `gamev2/tiled/`, `devhouse.world`: must come out unchanged (`git status`).

### Docs

`gamev2/docs/landmarks-and-towns.md`, "Sapporo's own art": one sentence that Odori's pieces and the lantern
post are in the house look through `odori_finish` (pack colours, `form()` snow, `P_INK`), and that the shared
snow helpers are untouched until #285.

### `gamev2/tools/tests/sapporo.test.js`

One new test, "Odori Park: its pieces are in the pack's colours - shaded snow, tents roofed from above, a dim
gold lamp - at the sizes the map places them by (#289)". Decode each of the nine PNGs with
`require(path.join(GV2, 'tools', 'png')).decode` (as `konbini.test.js` line 217 does) and assert:

- width and height are its `PIECES` cells × 64 (castle 5x4, tanuki 2x3, bear 3x2, the tents and the fountain
  3x3, lamp 1x2, bench 2x1, lantern post 1x2);
- no opaque pixel is any of `f2f5fb c9d6ea a9bbd6 8497b8 f9c22e f6dc8c fbf3d2 fde38a c98f1c 3a5fb0 2a2330
  5a3b34 d2a58c bfe3f6 e6f6fd 8fc3e6 f0669e 66dcea 3d6a52 5d8f70 294a3b 0a1627`;
- each has `080d16` (the outline) and at least three of the six `O_SNOW` tones, `b7c3e3` among them;
- the lamp has at least 300 pixels of `c6a663` and has `f3d890` and `a7843b`;
- each tent has three tones of its stripe in rows 0-71 (corn `f3d890 c6a663 a7843b`, drinks
  `588cc6 425faa 314b8e`).

## Data and interfaces

None. Sprite keys, sizes, anchors (`spriteMetadata`), `tileNames`, prefabs, colliders, `Glows.SPRITES`,
`Seats`, `Interactions` and the blog spots are all unchanged. `form`, `odori_finish` and the `O_*` constants
are new module-level names in `generate_sapporo_art.py`; nothing imports them.

## Tests

From `gamev2/`:

```bash
python3 tools/generate_sapporo_art.py --scenes /tmp/sap      # same 63 keys and sizes printed as before
node tools/play.js render Sapporo /tmp/after.png             # against a render taken before the change
node tools/test_game.js
python3 tools/test_blog_to_npc.py
node tools/play.js check
python3 tools/check_generators.py        # after make_worldmap.py --pil; only generate_ads / extract_city may skip
python3 tools/sync_cities.py --check
```

- Once, by hand: every opaque colour of the nine PNGs is in the pack (collect the colours of
  `art-source/GuttyKreum/**/*.png` with Pillow and diff). The prototype had none outside it.
- Look at before and after (the Odori blocks are cells x 0-43, rows 21-30 of the render; take the before
  render before editing) and say in the summary which sprites still read as flat.
- Browser: `tools/browser/regress.js` (see `tools/browser/README.md`), then walk Odori on a Hokkaido trip date
  at desktop and phone size, by day and with `?tod=night` (the lamp's halo, the tents' glow), sit on a bench,
  bump the drinks tent; screenshots to `/work/media/`. Say so if it could not be run.
- Commits: `gamev2: <what changed> (#289)`, the art and the world map.

## Risks and open questions

- **The approved look (#278's comment) could not be read from here.** The look is taken from the ticket's
  words and the worked examples on master. The tent roof seen from above is the largest reading of "a roof,
  not a flat fill"; if the owner wants the front-on tent kept, the fallback is the old triangle with the same
  four-tone stripes and valance shade, and nothing else in this design changes.
- **Snow beside snow.** The nine will be in the pack's blues while the snowbanks, the snow tiles and every
  other `snow_cap` user stay in the old whites until #285 and #305. The sculptures stand on the snow tile
  (`e8f0f9`): they hold against it by the outline and the `b7c3e3` shade, which is why the stronger of two
  tried mappings is the one above.
- **#305 edits the same file.** The conflict surface is the new block, the nine builders, their `PIECES`
  descriptions and the docstring lines; either order works. `world-map.png` conflicts with every sibling
  redraw: rebuild it after rebasing rather than merging it.
- **Pillow.** The kept ellipses and arcs are pixel-stable only on the pinned Pillow, as they are today.
- `form()` lights any snow pixel next to a transparent one, including inside holes (under the bear, between
  the tanuki's arm and body): looked right in the prototype; check the after render.
