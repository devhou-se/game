# Title screen, new-player intro, dialogue portraits and post captions

The boot flow (title, creator, intro), How to Play, the dialogue portrait, the `from: <post>` caption and hand-drawn portrait art.

A "see X" in the text names a section; if it is not in this file, the index in [`../CLAUDE.md`](../CLAUDE.md) says which file has it.

### Title Screen and Character Portraits (issue #9)

**Title screen** (`src/TitleScreen.js`, `scene.titleScreen`): shown on every page load, after
`window.hideLoader()` and BEFORE the first-run character creator — `GameScene.create()` passes the rest of
the boot flow (the `CharacterCreator.shouldAutoShow()` check) as the `show(onStart)` callback. It draws the
game title (`config.game.title`), the devhouse members (`CharacterSelect.lineup()`, from `config.members`) lined up with a small hop
travelling along the line, and a blinking start prompt, at depth 9000 on an opaque backdrop the colour of
the HTML loader.
- SPACE / ENTER / ESC (so touch A and B too) or a tap/click anywhere dismisses it. While it is up it is
  **priority 0 in `InputHandler.handleInput()`**: no movement, menu or overlay input reaches the game.
  The triple-backtick debug chord is ignored too (`DebugManager.onBacktick` checks `titleScreen.isVisible()`).
- **`?notitle=1` skips it** — use it in tests and dev URLs that drive input straight after boot
  (the loader contract is unchanged: `#loader` is removed as before and the scene is live underneath).
- **In-game reloads skip it once**: `setGameDate()` (Time Travel / the HUD date) navigates with a full page
  load, so it sets the one-shot `sessionStorage` flag `gamev2_skip_title` first and `TitleScreen.shouldShow()`
  consumes it — a date hop lands straight back in the world, while a manual refresh of that URL shows the
  title again. Any future in-game action that reloads the page should set the same flag.

### New-Player Intro (issue #39)

`src/Intro.js` (`scene.intro`): a three-page overlay in the usual panel style (depth 2000-2003).
1. **Welcome to devhouse** (`Intro.welcomeCopy`, see Trips) — the friends: the members of the game date's
   trip (`Intro.cast` — `CharacterSelect.lineup` of that trip's `members`, alphabetical), drawn in the cast
   row above and named in the sentence under it (not `credits`, not James); which trip it is ("They are on devhouse 3 right now, in Hokkaido" while it is on, "This is
   devhouse 2, their trip to Japan" otherwise); NPC lines coming from the blog posts ("once they start
   writing" for a trip with no posts yet); and the HUD date picking the day ("Time Travel in the menu" to
   visit another day or another trip — the game always opens on a trip day, see the default game date
   under `npcs`). On a lead-in day it says when the trip starts instead, and in the real days before a
   trip it adds "devhouse 3 starts on February 18." (issue #164, see Trips).
2. **How to play** — move / sprint / interact / talk / menu drawn as keycaps (the interact row also
   lists what a bump starts: people, shops, trains, the izakaya); when
   `touchControls.enabled` the same rows are drawn as the on-screen d-pad, sprint pill and A / B buttons,
   plus a one-line keyboard reminder (the page is redrawn if the input in use changes while it is up).
3. **Where to start** — there is no quest system, so it points at real things: the friends (`whereFriendsAre()`
   → `Trips.whereText`: the ones in the room — the district, in a stitched city — the player is standing in are named — "Today Bailey, Damian
   and Julia are here in Machi, and Dylan is in Inaka.", "Today everyone is here in Sapporo." — and
   other rooms are listed by display name, three at most; whoever the player is playing as is not
   counted; on a lead-in day "They have not arrived yet: …", `Intro.meetCopy`), exploring, and Paint the Board (with the live progress bar from `achievementManager`).

Fishing controls and map travel are **deliberately absent** (fishing is learned when a rod is bought; map
travel is a debug feature) — keep them out when editing the copy.
- **Input**: SPACE / ENTER (touch A) or a tap anywhere turns the page and the last page closes it; ESC
  (touch B) skips the lot. It is the first entry in `InputHandler`'s overlay list, so nothing moves or
  opens underneath, and `DebugManager.onBacktick` ignores the debug chord while it is up.
- **Boot flow is strictly sequential, never stacked**: loader → title → (first visit) character creator →
  intro → world. `CharacterCreator.show({ onClose })` runs the callback once from `hide()` — confirmed or
  cancelled — and `GameScene.create()` uses it to open the intro.
- **Gate**: localStorage `gamev2_intro_seen`. `Intro.shouldAutoShow(firstVisit)` sets it to `pending` when a
  first visit begins (so a reload half way through the creator or the intro still gets the intro) and
  `hide()` sets it to `1` (finished or skipped). A returning player — a character already saved, key absent
  — is never shown it automatically, and a Time Travel reload does not replay it.
- **`?nointro=1`** suppresses the automatic showing (and leaves the gate untouched) — combine with
  `?notitle=1` in tests that start from a fresh profile. Tests that pre-seed `gamev2_character` never see it.
  NOTE: every profile, seeded or not, starts next to the cast of the game date (e.g. Machi 22,10 on
  2025-11-11) since #166 — there is no fixed Tokyo 29,38 spawn any more. A test that needs a known cell
  must pin the date (`?date=`) and read `Trips.startFor`, or move the player itself
  (`roomManager.switchRoomInstant`).
- **How to Play** in the ESC menu replays it at any time (`scene.intro.show()`). It is the only controls
  reference: the separate Controls menu entry and overlay (#38) were folded into page 2 (#55), so a new
  global binding or bump interaction is documented there.

**Dialogue portrait** (`DialogueManager.showPortrait`): the speaker is shown dating-sim style as a large
bust in the same wooden frame as the blog photo (`drawFrame`, shared by both), standing on the panel's
top-left corner with the name plate bridging frame and panel. The blog-photo frame keeps the top-right;
the two never overlap (20px gap) and share a bottom edge (`panelY - 12`). The bust is the head-and-shoulders band of `<name>_front_frame_0`
(`DialogueManager.BUST`, a 48x40 crop) at 5x in a 240x200 window. A speaker whose sprite is not a
directional `<name>_front` 64px character sprite falls back to the old look (`showFullSprite`: whole sprite
at 2x centred above the panel, name above it).

**Post caption** (issue #79): a dated state may carry `"posts": [{id, lines, title?, url?}, ...]` — which
blog post each run of its dialogue lines came from (`tools/blog_to_npc.py` writes it; same-day posts share
a state). `postForLine` in `src/utils/NpcStates.js` maps the line being said to its post, and
`DialogueManager.updatePostCaption` shows `from: <post title>` on a small plate straddling the panel's top
edge at its right end (under the blog photo when there is one), cut with an ellipsis at
`CAPTION_MAX_WIDTH`. It appears only when a title is recorded and the `lines` counts add up to the
dialogue — states placed before titles were kept show nothing, and nothing is invented for them. With a
`url` (http/https only) the caption is light blue and a click or tap on it opens the post in a new tab
instead of advancing; without one a click on it advances like the rest of the overlay. The link opens on
release, and only when the press began on that same link, so the release of a press that advanced the
dialogue never opens the next line's post; the hit area reaches `CAPTION_HIT_PAD` above and below the
plate for fingers. It adds no key
binding and changes no hint or panel size. `posts` belong to the dialogue they were written with:
`resolveNpc` clears them when a later state changes the dialogue without naming its own (same rule as
`voice`). The plumbing is `resolved.posts` → `NPCManager.spawnNPC` → `npc.posts`, exactly like `photo`;
`play.js` prints `from: <title> <url>` under an NPC's lines.
- **Recording**: the payload's `title` is always kept; `url` only if the payload has one (today's payload is
  `{post_id, title, author, date, content}` — the www-jp workflow has to add `url` for links to appear).
- **Backfill**: `python3 tools/blog_to_npc.py --backfill-posts posts.json [--dry-run]` fills title/url into
  existing states from a list of `{id, title, url}` (optionally `author`, `date`). A state is matched by
  its `posts` ids, else by its photo id (a photo is filed under its post's id), else by author + date when
  exactly one listed post fits; anything else is reported and left alone. No LLM call, no placement.
  The shipped states have not been backfilled (the post list lives in the www-jp repo: `site/content/<id>.md`
  front matter), so no caption shows in the live game yet.

**Real art drop-in, no code change**: put `assets/portraits/<name>.png` in place and add `<name>` to
`assets/portraits/manifest.json` (`{"portraits": ["bailey", ...]}`, shipped empty). `preload()` loads only
the listed names as textures `portrait-<name>` (so a character without art never 404s; a malformed
manifest is treated as empty; a listed name with no PNG logs one 404 and falls back to the sprite), and both the dialogue
frame and the title line-up use that texture instead of the sprite when it exists. Size/format rules are in
`assets/portraits/README.md` (240x200 window, 6:5; 240x200, 120x100 or 48x40 PNGs scale cleanly).
No hand-drawn portraits exist yet — everything shown today is derived from the overworld sprites.
