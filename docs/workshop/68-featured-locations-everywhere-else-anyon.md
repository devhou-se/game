# #68 Featured locations: the five small walkable places, one run at a time

## Context

Everything else on #68 has landed. What is left is the five places members wrote posts from that have no
map: **Nara, Himeji, Okayama, Lake Biwa, Karuizawa**. Their ten posts stand in as NPCs on Osaka's streets
and on station platforms.

The owner's standing decisions: small places you **walk** to, not train stops; each joins its nearest full
town on foot the way Tokyo's districts join (Nara, Himeji, Okayama, Lake Biwa around Osaka; Karuizawa out of
Tokyo); only real places; no ordinary sealed buildings (landmarks may be sealed); no rubbish bins.

The earlier design planned all five as six commits in one ticket. Implementation ran out twice (300 turns,
then 300 minutes), and the owner asked for the work to be **broken into smaller tasks first**. This revision
does that:

- **This ticket is the first stage only: the code the five places need before any of them is built.** No
  room, no art, no map data. A player sees one small change (Map labels on a narrow phone, under Approach).
- **Each place is a later ticket**, one place per run (#255, #256, #257), following the plan kept at the end
  of this file ("Plan for the later tickets").

Outcome of this ticket: the Map can carry fifteen places with every label shown, a small place's label
giving way to the towns', and a canal that carries on into a neighbouring district is one waterway for the
boats. Both are needed by the first place ticket.

The branch was 35 commits behind `master` (the Godot project has gone, `Assets/` is `art-source/`, the Map
has an overseas place); this revision merges `origin/master` (74d698b4) and every fact below was checked
against it. The design was then reviewed against a prototype (the Review at the end): the review took out
the labels that were left off the Map, which turned out not to be needed.

## Approach

**The split.** Map data is serial (`config.json` rooms and palette, `tiled/`, `devhouse.world`), so the
place tickets land one after another; this ticket is code only and can land at any time.

| Run | Ticket | What | Needs |
|---|---|---|---|
| 1 | **#68 (this)** | Map: a stuck label is laid out first; `minor` places, whose labels are laid out after the towns'. Boats: runs that abut are one run. | nothing |
| 2 | Kansai and Himeji | `KansaiCity` = Osaka + Himeji; Osaka and Fukuoka move in the world file; post 754 | run 1 |
| 3 | Karuizawa | fifth district of `TokyoCity` through Tokyo's west gate; three shops; posts 544, 572 | run 1 |
| 4-6 | Okayama, Nara, Lake Biwa (three runs) | one district each, in that order; posts 745, 764, 568/590/615/636/681 | run 2 |

Runs 2 and 3 do not depend on each other (checked: Karuizawa's world cell clears Osaka where it stands
today). The last ticket is three runs: its design does Okayama and opens Nara and Lake Biwa as their own
tickets.

**Map: every place keeps its label.** All five get a dot of their own (the alternative, no dots, would say
"Todaiji (in Osaka)" and "Shiraito Falls (in Tokyo)"). On `master`, fifteen labels fail the narrowest
portrait view: 270 of 272 layouts leave a label no room. That is the layout's one greedy order failing, not
the room: laid out again with the stuck label first (below), **all fifteen labels have a spot in every
view**. So no label is ever left out, and the Map needs two things:

- **A stuck label goes first.** `Places.layout` is greedy in one order (most hemmed-in dot first), and a
  new dot can leave another label no room: with Himeji alone, in the narrowest view, Fukuoka's label has no
  spot when you are in Tokyo and friends are in Fukuoka. So when a label is left with no spot, it is moved
  to the front of the order and the labels are laid out again; this repeats while a label is stuck, as often
  as there are dots at most, and stops at once when the stuck label is already first (no order can help it).
  The layout that left the fewest labels stuck is the one kept, so a map where no order fits is laid out
  exactly as today. It changes one thing on today's Map, for the better: in the narrowest portrait view
  with the player in Tokyo, a label stands on the flight's course today and half its dashes (6 of 12) are
  not drawn (8 of the test's 440 layouts); laid out again, every label keeps off the course and all the
  dashes are drawn (0 of 440).
- **A place can be `minor`.** `config.places.<key>.minor` marks a small place: its label is laid out after
  every other label, so the towns keep the spots beside their dots and the small places take what is left.
  It is laid out with the towns when the player is standing there or friends are there (that label is the
  one being looked for). `minor` never hides anything.

Measured with the change below and the five places stubbed in (their `geo` and labels under Data and
interfaces), for every "you are here" and "friends in" case of the label test:

- every subset of the five places (32 configs) in eight views (the test's four, 390x844 as the game really
  draws it, and three tall phones at the narrowest width): **no label without room, no label on the flight's
  course**, 6,304 layouts a view;
- the ten states the Map will pass through as the tickets land, in every portrait touch window from 280x480
  to 520x1200 CSS px, sampled every 4 by 8 px (1,094 distinct views, 2,166,120 layouts): the same, none;
- all 400 unit tests pass with the change applied.

What `minor` buys, with all five places (4,080 labels over the 272 cases; "far" is more than 40 px from the
dot's ring, so found by its leader line):

| View | Today's 11 places: far | 15, no `minor`: far / your own label far | 15, `minor`: far / your own label far |
|---|---|---|---|
| desktop 1280x960 | 0 of 1,320 | 14 / 0 | 13 / 0 |
| 390x844 phone | 13 of 1,320 | 1,098 / 24 | 856 / 5 |
| narrowest (320x780) | 331 of 1,320 | 1,618 / 66 | 1,654 / 62 |

It helps on the common phone and is a wash elsewhere (on desktop 534 labels have a short leader instead of
364, and 13 are far either way; on the narrowest view the two columns are within 2%). The table is also
the cost of five more dots round Osaka, whatever the layout: see Risks.

- **Nara's dot stands beside Osaka's.** With Nara at Todaiji's coordinates the dots are 9 to 13 px apart in
  the phone views, under the test's "towns stand clear" distance. The test's "may touch but never hide one
  another" exception, today the three Hokuriku towns, becomes a list of pairs that also names Nara/Osaka.

`/work/media/68-review-minor-labels-last-*.png` show the prototype with the five places stubbed in on a
320x780, a 360x840 and a 390x844 phone and on desktop (the two `68-map-minor-labels-*.png` pictures are
from the earlier revision, which left labels out).

**Boats: runs that abut are one run.** `AmbientBoats.declaredRuns` calls an end of a waterway "open" (the
boat sails in from off the map) only on the room's edge. Once Osaka is a district of a city, both ends of
its canal are inside the room, so boats would fade out mid-canal where the water visibly goes on. The place
tickets have Himeji and Nara declare the arm of water they carry on; here, `declaredRuns` joins runs that
meet end to end on the same axis and share enough water for a boat into one. No room has two such runs
today, so nothing changes.

Not in this ticket: any room, sprite, palette entry, `config.places` entry, world-file move or blog post.

## Changes

All paths under `gamev2/`. One commit, `gamev2: … (#68)`.

**`src/utils/Places.js`** (prototyped and measured; this is the whole change to `list` and `layout`):

```diff
@@ list()
                 overseas: !!p.overseas,
+                minor: !!p.minor,
@@ layout()
-        const order = dots.slice().sort((a, b) => crowd(a) - crowd(b) || (a.key < b.key ? -1 : 1));
-        const place = (shun) => {
+        const sorted = dots.slice().sort((a, b) => (!!a.minor - !!b.minor) || crowd(a) - crowd(b) || (a.key < b.key ? -1 : 1));
+        const once = (shun, order) => {
             const taken = [], out = {};
@@
             return out;
         };
+        // the order is a guess: a label left with no spot goes first and the rest are laid out again
+        // (as often as there are dots, at most); the layout that leaves the fewest without a spot is kept
+        const place = (shun) => {
+            const stuck = (out) => Object.values(out).filter(at => !at.fits).length;
+            let order = sorted, out = once(shun, order), best = out;
+            for (let n = 0; n < dots.length && stuck(best); n++) {
+                const d = order.find(o => !out[o.key].fits);
+                if (!d || d === order[0]) break;          // first already: no order gives it a spot
+                order = [d].concat(order.filter(o => o !== d));
+                out = once(shun, order);
+                if (stuck(out) < stuck(best)) best = out;
+            }
+            return best;
+        };
```

  The last two lines (`const out = place(…)`, `avoid.length && … ? place([]) : out`) and `uncovered()` are
  unchanged. A stuck label may go first more than once: forbidding that was tried and leaves a label no room
  (Okayama, Nara, Lake Biwa and Karuizawa together, narrowest view). The header comment's `places` example
  and `layout`'s doc comment say what `minor` means and that a stuck label is laid out first.

**`src/GameScene.js` `showMap()`**: one field on each dot, beside `r: Places.reach(isHere, isPresent) * k`:
`minor: p.minor && !isHere && !isPresent`. Nothing else: every label is still drawn, `this.mapDots` is as it
is, and the two lines `japan-map.test.js` pins (`const spots = Places.layout(…` / `Places.uncovered`) stay.

**`src/AmbientBoats.js`**:
- new `static joinRuns(runs, across)`: pure. `across` is the width of the narrowest hull
  (`Math.min(...Object.keys(AmbientBoats.HULLS).map(h => AmbientBoats.size(h).across))`, the default). Two
  runs join when they have the same `axis`, one's `to` equals the other's `from`, and the bands they share
  (`max(band0)` to `min(band1)`) are at least `across` wide. The joined run keeps the first's `from` and
  `open[0]`, the second's `to` and `open[1]`, the shared band, and both `under` lists. Repeats until nothing
  joins (three in a row become one). Runs that do not join come back unchanged and in their order; a joined
  run stands where its first part stood.
  The band is not compared for equality on purpose: each district measures its band on its own first cell
  (`stackBand` on the first cell no bridge covers), which for Himeji is where the arm leaves the moat's
  ring, so two arms of one canal can differ by a few pixels of bank.
- `declaredRuns`: build each run as today but without `fit` / `clearWater`, then
  `return AmbientBoats.joinRuns(raw).map(r => this.fit(this.clearWater(r))).filter(Boolean)`. All the
  deciding is in `joinRuns`: `declaredRuns` needs the scene's textures and has no unit test.
- the header comment's `waterways` paragraph says so.

**`tools/tests/japan-map.test.js`**, the label test (`labels never cover each other…`):
- a helper `small(keys)`: `realConfig()` plus, for each key, a stub room `{ name }` and a place
  `{ geo, label, minor: true }` from the table under Data and interfaces. The configs loop becomes
  `realConfig()`, `before()` and the **nine states the tickets pass through**: Himeji; then Okayama, Nara and
  Lake Biwa added in that order (four); each of those with Karuizawa (four more); Karuizawa alone.
  `small(['Himeji'])` is the case the retry is for (without it: no room for Fukuoka's label at Tokyo with
  friends in Fukuoka, narrowest view).
- dots carry `minor: p.minor && p.key !== here && !present.includes(p.key)`, as the scene's do.
- **the views the game really draws.** The row `['portrait phone 390x844', 612, true, 1.3, 2.5]` is not what
  a 390x844 phone gets: the game grows its text 1.57 there (read from the running game), and no row covers a
  tall phone, which gets the narrowest width with less growth. Keep the four rows (they are the extremes)
  and add rows worked out from window sizes with the game's own functions:

  ```js
  // the view a portrait touch window gets: canvas width in view, text growth, the picture's scale
  const viewOf = (name, winW, winH) => {
      const l = game('Viewport').layout(winW, winH, true), U = game('UIScale');
      const W = 1280 - l.crop.left - l.crop.right, down = 1 / l.scale;
      const k = Math.round(100 * Math.min(U.MAX_TEXT_GROWTH, down > 1.02 ? Math.min(U.MAX_ZOOM, down) : 1)) / 100;
      return [name, W, W < 1280, k, fit(W, 960, meta.width, meta.height, W < 1280, MAX)];
  };
  ```

  for 320x780, 360x840, 360x800, 390x844 and 412x915, and assert what they come to, so the helper cannot
  drift from the game: `[560, 1.6, 2]`, `[560, 1.56, 2]`, `[597, 1.6, 2.5]`, `[612, 1.57, 2.5]`,
  `[579, 1.41, 2.5]` (each read from the running game at that size: `scene.uiScale.textSize('100px')` and
  the spacing of the dots). A new row that fails any rule of the test is a finding, not a row to drop.
- every label `fits` in every config and view (no allowance anywhere), and for `realConfig()` no label
  touches the flight's course in any view: the `if (!cropped || W > game('Viewport.MIN_VISIBLE'))` in front
  of that assertion stays only for the other configs, and the comment above it says why it is no longer
  needed for today's Map.
- the dot rule's exception becomes a list of pairs, `MAY_TOUCH`: the three Hokuriku pairs and
  `['Nara', 'Osaka']`.
- unit cases beside the existing "a label with nowhere to go says so":
  - that case still comes back `fits: false` with the same spot as before (nothing can help it, the loop
    stops, the first layout is kept);
  - two dots that want the same spot: the one that is not `minor` gets it, whichever key sorts first, and
    the `minor` one still gets a spot and `fits`;
  - a small made-up layout where the first order leaves a label stuck and the second does not (three dots
    in a narrow `bounds` is enough; take one from the Himeji case if it is easier), asserting every label
    `fits`;
  - `P.list(realConfig())` has `minor: false` on every place and `P.list(small(…))` `true` on the stubs.

**`tools/tests/roads-waterways.test.js`**: a `joinRuns` test: two abutting runs become one (`from`, `to`,
`open`, `under` as above); three in a row become one; bands that differ by a few pixels join and the joined
band is the part they share; bands that share less than `across` do not join; different axes or a gap do
not; a list where nothing joins is returned deep-equal. And from `realConfig()` alone: no room or city has
two declared `waterways` on the same axis that meet end to end with rows (columns) in common, each
district's cells moved by its offset: that is what "nothing changes today" rests on.

**`tools/browser/regress.js`**: no change. `menu-map` still wants a label for every dot and every dot to
fit.

**Docs**: `docs/hud-input-touch.md` (the Labels bullet: `minor`, the stuck label going first),
`docs/ambient-traffic.md` (declared runs that abut are one run; an end is open only on the room's edge).

## Data and interfaces

- `config.places.<key>.minor` (boolean, optional, default false): a small place; its label is laid out
  after the others'. **No place sets it in this ticket.**
- `Places.list()` entries gain `minor`. `Places.layout` dots may carry `minor` (laid out after the others).
  The result is as today: nothing new on a spot, nothing new on `scene.mapDots`.
- `AmbientBoats.joinRuns(runs, across)`: static, pure.
- The stub places the test uses, which are the coordinates the place tickets will put in `config.places`
  (all on Honshu in `assets/map/japan.json`, checked):

  | Key | `geo` | Label |
  |---|---|---|
  | `Himeji` | [134.69, 34.82] | Himeji |
  | `Okayama` | [133.92, 34.66] | Okayama |
  | `Nara` | [135.84, 34.69] (Todaiji) | Nara |
  | `LakeBiwa` | [136.10, 35.30] | Lake Biwa |
  | `Karuizawa` | [138.63, 36.35] | Karuizawa |

- No save, room, palette, station, trip or shop change.

## Tests

From `gamev2/` (times measured in a Workshop container on `master`):

- `node tools/test_game.js` (400 tests, about 1 min 45 s; the new cases add a few seconds: the prototype
  laid out 44,000 label cases in under 5 s),
- `node tools/play.js check` (4 s), `python3 tools/sync_cities.py --check`,
  `python3 tools/test_blog_to_npc.py` (40 s), `python3 tools/rehearse_blog.py` (40 s),
  `python3 tools/check_distinct.py`,
- `python3 tools/check_generators.py` (17 s; needs Pillow: `python3 -m venv /work/venv &&
  /work/venv/bin/pip install -r tools/requirements-art.txt`, then run it with that Python; two art tools are
  skipped for want of a Japanese font, as on `master`),
- with `python3 -m http.server 8000` running: `REGRESS_TIME_SCALE=2 PORT=8000 node tools/browser/regress.js`
  (`tools/browser/README.md`; 90 to 130 s here).

In a browser, desktop 1280x960 and a phone size with touch: open the Map (eleven dots, eleven labels, as
on `master`; on a narrow portrait phone, 320x780 say, standing in Tokyo, the labels have moved off the
flight's course: look at that one before and after) and watch a boat sail the length of Osaka's canal and
out at the edge.
To see fifteen labels, add the five stub places (with `minor: true`) to `scene.config.places` and
`scene.config.rooms` from the console before `scene.showMap()`, as the pictures in `/work/media/` were made
(`window.game.scene.keys.GameScene` is the scene; set `gamev2_creator_seen` and `gamev2_intro_seen` in
localStorage first or the character creator is in the way); screenshots there at 320x780 and 390x844.

## Risks and open questions

- **Nothing uses `minor` or a joined run until the first place lands.** Both are covered by tests against
  the coordinates and the cases the places will bring, so a place ticket that finds them wrong will find it
  in a failing test, not on a phone.
- **Five more dots round Osaka crowd a phone's Map, and no test measures that.** Every label has a spot,
  but on a phone one label in five (390x844) to two in five (320x780) then stands more than 40 px from its
  dot on a thin leader line, and leaders cross other labels (the 320x780 picture: Lake Biwa's label is out
  in the Sea of Japan). The label test checks that labels fit, not how far they went. Nothing shows it until
  the places exist, so it is for the place tickets to look at, on a phone, as each dot arrives. Remedies,
  cheapest first: the label "Biwako"; a leader line that shows better on the sea; leaving a `minor` label
  out where it would stand far off, unless the player or friends are there (the earlier revision of this
  file, 2185151b, has the code for leaving labels out; it left Lake Biwa unnamed in three cases out of four
  on the narrowest phones, which is why it is not the default). That last one is the owner's call when there is a picture to judge.
- **The retry moves labels** only in layouts where the first order left a label no room: today that is the
  narrowest portrait in Tokyo (above), where the result is better and still passes every rule of the label
  test. The pass without `avoid` remains for a map where no order fits.
- **`joinRuns` loosens the cover rule.** `clearWater` drops a lane that scenery covers for more than a
  quarter of a run; over a joined run that quarter is of the whole canal, so a wall along a short arm's near
  bank can pass where it would not on the arm alone. Clearing each arm before joining was considered and
  fails the other way (a bridge on a short arm covers more than a quarter of it and the canal stays in
  pieces). The Himeji and Nara tickets check it by watching a boat through their arm.
- No question needs the owner. The split itself is what the owner asked for.

## Plan for the later tickets

Kept from the reviewed design (the review's twenty findings are folded in), corrected for `master`. It is
the brief for the tickets in the table under Approach; each gets its own design, which may change details
but should keep the cells, the seams and the rules, since the districts must meet. Test line numbers are
left out on purpose: find each by what it says.

**Pattern.** Hokuriku's, exactly (`tools/hokuriku.py`, `generate_shirakawago.py`,
`tools/tests/kanazawa.test.js`): a layout module that owns where districts meet, one generator per
district, hidden seam transporters for `?stitch=0`, `CityStitcher` unchanged.

**Kansai: a third stitched city, `KansaiCity`** (name `Kansai`; never shown to players): Osaka as it is plus
four districts. Osaka's Canal-side Avenue (rows 24-28) is open at both edges and becomes the road through
all of them: west to Himeji and on to Okayama, east to Nara. Osaka's canal (rows 20-22) runs on west as
Himeji Castle's moat and east as a river that bends north through Nara to Lake Biwa, with a towpath beside
it (post 568 is Dylan riding "along the Yodogawa river toward Otsu"). From the Himeji ticket on, the
runtime room is `KansaiCity`, as `HokurikuCity` is for Kanazawa; tests that use `Osaka` as a room of the
stitched world (`occlusion-camera.test.js` does) switch to Sendai.

**Karuizawa: a fifth district of `TokyoCity`**, west of the `Tokyo` room through the west gate `e3cb4d0d`
fenced (Tokyo `(0,41)`, `(0,42)`: today `flat-grey-brick-autotile_edge-w` + `fence-barriers_0_2` + a
collider), in the slot Machi had. The Nakasendo, the old road out of Edo, is the story of the walk.

Layout, in cells (sketch: `/work/media/68-district-layout.png`):

| Room key | Size | In the city's cells (`AT`) | `devhouse.world` cell | Ticket |
|---|---|---|---|---|
| `Okayama` | 44x40 | (0, 36) | (-258, 67) | Okayama |
| `Himeji` | 44x40 | (44, 36) | (-214, 67) | Kansai and Himeji |
| `Osaka` | 50x46 | (88, 30) | (-170, 61), was (-102, 61) | Kansai and Himeji |
| `Nara` | 52x40 | (138, 36) | (-120, 67) | Nara |
| `LakeBiwa` | 46x36 | (152, 0) | (-106, 31) | Lake Biwa |
| `Karuizawa` | 48x40 | TokyoCity | (-48, 8) | Karuizawa |
| `Fukuoka` | 62x62 | detached, moves only | (-330, 90), was (-175, 85) | Kansai and Himeji |

KansaiCity is 198x76 (depth scale stays 1: at most 83 rows). TokyoCity becomes 165x109 (height, and so its
scale, unchanged). The Osaka and Fukuoka moves were made on a copy of `master` (world file,
`make_worldmap.py`): all 400 unit tests, `check_generators`, `sync_cities --check` and `play.js check`
pass. They do not change the in-game Map (drawn from `places.geo`); they change `assets/map/world-map.*`
and, through `TrainTravel.dirTo`, which way the Kanazawa-Osaka train leaves (west out of Kanazawa, east out
of Osaka: the right way round; ride it once and look).

Seams (district-local cells; every seam cell is a hidden transporter landing `IN = 3` cells inside the
neighbour, with one back; the same Floor tile name on both sides):

| Seam | One side | Other side |
|---|---|---|
| avenue | Osaka x=0, rows 24-28 | Himeji x=43, rows 18-22 |
| avenue | Himeji x=0, rows 18-22 | Okayama x=43, rows 18-22 |
| avenue | Osaka x=49, rows 24-28 | Nara x=0, rows 18-22 |
| towpath | Nara y=0, cols 23-24 | LakeBiwa y=35, cols 9-10 |
| gate | Tokyo x=0, rows 41-42 | Karuizawa x=47, rows 34-35 |

Water carried across an edge in the same city cells (Water layer, solid): Osaka rows 20-22 = Himeji rows
14-16 at x=43 = Nara rows 14-16 at x=0; Nara cols 20-22 at y=0 = LakeBiwa cols 6-8 at y=35. Himeji declares
`waterways` `{axis:'h', row:14, rows:3, from:<first cell east of the moat's ring>, to:43}` and Nara
`{axis:'h', row:14, rows:3, from:0, to:<last cell before the bend>}` (`under` for any bridge), so
`joinRuns` makes the canal one run and boats leave Osaka along the moat and the river. The arms join only
if they share a boat's width of water with Osaka's canal: draw them with the canal's own tiles on the same
rows, start `from` clear of any corner tile, and let nothing but a declared `under` bridge stand over the
water; `kansai.test.js`'s "one canal run" and a boat watched through the arm are the checks. No `waterways`
north of Nara's bend or on the lake.

Rules every place ticket keeps:

- **An edge is open only when its neighbour is built.** `kansai.BUILT` (a tuple each ticket extends) drives
  both sides: until the neighbour is in it, that edge is drawn closed like every non-seam edge (hedge and
  wood across the road, water ending in a rounded bank inside the edge) and Osaka's edge cells on that side
  stay as they are today. Osaka's west end opens with Himeji, its east end with Nara; Himeji's west end with
  Okayama; Nara's river and towpath reach its top edge only with Lake Biwa. Every ticket leaves a
  finished-looking world.
- **A fingerpost inside every seam**, with a bump line through `Interactions` naming what lies each way.
  Each city draws its own (`kansai-fingerpost`, `karuizawa-fingerpost`, 1x2), so the Kansai and Karuizawa
  tickets do not wait on each other.
- **No `train-track*` tile in a new district.** `AmbientTrains.track()` runs the train on the topmost track
  row of the whole city room. The station of post 636 is a sign with a bump line. No district covers
  Osaka's rail rows 3-5 beside Osaka, so `backdrop.extend` carries the track west to the city's edge; east
  it stops `extendStop` short of Lake Biwa (why the lake stands 14 columns east of Osaka). Karuizawa ends
  at world row 47, north of the Palace railway (world row 50).
- Nara's pocket north-west of the river (cols 0-19, rows 0-13) stays unreachable wood: it hides the dead end
  of Osaka's track. If a screenshot shows the end, set `extendStop: 0` and stand a tunnel mouth on the
  lake's west edge.
- No `road-plain`, `road-div-vertical` or `road-edge-bottom` tile on an edge cell beside void
  (`backdrop.edges` would grow a road out of it); `Kit.dress` on every non-seam edge cell.
- **Distinctness** (`check_distinct.py`; districts count under their city: the Kansai four with Osaka,
  Karuizawa with Tokyo). Never borrow a sprite only one town uses (`shirakawa-paddy` is Hokuriku's: the
  lake draws `biwa-paddy`). Add `himeji-|okayama-|nara-|biwa-|karuizawa-|kansai-` to `LANDMARK_ART`.
  `--update` runs once, in the Himeji ticket, only to rename the `Osaka` key to `Kansai`, after comparing
  Kansai's numbers with Osaka's baseline (buildings 0.2, own 0.107, sprites 0.451) by hand; after that a
  city that gets worse is fixed in the art or the map.
- **Posts** move only with `python3 tools/blog_to_npc.py --rehome <NPC> <date> "<Room> · <label>"`
  (`--dry-run` first), to a `LANDMARKS` row scoped to the room with an anchor sprite and a free, reachable,
  outdoor cell beside it that is not a seam cell; labels at most 20 characters. `tools/districts.py` and
  the `LANDMARKS` rows land in the same commit as the room (`test_spots` and `test_districts` fail a room
  without them).
- **`config.places.<key>`** with `minor: true` and the `geo` in the table under Data and interfaces, in the
  same commit as the room; update `japan-map.test.js` (the label list, the places with no station, and for
  Lake Biwa `on('2025-11-06')`), which then drops that key from its stubs. Then look at
  the Map with the new dot on a 320x780 and a 390x844 phone, standing in a few towns: labels far from their dots are the known cost of these dots
  (Risks, above, with the remedies).
- Each generator goes in `check_generators.py`; `node tools/play.js lint <Room>` and `render`; tall sprites
  against `docs/occlusion.md`; lit props get `Glows` rows; docs in the same commit.

**Kansai and Himeji.** `tools/kansai.py` (`CITY`, `AT`, `SIZE`, the seams as named constants, `IN`,
`BUILT`, `seams(district)`, `open(district, side)`, `Kit` from `hokuriku`). `generate_osaka.py`, west end
only: Floor `(0,24)` becomes `flat-grey-brick-autotile_edge-n` and `(0,28)` `_edge-s` (corner tiles today),
the fingerpost, transporters through `rg.kept_order(prev, kansai.seams('Osaka'))`. `generate_himeji.py`:
the avenue on rows 18-22; the moat from the east edge closing in a ring round the castle hill north of the
avenue; a flat bridge and a walk-through gate; the white keep on `castle-wall-*` terraces with
`castle-stairs`; Koko-en south of the avenue. `generate_kansai_art.py` (palette append only): `himeji-keep`,
`himeji-turret`, `himeji-gate`, `himeji-bridge`, `kansai-fingerpost`. `config.json`: `cities.KansaiCity`
(`backdrop` copied from `HokurikuCity`), `places.Himeji`, `game.lookUp.sprites`; the world-file moves;
`sync_cities.py`, `config_to_tiled.py Osaka Himeji`, `make_worldmap.py`. New `tools/tests/kansai.test.js`
mirroring `kanazawa.test.js` (offsets and sizes equal `kansai.py`; every seam cell a hidden non-solid
transporter with one back; same Floor name across; the only reachable edge cells are seam cells and a step
out of any other does not move the player; water continuous; one canal run; no track tile and the train on
Osaka's row from the city's west edge; walks stitched and `--stitch=0`; depth scale 1; each re-homed post
in its room on a reachable outdoor cell; a fingerpost inside every seam). `kanazawa.test.js`: two stitched
cities become three. Re-home Damian 2025-11-13 (754) to `Himeji · Himeji Castle` (anchor `himeji-keep_`).

**Okayama.** `generate_okayama.py`: the avenue from the east edge ending in the town; the black "crow"
keep north of it; south of it the river as a closed ring round Korakuen's island (lawn, pond, cranes) with
the Tsukimi bridge; a Momotaro statue and a Bizen-ware stall as props with bump lines. Art: `okayama-keep`,
`okayama-bridge`, `okayama-crane`, `okayama-momotaro`, `okayama-bizen-stall`. Open Himeji's west seam.
Re-home Damian 2025-11-12 (745, on Hakata's platform today) to `Korakuen garden` (anchor `okayama-crane_`).

**Nara.** `generate_nara.py`: the avenue from the west edge; the river in at rows 14-16, north up cols
20-22, the towpath on cols 23-24, both closed short of the top edge until the lake exists. East of the
river Nara Park: the Great Buddha Hall (sealed landmark) behind the Nandaimon gate you walk through; deer
(solid, bump lines; a cracker stall); Kasuga Taisha as the `shrine-red` prefab among stone lanterns
(`generate_shrines.py` `NAMES` row `('Nara', 'shrine-building_0_0'): 'Kasuga Taisha'`, room `ShrineNara1`).
The two resting deer come from the UrbanAccessoriesv2 sheet `tools/extract_street.py` already reads
(`SHEETS['urban']`), the art the ticket names; draw only the bowing pose to match. Art: `nara-daibutsuden`,
`nara-nandaimon`, `nara-deer-bow`, `nara-senbei-stall`, `nara-stone-lantern`. Open Osaka's east end. Re-home
Damian 2025-11-14 (764) to `the Great Buddha Hall`. On the Map Nara's dot is 9 to 13 px from Osaka's on a
phone and Osaka's ring reaches about 25 px when the player or friends are there: look at it standing in
Osaka and in Nara, and if Nara's dot is lost in the ring, move Nara's `geo` east until it stands clear
(and take the pair out of `MAY_TOUCH` if it then passes the dot rule).

**Lake Biwa.** `generate_lakebiwa.py`: the river in at the south edge widening into the lake
(`pond-autotile`, so fishing works); the towpath reaching the Otsu lakefront and going on as the Biwaichi
cycle path up the east shore; Hikone Castle (sealed landmark) on a rise; a hill viewpoint over paddies; at
the north end the tunnel mouth, monkeys and the Takashima station sign; the Shirahige torii in the water.
Room `sentenceName: "Shiga, by Lake Biwa"` ("in Lake Biwa" is wrong; `dates-trips.test.js` lists the rooms
that have one). Art: `biwa-hikone-keep`, `biwa-torii`, `biwa-tunnel`, `biwa-monkey`, `biwa-cycle-sign`,
`biwa-paddy`, `biwa-station-sign`. Open Nara's top edge. Re-home Dylan: 2025-11-02 (568) and 11-07 (681)
to `the Otsu lakefront` (anchor `biwa-cycle-sign_`), 11-03 (590) to `the hill viewpoint` (a district),
11-04 (615) to `Hikone Castle`, 11-05 (636) to `the lakeside tunnel`.

**Karuizawa.** `generate_karuizawa.py` builds the room and owns the edit to the ported Tokyo map,
idempotent, as `generate_izakaya.py` and `generate_palace.py` edit theirs: Tokyo `(0,41)`, `(0,42)` Floor
back to `flat-grey-brick-autotile_center`, the fence and its collider removed, hidden transporters to
Karuizawa `(44,34)`, `(44,35)` (the reverse of `e3cb4d0d`), the fingerpost inside the gate. Karuizawa
`(47,34..35)` is the same brick, turning to a packed-dirt road; it runs west then north as Kyu-Karuizawa
Ginza with three shopfronts (3x4, door at `(1,3)` like Tanukikoji's; `roomgen.SHOP_DOORS`,
`generate_houses.py` `SHOP_TYPES`, `--shops Karuizawa`) selling `bakery`, `souvenirs` and a new
`Shop.VENUES` row `lounge: { title: 'LOUNGE', sells: … }` of drinks already in the catalogue (a room
`shopTitle` does not work: `Shop.titleFor` honours it only for `counter`); on through larch woods to
Shiraito Falls (a landmark sprite over a `pond-autotile` pool) with the bus stop and the corn stall. Art
(`generate_karuizawa_art.py`): `karuizawa-falls`, `karuizawa-larch`, `karuizawa-corn-stall`,
`karuizawa-shop-bakery/jam/lounge`, `karuizawa-fingerpost`. `cities.TokyoCity.rooms` gains
`{ room: 'Karuizawa', x: -48, y: 8 }`. New `tools/tests/karuizawa.test.js` (the gate both ways, the walk to
the falls stitched and unstitched, the three shops and the LOUNGE title, no track tile and the train still
on the Palace's row, TokyoCity's height unchanged). `madeup-towns.test.js` (four districts become five,
the fenced-gate test becomes "the gate leads to Karuizawa", Tokyo is no longer the city's west edge),
`palace.test.js` (its two tests that count what the generator touches in the Tokyo map must allow the
gate's transporters) and `test_blog_to_npc.py` `test_city_reach` change on purpose. Re-home Damian
2025-11-01 (544) to `Shiraito Falls`, Julia 2025-11-02 (572, on Tokyo Station's platform today) to
`the corn stall`.

**Start rooms will change on six day-and-character pairs** (`Trips.startFor`, rule unchanged: Dylan was
Osaka's only occupant on his lake days, and Karuizawa is one room from home). Measured on a stubbed copy
before `master` moved; re-measure with the real maps, pin each in the ticket that causes it, and say so in
`trips-and-dates.md`:

| Day | Playing as | Today | After | Caused by |
|---|---|---|---|---|
| 2025-11-02 | Bailey | Osaka | Karuizawa, beside Julia (LakeBiwa if the lake lands first) | Lake Biwa, Karuizawa |
| 2025-11-03, 11-04 | Bailey | Osaka | Shirakawago | Lake Biwa |
| 2025-11-05 | Damian | Osaka | Shirakawago | Lake Biwa |
| 2025-11-12 | Bailey, Julia | FukuokaStation | Fukuoka | Okayama |

Tests pinned to today's stand-ins change with them: `madeup-towns.test.js` (the `moved` table, the
2025-11-12 start), `dates-trips.test.js` (754 and 764 leave Osaka), `test_blog_to_npc.py` (`REPLACED_219`
pins Damian 2025-11-12 to FukuokaStation; the shipped-history pins).

**Risks carried by the place tickets.** Osaka's #219 rebuild must keep the avenue rows 24-28 and the canal
rows 20-22 at both edges, or move the seam constants with it. Measure frame rate and first-entry time and
memory for `KansaiCity` (198x76, about 5,500 cells of void filled with woods) and the larger `TokyoCity` on
a phone size, as `stitched-city.md` describes; if it drops, narrow the districts (seam rows stay). The walk
is long (Okayama's garden and the lake's far shore are each about 100 cells from the middle of Osaka): the
owner's choice, so keep something to look at along the avenue. Art is the bulk of each ticket (five to
seven sprites); every landmark must read at a glance on a phone. Himeji can be dropped on its own (Okayama
then takes Osaka's west seam); Nara cannot, since the lake is reached through it.

## Review

An adversarial pass over revision 2185151b, against a prototype of `Places.layout` run outside the repo over
the label test's cases, and the game in a browser at 320x780, 360x840, 360x800, 390x844, 412x915 and
1280x960. The body above is already revised; this is what was wrong and what was done.

| # | Criticism | Fix | Adopted |
|---|---|---|---|
| 1 | **"Fifteen labels do not fit the narrowest portrait view" was false.** The 270 of 272 failures are `master`'s single greedy order. With the design's own retry and every label required, all 32 subsets of the five places fit in every view measured, with nothing on the flight's course. Leaving labels out was built on that premise: `optional` dots, `hidden` spots, the `uncovered` change, `setVisible` in `showMap`, two new `mapDots` fields and a looser `menu-map` assertion in `regress.js`. | Take all of it out. Every label is always drawn; `regress.js` does not change. | Yes |
| 2 | **The labels left out were the ones that mattered.** Lake Biwa, the place with five of the ten posts, was unnamed in 207 of 272 cases on the narrowest view; a dot with friends alone in it was unnamed in 25; the player's own place in 15. "Laying the player's place out as required was measured earlier and is worse" did not reproduce with the retry in place: no label without room in any subset, and fewer left out. | Moot once nothing is left out (1). What survives: a `minor` place is laid out with the towns when the player or friends are there. | Yes |
| 3 | **"Only on the narrowest portrait" was wrong, and the test allowed it wrongly.** Labels were left out wherever the picture is drawn at scale 2 with large text: windows up to about 316 wide (560 to 566 in view), and tall phones such as 358x840, 370x876 and 382x888. The test allowed it at `W === Viewport.MIN_VISIBLE` and tested no other width under 612, so a window with 566 in view would have left labels out untested. | Moot (1); the test gains the views real phones get (5). | Yes |
| 4 | **The retry loop was not what the text said.** "At most once per dot" is not what it did (a dot may go first again, and must: forbidding it leaves a label no room in one subset); when the stuck label was already first it laid out the same order again up to `dots.length` times (the existing "nowhere to go" unit case did); and it returned the last layout tried, not the best. | Stop when the stuck label is already first; keep the layout with the fewest stuck labels, the first one on a tie, so a map no order fits is laid out as today. The text now says what the loop does. Measured: same results as the design's loop wherever that fitted, 400 unit tests pass. | Yes |
| 5 | **The label test's phone row is not what a phone gets.** `['portrait phone 390x844', 612, true, 1.3, 2.5]`: the game grows text 1.57 there, not 1.3 (read from the running game). And no row covers a tall phone (narrowest width, growth from about 1.4), which is where the design's left-out labels turned up unnoticed. | Rows worked out from window sizes with `Viewport.layout` and `UIScale`, their values asserted; five sizes checked against the running game. The four old rows stay as extremes. | Yes |
| 6 | **Too few configs in the test.** All five and Himeji alone; the Map passes through nine states as the tickets land, and it was one place alone that broke a label. | The nine states (the Kansai places in their order, with and without Karuizawa). All 32 subsets were measured; nine keeps the test quick. | Yes |
| 7 | **Sorting `minor` labels last is not free.** With all five on desktop, 534 labels get a short leader line instead of 364. | Kept: the far labels are the same (13 against 14), and on a 390x844 phone `minor` cuts far labels from 1,098 to 856 and keeps the player's own label by its ring (far in 5 cases, not 24). Without that gain `minor` would have gone with the rest of (1). | No change needed |
| 8 | **Nothing measures how far labels go.** Five more dots round Osaka put one label in five more than 40 px from its dot on a 390x844 phone (1 in 100 today), two in five on the narrowest, with leaders crossing other labels. The design called the layout good because every label "fits". | Not fixed in code: no place exists to look at, and the remedies (a shorter name, a clearer leader, leaving labels out after all) are a matter of looking. Written into Risks and into the plan for the place tickets, with the numbers. | Recorded, not fixed: needs the real places and the owner's eye |
| 9 | **`joinRuns` compared bands for equality.** Each district measures its band on its own first cell; Himeji's is where the arm leaves the moat's ring, so a few pixels of bank would leave the canal in two runs and boats fading at the seam, with no error anywhere. | Join when the shared band is at least the narrowest hull wide; the joined band is the shared part. | Yes |
| 10 | **Joining before `clearWater` weakens the cover rule** (a quarter of the run becomes a quarter of the whole canal). | Clearing each arm first was worked through and rejected: a bridge on a short arm covers more than a quarter of it and the canal would never join. Left as designed, written into Risks, checked in the Himeji and Nara tickets by watching a boat. | No: the alternative fails worse |
| 11 | **`declaredRuns` cannot be unit-tested** (it reads textures; no test calls it today), and the design's test rebuilt its arithmetic from config to prove "nothing joins today". | All the deciding stays in pure `joinRuns`; the real-config check is a plain one on `waterways` cells (no two declared runs meet end to end today). | Yes |
| 12 | **`MAY_TOUCH` for Nara and Osaka only stops the test failing.** With the player or friends in Osaka its ring reaches about 25 px at the largest text, and Nara's dot is 9 to 13 px away. | Carried to the Nara ticket as a thing to look at, with what to do if it reads badly (plan, below). | Yes, as a note |
| 13 | **The retry's one visible gain was not pinned.** The design said labels leave the flight's course on today's Map in the narrowest view, but the test still excused that view. | For `realConfig()` the excuse goes: no label touches the course in any view. | Yes |

Considered and not raised: the split itself (what the owner asked for, and the tickets exist); `joinRuns` in
this ticket rather than Himeji's (small, pure, and Himeji's is the largest ticket); Osaka declaring its
waterway past its own edges instead of joining (breaks `?stitch=0`).

Checked, not assumed: the prototype's layout matches `Places.layout` on `master` on all 528 cases; its view
sizes match the running game at five window sizes; `node tools/test_game.js` passes (400) with the
`Places.js` and `GameScene.js` change of this design applied. The other suites and the browser regression
were not run for this review (no code is committed by it).
