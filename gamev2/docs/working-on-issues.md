# Working on issues

How any agent (or person) picks up, builds, checks and lands work on this repository. Several agents work
here at once and everything ends up on `master`, which deploys, so the rules below are about not colliding
and not breaking the live site. The game rules themselves are in `../CLAUDE.md` and the topic files it indexes.

## Two ways work lands

Work reaches `master` in one of two ways. Find out which one you are in before you start; the sections below
say where they differ, and everything else (the checks, verifying as a player, tests and docs, the commit
message) is the same in both.

- **By hand.** A person or an agent they are running picks an issue, claims it, commits on `master` in their
  own worktree and pushes. No feature branches, no pull requests. This is the workflow unless you were told
  otherwise.
- **Workshop.** Workshop is the automated pipeline that takes a ticket through design, implementation and
  code review, one unattended agent per stage. You are in it if your instructions say so; the checkout is
  then already on a branch named `workshop/<n>-<slug>` cut from `master`. You commit on that branch and stop:
  Workshop pushes it, opens and updates the pull request, labels the ticket and posts your summary. You do not
  push, switch branches, open a pull request, or label, comment on or close the issue yourself, and you
  usually could not (the container has no GitHub access). Where Workshop's instructions for the run and this
  file disagree, Workshop's instructions win.

## 1. Issues: claim, label, report

Issues are in `devhou-se/game` (`gh issue list -R devhou-se/game`).

**Under Workshop** the ticket is claimed for you and its `workshop/*` labels are the claim, so skip the
claiming, labelling and commenting below. The summary you return takes the place of the closing comment: say
what changed, how it was checked, what was not checked and anything you noticed outside the ticket (Workshop
may raise a ticket from that; do not work on it). If you cannot go on without an owner decision, stop and
return your questions instead of guessing. A larger ticket has a design file, `docs/workshop/<n>-<slug>.md`,
to follow; small ones normally have none. The rest of this section is for work by hand, except the commit
reference and the standing owner decisions, which hold for everyone.

- **Claim before you start.** Add the `in-progress` label and post one comment:
  `Claimed by <who you are>. Touching: <rooms / files / "code only">.` Check first that the issue is not
  already `in-progress`, and read the latest comments: most open issues carry a status comment saying what is
  done and what is left.
- **Do not take** an issue labelled `needs-decision`, `needs-art`, `blocked-external` or `parked` unless the
  owner has answered on it. Each has a comment saying what it is waiting for.
- **Do not take an issue that Workshop has.** Labels starting `workshop/` (its stage, its size, whether it is
  running) are set and removed by Workshop; leave them alone, and treat an issue that carries a
  `workshop/stage:*` label as claimed unless the owner hands it to you.
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
`devhouse-3` (needed for the February 2027 trip), `workshop/*` (Workshop's own, above).

Standing owner decisions that override anything older in an issue:

- The game shows only current members. James is the default player sprite and never a member. Do not edit
  credits. Do not guess GitHub logins or looks for Khoi, Sam or Xander (#117).
- Only real places. No sealed buildings: every building a player can walk up to opens into something, except
  landmarks, which stay sealed.
- The city redesign (#219) is the full redesign, one city at a time. Where its plan disagrees with an earlier
  owner decision, the earlier decision stands (the list is in a comment on #219).

## 2. Not colliding with other agents

- **Work in your own git worktree**, not in a checkout another agent is using:
  `git worktree add --detach ../game-<you> origin/master`. Under Workshop the checkout is already yours alone,
  on the ticket's branch: stay on it.
- **Map data is serial.** `gamev2/config.json` rooms and `tilePalette`, `gamev2/tiled/*.tmj`, town generators,
  `devhouse.world` and `gamev2/assets/map` conflict as soon as two changes touch them, because the palette is
  positional. So:
  - Only one agent rebuilds a given town at a time. Say which rooms you are touching in your claim comment and
    check the other `in-progress` claims first. As of 27 November 2026 the redesign lane is in **Sapporo**
    (#219), with the palace interior (#215, room `Tokyo`) and the removal of Machi, Inaka and Yukimura (#68)
    beside it.
  - A map change in a different room is fine, but expect to replay your data when master moves (below).
  - Do not add interiors to a town that is waiting for its redesign rebuild; its doors would be redone.
  - Under Workshop you cannot read the claims. Build on the `origin/master` you were given and name the rooms
    and map data you touched in your summary, so whoever merges the pull request can see what it collides
    with. A map pull request that master has moved under is replayed the same way (below) before it merges.
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

There is no build to work on the game. What players get is a build of it (one script file and three packs
of the JSON and images; "Loading and the deploy build" in `architecture.md`), which the deploy makes. To play
that one, for a change to what the game loads or to the build itself:

```bash
node tools/build_dist.js            # writes ../dist (not committed)
cd ../dist && python3 -m http.server 8001
```

## 4. Checks before you push

From `gamev2/`, all must pass (under Workshop: before you return your result, since Workshop does the push):

```bash
node tools/test_game.js                 # unit tests (about 90 s)
python3 tools/test_blog_to_npc.py       # blog pipeline
node tools/play.js check                # the world is playable on every trip day
python3 tools/sync_cities.py --check    # config cities and devhouse.world agree
/Library/Developer/CommandLineTools/usr/bin/python3 tools/check_generators.py   # needs Pillow
```

- Plain `python3` may have no Pillow; without it `check_generators.py` skips the art tools. Use an interpreter
  that has it and make sure the run reports `0 skipped`. Where there is none: a venv with
  `pip install -r tools/requirements-art.txt` (PNGs are compared by their pixels, so the art check runs on any
  machine; `generators-and-checks.md`).
- After a map edit: `node tools/play.js lint <Room>` (0 errors) and look at
  `node tools/play.js render <Room> out.png`.
- After touching the blog pipeline, a town's landmarks, the trips or the cast: `python3 tools/rehearse_blog.py`.
- After changing what stands in a town: `python3 tools/check_distinct.py` must not report a city as worse;
  then `--update` the baseline in the same commit.
- Anything a player can see: run the browser regression, `tools/browser/regress.js` (how:
  `tools/browser/README.md`). It must print `20/20 checks passed` (the count grows; all must pass).
  A change to what the game loads, to `index.html`'s script list or to `tools/build_dist.js` runs it against
  the built game too (a served `dist/`). On a slow
  machine that runs out of its 80 seconds, `REGRESS_TIME_SCALE=2` stretches the time limits and no assertion.
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
- Say in your issue comment (under Workshop, your summary) what you verified and, separately, what you did not.
- A Workshop container may have no browser. Then run everything that needs none, say in your summary what a
  player-visible change still needs checked, and ask for the ticket to get the `workshop/needs:browser` label.

## 6. Tests and docs are part of the change

- Add or extend a unit test for logic you change (`tools/tests/<area>.test.js`, found by name; a duplicate test
  name is an error). Pull a decision out of a Phaser class into a static function so it can be tested.
- When behaviour changes on purpose, update the assertion that pins it **strictly**. Never loosen an assertion
  to make a change pass, and never delete a failing test without saying why in the commit.
- Document a new system in its topic file under `gamev2/docs/`; add a line to the index in `gamev2/CLAUDE.md`
  only for a new file.

## 7. Landing

In both workflows: one change per commit, message `gamev2: <what changed, in plain words> (#N)`, no
attribution lines.

**Under Workshop:**

- Commit on the ticket's `workshop/<n>-<slug>` branch and leave it there. Do not push or open the pull
  request: Workshop pushes the branch and opens the pull request, with your summary as its description, and
  its Code reviewer stage reads the change before the owner merges it. That covers the diff-reading half of the
  independent review below; playing the change stays with your own verification (the `workshop/needs:browser`
  label gives the run a browser) or the owner before merging.
- Merging the pull request is the push to `master`, so the deploy below runs then. You cannot watch it; the
  person who merges does. The "Checks" workflow below runs on the pull request as a second signal.

**By hand:**

- Commit on `master`. No pull requests, no long-lived branches.
- **Fetch and rebase immediately before pushing**, re-run the checks if master moved, then push. Other agents
  and `dylan-botler[bot]` push to master during the day, and Workshop's pull requests are merged into it.

**In both workflows:**

- A change that touches camera, city stitching, the trips or date model, input routing, the save blob, the blog
  pipeline, or more than about six source files gets an independent review before it lands: a second agent
  that plays the change and reads the diff. Small fixes and art-only commits land on green checks.
- Every push that touches `gamev2/**` deploys to game.devhou.se (workflow "Deploy GameV2 Canvas"): the run
  builds `dist/` with `tools/build_dist.js` and publishes that. **Watch the
  run** (`gh run list -R devhou-se/game --workflow "Deploy GameV2 Canvas" -L 3`) and say so if it fails.
- A browser keeps what it has loaded. The game asks for its scripts, `config.json`, the Tiled maps and the
  manifests with a `?t=` cache-buster, and `firebase.json` serves every PNG with `Cache-Control: no-cache`, so
  the art is re-checked on each load and a redrawn sprite shows on the next reload (issue #241: the fixed
  sprite was live, and a browser drew the old one from its cache for up to an hour). The pages (`index.html`,
  which holds the list of scripts to load, and the Studio's and the editor's) and the fonts are served with
  the same header (issue #250), so a deploy that adds a script reaches a returning browser on its next load.
  Anything else asked for by a fixed URL (the editor's stylesheet, a voice clip) keeps the host's default of
  an hour.
- The "Checks" workflow (`.github/workflows/checks.yml`) runs the five checks of section 4 on every push to
  master and every pull request that touches the game. It installs the Pillow pinned in `tools/requirements-art.txt`, so it checks
  the art tools too (all but the two that need a Japanese system font, which it lists as `skip`),
  and it does not gate the deploy: it is a second signal, not a replacement for running the checks yourself.

## 8. When something is broken

Under Workshop, "say so on the issue" below means say so in your summary.

- **A check fails on master before your change**: say so on the issue, find the commit (`git log`,
  `git bisect`), and fix forward in its own commit. Do not build on a red master.
- **Your change broke something after landing**: fix forward with a new commit that says what it repairs and
  names the commit it follows. Revert only if the fix is not quick, and say so on the issue.
- **A deploy failed**: read the run log before retrying; a root-only commit (nothing under `gamev2/`) does not
  deploy and that is expected. A failed "Build the published site" step means the game asks for a file that is
  not there, or loads one without going through `Assets` (`node tools/build_dist.js` says which). Do not run
  `firebase deploy` by hand without running the build first: it publishes whatever is in `dist/`.
- **A fix has landed and someone still sees the old thing**: compare what the live site serves with the commit
  before changing anything (`curl -s https://game.devhou.se/<path> | cmp - gamev2/<path>`). If they match, the
  browser is showing a cached file (section 7).
- **A generator no longer reproduces the world** (`check_generators` fails): the generator is the source of
  truth for a generated room. Fix the generator or re-run it; do not hand-edit its output and leave it failing.
  Ported Tokyo rooms have no generator; their Tiled map is the source of truth.
- **Reviewer findings**: fix what blocks; list what you noticed and left alone in the issue comment.
