# #314 Shrine worship-hall sprites in the house look

## Context

`gamev2/tools/generate_shrine_art.py` draws the inside of the seven shrine worship halls (`ShrineTokyo1`,
`ShrineKanazawa1` in the blue look; `ShrineMarket1`, `ShrinePark1`, `ShrineNara1`, `ShrineFukuoka1`,
`ShrineFukuoka2` in the red). It registers 46 keys, all `shrine-in-*`: 16 per look and 14 shared. **It has
no outdoor keys**: a shrine's building, roof and torii are pack art cut by other tools, and `shrine-in-rope`
is pack art cut by `extract_shrine.py`. So this ticket is the interior only, as the owner's sizing comment
accepted.

Six of the 46 are #299's and must not change: `shrine-in-honden-{red,blue}` and
`shrine-in-runner-{l,r}-{red,blue}`. That leaves **40 keys in scope**.

Today none of the tool's colours is one the GuttyKreum sheets use: the outline is `(38, 43, 68)`, shadows
are black, and lamps, the paper screen, the threshold and the doorway's daylight are lit yellow (`GLOW`,
`GLOW_HI`, `(255, 232, 170)`), partly as continuous `mix()` ramps.

Outcome: the same 46 keys at the same sizes, anchors and `depthBias`; the 40 redrawn so that every pixel
is a colour of the pack's sheets, outlined in the pack's navy, with lamps in its dim gold `c6a663`; the six
left pixel for pixel and byte for byte as committed. No new shapes, no map data.

This is the recipe of #326 (the temple hall, merged), which the implementer should read beside this:
`docs/workshop/326-temple-interior-sprites-temple-in-in-the.md`, `tools/generate_temple_art.py`.

Everything below was built in a scratch copy. It came out at 52 colours in all (at most 19 in one sprite,
the counter), every one in the sheets; `settle()` had nothing left to move; `config.json` and the six kept
PNGs were byte-identical; the new test passed on it and fails on today's sprites
(`shrine-in-bell: #262b44`). Before and after pictures are attached to the ticket.

The branch was 26 commits behind `master` and had none of its own, so it was fast-forwarded to
`origin/master` (`adc5c45c`) before this design was written: #326 and `tools/house_look.py` are in it.

## Approach

Four changes to the one tool:

1. **The palette block becomes pack hexes** under the same constant names, so the drawing code barely
   changes. A few names are added for inline literals (`SHADE`, `DAY`, `LAMP*`, `ROOF*`, `SKIN`, ...).
2. **Lit yellow goes.** The standing lamp's pane is `c6a663` with `a7843b` rows at top and bottom and a
   small `f3d890` core (#326's pane). Paper, the threshold and the doorway's shaft are daylight
   (`e4cecc`/`fafcfd`), not lamplight. The hanging lanterns keep their body colour (red, or the blue
   look's white paper) in three flat tones. The night glow stays `DayNight`'s halo on every `*-lanterns*`
   tile of a `lanternLight` room; no JavaScript changes.
3. **`settle(im)`**, #326's backstop, on each of the 40 before it is doubled: any pixel not in the tool's
   closed list `PACK` moves to the nearest colour that is. With the edits below it moves nothing; it is
   there for the next edit.
4. **The six kept sprites are drawn with the old colours.** `honden()`, `runner()` and `_sanbo()` are not
   edited at all (so #299, which rewrites exactly those, merges without a conflict in them); they and the
   helpers they call (`bar`, `post`, `box`) read module globals, so a wrapper `before_314()` swaps the
   globals back to the pre-#314 values while one of the six is drawn. They are not settled. A
   `save_png()` (the #384/#390 pattern) leaves a file whose pixels are unchanged alone, so the six PNGs
   are not even re-encoded (a plain rerun today rewrites every shrine PNG's bytes on Pillow 11.3.0).

Alternative for 4, rejected: renaming the constants the 40 use and leaving the old ones in place. It
touches every function and leaves two palettes with no marker of which is temporary.

`tools/house_look.py` is not imported: nothing here needs its helpers (no new shapes), and #326's tool,
this one's sibling, carries its own closed list the same way.

## Changes

### `gamev2/tools/generate_shrine_art.py`

Add `import os`. Replace the palette block (lines 57-94, `INK = …` to the end of `LOOKS`) with:

```python
def rgb(h):
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


# Every colour is one the GuttyKreum sheets use (art-source/GuttyKreum; shrines.test.js checks it).
INK = rgb('1f1f3b')                      # the temple sheets' outline navy
VOID = rgb('080d16')
SHADE = rgb('080d16')                    # shadows on the floor, with alpha
DAY = rgb('e4cecc')                      # daylight and what it falls on: the doorway, a drum's head
WHITE, PAPER, PAPER_SH, PAPER_WARM = rgb('fafcfd'), rgb('e4cecc'), rgb('bcc7cc'), rgb('d7b6ab')
LAMP, LAMP_SH, LAMP_HI = rgb('c6a663'), rgb('a7843b'), rgb('f3d890')   # a paper lamp's pane; its small core
STRAW, STRAW_HI, STRAW_DK, STRAW_LAY = rgb('c6aa71'), rgb('e3c587'), rgb('a7843b'), rgb('86624f')
GOLD, GOLD_HI, GOLD_DK = rgb('c6a663'), rgb('e3c587'), rgb('a7843b')
WOOD, WOOD_HI, WOOD_DK = rgb('aa775f'), rgb('bb8971'), rgb('86624f')
PALE, PALE_HI, PALE_DK = rgb('e3c587'), rgb('d7d0ba'), rgb('c6aa71')              # bare cypress
PLAQUE = rgb('d7b6ab')
DARK, DARK_HI, DARK_DK = rgb('5a3827'), rgb('86624f'), rgb('322b38')
RED, RED_HI, RED_DK = rgb('aa4d31'), rgb('d16b56'), rgb('8a3a22')                 # the pack's shrine red
GREEN, GREEN_HI, GREEN_DK = rgb('678e57'), rgb('83af6f'), rgb('506b6b')
TATAMI, TATAMI_HI, TATAMI_DK = rgb('b2ad73'), rgb('b0c276'), rgb('b2a168')
HERI = rgb('2e4040')
STONE, STONE_HI, STONE_DK = rgb('949bb2'), rgb('bcc7cc'), rgb('656e92')
PURPLE, PURPLE_HI, PURPLE_DK = rgb('5c527d'), rgb('8f72b6'), rgb('3f3651')
BLUE = rgb('425faa')
ROOF, ROOF_HI, ROOF_DK = rgb('53596d'), rgb('8689a6'), rgb('3c3a4c')              # the plaque rack's little roof
SKIN, HAIR, SLOT = rgb('ebbca2'), rgb('2a2636'), rgb('2a2636')

LOOKS = {
    'red': dict(
        floor=rgb('5a3827'), floor_alt=rgb('68422d'), floor_hi=rgb('86624f'), floor_dk=rgb('3f210f'),
        post=RED, post_hi=RED_HI, post_dk=RED_DK, shine=rgb('e78d7b'),
        trim=GOLD, trim_hi=GOLD_HI, trim_dk=GOLD_DK,
        plaster=rgb('e4cecc'), plaster_sh=rgb('d7b6ab'),
        board=rgb('71412a'), board_hi=rgb('86624f'), board_dk=rgb('4d3326'),
        cloth=PURPLE, cloth_hi=PURPLE_HI, cloth_dk=PURPLE_DK, crest=GOLD_HI,
        lamp=rgb('d16b56'), lamp_hi=rgb('e78d7b'), lamp_dk=rgb('aa4d31'), lamp_mark=rgb('322b38'),
    ),
    'blue': dict(
        floor=rgb('443d4a'), floor_alt=rgb('4c4754'), floor_hi=rgb('655d6d'), floor_dk=rgb('322b38'),
        post=PALE, post_hi=PALE_HI, post_dk=PALE_DK, shine=WHITE,
        trim=rgb('949bb2'), trim_hi=rgb('d1e2eb'), trim_dk=rgb('656e92'),
        plaster=rgb('e1e9ec'), plaster_sh=rgb('bcc7cc'),
        board=rgb('554e62'), board_hi=rgb('78768a'), board_dk=rgb('3c3a4c'),
        cloth=rgb('314b8e'), cloth_hi=rgb('425faa'), cloth_dk=rgb('172459'), crest=WHITE,
        lamp=rgb('e1e9ec'), lamp_hi=rgb('fafcfd'), lamp_dk=rgb('bcc7cc'), lamp_mark=rgb('314b8e'),
    ),
}

# the closed list settle() moves every pixel onto: the constants above and the two looks, in order
PACK = list(dict.fromkeys([
    INK, VOID, SHADE, DAY, WHITE, PAPER, PAPER_SH, PAPER_WARM, LAMP, LAMP_SH, LAMP_HI,
    STRAW, STRAW_HI, STRAW_DK, STRAW_LAY, GOLD, GOLD_HI, GOLD_DK, WOOD, WOOD_HI, WOOD_DK,
    PALE, PALE_HI, PALE_DK, PLAQUE, DARK, DARK_HI, DARK_DK, RED, RED_HI, RED_DK,
    GREEN, GREEN_HI, GREEN_DK, TATAMI, TATAMI_HI, TATAMI_DK, HERI, STONE, STONE_HI, STONE_DK,
    PURPLE, PURPLE_HI, PURPLE_DK, BLUE, ROOF, ROOF_HI, ROOF_DK, SKIN, HAIR, SLOT,
] + [c for P in LOOKS.values() for c in P.values()]))
PACK_SET = set(PACK)
```

`GLOW`, `GLOW_HI` and the looks' `deep`/`deep_hi` leave the live palette (only `honden()` and `runner()`
read them, through `BEFORE_314` below). `shine` is the one new key of a look.

Then, by the current line numbers. Do not edit `runner()` (389-415), `_sanbo()` (468-487) or `honden()`
(489-602).

| Where | Now | Becomes |
|---|---|---|
| shadows: 461, 640, 748, 771, 808, 848, 870, 930 | `fill=(0, 0, 0, 70)` | `fill=SHADE + (70,)` |
| `wall_shoji` 296-299 | `GLOW_HI` box, then a `mix(GLOW_HI, PAPER, …)` ramp over rows 12-57 | `d.rectangle([6, 12, 30, 58], fill=P['plaster'])`, then `d.rectangle([7, 21, 29, 35], fill=WHITE)`; comment "a paper screen, daylight behind it" |
| `threshold` 353-356 | two `mix()` ramps | `d.rectangle([0, 0, 31, 31], fill=WHITE)`; rows 0-5 are `(P['floor_hi'], P['floor_hi'], PAPER_WARM, PAPER_WARM, DAY, DAY)` |
| `threshold` 358-361 | joints `(236, 226, 190)`, `(240, 232, 204)`; a `WHITE` line at y=21 | the three joint lines `DAY`; the y=21 line dropped (the line at y=6 stays `STONE_HI`) |
| `doorlight` 385 | `(255, 232, 170, int(a * 255))` | `DAY + (int(a * 255),)` |
| `pillar` 429 | `mix(P['post_hi'], WHITE, 0.35)` | `P['shine']` |
| `saisen` 646 | `(36, 26, 34)` | `SLOT` |
| `bell` rope | `strands = (RED, WHITE, PURPLE)`, each strand `mix`ed toward `WHITE` at `k == 0` and `INK` at `k >= 5` | `strands = ((RED_HI, RED, RED_DK), (WHITE, WHITE, PAPER_SH), (PURPLE_HI, PURPLE, PURPLE_DK))`; `fill=strands[band][0 if k == 0 else 2 if k >= 5 else 1]` |
| `hanging_lantern` body | `mix(P['lamp'], P['lamp_hi'], glow)`, `mix`ed to `lamp_dk` when `u > 0.82` | `P['lamp_dk'] if u > 0.82 else P['lamp_hi'] if glow > 0.6 else P['lamp']` |
| `hanging_lantern` ribs | `mix(P['lamp'], P['lamp_dk'], 0.6)` | `P['lamp_dk']` |
| `floor_lantern` 751-755 | `GLOW_HI` box, a `mix(WHITE, GLOW, …)` ramp, a white flame ellipse | `box(d, 8, 24, 23, 48, LAMP, INK)`; `d.rectangle([9, 25, 22, 27], fill=LAMP_SH)`; `d.rectangle([9, 45, 22, 47], fill=LAMP_SH)`; `d.rectangle([14, 34, 17, 40], fill=LAMP_HI)` |
| `ema` 774 | `(70, 48, 50)` | `DARK_DK` |
| `ema` plaques | `woods` = three literals; highlight `mix(col, WHITE, 0.4)`; writing `mix(col, INK, 0.65)` | `woods = ((PALE, PALE_HI), (STRAW, PALE), (PLAQUE, PALE_HI))`; `col, lit = rnd.choice(woods)` (keep `w = 9` and the order of the `rnd` calls); highlight `lit`; writing `DARK` |
| `ema` roof 794-797 | `(74, 84, 110)`, `(52, 60, 86)`, `(120, 132, 160)` | `ROOF`, `ROOF_DK`, `ROOF_HI` |
| `counter` 872-910 | `(232, 222, 200)`; `(40, 34, 48)` ×3; face `(246, 214, 186)`; `(204, 110, 100)`; `(72, 116, 196)` ×2 | `DAY`; `HAIR`; `SKIN`; `RED_HI`; `BLUE` |
| `drum` 935-944 | `(150, 60, 48)`, `(120, 44, 44)`, `(240, 228, 196)`, `(250, 242, 216)`, `(206, 190, 160)` | `RED`, `RED_DK`, `DAY`, `WHITE`, `PAPER_WARM` |
| `shimenawa` twist | `col = mix(col, STRAW_DK, 0.55)` | `col = STRAW_DK if u < 0.7 else STRAW_LAY` |
| `sprites()` | `honden(look)`, `runner(look, 'l')`, `runner(look, 'r')` | `before_314(honden, look)`, `before_314(runner, look, 'l')`, `before_314(runner, look, 'r')` |
| `main()` 1033-1041 | `im = fn()`; `im.save(path)` | `im = fn() if name in KEPT else settle(fn())` (`name` being the key without `_0_0`, as `KEPT` holds it); `save_png(im, path)` |

After these no `mix()` call and no colour literal is left outside the three untouched functions.

Above `main()`, add (`settle` is #326's, `save_png` is `generate_kanazawa_art.py`'s):

```python
# ---- the six sprites #299 redraws ----
# The sanctuary and the runner, in both looks, are left exactly as they were: #299
# redraws them. Until it does they are drawn in the colours this tool had before #314
# and are not settled; honden(), runner() and _sanbo() above are untouched. When #299
# lands: delete BEFORE_314, before_314(), KEPT and their uses.
BEFORE_314 = dict(
    INK=(38, 43, 68), WHITE=(250, 250, 246), PAPER=(240, 238, 226), PAPER_SH=(206, 208, 220),
    GOLD=(232, 184, 74), GOLD_HI=(252, 228, 138), GOLD_DK=(168, 118, 52),
    PALE=(222, 190, 138), PALE_HI=(244, 222, 172), PALE_DK=(170, 134, 96),
    DARK=(92, 60, 52), DARK_HI=(124, 84, 68), DARK_DK=(62, 40, 42),
    RED=(204, 62, 50), RED_HI=(236, 104, 72), RED_DK=(146, 40, 46),
    GLOW=(255, 214, 130), GLOW_HI=(255, 244, 200),
    LOOKS={
        'red': dict(
            floor=(88, 54, 46), floor_hi=(132, 88, 66), floor_dk=(64, 40, 40),
            post=(204, 62, 50), post_hi=(236, 104, 72), post_dk=(146, 40, 46),
            trim=(232, 184, 74), trim_hi=(252, 228, 138), trim_dk=(168, 118, 52),
            plaster_sh=(212, 196, 170),
            board=(104, 64, 52), board_hi=(136, 90, 68), board_dk=(72, 44, 42),
            cloth=(116, 76, 148), cloth_hi=(156, 116, 186), cloth_dk=(80, 50, 108),
            deep=(40, 22, 34), deep_hi=(74, 36, 44),
        ),
        'blue': dict(
            floor=(70, 64, 78), floor_hi=(112, 104, 122), floor_dk=(50, 46, 62),
            post=(222, 190, 138), post_hi=(244, 222, 172), post_dk=(170, 134, 96),
            trim=(150, 158, 178), trim_hi=(214, 220, 232), trim_dk=(96, 104, 132),
            plaster_sh=(204, 210, 222),
            board=(86, 78, 92), board_hi=(120, 110, 126), board_dk=(58, 52, 70),
            cloth=(54, 76, 136), cloth_hi=(92, 118, 178), cloth_dk=(36, 50, 96),
            deep=(24, 28, 52), deep_hi=(44, 54, 92),
        ),
    },
)
KEPT = {f'shrine-in-{piece}-{look}' for piece in ('honden', 'runner-l', 'runner-r') for look in LOOKS}


def before_314(factory, *args):
    """factory(*args)'s sprite, drawn with the module's colours set back to BEFORE_314."""
    def draw():
        now = {k: v for k, v in globals().items() if k in BEFORE_314}
        globals().update(BEFORE_314)
        try:
            return factory(*args)()
        finally:
            for k in BEFORE_314:
                del globals()[k]
            globals().update(now)
    return draw


def settle(im):
    """Move every pixel that is not a PACK colour to the nearest one that is; alpha is kept."""
    px, memo = im.load(), {}
    for y in range(im.height):
        for x in range(im.width):
            r, g, b, a = px[x, y]
            if a == 0 or (r, g, b) in PACK_SET:
                continue
            k = (r, g, b)
            if k not in memo:
                memo[k] = min(PACK, key=lambda c: 2 * (c[0] - r) ** 2 + 4 * (c[1] - g) ** 2 + 3 * (c[2] - b) ** 2)
            px[x, y] = memo[k] + (a,)
    return im


def save_png(im, path):
    """Write im unless the file already holds these pixels, so a rerun leaves the
    committed PNGs byte for byte as they are whatever Pillow's encoder does."""
    if os.path.exists(path):
        with Image.open(path) as old:
            if old.size == im.size and old.convert('RGBA').tobytes() == im.convert('RGBA').tobytes():
                return False
    im.save(path)
    return True
```

`BEFORE_314` holds exactly the old values `honden()`, `runner()`, `_sanbo()` and their helpers read
(copied from today's lines 57-93); `factory(*args)()` is called inside the swap because the factories read
`LOOKS[look]` when called.

Update the docstring: "a 1px ink outline" becomes the pack's navy, GuttyKreum colours only, dim lamps;
`wall-shoji` is "a paper screen", not "a lit paper screen"; and one line that honden and runner are #299's
and still in the old colours.

Do not touch the keys, sizes, anchors, `DEPTH_BIAS` or the config-writing half of `main()`.

If a colour is wanted that the block does not have, take it from a sheet and add it to the block and to
`PACK`; the test fails on anything the sheets do not have. Do not use `2b373c` (#375/#378: it is not a
pack colour).

### `gamev2/assets/sprites/shrine-in-*_0_0.png` (40 files)

Regenerated from `gamev2/`: `python3 tools/generate_shrine_art.py`. `git status` must show the 40 PNGs
and not the six kept ones, `shrine-in-rope_0_0.png` or `config.json`. Run it a second time: nothing more
changes. `tiled/`, `assets/map` and `src/` are not touched.

### `gamev2/tools/tests/shrines.test.js`

New test, "the worship halls are drawn in the GuttyKreum pack's colours, with dim lamps (#314)", built as
`temple.test.js`'s #326 test is (lines 362-398: the same `walk`, `hex` and `pack` set):

- keys: every `shrine-in-*` key of `spriteMetadata` except `/^shrine-in-(honden|runner-[lr])-(red|blue)_0_0$/`
  (comment: #299's, to be removed from the exclusion when it lands); there are 41 (the 40 and the pack's
  rope, which passes as it is).
- every pixel with alpha > 0 has an RGB in the pack set (message: key and hex).
- no lit yellow: a pixel with `r >= 0xf3`, `g >= 0xd0`, `b < 0xc8` is `f3d890`.
- `f3d890` is at most 4% of the shown pixels of any sprite (prototype: 1.7% in `lanterns-floor`, the only
  one that has it), and `shrine-in-lanterns-floor` has more `c6a663` than `f3d890`.
- `1f1f3b` is in at least 30 of the sprites (prototype: 34; the floors, tatami and doorlight have no
  outline).

No rerun-leaves-bytes test as #384/#390 have: this tool's `main()` writes `config.json` and a fixed
folder, and making that redirectable is not this ticket. The two runs and `git status` above cover it.

### `gamev2/docs/landmarks-and-towns.md`

The **Art** bullet of "Shrine worship halls (issue #212)" (line 1241): after "in the two looks (…)", say
the pieces are in the pack's colours only (`PACK`, enforced by `settle()` and `shrines.test.js`), outlined
in the temple sheets' navy, with the standing lamp in the pack's dim gold and the night glow left to the
lantern halo; and that the sanctuary and the runner are still in the old colours until #299.

## Data and interfaces

None. No key, size, anchor, `depthBias`, palette index, room layer, door cell or JavaScript changes.
Rooms touched: none as map data. The seven `Shrine*` rooms look different.

## Tests

From `gamev2/`, with renders made **before** the change kept for comparison:

```bash
node tools/play.js render ShrinePark1 /tmp/before-park.png        # also ShrineTokyo1, ShrineFukuoka1
python3 tools/generate_shrine_art.py --preview /tmp/sheet.png     # look at it, zoomed
python3 tools/generate_shrine_art.py && git status --short        # the tool, 40 PNGs (+ test, doc); twice
node tools/play.js render ShrinePark1 /tmp/after-park.png         # red; ShrineTokyo1 blue; ShrineFukuoka1 large
node tools/test_game.js
python3 tools/test_blog_to_npc.py
node tools/play.js check
python3 tools/check_generators.py           # generate_shrine_art, generate_shrines, extract_shrine: ok
python3 tools/sync_cities.py --check
```

Then the browser regression (`tools/browser/regress.js`, `tools/browser/README.md`; it asserts nothing
about these pixels) and playing it on desktop and a phone size: walk into a red hall and a blue one (the
top step of the shrine in Park and in Tokyo), bump the offering box and the fortune stand, by day and with
`?tod=night`. At night check that every hanging lantern and standing lamp still has its halo and that no
pane, screen or doorway reads as lit without one. Save before and after captures to `/work/media/`.

The summary must say which sprites still read flat. From the prototype, expect to name: the side walls
(68% one colour) and `wall-front` (46%), which are mostly the dark beyond the wall; the threshold (58%
white); the zabuton (61% one purple); the floors (4 colours); the doorlight (one tint under alpha). The
ticket rules out new shapes, so these are reported, not reworked.

## Risks and open questions

- **The sanctuary and the runner will not match until #299.** They stay bright vermilion `(204, 62, 50)`
  with lit-yellow lamps and a glowing runner foot, beside the pack's brick red `aa4d31` and dim lamps
  (see the attached renders: the runner is the loudest thing in a red hall). That is the ticket's
  instruction. #299 is currently labelled `workshop/skip`; the owner may want to un-park it.
- **Merge with #299.** Only `sprites()`' three lines and the top-of-file palette can conflict; the three
  functions it rewrites are untouched here. Whoever lands second removes `BEFORE_314`, `before_314()`,
  `KEPT` and the test's exclusion, and puts the six through `settle()`. If #299 is already on `master`
  when this is implemented, the rule is the same (the six stay pixel-identical to what is committed):
  keep in `BEFORE_314` only what its `honden()`/`runner()` still read, or drop the mechanism if nothing.
- **Outdoor pieces.** The ticket's title names them but this tool has none, and the red pagoda roofs and
  shrine tops are pack art. Nothing outdoor is drawn here; the owner should confirm that is a separate
  ticket if any generated outdoor shrine piece exists elsewhere.
- **Which navy.** `1f1f3b` is the temple sheets' outline and what #326 used; the recipe's city navy is
  `0a1627`/`080d16`. One constant (`INK`) and one test line if the owner prefers the other.
- **Red is calmer.** Vermilion lacquer becomes the pack's shrine red (`aa4d31`, `d16b56` lit), the gilt
  its unlit gold. The red halls lose some of their brightness; that is the look, but it is the most
  visible change. The red look's plaster and paper (`e4cecc`) have the pack's slight pink.
- **Daylight at night.** The threshold and the doorway's shaft are drawn as day, as today, and only take
  the room's night tint. Not changed here; say so in the summary if it looks wrong at `?tod=night`.
