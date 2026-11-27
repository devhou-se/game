# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) and to any other agent working with code in this
repository. `AGENTS.md` sends agents that read that file here.

## Project Overview

The live game is the browser game in **`gamev2/`**, served at https://game.devhou.se. It is a 2D pixel-art
grid game built with Phaser, with no build step, in which blog posts from the devhouse trips become dated NPCs
you can walk up to and talk to.

**Read `gamev2/CLAUDE.md` before working on the game.** It is the real guide: architecture, the map and
world tooling, the blog-to-NPC pipeline, fonts, phones, trips, and the checks to run.

The original Godot 3.6 project that used to fill the repository root was removed in #229; it is in git
history (`README.md` names a commit that has it).

## Where things are

- `gamev2/` — the game: `index.html`, `src/` (JavaScript), `config.json` (rooms, NPCs, trips), `tiled/`
  (Tiled maps generated from the config), `assets/`, `tools/` (generators, checks, the blog pipeline),
  `studio/` and `editor/` (in-browser tools).
- `art-source/` — source art, not deployed: the GuttyKreum tile sheets that `gamev2/tools/extract_*.py` cut
  sprites from (purchased packs: do not copy them into `gamev2/`, which is published) and the team's Pixaki
  drawings. `art-source/README.md` says how to bring another sheet back from history.
- `devhouse.world` — the Tiled world file that places the rooms; `gamev2/tools/sync_cities.py` keeps it in
  step. `devhouse.tiled-project` opens `gamev2/tiled/` in Tiled.
- `.claude/skills/` — project skills for playing the game from a terminal and for generating or adjusting rooms.
- Blog posts come from the separate `devhou-se/www-jp` repository, whose workflows call the NPC pipeline here.

## Running and checking the game

```bash
cd gamev2
python3 -m http.server 8000        # then open http://localhost:8000
node tools/test_game.js            # unit tests, no browser
python3 tools/test_blog_to_npc.py  # blog pipeline tests
node tools/play.js check           # is the world still playable?
python3 tools/check_generators.py  # do the generators still reproduce the committed world? (needs Pillow)
python3 tools/sync_cities.py --check   # config cities and devhouse.world agree
```

Anything a player can see also needs the browser regression, `gamev2/tools/browser/regress.js`
(`gamev2/tools/browser/README.md`).

## Working on issues (read this before starting)

**`gamev2/docs/working-on-issues.md` is the full guide** to claiming an issue, not colliding with other agents,
running, checking, verifying as a player, landing and fixing. The short version:

- **Several agents push to `master` at once.** Work in your own git worktree
  (`git worktree add --detach ../game-<you> origin/master`), and fetch and rebase immediately before every push.
- **Claim an issue before you start**: add the `in-progress` label and comment who you are and which rooms or
  files you will touch. Do not take issues labelled `needs-decision`, `needs-art`, `blocked-external` or
  `parked`. When you finish or stop, comment what was done, how it was checked and what is left, and remove
  `in-progress`. Do not file follow-up issues unless the owner asks.
- **Map data is serial.** `gamev2/config.json` rooms and palette, `gamev2/tiled/`, town generators and
  `devhouse.world` conflict when two changes touch them. Only one agent rebuilds a given town at a time; check
  the other `in-progress` claims. Code-only and art-only work can run and land at any time.
- **All checks pass before a push** (below, plus the browser regression for anything a player can see), and the
  change is **verified by playing it** in a browser with real keys and touches, on desktop and a phone size,
  with screenshots looked at.
- **Watch the deploy** after each push and say so if it fails. Fix forward.

## Git Workflow

When making commits:
- Commit directly to master branch
- Use force push when needed, but never over commits that are not yours: fetch first, and if master has moved, rebase
- Do NOT include Claude attribution in commit messages
- Do NOT create pull requests
- Do NOT create feature branches (a pushed `wip/<issue>-<slug>` branch is allowed only to park unfinished work
  when you stop, and the issue must say so)
- One change per commit; the message is `gamev2: <what changed, in plain words> (#N)`
- Fetch and rebase onto `origin/master` immediately before pushing

## CI/CD Pipeline

- **Deploy GameV2 Canvas** (`.github/workflows/firebase-hosting-gamev2.yml`) deploys `gamev2/` to Firebase
  Hosting (project `devhouse-80936`, target `devhouse-game-canvas`) on every push to master that touches
  `gamev2/**` (or `firebase.json`, or the workflow itself), and can be run by hand. The run is green only if the live site serves the commit.
- **Checks** (`.github/workflows/checks.yml`) runs the five no-browser checks above on every push to master
  and every pull request that touches the game, the source art or `devhouse.world`. It has no Pillow, so the
  art tools are listed as `skip` there, and it does not gate the deploy.
