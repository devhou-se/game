# #94 Shinjuku: a street of high-rises west of Marunouchi

## Context

#18 asked for high-rises along the Market and Palace roads. Those two districts are ported maps with no
free street frontage, so only three towers went into infill pockets. Workshop's call on this ticket: leave
Market and Palace as they are (nothing removed, no NPC or landmark moved) and add **one new generated
outdoor district of high-rises, reached from Palace, built from the existing `highrise-*` and
`midrise-apartment` prefabs**.

Outcome: from Marunouchi (room `Palace`) you walk west over the west road into **Shinjuku**, an avenue with
nine towers, each of which opens into a lobby. Standing owner rules apply: only real places, no sealed
buildings, no rubbish bins, a road that leaves a junction leads somewhere.

Everything below was built in a scratch copy of the game and checked there (numbers under Tests);
captures of it are attached to the ticket.

## Approach

**A fifth stitched district of `TokyoCity`, not a room behind a door.** Room key and display name
`Shinjuku`, 34x36 cells, at world cell (24, 51): the woods west of the Palace/Park west road. You walk
in, as between the other districts; `?stitch=0` uses hidden seam transporters.

**The way in is the road that is already there.** The road between Palace and Park (world rows 65-67 =
Palace rows 18-20 = Park rows 0-2) ends at the west road in a junction box that is open on every side
(`square_junctions.JUNCTIONS['Palace']`). Shinjuku's east column (local x 33 = world x 57) is the west
road's west kerb, which the stitched backdrop draws today (`road-edge-left`); the district draws the same
kerb itself, with `road-plain` on rows 14-16, so that road carries on west as Shinjuku's avenue and the
junction becomes a crossroads. **No Floor tile of Tokyo, Market, Palace or Park changes.** The only edit to
a ported map is three hidden transporters on Palace for `?stitch=0`.

**Why this slot.** World x 24..57, y 51..86 is void (woods) today and lies inside the city's bounding box,
so the city stays 117x109 and its depth scale does not change. It is south of the railway cutting the
backdrop carries west from Palace (world rows 47-50; the district has no `train-track` tile), south of
Tokyo (rows 1..46), north of the kerb cells `roads-waterways.test.js` pins at Park's south-west bend
(world rows 105-106), and clear of the slot #68 plans for Karuizawa (world x -48..-1).

**Layout** (district cells; a tower "stands on" the row of its door):

| Rows | What |
|---|---|
| 0-11 | Five towers standing on row 11, one of each prefab, woods (solid) behind and between. Vending machines at (9,10) white and (14,10) red, a utility pole at (20,9) |
| 12-13 | North pavement, x 2..32 (`flat-grey-brick-autotile`) |
| 14-16 | The avenue: `Kit.road_h(4, 32, 14, cap_w=True)`, joined to the west road at x 33. Zebra crossing (two `crossing-h`) at x 22, 23 with `traffic-light` at (21,11) and (24,15). The west end is a turning box: `road-plain` at (5,15), (6,15), so the centre line does not run into the kerb (the junction tests refuse that) |
| 17-18 | South pavement, x 2..32; `bus-stop` at (4,17), solid (the avenue ends at a bus bay, as Shirakawa-go's road does) |
| 19-29 | The south block: four towers standing on row 29, trees and shrubs (solid) round them |
| 30-32 | The promenade the south towers open onto, x 2..32, joined to the avenue's pavements by pavement at x 2-3 and x 31-32, rows 19-29 |
| 33-35, x 0-1 | Woods (solid), the same `tree-green` as the backdrop |

| Lobby | Tower | Origin (x, top row) | Door cell(s) |
|---|---|---|---|
| `LobbyShinjuku1` | highrise-apartment 5x8 | (4,4) | (6,11) |
| `LobbyShinjuku2` | highrise-glass 4x10 | (10,2) | (11,11) (12,11) |
| `LobbyShinjuku3` | highrise-blue 5x11 | (15,1) | (17,11) |
| `LobbyShinjuku4` | highrise-yellow 4x8 | (21,4) | (22,11) |
| `LobbyShinjuku5` | midrise-apartment 5x6 | (26,6) | (28,11) |
| `LobbyShinjuku6` | highrise-blue | (5,19) | (7,29) |
| `LobbyShinjuku7` | highrise-glass | (12,20) | (13,29) (14,29) |
| `LobbyShinjuku8` | highrise-apartment | (18,22) | (20,29) |
| `LobbyShinjuku9` | highrise-yellow | (25,22) | (26,29) |

Lobbies come from the existing tool (`generate_houses.py --lobbies Shinjuku`; names "Lobby · Shinjuku 1..9";
`--dry-run` lists nothing skipped). No new art, no palette entry, no engine code.

**The name.** Shinjuku is the real skyscraper district and the one the ticket names; Marunouchi is
Palace's name already, and Ueno and Shibuya are spoken for (`districts.py`). No blog post mentions it.

## Changes

All paths under `gamev2/` unless they start elsewhere. One commit.

1. **`tools/generate_shinjuku.py`** (new), in the style of `generate_shirakawago.py`, on `hokuriku.Kit`.
   Module docstring as the other generators have (what, where, how to run); the same imports and
   `cfg = rg.load_config()`, and a closing `print`. The rest, as validated:

   ```python
   W, H = 34, 36
   AT = (24, 51)                     # in TokyoCity's cells; devhouse.world is the truth (sync_cities.py)
   KERB = W - 1                      # the west road's west kerb (world x 57)
   AVE = 14                          # the avenue: rows 14-16 (world 65-67, the Palace/Park road carried on west)
   FRONT_N, FRONT_S = 11, 29         # the rows the two rows of towers stand on
   NORTH = [('highrise-apartment', 4, 5, 8), ('highrise-glass', 10, 4, 10), ('highrise-blue', 15, 5, 11),
            ('highrise-yellow', 21, 4, 8), ('midrise-apartment', 26, 5, 6)]          # prefab, x, w, h
   SOUTH = [('highrise-blue', 5, 5, 11), ('highrise-glass', 12, 4, 10), ('highrise-apartment', 18, 5, 8),
            ('highrise-yellow', 25, 4, 8)]
   CROSSING = (22, 23)

   b = rg.Builder(W, H); k = hk.Kit(b); rng = random.Random(94)
   b.fill('grass-autotile')
   b.autotile('flat-grey-brick-autotile',
              sorted(set(rect(2, AVE - 2, KERB - 1, AVE - 1) + rect(2, AVE + 3, KERB - 1, AVE + 4)
                         + rect(2, AVE, 3, AVE + 2)
                         + rect(2, AVE + 5, 3, FRONT_S + 3) + rect(KERB - 2, AVE + 5, KERB - 1, FRONT_S + 3)
                         + rect(2, FRONT_S + 1, KERB - 1, FRONT_S + 3))))
   k.road_h(4, KERB - 1, AVE, cap_w=True)
   for y in range(H):
       b.put('Floor', KERB, y, 'road-plain_0_0' if AVE <= y <= AVE + 2 else 'road-edge-left_0_0')
   for x in (5, 6) + CROSSING:
       b.put('Floor', x, AVE + 1, 'road-plain_0_0')
   for x in CROSSING:
       b.stamp('crossing-h', x, AVE)
   b.stamp('traffic-light', CROSSING[0] - 1, AVE - 3)
   b.stamp('traffic-light', CROSSING[1] + 1, AVE + 1)
   for name, x, w, h in NORTH:
       k.building(name, x, FRONT_N - h + 1, w)
   for name, x, w, h in SOUTH:
       k.building(name, x, FRONT_S - h + 1, w)
   b.stamp('vending-white', 9, FRONT_N - 1); b.stamp('vending-red', 14, FRONT_N - 1)
   b.stamp('utility-pole', 20, FRONT_N - 2)
   b.stamp('bus-stop', 4, AVE + 3); b.solid(4, AVE + 3)
   k.woods(0, 0, KERB - 1, FRONT_N, ['tree-green'], rng)
   k.woods(0, FRONT_N + 1, 1, H - 1, ['tree-green'], rng)
   k.woods(4, AVE + 5, KERB - 3, FRONT_S, ['tree-green'], rng)
   k.woods(2, FRONT_S + 4, KERB - 1, H - 1, ['tree-green'], rng)

   prev = cfg['rooms'].get('Shinjuku', {})
   seams = [rg.transporter(KERB, AVE + i, 'Palace', 3, 18 + i, hidden=True) for i in range(3)]
   k.dress()
   b.finish()
   cfg['rooms']['Shinjuku'] = b.room('Shinjuku', npcs=prev.get('npcs', []), transporters=rg.kept_order(prev, seams))
   for i in range(3):                # Palace is a ported map: its side of the seam is pinned, nothing else touched
       rg.pin(cfg['rooms']['Palace']['transporters'],
              rg.transporter(0, 18 + i, 'Shinjuku', KERB - 3, AVE + i, hidden=True))
   if not any(m['room'] == 'Shinjuku' for m in cfg['cities']['TokyoCity']['rooms']):
       cfg['cities']['TokyoCity']['rooms'].append({'room': 'Shinjuku', 'x': AT[0], 'y': AT[1]})
   rg.save_config(cfg)
   ```

   It is idempotent, keeps blog NPCs, and the lobby doors survive a re-run (`roomgen.save_config`).
2. **`tools/check_generators.py`**: `GENERATORS += ['generate_shinjuku']` before the `districts` entry
   (which must stay last).
3. **`../devhouse.world`**: one map entry, in the file's own formatting, after `park.tmj`:
   `gamev2/tiled/shinjuku.tmj`, `x` 1536, `y` 3264, `width` 2176, `height` 2304.
4. **`tools/districts.py`** `DISTRICTS`, before `'Park'`:

   ```python
   'Shinjuku': [
       d('shinjuku', 'Shinjuku',
         'the skyscraper district: an avenue of office towers and blocks of flats west of Marunouchi, '
         'a zebra crossing under the signals, vending machines, the bus bay at the end of the avenue',
         (2, 2, 32, 32), stand=(16, 13)),
   ],
   ```

   Its named spot is the generic "the vending machines" (`vending-white`), which is what `test_spots` needs
   of an outdoor room.
5. **Build**, from `gamev2/`, in this order:

   ```bash
   python3 tools/generate_shinjuku.py
   python3 tools/generate_houses.py --dry-run --lobbies Shinjuku   # nine lobbies, nothing skipped
   python3 tools/generate_houses.py --lobbies Shinjuku
   python3 tools/generate_shinjuku.py                              # a re-run changes nothing
   python3 tools/sync_cities.py
   python3 tools/districts.py
   python3 tools/config_to_tiled.py Shinjuku Palace LobbyShinjuku1 LobbyShinjuku2 LobbyShinjuku3 \
       LobbyShinjuku4 LobbyShinjuku5 LobbyShinjuku6 LobbyShinjuku7 LobbyShinjuku8 LobbyShinjuku9
   <python with Pillow> tools/make_worldmap.py
   ```

   Generated and committed: `config.json` (rooms `Shinjuku`, `LobbyShinjuku1..9`; Palace's three
   transporters; `cities.TokyoCity.rooms`; `districts.Shinjuku`), `tiled/shinjuku.tmj`,
   `tiled/palace.tmj`, the nine lobby maps, `assets/map/*`.
6. **`tools/distinct_baseline.json`**: Tokyo's entry only, by hand: `buildings` 0.186, `sprites` 0.329,
   `own` 0.534 (was 0.158 / 0.324 / 0.551; see Risks). Do not run `--update`: it would also record four
   other cities that are already worse than the baseline on `master`.
7. **Tests** (below) and the pinned lists a fifth district changes.
8. **Docs**: `docs/stitched-city.md` (five districts; Shinjuku's offset and how it joins; it is generated,
   the other four are ported), `docs/landmarks-and-towns.md` (Tower lobbies: "twenty-five lobbies in nine
   towns", a Shinjuku row in the table; the district under Tokyo), `docs/buildings-and-street-props.md`
   (line 18 "sixteen in the eight towns"; where the towers and the signalled crossing are placed),
   `docs/generators-and-checks.md` (Tokyo's baseline numbers), `tools/browser/README.md` (the new check),
   and the wording that counts or lists Tokyo's districts: `gamev2/CLAUDE.md` ("The four Tokyo districts
   are stitched"), `tiled/README.md`, `src/systems/CityStitcher.js` header comment,
   `.claude/skills/play-game/SKILL.md`, `.claude/skills/adjust-game/SKILL.md`. The list of ported rooms
   (Tokyo, Market, Park, Palace) does not change.

Rooms touched, to name in the summary: Shinjuku (new), LobbyShinjuku1-9 (new), Palace (three hidden
transporters), plus `config.json` `cities` and `districts`, `devhouse.world`, `assets/map`.

## Data and interfaces

- `config.json` `rooms.Shinjuku`: `name` "Shinjuku", 34x36 (`worldWidth` 2176, `worldHeight` 2304), 14
  transporters: three hidden seams (33,14..16) -> Palace (3,18..20), eleven lobby doors.
- `rooms.Palace.transporters`: + hidden (0,18..20) -> Shinjuku (30,14..16). Used only with `?stitch=0`.
- `cities.TokyoCity.rooms`: + `{"room": "Shinjuku", "x": 24, "y": 51}`, last. `backdrop`, `patch`, `drop`
  unchanged.
- `districts.Shinjuku`: one district, key `shinjuku`, bounds (2,2,32,32), stand (16,13), spot "the vending
  machines". The blog pipeline will offer it for Tokyo posts.
- `tilePalette`: unchanged (959 entries). No new sprite, prefab, localStorage key or URL parameter.

## Tests

New **`tools/tests/shinjuku.test.js`** (helpers as in `sapporo.test.js` / `lobbies.test.js`):

- the room is 34x36 and sits at (24,51) in `cities.TokyoCity`; with it the stitched city is still 117x109
  and no district overlaps it;
- column 33 is `road-plain` on rows 14-16 and `road-edge-left` on every other row; no tile of the room is
  a `train-track*`; no `rubbish-bin`;
- the seams round-trip: Shinjuku (33,14..16) -> Palace (3,18..20) and Palace (0,18..20) -> Shinjuku
  (30,14..16), all hidden, every target cell walkable;
- nine towers, each prefab present, every door cell a transporter to `LobbyShinjuku<n>` whose way out is
  the cell below the door, and that cell is walkable;
- stitched, the player's cell west of Palace (0,19) is Shinjuku (33,15) and every lobby door is reachable
  from the junction (`play.js reach Shinjuku` holds the cell below each door);
- running `generate_shinjuku.py` twice leaves `config.json` unchanged (covered by `check_generators.py`).

Pinned lists to update:

- `tools/tests/madeup-towns.test.js:24`: the districts are `['Tokyo','Market','Palace','Park','Shinjuku']`
  ("Tokyo is five districts").
- `tools/test_blog_to_npc.py:498` (`test_city_reach`): the same list. Nothing else in that file changes.
- `tools/tests/lobbies.test.js`: a `Shinjuku` row of nine in the table (rows as in the Approach table,
  tile keys `<prefab>_0_0`), `Shinjuku` in the two town lists (lines 128, 131) and in the `--dry-run` call.
- `tools/tests/hud-phone-layout.test.js` (lines 186, 206): `Lobby · Shinjuku 1..9` join the lobbies whose
  name is one character too long for the lead-in countdown on a landscape phone (the date shows instead,
  as for Kanazawa's two).

Browser regression (`tools/browser/regress.js`, new check `shinjuku-avenue`, in the manner of
`seam-stitched`): from Palace (3,19) (stitched, Park owns that cell: Park (3,1)) walk west with real keys;
the HUD names Shinjuku on the avenue;
walk to (28,12), step up into the door, the room is `LobbyShinjuku5`; step out, back on (28,12). Repeat the
walk in on the landscape phone with the d-pad. Update the count in `tools/browser/README.md`.

Run, from `gamev2/`: `node tools/test_game.js`, `python3 tools/test_blog_to_npc.py`,
`node tools/play.js check`, `<python with Pillow> tools/check_generators.py`,
`python3 tools/sync_cities.py --check`, `node tools/play.js lint Shinjuku` (also `Palace`, `TokyoCity`),
`python3 tools/check_distinct.py` (Tokyo must not be listed as worse), `python3 tools/rehearse_blog.py`,
the browser regression, then play it: desktop and a phone size, day and night, stitched and `?stitch=0`,
screenshots looked at.

In the scratch copy: lint 0 errors and 0 warnings for Shinjuku, Palace and TokyoCity; `play.js check` no
problems; every generator reproduces; `sync_cities.py --check` in sync; `test_blog_to_npc.py` ok and
`test_game.js` clean once the four pinned lists above are updated; `rehearse_blog.py` 313/313.

## Risks and open questions

- **Serial map data.** Must not run alongside #255, #256, #257. #256 (Karuizawa) also joins `TokyoCity`
  and edits the same pinned lists and "five districts" wording: whichever lands second rebases them. If
  Karuizawa is west of world x 0 the city's origin moves and `sync_cities.py` rewrites Shinjuku's offset;
  the generator only adds the entry when it is missing, so that is safe, and the new test should then read
  the offset relative to Palace's (-34, +4) rather than as (24,51).
- **Tokyo is a little less its own.** Three tower sprites are new to Tokyo (`highrise-apartment`, `-blue`,
  `-glass`), which Fukuoka and Osaka also use: building overlap 0.16 -> 0.19, own art 55% -> 53%. It still
  passes all three targets (0.25 / 0.40 / 33%). This follows from the ticket's call to use the existing
  prefabs; the baseline records it. Shinjuku-only tower art would be a separate ticket.
- **Nine more lobbies** (25 in all), each the same room with the Career desk. Required by "no sealed
  buildings".
- **The avenue is a dead end** with a turning box and a bus bay. A loop back to Park's road would need a
  junction cut into Park's ported map, which the ticket rules out.
- **`?stitch=0`**: the district's east column is half of the west road at the map's edge, and only the
  three junction cells are seams; stitched, the whole kerb column is open, as on every shared road.
- **The blog pipeline may place Tokyo posts in Shinjuku** from now on. No existing placement moves.
- Open questions: none that block. The name is one string in the generator and `districts.py` if the owner
  prefers another real district.
