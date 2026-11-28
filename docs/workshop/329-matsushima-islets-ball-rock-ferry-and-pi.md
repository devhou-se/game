# Design: the Matsushima islets, ball rock, ferry and pier in the house look (#329)

## Context

Five sprites that `gamev2/tools/generate_sendai_art.py` draws for Matsushima bay are still in the old
look: smooth ellipse pines and a flat tan block for the islets, an `ellipse` ball, a ferry in flat side
elevation built from polygons, and a pier that is one brown rectangle. Around them the bay is the
GuttyKreum pack: its water, its white shore boulders, its pines on the promenade. #329 (part 2 of 6 of
#288) redraws the five in place in the house look: the pack's colours, ragged foliage shaded
pale green → teal → blue → purple, grey stone with a shaded face, a boat seen from the three-quarter
view, a 1px ink silhouette, light from the upper left.

Only the pictures change. Keys, pixel sizes, anchors, the pier's `depthBias`, the prefabs, the map and
every collider stay as they are, so no room is rebuilt. The one room that places them is **Sendai**
(pier at (59,30), ferry at (60,28), three islets, the ball rock, four small islets, all in the bay,
columns 59 to 69).

## Approach

Rewrite the five builders and add four small helpers beside them, all inside the Matsushima section of
`generate_sendai_art.py`. A design-stage prototype of exactly that code is in the appendix; it was run
against a scratch copy of the game and its renders are on the ticket
(`329-sprites-before-and-prototype.png`, `329-bay-north-…`, `329-bay-south-…`,
`329-ferry-and-pier-…`). The implementer starts from the appendix, looks at its own renders, and may
tune tones and shapes inside the rules below. The appendix is the default wherever this text is silent.

Decisions:

- **No dependency on `tools/house_look.py`.** #279 is merged on `master` but this branch was cut before
  it, and `generate_sendai_art.py` (identical here and on `master`) already has its own house-look
  helpers, which other tools import from it: `speck`, `foliage`, `limb`, `pane`, `P_INK`, `NEEDLE`,
  `P_SHADE`. Use those. Do not change their signatures or what they draw.
- **`rock`, `blob`, `trunk` and the `ROCK*`, `PINE*`, `BARK*` constants stay exactly as they are.**
  `generate_sendai_town_art.py` imports them (its `godaido()` calls `rock(d, 16, 120, 84, 122, 4)`), and
  that tool is #345's and is not covered by `check_generators.py`, so a change would go unseen. The new
  rock is a new helper, `crag`. `small_pine` (no other user) is deleted; so are `HULL`, `HULL_LO`, `BLUE`,
  `BLUE_DK` (used only by the old ferry; nothing imports them). Leave the `generate_hokkaido` import
  list alone: other tools read names through this module.
- **Stone is the pond set's own boulder ramp**, the white-grey rocks that line the bay's shore two
  cells away, so the islets and the shore are one material. The ticket asks for grey stone; the old tans
  are in no sheet.
- **The ferry is drawn in the three-quarter view the pack uses for buildings**: the near side of the
  hull and the saloon wall as faces, and above them what you see from on top — the awning's ribbed
  sheet, the wheelhouse roof, the funnel standing on the awning with its shade, the planked fore and
  aft decks inside a white bulwark. No blue on the hull that the water tile (`425faa`) would swallow:
  the boot is navy.
- **The pier stays a plan view**, because it is walked on: 8px boards laid across, a lit string along the
  north edge and a shaded face along the south, posts with a lit top and a shade, piles and a shade on the
  water under the south edge. The board pattern of the pack's own decking (4px, navy joints) was tried
  and read as a purple grille at this length; do not go back to it.

Rules (the house-look recipe, `gamev2/docs/generators-and-checks.md` "House look: GuttyKreum" on `master`):

- Every opaque colour is one the `art-source/GuttyKreum` sheets use. The closed list for these five is in
  Data and interfaces; all 38 were checked against the sheets.
- Draw with `d.rectangle`, `d.point`, pixel writes and the file's `limb`, `foliage`, `pane` only, in
  whole numbers: no `ellipse`, `chord`, `polygon`, `line` or float maths, so every Pillow draws the same
  pixels. Noise comes from `speck`, never `random`.
- `outline(im, P_INK)` once, after the drawing. The foam (`surf`) and the pier's shade on the water go
  on **after** the outline, on clear pixels only, so they carry no ink.
- Light from the upper left: lit top and west edges, shade to the east and toward the water.
- No colour covers more than about a third of a sprite's opaque pixels; dither is at most one row.

## Changes

**`gamev2/tools/generate_sendai_art.py`** (the only tool changed)

- Module docstring, the five `matsushima-*` lines: say what is drawn now (grey-white faceted rock,
  ragged pines; the boat in three-quarter view; the pier's boards and posts).
- Remove `HULL`, `HULL_LO`, `BLUE`, `BLUE_DK` and `small_pine`. Keep `rock` where it is, with one line
  added to its docstring: kept for `generate_sendai_town_art.py`'s Godaido, the bay's islets use `crag`.
- After `rock`, add the constants and helpers of the appendix: `BAY_STONE` (seven tones, light to dark),
  `P_FOAM`, the deck, timber, hull, boot and stripe tones, and
  - `crag(im, x0, x1, y0, y1, seed)` — the rock as upright facets 5 to 10 px wide, each with a lit west
    column and a crevice on its east, darker to the east and in the bottom quarter, broken strata every
    6 rows, rounded shoulders, and a 3-row notch in the two darkest tones at the waterline;
  - `surf(im, x0, x1, y)` — two broken rows of `8ec2fa` under a foot or a hull (after the outline);
  - `bay_pine(im, d, x, y, seed, lean)` — a bent two-piece trunk and a branch from `limb`, three pads
    from `foliage(..., NEEDLE, seed)`;
  - `scrub(im, x0, x1, y, seed)` — a ragged run of small `foliage` clumps along a rock's top.
  Where a constant in the file already has the same value (`P_WHITE` `fafcfd`, `P_GREY` `a4b0b5`,
  `P_PLASTER` `e4cecc`, `P_GLASS` `2c2d51`, `P_BARK_HI` `a68777`, `P_BARK_LO` `594b45`), use it instead of
  adding a second name.
- Replace the bodies of `islet`, `islet_small`, `ball_rock`, `ferry`, `pier` with the appendix's. What
  must hold however they are tuned:

  | Sprite | Canvas (half size) | Fixed |
  |---|---|---|
  | `islet` | `canvas(3, 2)` 96×64 | rock foot on row 57, ink on 58, foam rows 59–60; three pines, a sea cave; rock within x 10–85 |
  | `islet_small` | `canvas(2, 2)` 64×64 | the same foot rows; one pine; rock within x 16–48 |
  | `ball_rock` | `canvas(2, 2)` 64×64 | the same foot rows; a round boulder (integer circle test, shaded by `dx*5 + dy*7`) sitting on a low crag, its shade on the crag; two tufts |
  | `ferry` | `canvas(5, 2)` 160×64 | bow to the right; hull foot on row 57, foam 59–60; two decks of windows (`pane`), awning and wheelhouse roof seen from above, funnel, two lifebuoys, pennant at the bow |
  | `pier` | `canvas(5, 1)` 160×32 | deck from x 0 (it meets the shore cell) to x 157; boards on rows 6–23 so the walker's feet are on boards; six pairs of posts every 30 px from x 6; `P_SHADE` (alpha 90) only on clear pixels of rows 30–31 |

- `SPRITES`, `FLAT`, `main()` and `--preview`: unchanged.

**Regenerated, from `gamev2/`**

- `python3 tools/generate_sendai_art.py` — rewrites its PNGs; only the five `matsushima-*_0_0.png` may
  differ (`git status` must show no other sprite and no `config.json` change).
- `python3 tools/make_worldmap.py --pil` — the world map is drawn from the sprites; commit what changes
  under `assets/map`.
- Not run: `make_prefabs.py`, `generate_sendai.py`, `config_to_tiled.py`, `sync_cities.py` — nothing they
  read changes.

**`gamev2/docs/landmarks-and-towns.md`** — line 28 (the Matsushima row) and the Matsushima bay paragraph
near line 198: say the five are in the house look and name `crag`, `bay_pine` and `surf` as the helpers
for more bay rocks, pines and waterlines.

**`gamev2/tools/tests/sendai.test.js`** — one new test (below).

## Data and interfaces

No schema, config, map or API change. Unchanged and asserted by the new test:

| Key | PNG | anchor | depthBias |
|---|---|---|---|
| `matsushima-islet_0_0` | 192×128 | 1/6, 0.25 | – |
| `matsushima-islet-small_0_0` | 128×128 | 0.25, 0.25 | – |
| `matsushima-ball-rock_0_0` | 128×128 | 0.25, 0.25 | – |
| `matsushima-ferry_0_0` | 320×128 | 0.1, 0.25 | – |
| `matsushima-pier_0_0` | 320×64 | 0.1, 0.5 | −200 |

The closed palette (the prototype uses 9 to 20 of these per sprite):

| Use | Colours |
|---|---|
| ink | `080d16` |
| stone, light to dark | `ffffff f2f2f2 e3e3e3 bebaba 919191 737373 47485d` |
| needles (`NEEDLE`) and trunk | `93c297 83af6f 508582 4a6262 3c396d 2a3151`, `7f513b 594b45` |
| foam | `8ec2fa` |
| hull and superstructure | `fafcfd dae2e4 a4b0b5 848295 575f79 2a2636` |
| boot, glass (`pane`) | `314b8e 172459`, `2c2d51 4b6396` |
| stripe, funnel, buoys, pennant | `e78d7b d16b56 aa4d31 8a3a22` |
| deck boards on the boat | `c69f96 967f79 3c396d` |
| pier timber | `e4cecc c69f96 bb8971 a68777 967f79 86624f 594b45` |
| shade on the water | `2a3151` at alpha 90 (the pier only) |

New names other tools may import later: `crag`, `surf`, `bay_pine`, `scrub`, `BAY_STONE`, `P_FOAM`.
Nothing that is imported today is renamed or removed.

## Tests

Add to `tools/tests/sendai.test.js`: **"Sendai: the Matsushima islets, ball rock, ferry and pier are in
the pack's colours, at the sizes and anchors they had (#329)"**. With
`require(path.join(GV2, 'tools', 'png'))` (as `shrines.test.js` does) decode the five PNGs and assert:

- width, height, `anchorX`, `anchorY`, `frameCount` 1, `depthBias` and `tileNames` as in the table above;
- every pixel is clear, or opaque and in the closed palette above, or (pier only) `2a3151` at alpha 90
  (so none of the old tan, pine or hull colours can be left);
- shaded, not recoloured: each islet and the ball rock has at least 5 of the 7 stone tones and at least
  4 of the 6 needle tones; the ferry has at least 3 hull tones and 3 stripe tones; the pier at least 5
  timber tones; no colour is more than 35% of a sprite's opaque pixels;
- pixel-doubled: every 2×2 block of each PNG is one colour.

The existing bay test (pier walkable, ferry moored, islets clear of the boat lane) must pass untouched.

Run, from `gamev2/`: `node tools/test_game.js`; `python3 tools/test_blog_to_npc.py`;
`node tools/play.js check`; `python3 tools/check_generators.py` (no DRIFT; a stale world map fails it);
`python3 tools/sync_cities.py --check`; then the browser regression, `tools/browser/regress.js`
(`tools/browser/README.md`).

By eye: `node tools/play.js render Sendai out.png --scale 1` before and after, cropped to columns 57–68,
rows 8–47, both halves looked at; then in a browser (`?notitle=1&nointro=1`, Sendai) at desktop and at
a phone size, walk the pier end to end by day and with `?tod=night`, and check that the player stands
over the boards and posts, that the west end meets the shore boulders, and that nothing shows a seam
against the water. Save the before/after images to `/work/media/`. The summary must say which of the five
still read as flat. From the prototype: the pier is flat by design (a plan view you walk on); the hull's
near side and the islets' cliff are elevations by nature and read as shaded faces; the ball is the
piece most worth a second look at game scale.

## Risks and open questions

- **Same file, other tickets.** #324 redraws other sprites in `generate_sendai_art.py` and #345 redraws
  the Godaido in `generate_sendai_town_art.py`. Keep every edit inside the Matsushima section (and the
  two constant lines removed near the top) so merges stay textual. #345 may switch the Godaido's rock to
  `crag`; until then it keeps the old tan `rock`, next to grey islets. That is #345's to settle, not
  this ticket's.
- **`assets/map` is rebuilt by every art ticket**, so its PNGs will conflict with whichever lands first.
  Resolve by rerunning `make_worldmap.py --pil` after the merge, never by picking a side.
- **The branch is 28 commits behind `master`.** Nothing here needs what `master` added; if Workshop
  rebases, `house_look.py` appears but the design still does not use it (moving the file's helpers there
  is not this ticket).
- **Stone brightness.** The boulder ramp is close to white; against the water it is bright. If the render
  reads as chalk, shift the body one tone darker in `crag` (the thresholds on `t`) rather than adding
  colours. Keep it grey: the ticket asks for grey stone.
- **Pillow.** The appendix was run on Pillow 11.3.0 only; it uses nothing but rectangles, points and
  pixel writes, which is what keeps `check_generators.py` (pixel compare) stable across versions.
- No open question for the owner.

## Appendix: the prototype (half-size pixels; goes after `rock` in `generate_sendai_art.py`)

`canvas`, `outline`, `rgb`, `CLEAR`, `speck`, `foliage`, `limb`, `pane`, `NEEDLE`, `P_INK`, `P_SHADE` are
the file's own.

```python
# ---- Matsushima bay, in the pack's look ---------------------------------------
# The stone is the grey-white of the pond set's own boulders (the ones along the
# bay's shore), lit from the upper left; the pale rim is the one that set draws
# where stone meets water. Rectangles, points and limb() only, in whole numbers.
BAY_STONE = [rgb(c) for c in ('ffffff', 'f2f2f2', 'e3e3e3', 'bebaba', '919191', '737373', '47485d')]
P_FOAM = rgb('8ec2fa')
P_DECK, P_DECK_HI, P_DECK_JOINT = rgb('967f79'), rgb('c69f96'), rgb('3c396d')
P_TIMBER, P_TIMBER_HI, P_TIMBER_LO, P_TIMBER_DK = rgb('bb8971'), rgb('e4cecc'), rgb('86624f'), rgb('594b45')
P_HULL, P_HULL_LO, P_HULL_SH, P_HULL_DK = rgb('fafcfd'), rgb('dae2e4'), rgb('a4b0b5'), rgb('848295')
P_BOOT, P_BOOT_HI = rgb('172459'), rgb('314b8e')
P_STRIPE, P_STRIPE_HI, P_STRIPE_LO, P_STRIPE_DK = rgb('d16b56'), rgb('e78d7b'), rgb('aa4d31'), rgb('8a3a22')
P_DARK = rgb('2c2d51')
P_BOARD_ALT = rgb('a68777')
P_STEEL_DK, P_SOOT = rgb('575f79'), rgb('2a2636')


def crag(im, x0, x1, y0, y1, seed=0):
    """A Matsushima islet's rock, x0..x1 wide, its top at y0 and its foot in the
    water at y1: grey-white stone in upright facets, each with a lit west edge and
    a crevice on its east, the whole darker to the east and toward the water,
    broken strata across it, the notch the sea has cut under it."""
    px = im.load()
    w = x1 - x0
    fx, facets = x0, []                                           # the facets: (first column, last, how far its top drops)
    while fx <= x1:
        fw = 5 + speck(fx, 7, seed) % 6
        if x1 - (fx + fw) < 4:
            fw = x1 - fx + 1
        facets.append((fx, fx + fw - 1, speck(fx, 8, seed) % 3))
        fx += fw
    for i, (a, b, drop) in enumerate(facets):
        for x in range(a, b + 1):
            e = min(x - x0, x1 - x)                               # 0 at the ends
            top = y0 + drop + (7 if e < 2 else 4 if e < 4 else 2 if e < 7 else 0)
            foot = y1 - (1 if e < 3 else 0)
            for y in range(top, foot + 1):
                if y > y1 - 3:                                    # the notch, cut back under the rock
                    if e < 2:
                        continue
                    px[x, y] = BAY_STONE[5 if (y == y1 - 2 and speck(x // 2, y, seed) < 60) else 6]
                    continue
                t = (a + b) // 2 - x0                             # the facet's place across the rock
                n = 1 if t * 100 < w * 18 else 2 if t * 100 < w * 45 else 3
                n += (i + seed) % 2 if 0 < i < len(facets) - 1 and t * 100 >= w * 22 else 0
                if x == a and i:
                    n -= 1                                        # its lit edge
                elif x == b and i < len(facets) - 1:
                    n += 2                                        # the crevice
                elif x == b - 1 and b - a > 5:
                    n += 1
                if y - top < 2:
                    n -= 1                                        # the lit top
                if y > y1 - 4 - (y1 - y0) // 4 - speck(a, 1, seed) % 3:
                    n += 1                                        # darker toward the water
                if (y - y0 + drop * 2) % 6 == 5 and speck(x // 3, y, seed) >= 30 and x != a:
                    n += 1                                        # the strata, broken
                px[x, y] = BAY_STONE[max(0, min(5, n))]


def surf(im, x0, x1, y):
    """The pale rim where stone or a hull meets the water, drawn after the outline."""
    px = im.load()
    for x in range(x0, x1 + 1):
        if y < im.height and px[x, y][3] == 0 and (x + y) % 7 != 0:
            px[x, y] = P_FOAM
        if y + 1 < im.height and px[x, y + 1][3] == 0 and x % 5 < 2:
            px[x, y + 1] = P_FOAM


def bay_pine(im, d, x, y, seed=0, lean=1):
    """A wind-bent pine rooted at (x, y): a thin bent trunk and three pads of needles."""
    limb(d, x, y, x + lean * 2, y - 8, 2); limb(d, x + lean * 2, y - 8, x - lean, y - 17, 2)
    limb(d, x + lean * 2, y - 9, x + lean * 6, y - 13, 2)
    foliage(im, [(x - lean * 5, y - 14, 8, 4), (x + lean * 6, y - 18, 8, 4), (x - lean, y - 23, 7, 4)], NEEDLE, seed)


def scrub(im, x0, x1, y, seed=0):
    """Low growth along a rock's top: a ragged run of small clumps."""
    foliage(im, [(x, y - speck(x, 0, seed) % 2, 5, 3) for x in range(x0 + 4, x1 - 2, 7)], NEEDLE, seed)


def islet():
    im, d = canvas(3, 2)                 # 96 x 64
    crag(im, 10, 85, 30, 57, 1)
    px = im.load()
    for y in range(46, 55):                                       # a sea cave
        for x in range(40, 48):
            if not (y < 48 and x in (40, 47)):
                px[x, y] = BAY_STONE[6] if x > 41 and y > 47 else BAY_STONE[5]
    scrub(im, 11, 84, 31, 4)
    bay_pine(im, d, 24, 31, 1, -1); bay_pine(im, d, 48, 30, 3, 1); bay_pine(im, d, 70, 31, 5, 1)
    outline(im, P_INK)
    surf(im, 9, 86, 59)
    return im


def islet_small():
    im, d = canvas(2, 2)                 # 64 x 64
    crag(im, 16, 48, 33, 57, 2)
    scrub(im, 17, 47, 34, 6)
    bay_pine(im, d, 32, 34, 2, 1)
    outline(im, P_INK)
    surf(im, 15, 49, 59)
    return im


def ball_rock():
    im, d = canvas(2, 2)                 # 64 x 64
    crag(im, 11, 52, 41, 57, 3)
    px = im.load()
    cx, cy, r = 32, 29, 12                                        # the ball: a boulder, lit from the upper left
    for y in range(cy - r, cy + r + 1):
        for x in range(cx - r, cx + r + 1):
            dx, dy = x - cx, y - cy
            if dx * dx + dy * dy > r * r + r // 2:
                continue
            s = dx * 5 + dy * 7 + (speck(x // 2, y // 2, 9) - 50) * r // 40
            n = 0 if s < -8 * r else 1 if s < -4 * r else 2 if s < 0 else 3 if s < 4 * r else 4 if s < 7 * r else 5
            if dy in (-2, 5) and speck(x // 3, y, 9) >= 30 and n < 5:
                n += 1                                            # two bands round it
            px[x, y] = BAY_STONE[n]
    for x in range(22, 44):                                       # its shade on the rock it sits on
        for y in range(41, 44):
            if px[x, y][3] and (x - cx) ** 2 + (y - cy) ** 2 > r * r + r // 2:
                px[x, y] = BAY_STONE[4 if y < 43 else 3]
    foliage(im, [(15, 42, 5, 3), (49, 42, 5, 3)], NEEDLE, 8)
    outline(im, P_INK)
    surf(im, 10, 53, 59)
    return im


def ferry():
    im, d = canvas(5, 2)                 # 160 x 64, bow to the right
    R = lambda x0, y0, x1, y1, c: d.rectangle([x0, y0, x1, y1], fill=c)   # noqa: E731
    # ---- the hull's near side: white topsides, a red stripe, a navy boot, the stem raked
    for y in range(44, 58):
        x0 = 8 + (1 if y > 49 else 0) + (1 if y > 54 else 0)
        x1 = 157 - (y - 44) * 11 // 13
        c = P_HULL if y < 48 else P_STRIPE if y == 49 else P_STRIPE_LO if y == 50 else P_HULL_LO if y < 54 \
            else P_BOOT_HI if y == 54 else P_BOOT
        R(x0, y, x1, y, c)
        if 50 < y < 54:
            R(x1 - 3, y, x1, y, P_HULL_SH)                        # the bow turns away
    for x in range(10, 150, 2):
        d.point((x + 1, 53), fill=P_HULL_SH)                      # one dithered row above the boot
    R(8, 44, 157, 44, P_HULL_SH)                                  # the deck's edge
    for bx in (30, 92):                                           # lifebuoys
        R(bx, 45, bx + 5, 48, P_STRIPE); R(bx + 1, 44, bx + 4, 49, P_STRIPE)
        R(bx + 2, 46, bx + 3, 47, P_HULL_LO); d.point((bx + 1, 45), fill=P_STRIPE_HI)
        d.point((bx + 4, 48), fill=P_STRIPE_LO)
    # ---- the aft deck and the foredeck, seen from above: boards, a white bulwark
    for x in range(8, 18):
        for y in range(31, 44):
            d.point((x, y), fill=P_DECK_JOINT if y % 4 == 3 else P_DECK_HI if y % 4 == 0 else P_DECK)
    R(8, 29, 17, 30, P_HULL); R(8, 30, 17, 30, P_HULL_SH); R(8, 31, 9, 43, P_HULL); R(9, 31, 9, 43, P_HULL_SH)
    for x in range(127, 158):
        far = 31 + (x - 127) * 12 // 30
        for y in range(far, 44):
            c = P_HULL if y < far + 2 else P_HULL_SH if y == far + 2 else \
                P_DECK_JOINT if y % 4 == 3 else P_DECK_HI if y % 4 == 0 else P_DECK
            d.point((x, y), fill=c)
    R(136, 38, 141, 41, P_HULL_DK); R(136, 38, 141, 38, P_HULL_LO); R(141, 39, 141, 41, P_STEEL_DK)   # the windlass
    R(150, 30, 150, 40, P_HULL_DK)                                # the jack staff and its pennant
    R(144, 29, 149, 32, P_STRIPE); R(144, 29, 149, 29, P_STRIPE_HI); R(144, 32, 145, 32, CLEAR)
    # ---- the saloon: a white wall, a row of dark windows
    R(16, 33, 126, 43, P_HULL); R(16, 33, 126, 34, P_HULL_SH)     # the shade of the deck above
    R(16, 42, 126, 43, P_HULL_LO); R(16, 33, 16, 43, P_HULL_LO)
    for x in range(20, 122, 9):
        pane(d, x, 36, x + 5, 40, 5)
    # ---- the upper deck, open under its awning: the far rail in the dark, white stanchions
    R(18, 27, 104, 32, P_DARK)
    R(18, 30, 104, 30, P_HULL_DK)
    for x in range(20, 104, 8):
        R(x, 27, x, 32, P_HULL)
    R(18, 32, 104, 32, P_HULL_LO)
    # ---- the awning, seen from above: ribbed white sheet, a red edge
    R(16, 9, 106, 26, P_HULL_LO)
    for x in range(19, 106, 6):
        R(x, 10, x, 24, P_HULL_SH); R(x + 1, 10, x + 1, 23, P_HULL)
    R(16, 9, 106, 9, P_HULL); R(16, 24, 106, 24, P_HULL_SH)
    R(16, 25, 106, 25, P_STRIPE); R(16, 26, 106, 26, P_STRIPE_LO)
    R(105, 10, 106, 24, P_HULL_SH)
    # the funnel, standing on it, and its shade
    R(66, 13, 73, 18, P_HULL_SH); R(68, 19, 75, 20, P_HULL_SH)
    R(58, 2, 67, 16, P_STRIPE); R(58, 2, 59, 16, P_STRIPE_HI); R(65, 2, 67, 16, P_STRIPE_LO)
    R(58, 6, 67, 8, P_HULL); R(65, 6, 67, 8, P_HULL_LO)
    R(58, 2, 67, 3, P_SOOT); R(59, 2, 66, 2, P_HULL_DK)
    R(58, 16, 67, 16, P_STRIPE_DK)
    # ---- the wheelhouse forward: its roof from above, a wide dark window
    R(106, 24, 128, 33, P_HULL); R(127, 24, 128, 33, P_HULL_LO)
    pane(d, 109, 26, 125, 31, 6)
    R(104, 12, 130, 23, P_HULL_SH); R(104, 12, 130, 12, P_HULL); R(104, 12, 104, 22, P_HULL)
    R(105, 13, 129, 13, P_HULL_LO)
    R(104, 22, 130, 23, P_HULL_DK); R(129, 13, 130, 23, P_HULL_DK)
    R(116, 4, 117, 14, P_HULL_DK); R(111, 5, 122, 6, P_HULL_LO); R(111, 6, 122, 6, P_HULL_DK)       # the radar
    outline(im, P_INK)
    surf(im, 9, 147, 59)
    return im


def pier():
    im, d = canvas(5, 1)                 # 160 x 32
    for x in range(0, 158):                                       # boards laid across the walk, 8 wide
        board, col = x // 8, x % 8
        base = P_BOARD_ALT if speck(board, 0, 5) < 30 else P_TIMBER
        for y in range(6, 24):
            c = P_TIMBER_LO if col == 7 else P_DECK_HI if col == 0 else base
            if y == 6 and col != 7:
                c = P_DECK                                        # the string's shade
            if col in (2, 5) and y in (8, 21):
                c = P_TIMBER_DK                                   # nails
            if col == 3 and y == 9 + speck(board, 1, 5) % 11 and speck(board, 2, 5) < 45:
                c = P_TIMBER_LO                                   # a knot
            d.point((x, y), fill=c)
    d.rectangle([0, 3, 157, 3], fill=P_TIMBER_HI); d.rectangle([0, 4, 157, 4], fill=P_TIMBER)     # the north string
    d.rectangle([0, 5, 157, 5], fill=P_TIMBER_LO)
    d.rectangle([0, 24, 157, 24], fill=P_TIMBER_HI); d.rectangle([0, 25, 157, 25], fill=P_TIMBER)   # the south one
    d.rectangle([0, 26, 157, 27], fill=P_TIMBER_LO); d.rectangle([0, 28, 157, 28], fill=P_TIMBER_DK)  # ...and its face
    d.rectangle([156, 6, 157, 27], fill=P_TIMBER_LO); d.rectangle([156, 3, 157, 5], fill=P_TIMBER)
    for x in range(6, 158, 30):                                   # mooring posts along both edges
        for y in (0, 22):
            d.rectangle([x, y, x + 4, y + 7], fill=P_TIMBER)
            d.rectangle([x, y, x + 4, y + 1], fill=P_TIMBER_HI); d.rectangle([x, y, x, y + 7], fill=P_TIMBER_HI)
            d.rectangle([x + 4, y + 2, x + 4, y + 7], fill=P_TIMBER_LO); d.rectangle([x, y + 7, x + 4, y + 7], fill=P_TIMBER_DK)
            d.rectangle([x + 5, y + 6, x + 6, y + 7], fill=P_TIMBER_LO)       # its shade on the boards
        d.rectangle([x, 29, x + 4, 30], fill=P_TIMBER_DK)         # the pile under it
    outline(im, P_INK)
    px = im.load()
    for x in range(34, 158):                                      # the deck's shade on the water
        for y in (30, 31):
            if px[x, y][3] == 0:
                px[x, y] = P_SHADE
    return im
```
