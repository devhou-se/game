# The blog-to-NPC pipeline

How a devhou.se blog post becomes an NPC, where `tools/blog_to_npc.py` may place one, the end-to-end rehearsal, and re-homing a placement. Related: post captions (`title-intro-dialogue.md`), author logins (`cast-and-characters.md`), voice clips (`voice.md`), trip scoping and `utcOffset` (`trips-and-dates.md`).

A "see X" in the text names a section; if it is not in this file, the index in [`../CLAUDE.md`](../CLAUDE.md) says which file has it.

## How a post becomes an NPC

A new devhou.se blog post moves its author's NPC and gives them new dialogue:

1. The `game-npc-pipeline` workflow in the **www-jp** repository (`devhou-se/www-jp`, not this one) checks
   out this repository and runs, from `gamev2/`, `python3 tools/blog_to_npc.py --payload post.json` with the
   post as `{"post_id", "title", "author", "date", "content"}` (`author` is the GitHub login), then commits
   the result (`gamev2/config.json`, `gamev2/assets/photos`, `gamev2/assets/voice`). Pushing to master
   deploys via `.github/workflows/firebase-hosting-gamev2.yml`. That workflow depends on these `gamev2/`
   paths; it cannot be changed from here.
2. **Text**: one Claude call (`MODEL` in the tool, structured JSON output) reads the post and returns the
   spot the author should stand at (one of the landmarks found in the overworld rooms, or a district - see
   the next section), 3-4 first-person dialogue lines, and whether the post reads as drunk. Lines are trimmed
   to 160 characters on a sentence/word boundary, never mid-word.
3. **Photo** (optional, best-effort): the post's first image becomes a 160x144 pixel-art print in
   `assets/photos/<post_id>.png` (`tools/post_photos.py`).
4. **Voice** (optional, best-effort): with `ELEVENLABS_API_KEY` and `ELEVENLABS_VOICE_<NPC>` set, each
   line is spoken by ElevenLabs into `assets/voice/<voice id>/<line>.mp3` (`tools/post_voice.py`, `voice.md`).
   Unconfigured, the placement lands silent.
5. **Placement**: the result is written to `config.json` as a dated NPC state (`present`, `gridX`/`gridY`,
   `dialogue`, `photo`, `voice`, `posts`) in the chosen room, and `present: false` on that date in every
   other room. Two posts by one author on the same day share the state: the later post's spot wins and its
   lines follow the earlier post's (8 lines a day at most); `posts` records which lines came from which
   post, so re-running a post replaces only its own lines.
6. **Runtime**: `src/utils/NpcStates.js` resolves each NPC to the game date (today, or `?date=YYYY-MM-DD` /
   the in-game date picker), so the author stands at the spot and says the lines from the post's date on.
   The dialogue box (`src/DialogueManager.js`) shows the lines - Japanese included - with the photo framed
   beside the speaker and the clip for each line played if there is one.

Secrets (held by the www-jp workflow): `ANTHROPIC_API_KEY`; optionally `ELEVENLABS_API_KEY` and the
`ELEVENLABS_VOICE_*` voice ids. Authors map to NPCs in `AUTHOR_NPCS` in the tool (`cast-and-characters.md`).

Test without keys or network, from `gamev2/`:

```bash
python3 tools/blog_to_npc.py --payload post.json --mock --dry-run   # canned LLM reply, nothing written
python3 tools/test_blog_to_npc.py                                   # unit checks
```

## Placement, the rehearsal and re-homing

- **Where blog NPCs may be put** (`find_spots` / `walkable_near` in `tools/blog_to_npc.py`): outdoor rooms
  offer the ordinary landmarks. Interiors are opt-in: a station room (a key of `config.stations`; they
  carry no `interior` flag) offers only `indoors` landmarks — today `the platform`, its west end by the
  vending machine — and the model is told to pick it only for a post about that station or the train ride
  itself. `interior: true` rooms (konbini, izakaya, shrine worship halls, the airports) are never offered, and neither is a room that says `"blog": false` (the home city San Franbourne and Haneda's rail stop, issue #218: on no trip, so no spot there - `overworld_rooms` leaves them out). The cell chosen is the nearest free
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
  Asahikawa's `ramen alley` was one cell wide: its standing cell (10,15) was refused and the author stood in
  the shop doorway beside it (9,14); before the rule a ramen post sealed off the west half of the alley,
  Sam's base spot included. The alley is two cells wide since its rebuild (#219: no prop's foot on row 14
  within two columns of a bank shrub), and every cell of its south row is accepted (`asahikawa.test.js`,
  `test_not_in_the_way`, which keeps the one-cell case on a made-up room). `walk_region` is the whole stitched city for a district, so a walk that leaves
  the district and comes back counts.
- **Districts** (issue #219, config `districts`, written by `tools/districts.py`; the list and the fields are
  in `landmarks-and-towns.md`, "Districts"). A post often names an area and no landmark ("we stayed in
  Asakusa"); before, the model could only choose among named spots and such a post went to whatever sounded
  closest. Now:
  - `find_areas` offers every district of every outdoor room as `Room · Name (area)` (`AREA`, so
    `Sapporo · Odori Park`, the spot, and `Sapporo · Odori Park (area)`, the park, are two ids). Stations and
    interiors have none. `all_spots` is `find_spots` plus the areas, and is what `main` and `--rehome` use.
  - `offer_lines` is the list the model reads: `- Market · Senso-ji temple (in Asakusa)` for a named spot
    inside a district, `- Market · Asakusa (area): Senso-ji temple and its five-storey pagoda, ...` for a
    district, with its description. The system prompt says to prefer the named spot a post is about and to
    choose an area when the post names the district, or is about what its description says, and no named
    spot fits.
  - `area_cell` picks the cell: the free one nearest the district's `stand` that is inside its `bounds`, on
    ordinary ground (`plain_cells`: not road, rail, a crossing, a stair or a bridge deck), in the open, not
    a doorway or the cell in front of one (`doorway_cells`: every transporter and its four neighbours, seams
    into the next district included), not on the room's edge row or column, and everything `walkable_near`
    asks (reachable, free for the whole stay, nobody walled in). Only when every such cell is taken does a
    road cell inside the bounds do (Shirakawa-go's far bank is a bus bay); never a stair, a deck or the track.
    `stand_cell` is the one place that knows an area from a landmark.
  - `--mock` with no steered spot answers with the district the post's text names (`named_area`: the longest
    name on offer that appears as a whole word), else the first spot as before; the real model reads the same
    names with their descriptions.
  - Room-scoped `LANDMARKS` rows for what a post about Asakusa or the palace names: `Senso-ji temple` (the
    foot of the main hall's steps), `the temple gate`, `the izakaya` (beside its door, not in front),
    `the Imperial Palace gate`, `the palace moat`.
  - `test_districts` in `tools/test_blog_to_npc.py` checks every district (in step with `districts.py`,
    inside its room, no overlap, seven authors each given a cell that is none of the above) and places a post
    whose text names "Asakusa" and nothing else. The rehearsal places one post that only names a district and
    one steered to a district, and its last lines say how many districts were offered.
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
  - `Sapporo · Odori Park` is a spot (hung on the park's hot-drinks tent, standing its visitor on the plaza beside the fountain; `rooms: ('Sapporo',)`): the six landmarks issue
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
  before #73, for posts about somewhere else, were moved this way (to the made-up towns of the time and to Market's 7-Eleven; every one of them has since moved again, to
  the real place it is about - see the stages below); the travel-day posts stay on their platforms. Stage 0 of the
  world rework (issue #68: real places only, laid out like Japan) moved eight more: Osaka, which had hosted
  no post, now tells its own (Damian's 768 at the Dotonbori arch, Bailey's 769 at Tsutenkaku Tower) and,
  until that town exists, the day trip that ends the day there (Nara 764 on the canal bank under the
  ferris wheel; Himeji's 754 stood in at Osaka's sakura trees too, until Himeji was built - issue #255
  moved it to `Himeji · Himeji Castle`, in front of the keep); the four October test / bug-report posts (382, 391, 396,
  406) left the vending machines of Machi, a made-up town, for Tokyo's. Stage 2 (issue #67) moved Fukuoka's eight to Fukuoka: 693 and
  750 to the yatai stalls, 719 and 746 to Hakata Station (both off the Tokyo platform or Market), 712 to Kushida
  shrine, 727 to Canal City, 731 to Fukuoka Tower and 740 to Dazaifu Tenmangu. Stage 3 (Hokuriku) moved
  fourteen to the place each is about: Toyama's 576 / 583 / 611, Shirakawa-go's 610 / 631, and Kanazawa's
  635, 642 (to Kanazawa Station's platform: the train ride there), 652, 653, 662, 669, 677, 686 and 707.
  Step 1 of the city redesign (issue #219) moved the four the audit found
  in the wrong place for want of labels, each checked against its post: Bailey's Senso-ji day (560, 1 Nov
  2025) from the palace pond to `Market · Senso-ji temple`, Julia's four Don Quijotes (545, 1 Nov) from the
  palace's vending machines to `Market · the Don Takote discount store`, Dylan's izakaya and karaoke night
  (549, 1 Nov) from a 7-Eleven to `Market · the izakaya`, and Damian's Hakata-to-Okayama shinkansen (745,
  12 Nov) from Tokyo's Park to `FukuokaStation · the platform`. A district is a target too:
  `--rehome Bailey 2025-11-01 "Market · Asakusa (area)"`.
  The cell is free for the
  whole stay (`occupied_during`: from that date until the NPC's next placement, or until a later trip or
  stay starts everyone from its base again — `trip_window`), not just on the day — history is not always
  written in date order — and `process_post` uses the same check.
  `test_blog_to_npc.py` also checks the shipped history: each NPC is in at most one room on any dated
  day, and no two share a cell.
