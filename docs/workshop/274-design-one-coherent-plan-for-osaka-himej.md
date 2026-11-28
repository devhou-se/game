# Design: one coherent plan for Osaka, Himeji and Okayama (#274)

Part 1 of 4 of #273 ("Okayama and Himeji are too similar ... I want a redesign of the Osaka region with all 3
zones designed in consideration with the other 2"). #275 (Himeji), #276 (Okayama) and #277 (Osaka) build it.

## Context

`KansaiCity` is three generated rooms stitched into one: Okayama 44x40, Himeji 44x40, Osaka 50x46
(`gamev2/tools/kansai.py`). Himeji (#255) and Okayama (#267) were each designed alone from the same recipe,
and side by side they are one room drawn twice; Osaka between them and its planned neighbours is still the
generic town of towers and houses, with its own art (#219, 52 PNGs) drawn but never placed.

This ticket writes the plan the three rebuilds follow, as a section of
`gamev2/docs/landmarks-and-towns.md`. It changes no code, no map and no test.

## Approach

One section, added after the existing "Kansai" section, that: names what repeats; gives the region one
idea (a single walk west along one road, on which road, water, ground and skyline each change role per
district); fixes the cells no ticket may move (seams, the cells of the dated posts that stay); gives each
district a target layout; says what happens to every dated post; and gives the build order and the rooms
each ticket touches. The existing "Kansai" section keeps describing the rooms as built; each follow-up
rewrites its own district's bullet there and deletes its part of the plan.

The layouts below were drawn to cell on a schematic (attached to the ticket with this design: no
overlaps, every seam on its rows, every kept post on a walkable cell). They are **targets**: each follow-up
has its own design stage and settles them by blockout. What is marked **fixed** it may not move.

Choices that were close:

- **The avenue stays straight on its rows in Himeji** rather than bending round a central castle hill. The
  bend would give the castle more depth, but the kit has no road bend, and Okayama is reached only through
  Himeji, so every through-walk would pay for it. The hairpin of courts gives the climb instead.
- **Okayama's garden moves to the south-west bank of a bending river**, so Damian's 12 November post moves
  with the cranes (same label, new cell). Keeping (27,31) would mean keeping the island where it is, which
  is the composition being removed.
- **Osaka is #219's unbuilt Stage E, amended**, not a new design: the art exists and the plan was agreed.
  Stage E predates the Kansai seams and closes the avenue's ends; the amendment keeps the avenue.
- **`kansai.py` is not edited by any of the three tickets**: every seam keeps its rows, so each ticket
  touches one outdoor room and none collides with #268 (Nara), which does edit it.

## Changes

### `gamev2/docs/landmarks-and-towns.md`

1. In the opening paragraph of "### Kansai: Osaka, with Himeji and Okayama on foot", add one sentence at
   its end: `All three are to be rebuilt to one plan: see "Kansai: one plan for Osaka, Himeji and Okayama"
   below.`
2. Insert the section below between the end of that section (its "Build order" bullet) and
   "### Karuizawa". Carry it over as written (re-wrap to the file's line width; do not change a cell, a
   name or a rule).

~~~markdown
### Kansai: one plan for Osaka, Himeji and Okayama (issue #273; the plan #274, built by #275, #276, #277)

**This is a plan, not what is built**: the section above describes the rooms as they are. Each of the three
tickets rebuilds one room to this plan, rewrites that room's bullet above, and deletes its part here.
**Fixed** means a ticket may not move it. A **target** is the cell the plan was drawn with: the ticket's own
design may shift it by blockout, but not change what it is or which side of what it stands on.

- **What repeats today.** Himeji and Okayama are the same room twice:
  1. *The same three bands on the same rows of a 44x40 room*: castle north (Himeji rows 0-13, Okayama
     3-14), the avenue straight through on rows 18-22, a garden south (rows 24-37).
  2. *The same castle*: a salmon `gravel-autotile` terrace as wide as the room (Himeji 6..41, Okayama
     13..40) above a retaining wall along its whole south side, with one two-column way up (the gateway on
     32-33, the steps on 21-22), four `sendai-pine` and two or three `sendai-stone-lantern` on the gravel,
     and a frontal grey-roofed keep on a stone base at the top with its visitor in front.
  3. *The same garden*: a rectangle entered on columns 21-22 in both (Koko-en's gate, the Tsukimi bridge)
     with lanterns flanking the entry, a rectangular two-cell gravel loop (8..38 x 27..35 and 9..36 x
     28..34) round a lawn with a two-row `b.pond`, three maples and some pines. Both gardens' district
     `stand` is (22,28).
  4. *The same water*: a three-row rock-rimmed `pond-autotile` band crossed north-south by one 2x4 deck.
  5. *The same edges*: the same `AUTUMN` list (`sendai-maple`, `-pine`, `-cedar`) as solid wood all round.
  6. *The same arrival*: in from the east on rows 18-22 along an empty three-lane road, a wall behind a
     verge to the north, the garden's boundary to the south, a fingerpost with its feet on (39,23).

  Osaka shares nothing with them and has little of its own: three generic towers, two generic houses and
  a house for a station on grey brick, and the same road.
- **The idea: one walk west along one road, from the city to where the road ends.** Each thing the three
  share changes role from district to district, so no two use it the same way:

  | | Osaka: the city on the canal | Himeji: the castle on its hill | Okayama: the garden in the river |
  |---|---|---|---|
  | You | browse | climb | stroll |
  | Shape | east-west strata crossed by one north-south street | a hairpin of walled courts north, a row of walled garden rooms south; everything square and enclosed | two banks of a river that bends; nothing on an axis, nothing walled |
  | The road | a city avenue: lights, a crossing, fronts and signs | a quiet road under the castle wall, passing through | stops at the river after ten cells |
  | Water | a straight canal between quays, with boats | the canal's west end as the moat, rock-rimmed under a white wall; the same boats | an open river, off the map by two edges; a garden pond |
  | Ground | paved edge to edge: grey brick, boardwalk, retro paving; no lawn | swept `sand-autotile` courts; lawn only inside Koko-en | lawn; `gravel-autotile` only as paths |
  | Skyline | towers and signs: Tsutenkaku, the wheel, sign towers | one white keep on the top row, one turret | low: trees, a mound, the black keep down at the water |
  | Trees | none but the tower's garden | pines; maples only inside Koko-en | maples and cedars; a pine only as a specimen |
  | Its own art | `osaka-*` (#219) | `himeji-*` | `okayama-*` |

- **Fixed for all three tickets.**
  - `tools/kansai.py` is not edited: `AT`, `SIZE`, the avenue and water rows, `JOINS` and `seams()` stay.
    (#268 and #269 edit it to add their districts.)
  - The seams, and the two columns inside each (x 0-1, x W-2..W-1), which hold only the avenue, water, a
    verge and wood or hedge:

    | Edge | Avenue (pavement, three road rows, pavement) | Water |
    |---|---|---|
    | Okayama x=43 = Himeji x=0 | rows 18-22 both | none |
    | Himeji x=43 = Osaka x=0 | Himeji 18-22 = Osaka 24-28 | Himeji 14-16 = Osaka 20-22, one `waterways` run |
    | Osaka x=49 (= Nara x=0, #268) | Osaka 24-28 | Osaka 20-22 |

    with `edge-n` / `edge-s` pavement pieces on the edge cells and the five hidden transporters each way.
  - The fingerposts, by the cell each is stamped at (1x2, feet one row below): Osaka (2,28); Himeji
    (39,22) and (4,22); Okayama (39,22). `Places.arrival` for Himeji and Okayama stays (40,18).
  - Himeji and Okayama have no station, no `train-track*` tile, no door and no ordinary sealed building.
    No bins. Real places only.
  - "the pond" stays a spot of the garden in both: the first `pond-autotile_corner-nw` in `"x,y"` string
    order must be the garden pond's.
  - `check_distinct.py`: no ticket leaves Kansai worse than `tools/distinct_baseline.json`. It is "most
    like Sendai" through the `sendai-*` trees, lantern and wall: no ticket adds another `sendai-*` kind.

- **Himeji (#275): a climb.** The castle is the district, and you earn the keep.
  - *Fixed*: the keep `himeji-keep` 10x8 at (8,0) and its visitor's cell (12,8); the moat on rows 14-16
    from its bank at x=6 to x=43 with its `waterways` entry from 7; the avenue on rows 18-22 across the
    whole room.
  - *North of the moat, three courts walked as a hairpin* (targets): over the bridge (columns 32-33) and
    through the gatehouse (6x4 at (30,10)) in the white wall on its stone base (rows 10-13, x 6..41) into
    **Sannomaru** (23..41, 6..9); east to steps (38-39) up an inner stone wall (rows 4-5, x 20..41); back
    west along the **upper walk** (18..41, 2..3); down the lane by the keep's east flank (18..19, 2..7)
    into **Honmaru** (6..19, 8..9), in front of the keep. The turret (3x4, solid) stands on (20,6) and
    closes Honmaru from Sannomaru, so the hairpin is the only way. About 50 cells from the bridge to the
    visitor, where it is 28 today.
  - *South of the avenue, Koko-en as three walled rooms in a row* (targets), not a loop: the earthen wall
    on row 24; the roofed gate 4x3 at (8,23), gateway columns 9-10, at the Okayama end; rooms A (7..16), B
    (19..30) and C (33..40) on rows 26-37, parted by solid tree lines two cells thick with one opening
    each, staggered (A-B on rows 28-29, B-C on rows 34-35) so the walk is a zigzag. B is the lord's garden
    with the koi pond (21..28, 30..32) under the timber bridge; A is pines and lanterns; C is maples.
    Paths are one cell of `k.paved`, not gravel.
  - *Ground and trees*: `sand-autotile` for all three courts; no `gravel-autotile` in Himeji. (The sand
    is Fukuoka's beach, from `generate_fukuoka_art.py`. If `check_distinct.py` counts that against
    Kansai, #275 recolours a court family of its own in `generate_kansai_art.py`.) Pines north of the
    avenue and in the border woods (pine and cedar); maples only in Koko-en.
  - *On arrival from Osaka* the canal becomes the moat beside the road and the white wall rises behind it;
    the bridge and gate are eight cells in, and the keep is not seen until the upper walk. *From Okayama*
    the Koko-en gate comes first, and the keep is overhead behind a wall with no way in until the far end.
- **Okayama (#276): a stroll.** The garden is the district; the keep is scenery, and the road ends.
  - *Fixed*: the avenue's cells at the seam; Momotaro, the Bizen-ware stall and two cranes stay in the
    room; Damian's post of 12 November stays in Korakuen beside the first crane (cells under "Posts").
  - *The river* (targets) is a bend of `pond-autotile`, solid: an east-west reach on rows 19-21 from the
    west edge to x=32 - the avenue's three road rows carried on as water - turning south as a reach on
    columns 29-32 to the bottom edge. It leaves by the city's own west and south edges only. The pond set
    has no inner-corner piece, so a heap of `okayama-bank-rock` covers the one inner corner, at the
    garden's north-east tip (28,22). It is not a `waterways` run.
  - *East bank* (targets): the avenue (34..43, 18..22; road from x=38, capped west) ends in the **plaza**
    (34..40, 14..23) on the outside of the bend, water ahead and to the south-west: Momotaro 2x3 at
    (35,16), the stall 3x3 at (37,14).
  - *North bank* (targets): west from the plaza along a small gravel **court** (22..33, 14..18) to the
    **keep** `okayama-keep` 8x7 at (14,12), its stone base on the bank (foot row 18) with no terrace in
    front and no wall across the room. The `Okayama Castle` visitor stands on the court beside it.
  - *The Tsukimi bridge* (`okayama-bridge`, 2x4 as drawn) at (22,19), beside the keep, is the only way
    into the garden, as it is in Okayama: plaza, court, keep, bridge, garden.
  - *Korakuen* (targets) is the inside of the bend (3..27, 22..37): open lawn to walk on, one cranked
    gravel path from the bridge's landing to the pond, the pond (6..13, 32..35), a mound (Yuishinzan, new
    art, about 5x4 at (4,25)), the cranes' feet on (14,27) and (16,28). From its north bank (row 22, x
    14..21) the keep is four cells north across the water, inside the look-up's fade (`lookUp.cells` 3,
    `fade` 3): the garden borrows the castle. #276 measures that in a browser at desktop and phone size.
  - *On arrival* the road runs through wood for a few cells and stops at a small plaza on the water: the
    statue, the stall, the river ahead, the keep low on the far side of the court, the lawn over the bend.
- **Osaka (#277): a browse.** `docs/workshop/219-city-redesign-plan-from-the-210-audit-ne.md`, "Stage E -
  Osaka", with its fixed cells, row bands for rows 0-22, interiors, labels and tests, and three amendments:
  1. **The avenue stays**: rows 24-28 from edge to edge (pavement, three road rows, pavement), open at
     x=0 and, once Nara is built, at x=49. Stage E's "the border closes the old avenue's ends" and "no
     road tile, traffic light" do not apply to it. The north-south main street (columns 23-26) does lose
     its asphalt, and meets the avenue at one crossing with the lights.
  2. **South of the canal**: row 23 is a one-row south quay of boardwalk. Stage E's south-bank row of
     fronts (rows 25-30) has no site. Shinsekai is rows 29-44 on `osaka-retro-paving-autotile`: the
     Shinsekai arch over the street south of the avenue, one row of fronts either side of the tower, the
     plaza on rows 38-43. #277's design picks which south-side sprites fit; the rest stay unplaced.
  3. **The canal** keeps rows 20-22 as water to both edges (`from 0` to `W-1`) and is `pond-autotile` on
     its edge cells, as the seam test asks.

  *On arrival* by train: out under the station's glass roof, the arch ahead down a street of fronts, the
  wheel to the north-east, then boardwalk, canal and bridge. *From Himeji*: the hedge opens onto the quay
  to the north and Shinsekai's fronts to the south, with Tsutenkaku ahead.
- **Along the seams.** *Osaka-Himeji*: the road and the water cross unchanged and everything else turns
  over within two columns - quay to rock rim, fronts to a white wall, paving to verge; the railway carries
  on west in the backdrop above Himeji, which has no track. *Himeji-Okayama*: only the road crosses, wood
  either side; west of it the road has ten cells left. *Osaka's east edge* is Nara's (#268): the avenue
  and the canal on their rows and nothing else.
- **Posts.** Every dated post keeps its room and its label. One changes cell:

  | Post | Today | After |
  |---|---|---|
  | Himeji: Damian 13 Nov (754), `Himeji Castle` | (12,8) | unchanged (fixed) |
  | Okayama: Damian 12 Nov (745), `Korakuen garden` | (27,31), beside the first crane (28,31) | **(13,27)**, beside the first crane (14,27): #276 re-runs `blog_to_npc.py --rehome Damian 2025-11-12 "Okayama · Korakuen garden"` and moves the pins in `test_blog_to_npc.py` and `kansai.test.js` |
  | Osaka: 568, 615 (Dylan) and 764 (Damian) at the wheel (39,19); 768 (Damian) at the arch (21,18); 769 (Bailey) at Tsutenkaku (26,43); 636 (Dylan) at the platform's vending machines (14,6) | | unchanged (Stage E's fixed cells) |
  | Osaka: 590 (Dylan) (17,35); 681 (Dylan) (30,17) | under a sakura; the crab house's door front | re-homed by #277 as Stage E says: `Osaka · the Dotonbori boat pier`, `Osaka · Dotonbori (area)` |

  A stand-in that #268 or #269 has moved out of Osaka by then is no longer Osaka's.
- **Build order and rooms.** One at a time, because map data is serial; each leaves the city walkable end
  to end and the checks green.
  1. **#275 Himeji** - room `Himeji` only. Okayama is still the old room beside it.
  2. **#276 Okayama**, after #275 is merged - room `Okayama` only.
  3. **#277 Osaka**, after both - room `Osaka` and its interiors (`LobbyOsaka1` kept, `LobbyOsaka2`,
     `LobbyOsaka3`, `HouseOsaka1`, `HouseOsaka2` pruned, the shop rooms Stage E adds; the doors of
     `OsakaStation`, `DonTakoteOsaka` and `DevhouseOsaka1F` keep their cells). **Not while #268 (Nara) is
     being built**: both rebuild `Osaka`. Whichever is second runs `generate_osaka.py` on the other's.

  Each ticket: its generator, `config.json` (`rooms.<Room>`, its `districts`), its `LANDMARKS` rows,
  `tiled/<Room>.tmj`, its tests in `kansai.test.js` (for Osaka, the files Stage E lists),
  `make_worldmap.py --pil`, `check_distinct.py`. Sizes and slots do not change, so `devhouse.world` and
  `cities.KansaiCity` should not: `sync_cities.py --check` says.
- **Later districts.** A castle added to the region later (Hikone, #269) says in its design how its
  ground, its approach and its water differ from Himeji's hairpin and Okayama's riverbank. The terrace
  above a full-width wall with one stair is not used again.
~~~

### Nothing else

No generator, config, map, test or other doc changes. `gamev2/CLAUDE.md`'s index is unchanged (no new file).

## Data and interfaces

None in this ticket. For the follow-ups the plan implies: no `kansai.py`, `cities` or world-file change; no
new `lookUp` entry (both keeps are in it; `osaka-tsutenkaku` is Stage E's); new `districts` bounds and
`LANDMARKS` offsets per room; one re-homed placement in Okayama and two in Osaka.

## Tests

Doc only. From `gamev2/`: `node tools/test_game.js` and `python3 tools/sync_cities.py --check` still pass
(both pass on this branch before the change). `git diff --stat origin/master` shows the doc and this design
only. No browser is needed.

## Risks and open questions

- **The look-up across Okayama's river** is reasoned from `lookUp` (3 cells full, 3 fading), not measured:
  there is no browser here. If it fails at phone size, #276 keeps the layout and gives up the borrowed
  view, or adds a walkable landing in the river; it does not put the terrace back.
- **Koko-en's partitions** are tree lines because the kit has no north-south wall piece. If they read as
  wood rather than rooms, #275 draws one.
- **Not all of Osaka's 34 sprites fit** once the avenue stays; that is accepted here rather than moving a
  seam.
- **Between #275 and #276** the new Himeji stands beside the old Okayama. Both work; the pair is only
  fully apart after #276.
- **#268 (Nara) is in design now** and will edit the same "Kansai" section. The plan is a separate section
  to keep the merge small; the one added sentence may conflict.
- **Owner's call, not blocking** (the ticket allows a stated move): Damian's 12 November cell moves to
  (13,27). The alternative keeps Korakuen where it is, and with it the composition #273 objects to.
