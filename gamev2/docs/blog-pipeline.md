# The blog-to-NPC pipeline

Where `tools/blog_to_npc.py` may place an NPC, the end-to-end rehearsal, and re-homing a placement. Related: post captions (`title-intro-dialogue.md`), author logins (`cast-and-characters.md`), voice clips (`voice.md`), trip scoping and `utcOffset` (`trips-and-dates.md`).

A "see X" in the text names a section; if it is not in this file, the index in [`../CLAUDE.md`](../CLAUDE.md) says which file has it.

## Placement, the rehearsal and re-homing

- **Where blog NPCs may be put** (`find_spots` / `walkable_near` in `tools/blog_to_npc.py`): outdoor rooms
  offer the ordinary landmarks. Interiors are opt-in: a station room (a key of `config.stations`; they
  carry no `interior` flag) offers only `indoors` landmarks — today `the platform`, its west end by the
  vending machine — and the model is told to pick it only for a post about that station or the train ride
  itself. `interior: true` rooms (konbini, izakaya) are never offered. The cell chosen is the nearest free
  one to the landmark's standing cell that can be walked to from one of the room's ways in, so a
  landmark inside a fence (Market's fox statues) puts its visitor outside it. A room on its own is entered
  by its transporters; a district of the stitched Tokyo city is also walked into from its neighbours, so
  `reachable_cells` floods the whole city as the game merges it (`city_districts` / `city_reachable`: doors
  and the spawn point as seeds, a later-listed district owning the cells it overlaps — issue #124) and
  `occupied_cells` counts a neighbour standing on a shared cell. Tokyo, whose only transporters are seams,
  is judged like the rest; an outdoor room with no way in at all now fails the test instead of silently
  skipping the reachability filter. `python3
  tools/test_blog_to_npc.py` checks all of this over every room in `config.json`: add a room or a
  landmark and it tells you if a spot is mislabelled, unreachable, or lands on a station's doors.
  **Never in the way** (issue #119, `walls_in`): an NPC is solid, so the cell must also leave everything
  that could be walked to still walkable — not the middle of a one-cell lane, the mouth of a dead end or
  the cell in front of a door — and must not take the only cell a neighbour could be walked up to from.
  Asahikawa's `ramen alley` is one cell wide: its standing cell (10,15) is refused and the author stands in
  the shop doorway beside it (9,14); before the rule a ramen post sealed off the west half of the alley,
  Sam's base spot included. `walk_region` is the whole stitched city for a district, so a walk that leaves
  the district and comes back counts.
- **The blog rehearsal** (issue #119): `python3 tools/rehearse_blog.py [--keep DIR] [-v]` (`--keep` takes a new or empty
  directory, or one an earlier rehearsal kept — it refuses anything else, and anything in or around `gamev2/`) runs
  `blog_to_npc.py` end to end the way the www-jp `game-npc-pipeline` workflow does (one `--payload … --mock
  --summary-out …` per post) for a devhouse 3's worth of synthetic posts — all seven members, Sapporo and
  Asahikawa days, a lead-in post, a day trip, two posts on one day, photos, voices, a drunk post, posts
  published before 09:00 in Japan, a re-run — in a SCRATCH directory, never the committed `config.json` or
  assets (both are fingerprinted before and after). Nothing leaves the machine: `--mock` for the LLM, local
  stand-ins for the photo download and the ElevenLabs call, `anthropic` un-importable, every socket connect
  refused and counted. The result is checked against the written config AND through the game's own code
  (`node tools/play.js --config=<scratch>/config.json`: every NPC resolved on every day from 19 Jan to 1 Mar
  2027, plus `check`). Run it after touching `blog_to_npc.py`, a Hokkaido map, the trips or the cast.
  What it needs from the tools:
  - `--mock` is steerable: a payload's `"mock": {"spot", "dialogue", "drunk"}` overrides the canned
    response (ignored without `--mock`), so a rehearsed post goes to the landmark it is "about".
  - `node tools/play.js --config=<file>` plays another config against this checkout's maps and sprites,
    with its own session file.
  - **Posts are dated by the day in Japan** (`post_date`, the trip's `utcOffset`): the payload's `date` is
    GitHub's `createdAt`, in UTC, and the pipeline used to keep its first ten characters — so a post
    written before 09:00 in Japan was dated the day before, and on the two days the game starts everyone
    afresh (18 Feb, and 25 Feb when the base moves to Asahikawa) it was history before it was published.
  - The new members' logins are still placeholders (`AUTHOR_NPCS`): the rehearsal proves such a post is
    skipped with the warning, then maps made-up `rehearsal-<name>` logins in memory only. A real login is
    used as soon as it is filled in. The run ends with a TO DO line while any placeholder remains.
  - `Sapporo · Odori Park` is a spot (the park's lanterns, `rooms: ('Sapporo',)`): the six landmarks issue
    #119 names all have one.
  - The photo print is rendered for real only where `tools/requirements-photos.txt` is installed
    (opencv-contrib: `cv2.saliency`); elsewhere a stand-in writes the 160×144 print and the summary line
    says so. Serve a kept scratch directory to a browser (route `config.json`, `assets/photos/9*.png`,
    `assets/voice/`) to see the result in the game.

- **Re-homing a placement** (issue #121): `python3 tools/blog_to_npc.py --rehome <NPC> <YYYY-MM-DD>
  "<Room> · <label>" [--dry-run]` (repeatable) moves an existing placement to another spot with no LLM call
  — `rehome()` hands the day's dialogue, photo, voice and `posts` to `apply()`, so the room left behind
  keeps a bare `present: false`, the new room gets a hidden base def if needed and later history is
  re-checked. Use it instead of hand-editing a cross-room move. Seven placements made on a station platform
  before #73, for posts about somewhere else, were moved this way (Karuizawa apple pie and Shirakawa-go to
  Yukimura, the Lake Biwa rides to Inaka, the castles to Machi's pagoda, the izakaya night and Hakata
  ramen to Market's 7-Eleven); the travel-day posts stay on their platforms. The cell is free for the
  whole stay (`occupied_during`: from that date until the NPC's next placement, or until a later trip or
  stay starts everyone from its base again — `trip_window`), not just on the day — history is not always
  written in date order — and `process_post` uses the same check.
  `test_blog_to_npc.py` also checks the shipped history: each NPC is in at most one room on any dated
  day, and no two share a cell.
