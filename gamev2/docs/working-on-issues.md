# Working on issues

How any agent (or person) picks up, builds, checks and lands work on this repository. Several agents work
here at once and all push to `master`, so the rules below are about not colliding and not breaking the live
site. The game rules themselves are in `../CLAUDE.md` and the topic files it indexes.

## 1. Issues: claim, label, report

Issues are in `devhou-se/game` (`gh issue list -R devhou-se/game`).

- **Claim before you start.** Add the `in-progress` label and post one comment:
  `Claimed by <who you are>. Touching: <rooms / files / "code only">.` Check first that the issue is not
  already `in-progress`, and read the latest comments: most open issues carry a status comment saying what is
  done and what is left.
- **Do not take** an issue labelled `needs-decision`, `needs-art`, `blocked-external` or `parked` unless the
  owner has answered on it. Each has a comment saying what it is waiting for.
- **One commit references its issue**: the message ends `(#N)`.
- **When you finish**: comment what changed, how it was checked and what was not checked, then close the issue
  only if everything it asks for is done. Otherwise remove `in-progress` and say what is left.
- **When you stop without finishing** (blocked, out of time): remove `in-progress`, say where the work is
  (a pushed `wip/<issue>-<slug>` branch is fine for that), and what the next person needs.
- **Do not file follow-up issues on your own.** Put what you noticed in your closing comment. File a new issue
  only when the owner asks for one. Big or unclear work is parked with a label and a comment, not started.
- A label always comes with a comment that says what is being waited for.

Labels: `in-progress` (someone is on it now), `needs-decision` (owner must choose), `needs-art` (needs drawn
assets), `blocked-external` (needs a key, a file or another repository), `parked` (set aside on purpose),
`devhouse-3` (needed for the February 2027 trip).

Standing owner decisions that override anything older in an issue:

- The game shows only current members. James is the default player sprite and never a member. Do not edit
  credits. Do not guess GitHub logins or looks for Khoi, Sam or Xander (#117).
- Only real places. No sealed buildings: every building a player can walk up to opens into something, except
  landmarks, which stay sealed.
- The city redesign (#219) is the full redesign, one city at a time. Where its plan disagrees with an earlier
  owner decision, the earlier decision stands (the list is in a comment on #219).

## 2. Not colliding with other agents

- **Work in your own git worktree**, not in a checkout another agent is using:
  `git worktree add --detach ../game-<you> origin/master`.
- **Map data is serial.** `gamev2/config.json` rooms and `tilePalette`, `gamev2/tiled/*.tmj`, town generators,
  `devhouse.world` and `gamev2/assets/map` conflict as soon as two changes touch them, because the palette is
  positional. So:
  - Only one agent rebuilds a given town at a time. Say which rooms you are touching in your claim comment and
    check the other `in-progress` claims first. As of 27 November 2026 the redesign lane is in **Sapporo**
    (#219), with the palace interior (#215, room `Tokyo`) and the removal of Machi, Inaka and Yukimura (#68)
    beside it.
  - A map change in a different room is fine, but expect to replay your data when master moves (below).
  - Do not add interiors to a town that is waiting for its redesign rebuild; its doors would be redone.
- **Code-only and art-only work never waits.** A change that touches no map data (source, tests, docs, new
  sprites and their art tool) can be built and landed at any time.
- **When master moved under a map change**: rebase; for `gamev2/config.json`, `gamev2/tiled/`, `devhouse.world`
  and `gamev2/assets/map` take master's side (`git checkout origin/master -- <paths>`), merge the source files
  by hand, then re-run your generators so the data is rebuilt on master's palette. Never hand-merge palette
  indices. Keep the commands you ran as a small script so the replay is one step.

## 3. Running the game

```bash
cd gamev2
python3 -m http.server 8000     # http://localhost:8000
```

Useful URL parameters: `?notitle=1&nointro=1`, `?date=YYYY-MM-DD`, `?tod=day|night`, `?touch=1`, `?stitch=0`.
`node tools/play.js help` plays the game as text with no browser (walk, talk, ride, inspect, `lint`, `render`,
`check`, `npcs`).

## 4. Checks before you push

From `gamev2/`, all must pass:

```bash
node tools/test_game.js                 # unit tests (about 90 s)
python3 tools/test_blog_to_npc.py       # blog pipeline
node tools/play.js check                # the world is playable on every trip day
python3 tools/sync_cities.py --check    # config cities and devhouse.world agree
/Library/Developer/CommandLineTools/usr/bin/python3 tools/check_generators.py   # needs Pillow
```

- Plain `python3` may have no Pillow; without it `check_generators.py` skips the art tools. Use an interpreter
  that has it and make sure the run reports `0 skipped`.
- After a map edit: `node tools/play.js lint <Room>` (0 errors) and look at
  `node tools/play.js render <Room> out.png`.
- After touching the blog pipeline, a town's landmarks, the trips or the cast: `python3 tools/rehearse_blog.py`.
- After changing what stands in a town: `python3 tools/check_distinct.py` must not report a city as worse;
  then `--update` the baseline in the same commit.
- Anything a player can see: run the browser regression, `tools/browser/regress.js` (how:
  `tools/browser/README.md`). It must print `20/20 checks passed` (the count grows; all must pass).
- If Node cannot start in a sandbox, set `OPENSSL_CONF=/dev/null`.

## 5. Verifying as a player

Tests passing is not the bar; the change working for a player is.

- Drive the real game in a browser with **real key presses and real touches**, not by calling game functions:
  walk to the thing, bump it, open it, leave. Use `tools/browser/browser.js` (`open`, `ready`, `hold`) for
  scripts; one shared headless Chrome, never one per script.
- Check a desktop size (1280x960) and a landscape phone (844x390, touch). For HUD or text changes also 667x375
  and a portrait phone (390x844).
- Check by day and at `?tod=night`, and on a trip date when cast or towns are involved
  (`?date=2027-02-20` is devhouse 3 in Sapporo; `2025-10-27` to `2025-11-16` is devhouse 2).
- In Tokyo or Hokuriku check both the stitched city and `?stitch=0`.
- **Look at screenshots.** For art and maps, open the render or the screenshot and judge it honestly: does it
  read as the place, does anything float, can you walk behind or inside a building.
- No console or page errors.
- Say in your issue comment what you verified and, separately, what you did not.

## 6. Tests and docs are part of the change

- Add or extend a unit test for logic you change (`tools/tests/<area>.test.js`, found by name; a duplicate test
  name is an error). Pull a decision out of a Phaser class into a static function so it can be tested.
- When behaviour changes on purpose, update the assertion that pins it **strictly**. Never loosen an assertion
  to make a change pass, and never delete a failing test without saying why in the commit.
- Document a new system in its topic file under `gamev2/docs/`; add a line to the index in `gamev2/CLAUDE.md`
  only for a new file.

## 7. Landing

- Commit on `master`, one change per commit, message `gamev2: <what changed, in plain words> (#N)`. No
  attribution lines, no pull requests, no long-lived branches.
- **Fetch and rebase immediately before pushing**, re-run the checks if master moved, then push. Other agents
  and `dylan-botler[bot]` push to master during the day.
- A change that touches camera, city stitching, the trips or date model, input routing, the save blob, the blog
  pipeline, or more than about six source files gets an independent review before it lands: a second agent
  that plays the change and reads the diff. Small fixes and art-only commits land on green checks.
- Every push that touches `gamev2/**` deploys to game.devhou.se (workflow "Deploy GameV2 Canvas"). **Watch the
  run** (`gh run list -R devhou-se/game --workflow "Deploy GameV2 Canvas" -L 3`) and say so if it fails.

## 8. When something is broken

- **A check fails on master before your change**: say so on the issue, find the commit (`git log`,
  `git bisect`), and fix forward in its own commit. Do not build on a red master.
- **Your change broke something after landing**: fix forward with a new commit that says what it repairs and
  names the commit it follows. Revert only if the fix is not quick, and say so on the issue.
- **A deploy failed**: read the run log before retrying; a root-only commit (nothing under `gamev2/`) does not
  deploy and that is expected.
- **A generator no longer reproduces the world** (`check_generators` fails): the generator is the source of
  truth for a generated room. Fix the generator or re-run it; do not hand-edit its output and leave it failing.
  Ported Tokyo rooms have no generator; their Tiled map is the source of truth.
- **Reviewer findings**: fix what blocks; list what you noticed and left alone in the issue comment.
