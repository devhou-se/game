# #326 Temple interior sprites in the house look

## Context

`gamev2/tools/generate_temple_art.py` draws the 29 sprites of Senso-ji's main hall (room `TempleMarket1`),
all keyed `temple-in-*` (the ticket says "about 27"; the tool has no outdoor keys). The shapes are coherent
with each other, but none of their 354 colours is one the GuttyKreum pack uses: the outline is a near-black
purple `(30, 26, 44)`, shadows are `(0, 0, 0)`, ramps are continuous `mix()` gradients (the big lantern alone
has 214 colours), and lamps, flames and embers are baked lit yellow (`GLOW`, `FLAME`, `(255, 150, 70)`).

Outcome: the same 29 keys at the same sizes and anchors, redrawn so that every pixel is a colour found in
the pack's sheets, the outline is the pack's navy, and a lamp is the pack's dim gold `c6a663`. No new
shapes. Part 4 of 8 of #293; it needs nothing from #279 or #334 (neither is on master), so the tool carries
its own palette, as `generate_sendai_art.py` (`P_*`) and `generate_fukuoka_art.py` (`PACK_SWAP`) do.

A prototype of everything below was built in a scratch copy; before and after renders are attached to the
ticket. It came out at 85 colours in all (at most 36 in one sprite), every one in the sheets; `config.json`
came out unchanged, and the test rules below pass on it and fail on today's sprites.

## Approach

Three changes to the one tool, in the way the approved Sendai and Fukuoka redraws did it:

1. **The palette block becomes pack hexes.** Same constant names, so the drawing code barely changes.
2. **Lit yellow goes.** A lamp pane is `c6a663` with `a7843b` at its top and bottom and a small `f3d890`
   core (the Sendai pub's pane, `P_LAMP`/`P_LAMP_HI`); a flame is `c6a663` with an `f3d890` core; embers
   are the lantern's red with a gold middle. What makes the hall glow at night stays `Glows.js`, untouched.
3. **`settle(im)`, a backstop every sprite passes through before it is doubled**, moves any pixel whose
   colour is not in the tool's own list `PACK` to the nearest one that is, alpha kept. It is what turns the
   remaining `mix()` ramps (lantern barrel, the glow inside the kuden) into flat bands, and it catches
   blends the tool cannot name: the lattice veil's `alpha_composite` and Pillow's shape edges.

`PACK` is a closed list in the tool rather than the sheets read at run time: the tool stays self-contained
(no `art-source` path, nothing for `repo-layout.test.js`), and a unit test proves the list against the sheets.

## Changes

### `gamev2/tools/generate_temple_art.py`

Replace the palette block (lines 55-75) with:

```python
def rgb(h):
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))

# Every colour is one the GuttyKreum sheets use (art-source/GuttyKreum; temple.test.js checks it).
INK = rgb('1f1f3b')                      # the temple sheets' outline navy
VOID = rgb('080d16')
SHADE = rgb('080d16')                    # shadows and the lattice veil, with alpha
DAY = rgb('e4cecc')                      # daylight: slats' sun, the doorway, with alpha
WHITE, PAPER, PAPER_SH = rgb('fafcfd'), rgb('e4cecc'), rgb('be9e8c')
LAMP, LAMP_SH, LAMP_HI = rgb('c6a663'), rgb('a7843b'), rgb('f3d890')   # a pane; its core
FLAME, FLAME_HI = rgb('c6a663'), rgb('f3d890')
LQ, LQ_HI, LQ_DK = rgb('2a2636'), rgb('524b59'), rgb('171831')
RED, RED_HI, RED_DK = rgb('8a3a22'), rgb('aa4d31'), rgb('5b283b')
VERM, VERM_HI, VERM_DK = rgb('d16b56'), rgb('e78d7b'), rgb('aa4d31')
GOLD, GOLD_HI, GOLD_DK = rgb('c6a663'), rgb('e3c587'), rgb('a7843b')
LEAF_A, LEAF_B, LEAF_C = rgb('a7843b'), rgb('b2a168'), rgb('a7843b')
STONE, STONE_ALT, STONE_HI, STONE_DK = rgb('443d4a'), rgb('4c4754'), rgb('655d6d'), rgb('322b38')
STONE_GLINT = rgb('826f60')
WOOD, WOOD_HI, WOOD_DK = rgb('6d483b'), rgb('85553e'), rgb('4d3326')
BRONZE, BRONZE_HI, BRONZE_DK = rgb('506b6b'), rgb('6c8e7f'), rgb('2e4040')
BRASS, BRASS_HI, BRASS_DK = rgb('c6aa71'), rgb('e3c587'), rgb('86624c')
PURPLE, PURPLE_HI, PURPLE_DK = rgb('5c527d'), rgb('8f72b6'), rgb('3f3651')
TATAMI, TATAMI_HI, TATAMI_DK = rgb('716555'), rgb('928372'), rgb('584a43')
SKIN, SKIN_SH = rgb('ebbca2'), rgb('c69f96')
TEAL, TEAL_HI = rgb('3f827f'), rgb('6c8e7f')
PINK, PINK_HI = rgb('bb6479'), rgb('d78bc1')
LOTUS_G, LOTUS_G_HI = rgb('506d33'), rgb('83af6f')
SMOKE = rgb('d0ccdc')
# the rest of what settle() may leave in a sprite: frieze grounds, steel, ash, fruit, the bowl bell, charms
PACK_MORE = [rgb(h) for h in (
    '514542 232446 2d4051 35444a c66347 d7d0ba 20212a 413130 6b5241 3a5252 b0c276 e77f6a db785c 6b7d9a '
    '949494 949bb2 6d574e 433830 1b1e2a aaaaaa adb2c2 4a6262 dedede 7f513b 3a5792 dfdfdf f27e66 95402c '
    'e6d6cd d7af9e efefef 3a3b54 726f86 dae2e4 747e93 e75d42 8fb2b0 9599bb ebebe9 201c2d 76cae3').split()]
```

`GLOW` and `GLOW_HI` are gone: `LAMP_SH`, `LAMP` and `LAMP_HI` replace them where a pane is drawn.
`PACK` is a list of every constant above (order as written, no duplicates) followed by `PACK_MORE`;
`PACK_SET = set(PACK)`. Those are the only uses of `GLOW`/`GLOW_HI` in the file (lines 195, 211, 404, 769,
1034, 1037), all in the table below.

Then, by the current line numbers:

| Where | Now | Becomes |
|---|---|---|
| `shadow()` 131; naijin back shadow 729; lattice veil 805-806 | `(0, 0, 0, a)`, `(14, 10, 22, 96)` | `SHADE + (a,)`, `SHADE + (96,)` |
| `slab` glint 195 | `mix(STONE_HI, GLOW, 0.35)` | `STONE_GLINT` |
| `wall_side` slats 211 | `mix(GLOW_HI, RED_DK, 0.35)` | `PAPER_SH` |
| `sun` 233, `doorlight` 276 | `(255, 226, 170, a)`, `(255, 228, 170, a)` | `DAY + (a,)` |
| `threshold` 255 | `mix((255, 232, 190), WHITE, y / 31)` | `DAY if y in (0, 1, 2, 3, 5, 8) else WHITE` (bands that thin out) |
| `_toro(lit=True)` ~404 | pane `GLOW_HI` | pane `LAMP`, then `d.rectangle([x - 1, y + 8, x + 1, y + 9], fill=LAMP_HI)` |
| naijin standing lanterns 769 | `box(…, GLOW_HI)` | `box(…, LAMP)`, then `d.rectangle([lx - 2, 17, lx + 2, 23], fill=LAMP_HI)` |
| `jokoro` 975-978 | stick tips `(255, 120, 60)`, embers `(255, 150, 70)` with `FLAME_HI` | tips `VERM`, embers `VERM` with `GOLD` |
| `toro_hang` 1034-1037 | pane `GLOW_HI`, then a `mix(GLOW_HI, GLOW, …)` ramp over rows 24-40 | pane `LAMP`; rows 24-26 and 38-40 `LAMP_SH`; `d.rectangle([13, 29, 18, 35], fill=LAMP_HI)` |

Every other inline `(r, g, b)` colour literal (about 40: dragon, frieze grounds, night-blue, clouds, steel
cylinder, ash, bowl bell, drum skin, fruit, jewel, …) is replaced in the source by its nearest `PACK`
colour as `rgb('…')`, so the source says what is drawn; all of them are in `PACK_MORE` already. `mix()`
stays where it draws a ramp or a tint (chochin, kuden, charms, omikuji, pillar); `settle()` flattens it.

Add `settle(im)` above `main()` and call it on each sprite as it is built (`im = settle(fn())`), so the
preview sheet and the saved files both get it:

```python
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
```

Integer arithmetic and `min` over an ordered list (first wins a tie), so a re-run is identical on any
machine. Update the docstring ("a 1px ink outline" → the pack's navy, pack colours only, dim lamps).

Do not touch `main()`'s keys, sizes, anchors or `DEPTH_BIAS`, and import nothing from another generator.
Do not add `TEMPLE_`, `TempleMarket` or `temple-in-` to any other `generate_*.py` (`temple.test.js`).

After the first run, look at the preview sheet zoomed. Where `settle()` leaves a one-pixel sliver or a
speckle (most likely the chochin's ribs, the kuden's glow, the veiled lattice), draw that part as explicit
flat bands of `PACK` colours instead. If a colour is wanted that is not in `PACK`, take it from a sheet
and add it to `PACK_MORE`; the test below fails on anything the sheets do not have.

### `gamev2/assets/sprites/temple-in-*_0_0.png` (29 files)

Regenerated: `python3 tools/generate_temple_art.py` from `gamev2/`. `config.json` must come out unchanged
(same `spriteMetadata`, `tileNames`); `tiled/`, `assets/map` and `src/utils/Glows.js` are not touched
(interiors are not on the world map; the glow rows sit at fractions of unchanged sprites).

### `gamev2/tools/tests/temple.test.js`

New test, "the hall is drawn in the GuttyKreum pack's colours, with dim lamps (#326)":

- Build the set of RGBs of every fully opaque pixel of every PNG under `art-source/GuttyKreum` (walk the
  folder; `require(path.join(GV2, 'tools', 'png')).decode`; about 150 ms), minus `000000` and `ffffff`.
- For every `temple-in-*` key in `spriteMetadata`, every pixel with alpha > 0 has an RGB in that set
  (message: key and hex).
- No yellow brighter than the lamp core: a pixel with `r >= 0xf3`, `g >= 0xd0`, `b < 0xc8` is `f3d890`.
- `f3d890` is at most 8% of the non-clear pixels of any sprite (prototype: 5.5% in `toro-hang`, the most),
  and in `temple-in-toro-hang`, `-shokudai` and `-candles` there is more `c6a663` than `f3d890`.
- `1f1f3b` is in at least 20 of the sprites (the outline is the navy).

### `gamev2/docs/landmarks-and-towns.md`

The **Art** bullet of "The temple's main hall (issue #213)" (line 1344): after "draws all 29 sprites", say
they are in the pack's colours only (`PACK`, enforced by `settle()` and `temple.test.js`), outlined in the
pack's navy, with lamps in its dim gold and their night glow left to `Glows.js`.

## Data and interfaces

None. No key, size, anchor, `depthBias`, palette index, room layer or `Glows.SPRITES` row changes.
Rooms touched: none as map data; `TempleMarket1` is the only room that looks different.

## Tests

From `gamev2/`:

```bash
python3 tools/generate_temple_art.py --preview /tmp/sheet.png   # look at it, zoomed
python3 tools/generate_temple_art.py && git status --short      # only the tool, the 29 PNGs (+ test, doc)
node tools/play.js render TempleMarket1 /tmp/after.png          # against a render made before the change
node tools/test_game.js
python3 tools/test_blog_to_npc.py
node tools/play.js check
python3 tools/check_generators.py                               # generate_temple, generate_temple_art: ok
python3 tools/sync_cities.py --check
```

Then the browser regression (`tools/browser/regress.js`, `tools/browser/README.md`) and playing it: enter
the hall from Market (27,15) or (28,15), desktop and a phone size, by day and with `?tod=night`. At night
check that each glow still sits on its lamp (hanging lanterns, candlesticks, candle rack, big lantern,
censer, the inner sanctum's lanterns, the kuden) and that no sprite carries a pane that reads as lit
without its glow. Attach before and after captures.

## Risks and open questions

- **Which navy.** `1f1f3b` is the outline colour of the pack's own temple sheets, and visibly navy on the
  hall's dark floor. Sendai and Hokkaido outline in `080d16`/`0a1627` (the city sheets); the prototype was
  tried with `0a1627` too and it also reads well, only blacker. One constant if the owner prefers it.
- **Daylight at night.** The slats' sun, the threshold and the doorway shaft are drawn as day and are not
  dimmed apart from the room's night tint. That is how the hall is today; not changed here.
- **Glow colours** in `Glows.js` stay warm (`0xffb860`…): they are additive light, not sprite pixels, and
  no approved redraw has changed its rows. If a glow looks too hot over the dimmer pane, say so in the
  summary rather than retuning it here.
- **#320** (this file's outdoor keys) has nothing to redraw: the tool only has `temple-in-*` keys.
- The owner's written recipe for the look (#279) is not on master; this follows the code of the approved
  Sendai, Kanazawa and Fukuoka redraws.
