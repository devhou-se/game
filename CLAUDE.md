# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

The live game is the browser game in **`gamev2/`**, served at https://game.devhou.se. It is a 2D pixel-art
grid game built with Phaser, with no build step, in which blog posts from the devhouse trips become dated NPCs
you can walk up to and talk to.

**Read `gamev2/CLAUDE.md` before working on the game.** It is the real guide: architecture, the map and
world tooling, the blog-to-NPC pipeline, fonts, phones, trips, and the checks to run.

The repository root also holds the original **Godot 3.6** project (`project.godot`, `Scenes/`, `Scripts/`,
`Assets/`, `game.sln`). It is legacy: it is no longer built or deployed, and nothing in `gamev2/` runs it.
`gamev2/` still reads art from `Assets/` through its asset tools, so do not delete or reorganise that folder.
Leave the rest of the Godot project alone unless you are asked to work on it.

## Where things are

- `gamev2/` — the game: `index.html`, `src/` (JavaScript), `config.json` (rooms, NPCs, trips), `tiled/`
  (Tiled maps generated from the config), `assets/`, `tools/` (generators, checks, the blog pipeline),
  `studio/` and `editor/` (in-browser tools).
- `devhouse.world` — the Tiled world file that places the rooms; `tools/sync_cities.py` keeps it in step.
- `.claude/skills/` — project skills for playing the game from a terminal and for generating or adjusting rooms.
- Blog posts come from the separate `devhou-se/www-jp` repository, whose workflows call the NPC pipeline here.

## Running and checking the game

```bash
cd gamev2
python3 -m http.server 8000        # then open http://localhost:8000
node tools/test_game.js            # unit tests, no browser
python3 tools/test_blog_to_npc.py  # blog pipeline tests
node tools/play.js check           # is the world still playable?
python3 tools/check_generators.py  # do the generators still reproduce the committed world?
```

## Git Workflow

When making commits:
- Commit directly to master branch
- Use force push when needed
- Do NOT include Claude attribution in commit messages
- Do NOT create pull requests
- Do NOT create feature branches

## CI/CD Pipeline

- **Deploy GameV2 Canvas** (`.github/workflows/firebase-hosting-gamev2.yml`) deploys `gamev2/` to Firebase
  Hosting (project `devhouse-80936`, target `devhouse-game-canvas`) on every push to master that touches
  `gamev2/**`, and can be run by hand. The run is green only if the live site serves the commit.
- **Deploy Godot Game (retired)** (`firebase-hosting-merge.yml`) is manual-dispatch only and is kept in case
  the old Godot build is ever needed.
