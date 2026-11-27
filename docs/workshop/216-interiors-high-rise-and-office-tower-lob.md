# Design: tower lobbies in every town, and the HUD short name that goes with them (#216)

## Context

Every high-rise, office tower and block of flats should open into the one shared lobby. The generator
(`gamev2/tools/generate_houses.py --lobbies`), the lobby art, the lint rules and the tests are on master,
and Osaka (3) and Sapporo (2) have their lobbies. What is left:

1. **HUD short name.** On a landscape phone the bar shows `hudBrief(name)`. For a room named for its kind it
   leads with the town (`"Lobby · Osaka 2"` → `"Osaka lobby"`). In a long-named district that does not fit:
   `"Marunouchi lobby"` (16) and `"San Franbourne lobby"` (19) are wider than the 667x375 bar allows beside
   `Feb 10 2027 | ¥5,000`, so the year is dropped and the lead-in countdown never shows.
2. **Roll-out** to the towns that still have sealed towers: Market (Asakusa), Palace (Marunouchi), Fukuoka,
   Sendai, Kanazawa and San Franbourne.
3. **No sealed buildings** (owner rule): where a prop stands in front of a tower's door, move the prop in the
   same change.
4. **Phone-size verification** of the result.

Outcome: 16 lobbies in 8 towns, no tower skipped, one row of HUD with the year at 667x375 inside every one.

Everything below was built and checked in a scratch worktree before writing this (results under Tests).

## Approach

**HUD rule** — adopt the rule already drafted on `origin/wip/216-marunouchi-lobbies`: `hudBrief` keeps the
town-led form while it is at most `HUD_BRIEF_MAX = 15` characters (the longest that fits one row with the
short date, its year and the starting wallet on the 715px bar of 667x375: `10 + 16·len + 10 + 64 + 10 ≤ 715`
with `len = brief + " | Feb 10 2027 | ¥5,000"`); longer than that it falls back to the kind plus the room's
number: `"Lobby | Marunouchi 1"` → `"Lobby 1"`, `"Lobby | San Franbourne"` → `"Lobby"`,
`"Shrine | Imperial Palace"` → `"Shrine"`. General (no town list), applies to House / Lobby / Shrine alike,
and `layoutHUD` in `GameScene.js` needs no change. (Close alternative: leave `hudBrief` alone and let
`layoutHUD` drop the year. Rejected: the ticket asks for the rule in `hudBrief`, and those rooms would never
show the lead-in countdown.)

**Roll-out** — run the existing generator on the six towns; no new generator code except one exclusion:

| Town (display name) | Rooms | Tower → door cell in the town |
|---|---|---|
| Market (Asakusa) | `LobbyMarket1` "Lobby · Asakusa" | highrise-yellow (16,29) |
| Palace (Marunouchi) | `LobbyPalace1` "Lobby · Marunouchi 1", `LobbyPalace2` "… 2" | highrise-yellow (49,13); midrise-apartment (42,15) |
| Fukuoka | `LobbyFukuoka1..4` "Lobby · Fukuoka 1..4" | highrise-glass (17,18)+(18,18); -blue (22,18); -yellow (26,18); midrise-apartment (38,18) |
| Sendai | `LobbySendai1` "Lobby · Sendai" | highrise-yellow (23,20) |
| Kanazawa | `LobbyKanazawa1..2` "Lobby · Kanazawa 1..2" | highrise-yellow (15,28); midrise-apartment (28,28) |
| SanFranbourne | `LobbySanFranbourne1` "Lobby · San Franbourne" | highrise-glass (47,27)+(48,27) |

The way out of each is the cell below its (first) door. Osaka's and Sapporo's five are unchanged.

**Blocked doors**

- *Fukuoka*: two pavement lamps stand in front of doors, at (18,19) (the glass tower's right door) and
  (38,19) (the flats). Move each one cell, to (19,19) and (37,19), in `generate_fukuoka.py`, and rebuild
  Fukuoka. Nobody and no blog spot uses either cell.
- *Sendai flats* (`highrise-apartment` at (38,9), door (40,16)): the ticket's "opens onto a sealed verge" is
  not what is there. `generate_sendai.py` stands the town's 7-Eleven (`KONBINI = (38,17)`) directly across
  the door on purpose ("the 7-Eleven under an apartment block"), so the building is already entered through
  the store. Moving the store would redesign the block; instead the generator **excludes** this tower as in
  use (like a house with a shop sign), so it is reported as "not a tower", not as skipped, and Sendai's one
  lobby stays unnumbered.

**Not changed**: leaving a two-door glass tower puts you in front of its first (left) door. Same as Sapporo
station's door pair; remembering the door used would need per-visit state for no gain.

## Changes

All paths under `gamev2/`. Work in order; the map steps are a recipe, not hand edits.

1. **Port the WIP source** (do not bring the branch's `wip-handoff/` folder or its generated map data):
   `git diff origin/master...origin/wip/216-marunouchi-lobbies -- gamev2/src gamev2/tools gamev2/docs | git apply`
   (applies cleanly on master `c0e657fa`; if that ref is not in your checkout, write the same by hand from
   this section and steps 5-6). That gives:
   - `src/utils/NpcStates.js`: `hudBrief` as below, `HUD_BRIEF_MAX`, the doc comment.
     ```js
     function hudBrief(name) {
         const [head, rest] = String(name).split(' | ');
         if (!HUD_KINDS.includes(head) || !rest) return head;
         const town = rest.replace(/ \d+$/, ''), led = `${town} ${head.toLowerCase()}`;
         return led.length <= HUD_BRIEF_MAX ? led : head + rest.slice(town.length);
     }
     const HUD_BRIEF_MAX = 15;
     ```
   - first drafts of the test and doc changes, finished in steps 5 and 6.
2. **`tools/generate_houses.py`** — exclusion for a tower that is a store's block:
   - beside `SHOP_SIGNS`: `STOREFRONTS = ('seven-eleven_0_0',)`;
   - in `find_houses`, collect `stores` next to `signs` (`elif kind == 'lobby' and key in STOREFRONTS: stores.add((x, y))`);
   - in the exclusion chain, after the shop-sign branch:
     `elif any(y == door[1] + 1 and h['span'][0] < x < h['span'][1] for x, y in stores): h['excluded'] = 'in use: the 7-Eleven standing across its door is its ground floor'`;
   - mention it in the module docstring where exclusions are listed.
3. **`tools/generate_fukuoka.py`** — the street-side lamp row `for x in (18, 23, 38, 42, 47, 54, 58)` becomes
   `(19, 23, 37, 42, 47, 54, 58)`; reword the "sealed - no interiors" comment above the towers (line ~157).
   In `generate_sanfranbourne.py` the docstring line "Houses stay sealed" stays true; add that its glass
   tower's lobby comes from `generate_houses.py --lobbies`.
4. **Build the world** (needs Pillow: `pip install --break-system-packages pillow`), from `gamev2/`:
   ```bash
   python3 tools/generate_fukuoka.py
   python3 tools/generate_houses.py --lobbies Market Palace Fukuoka Sendai Kanazawa SanFranbourne
   python3 tools/config_to_tiled.py Market Palace Fukuoka Sendai Kanazawa SanFranbourne \
       LobbyMarket1 LobbyPalace1 LobbyPalace2 LobbyFukuoka1 LobbyFukuoka2 LobbyFukuoka3 LobbyFukuoka4 \
       LobbySendai1 LobbyKanazawa1 LobbyKanazawa2 LobbySanFranbourne1
   python3 tools/make_worldmap.py          # Fukuoka's two lamps moved
   ```
   The generator's output must match the table above with nothing "skipped" (check first with `--dry-run`).
   Result: `config.json` (11 new rooms, hidden transporters and door colliders off in six towns; palette
   untouched), 11 new `tiled/lobby*.tmj`, six town `.tmj`, `assets/map/world-map.png`. `check_distinct.py`'s
   baseline does not need re-recording.
5. **Tests** (strict updates; these eight fail after step 4 until changed):
   - `tools/tests/lobbies.test.js`: host list is the eight towns
     (`Fukuoka, Kanazawa, Market, Osaka, Palace, SanFranbourne, Sapporo, Sendai`), 16 lobbies; pin each new
     room's key, name, tower sprite and door(s) from the table; Fukuoka's and San Franbourne's glass towers
     have two doors into one lobby; Sendai's flats are found, excluded with the "in use" reason, have no
     lobby and their door cell stays solid; a sole lobby has no number (Asakusa, Sendai, San Franbourne).
   - `tools/tests/hud-phone-layout.test.js`: `hudBrief` cases for the fallback (`"Lobby 1"`, `"Lobby"`,
     `"Shrine"`, and a 15-character name still town-led); `HUD_BRIEF_MAX` equals what the 715px arithmetic
     gives; the loop over kind-named rooms expects `led.length <= HUD_BRIEF_MAX ? led : kind + number` (no
     per-town regex); every lobby fits one row with the year at 715 and 744. The lists of lobbies that
     cannot show a countdown change: at 844x390 (744px, brief ≤ 13) `['Lobby · Kanazawa 1', 'Lobby · Kanazawa 2']`
     instead of none; at 667x375 (715px, brief ≤ 11) Sapporo 1-2 plus Asakusa, Fukuoka 1-4, Kanazawa 1-2 and
     Sendai. Rename the test whose name says every lobby counts down at 844x390.
   - `tools/tests/airports.test.js` (~95, ~374): San Franbourne's doors also include `LobbySanFranbourne1`
     (both ways); houses still have no interiors there.
   - `tools/tests/fukuoka.test.js` (~60): the non-house transporters are the station, the konbini and the
     lobby doors; assert the five lobby doors (hidden, on a tower's door cell, into `LobbyFukuoka1..4`).
   - `tools/tests/kanazawa.test.js` (~225) and `tools/tests/sendai.test.js` (~84): "buildings are solid over
     their whole footprint" gains one exception, a tower's door cell that carries a hidden transporter into
     a room whose `lobby.host` is that town (Kanazawa (15,28), (28,28); Sendai (23,20)), written like
     Sendai's existing machiya `doorway()`.
6. **Docs**
   - `docs/landmarks-and-towns.md`, "Tower lobbies": applied to all eight towns (the table above); replace
     the reference to `.agent-queue/items/lobbies_apply.sh` (not in the repo) with the commands of step 4;
     replace the "Dry run of the other towns" bullet with the two decisions (Fukuoka's lamps, Sendai's flats
     excluded via `STOREFRONTS`); fix the per-town lines that say towers are sealed (San Franbourne ~405).
   - `docs/hud-input-touch.md` (~192): the `HUD_BRIEF_MAX` fallback.
   - `docs/buildings-and-street-props.md` (~12): "Doors are sealed and lead nowhere" → towers open into a
     lobby (pointer to Tower lobbies).

Commit as one change: `gamev2: every tower has a lobby … (#216)`, no attribution lines.

## Data and interfaces

- `config.json`: 11 new rooms `Lobby<Host><n>` (existing shape: `interior: true`, `shopEnabled: false`,
  `lobby: {host, door, doors}`), one hidden transporter per opened door in the host. No schema change, no
  palette change, no save-format change, no new keys or bindings.
- `hudBrief(name)` keeps its signature; new global `HUD_BRIEF_MAX` (tests read it with `game('HUD_BRIEF_MAX')`).
- `generate_houses.py`: new constant `STOREFRONTS`; `find_houses` may return `excluded` with the new reason
  for kind `lobby`.

## Tests

From `gamev2/`, all must pass:

```bash
node tools/test_game.js
python3 tools/test_blog_to_npc.py
node tools/play.js check
python3 tools/check_generators.py
python3 tools/sync_cities.py --check
python3 tools/check_distinct.py
for r in Market Palace Fukuoka Sendai Kanazawa SanFranbourne LobbyMarket1 LobbyPalace1 LobbyPalace2 \
    LobbyFukuoka1 LobbyFukuoka2 LobbyFukuoka3 LobbyFukuoka4 LobbySendai1 LobbyKanazawa1 LobbyKanazawa2 \
    LobbySanFranbourne1; do node tools/play.js lint $r; done
```

Browser regression (`tools/browser/README.md`): start a Chromium with
`chromium.launchServer({ port: 9333, host: '127.0.0.1', wsPath: 'pw' })` (without `host` it binds `::1` and
`browser.js` cannot connect), serve `gamev2/` over HTTP, then
`NODE_PATH=<dir holding playwright-core> PORT=<port> node tools/browser/regress.js`. No assertion in it changes.

Then play it with real keys and touches, screenshots to `/work/media/`: walk into and out of at least one
lobby per new town (both doors of a glass tower), day and night, on desktop and at 667x375 and 844x390 with
`?touch=1`; the HUD inside reads `Lobby 1 | <date with year> | ¥…` in Marunouchi and `Lobby | …` in San
Franbourne on one row.

Scratch-build results (master + the steps above): generator output as the table, no tower skipped; lint 0
errors / 0 warnings for all 17 rooms; `test_blog_to_npc`, `play.js check`, `sync_cities --check` pass;
`check_distinct` no town worse than baseline; `check_generators` every room generator `ok`; browser
regression 20/20; `test_game.js` fails exactly the eight tests of step 5 before they are updated.

## Risks and open questions

- **`check_generators.py` art tools**: under this container's Pillow 13 several art tools report `DRIFT`
  and two skip for want of a Japanese font, on untouched master too. Not caused by this change; compare
  against master and do not commit regenerated art.
- **Town redesigns (#210/#219)** will rebuild some of these towns. Lobby doors survive a town-generator
  rebuild where the tower still stands (`roomgen.save_config` / `keep_house_doors`); a tower a redesign
  removes leaves an orphan `Lobby` room for that redesign to drop by re-running `--lobbies`. Market and
  Palace are ported maps: their doors live only in `config.json` / `.tmj`.
- **Map data is serial**: this touches six towns' map data at once. If master moved in those towns, replay
  step 4 on top rather than merging `config.json` by hand.
- **Countdown on phones**: `"Kanazawa lobby"` (14) fits with the year but, like `"Asahikawa house"`, is too
  long for the lead-in countdown at 844x390; several town-led names are at 667x375 (listed in step 5). That
  is the existing behaviour for town-led names, kept.
- **Open, defaults taken** (owner can overrule in review): Sendai's flats count as the 7-Eleven's block
  rather than getting a lobby of their own; a glass tower's exit is always its left door.
