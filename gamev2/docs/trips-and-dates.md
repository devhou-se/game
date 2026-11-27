# Trips and dates

The devhouse trips as data (`config.trips`, `src/utils/Trips.js`): who exists on a date, where a player starts, the intro wording, Time Travel. The default game date is in `maps-and-rooms.md`.

A "see X" in the text names a section; if it is not in this file, the index in [`../CLAUDE.md`](../CLAUDE.md) says which file has it.

### Trips (issues #118, #131, #130, #96, #59)

The trips are data — `config.json` top-level `trips`, read through `src/utils/Trips.js` (pure functions
of the config and a date; `tools/play.js`, the studio and `tools/test_game.js` run the same code):

```json
"trips": [
  { "id": "devhouse2", "name": "devhouse 2", "where": "Japan", "start": "2025-10-02", "end": "2025-11-18",
    "members": ["bailey", "damian", "dylan", "julia"], "home": { "room": "Tokyo", "x": 29, "y": 38 } },
  { "id": "devhouse3", "name": "devhouse 3", "where": "Hokkaido", "start": "2027-02-18", "end": "2027-02-28",
    "members": ["bailey", "damian", "dylan", "julia", "khoi", "sam", "xander"],
    "home": { "room": "Sapporo", "x": 33, "y": 12 },
    "stays": [ { "from": "2027-02-18", "room": "Sapporo", "x": 33, "y": 12 },
               { "from": "2027-02-25", "room": "Asahikawa", "x": 31, "y": 12 } ],
    "utcOffset": 9 }
]
```

`members` are sprite base names (James is the default player sprite, never a member; `credits` is a
separate list and is not read for any of this). `stays` is optional: where the group is based from each
date. Give every stay its `x`, `y`: one without a cell is ignored as a start (the player lands at the
trip's `home`, possibly a room away from the cast) and `play.js check` reports it. devhouse 2's dates are the span of its blog posts.
`utcOffset` (hours ahead of UTC where the group is; optional) is read by the blog pipeline only: a trip
that has it dates its posts by the clock there (`blog_to_npc.post_date`, see The blog rehearsal in `blog-pipeline.md`).
devhouse 2 has none on purpose — its history was written with UTC dates, and an offset would re-date a re-run post.

**The trip a game date belongs to** (`Trips.forDate`) is the latest one that has OPENED by then — the
days after a trip still belong to it — or the first trip for a date before them all. A trip opens
`"lead"` days before its `start` (default `Trips.LEAD`, 14; `trip.opens`; devhouse 3 says `"lead": 30`, so it opens on 19 January 2027 and a
planning post up to 30 days out is its own — issue #170): a post from the travel days on
the way there is that trip's content day, not the previous trip's (it would otherwise join the previous
trip's cycle and shift the between-trips default date). On those lead-in days (`windowFor(...).early`)
the previous trip is history and the new trip's base NPCs are not standing anywhere yet — only people
who have posted since it opened are placed — and from the trip's first day the lead-in posts are history
too and everyone is at the base. A lead-in day is not a trip day (`Trips.during`): no
picker underline, and the default date only lands there once it has a post. Once the trip is over the
default date cycles over the trip's own days only (`Trips.defaultDate`), so a post from the road is never
the day a later visitor opens on (unless it is all the trip has). `blog_to_npc.py`
(`trip_window`, `TRIP_LEAD`) mirrors the rule.

**The lead-in says so** (issue #164, `Trips.leadIn(trips, date)` → `{ trip, days, stay }` or null): nobody
has arrived, and an empty base with no explanation read as a bug. On a lead-in day
- the HUD counts down — `devhouse 3 in 8 days | February 10 2027`, shortened to `in 8d`, then `soon`, then
  the bare date as the line runs out of room (`Trips.dateLabel`; in Sapporo with the starting ¥5,000 it is
  `in 8d`) — for new and returning players alike. A landscape phone's one-row bar has no room for
  both, so there the countdown takes the date's place (`Trips.countdown`, see `hud-input-touch.md`). This is the only time the HUD names a trip: on the
  trip's own days the date is bare (issue #163). The countdown is the `Trips.leadIn` line in
  `Trips.dateLabel`; with `lead` null there the HUD is the bare date every day;
- the intro's page 1 reads "devhouse 3, their trip to Hokkaido, starts on February 18. This is the little
  world they will be walking around." (`Intro.tripCopy(..., starts)`), and page 3 "They have not arrived
  yet: devhouse 3 starts here in Sapporo on February 18. Have a look around before they get here."
  (`Trips.arrivalText` → `Trips.whereText(groups, here, arrival)` → `Intro.meetCopy`; a room is named in these sentences by `Trips.placeName`: its `sentenceName` if it has one, "the Imperial Palace", else its display name). When somebody has
  posted from the road it is "Today Bailey is here in Palace. devhouse 3 starts in Sapporo on February 18.
  Walk into Bailey to say hello." (one person is walked into by name; "Go and find one to say hello." when
  nobody is placed on an ordinary day);
- the player starts at the trip's first base (the first stay's cell, Sapporo 33,12) — where they will
  arrive — unless somebody has posted, in which case beside them, like any other day (`Trips.startFor`).
A real visitor on those days is still shown a day of the trip before (the default game date); page 1
then ends "… devhouse 3 starts on February 18." (`Trips.upcoming(trips, today)`), and stops saying so the
day the trip starts. Days before the FIRST trip are not a lead-in (they show its base cast). The trip decides:

- **Who exists** (`Trips.windowFor` → `resolveNpc(npc, date, trips)`). A base NPC marked `"trip": "<id>"`
  is there only on that trip's dates, and with `"stay": "<room>"` only while the group is based in that
  room; otherwise it resolves as if its base said `present: false`. Dated states are applied only from
  the window's first day (the start of the stay, else of the trip) — earlier ones are another trip's
  history — and a state inside the window still places anybody anywhere. So: devhouse 2's base cast
  (Bailey, Damian, Dylan and Julia in one row in Tokyo, issue #68) carries `"trip": "devhouse2"`; devhouse 3 has a base
  NPC for all seven in Sapporo (`"stay": "Sapporo"`) and in Asahikawa (`"stay": "Asahikawa"`) with two
  neutral lines each, so on 18-24 Feb 2027 everyone stands in Sapporo and from the 25th in Asahikawa
  before anyone has posted; Khoi, Sam and Xander are nowhere on a 2025 date. A member's first post of a
  trip moves them as usual (`blog_to_npc.py` needs no trip knowledge: it writes a dated state where they
  are and `present: false` everywhere else, both inside the window), and when the group moves base
  everyone is at the new base until they post from it. NPCs with no `trip` (the izakaya opponents,
  the pipeline's hidden per-room defs) are unscoped apart from the state window.
  Resolution of every NPC on every devhouse 2 day was compared before and after the change: identical,
  apart from the three new members being absent.
- **The default game date** — see Default game date in `maps-and-rooms.md`.
- **Where the player starts** (`Trips.startFor(config, date, { played })` → `{ room, x, y }`,
  the same terms a door target is written in — a DISTRICT cell (`Tokyo 29,38`, `Market 5,24`), never a
  stitched-city one: `GameScene.startPosition()` is the one caller and puts the player there through
  `roomManager.resolve`, so the start is the same cell with `?stitch=0`; "the room" below is the district.
  EVERY player — new (#96, #59) or returning, after a reload or a Time Travel hop (#166) — starts where
  there is someone to talk to: the room with the most members that day, never counting the
  member they are playing as; a tie goes to a room outdoors before a station interior (a `config.stations` room: a platform is
  always one hop nearer than its town), then to the room fewest doors / train rides from home
  (`Trips.hopsFrom`), then config order. In the home room they stand on the home cell when somebody is
  within `Trips.NEAR` (6) cells; otherwise on the cell nearest the group, at least two cells from
  everyone, that can be walked to from the room's arrivals (`Trips.standNear`: Floor tile, no collider,
  inside the boundary, not a door). "The group" is the biggest cluster in the room — people within NEAR
  of one another, in a chain (`Trips.crowd`) — so with Bailey and Dylan on Sendai's bay promenade and
  Damian alone at Zuihoden the start is beside the two; and the cell is ordinary ground where there is
  any in sight of them (`Trips.plain`): not a stair tile, not a deck over water (a bridge, a pier). On every devhouse 2 post day, as any character, that is within 6
  cells of someone (unit-tested). "Home" (`Trips.homeFor`) is the trip's own cell for the date — the
  stay's cell (the first stay's on a lead-in day), else `home`, else `config.player.startRoom/X/Y` — and
  is where a player lands when nobody is anywhere (a lead-in day with no posts) or no cell can be found.
  Why not the trip home for returning players, as it was until #166: there is no saved position to
  restore, the home has nobody near it on most devhouse 2 days (Tokyo 29,38 while the cast is in Sendai or Fukuoka),
  and a Time Travel hop is made to see that day's people. Saving the last position was the alternative; it
  would put a returning player in a room the cast left weeks of game time ago after every date change.
  `CharacterSelect.become` calls `GameScene.resettleNewPlayer()`: a
  player who has not taken a step and has just become the only member near their start cell (the
  creator's name Easter egg, or Menu → Character) is moved to wherever `startFor` says now. With
  somebody still within `Trips.NEAR` cells (`Trips.hasCompany`) they stay exactly where they are, and
  the first step off the start cell ends it (`update()` clears `bootStart`; `GameScene.playerIsAt` compares
  through `resolve`).
  `config.player.startRoom/X/Y` — what the editor's Spawn tool writes — is now only the fallback for a
  config with no trips (and the reachability seed in `AchievementManager` / `world-model.js`): to move
  where the game opens, edit the trip's `home` / `stays` cell. The headless model (`tools/play.js`) still
  OPENS a session on the trip's own cell (`Trips.homeFor`: Tokyo 29,38 on a devhouse 2 day), the same
  place every day, which is what a script wants; `play.js start` goes where the game puts a player.
- **The intro** — who devhouse is (`Intro.cast`: `CharacterSelect.lineup` of the trip's members, alphabetical —
  the cast row draws them and the sentence under it names them), which trip this is and whether it is on right now (`Intro.welcomeCopy`), and where everyone
  is today (`Trips.membersByRoom` + `Trips.whereText`).
- **Time Travel** (`src/DatePicker.js`) — a trip's own days are underlined in the grid whether or not
  they have posts, and a row under the grid names every trip (the selected day's is lit). A click / tap
  on a name, or SHIFT + left/right (touch: hold the sprint pill and press ◀ ▶), jumps to that trip's
  first day with posts, or its first day when it has none (`Trips.jump` / `Trips.landing`). The row
  under the selected date jumps to today (SHIFT + up) or back to the day the game is on (SHIFT + down). No new key.
  The legend under the grid (`DatePicker.legend`) explains each mark: dot = blog post, underline = trip
  (only when the config has trips), and of the two coloured days only those on the month shown —
  gold = today, blue = you are here (the game's day, when it is not today; issue #98). It is worded
  shorter when the line would not fit the panel (52 characters).

**Adding a trip**: add it to `trips`; give its base cast NPC definitions in the room(s) they are based
in, marked with `trip` (and `stay` when the trip has stays) — the shape `tools/generate_cast.py`
`base_npc` writes; keep the lines neutral, they are what people say until their first post. Then
`node tools/play.js check` (it surveys every day of every trip: base NPCs must be walkable-up-to, and
every home / stay cell and every new-player start must be a free cell that leads somewhere) and
`node tools/play.js trips` / `start` to see where a player lands on the current `date`.
