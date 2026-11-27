# [DEVHOU.SE!!!](https://devhou.se) — the game

The devhouse game: a 2D pixel-art grid game in the browser, played at **https://game.devhou.se**. You walk
around Tokyo, Osaka, Hokkaido and the other places the devhouse trips went to, and the blog posts written on
those trips are the people you meet: every post puts its author somewhere in the world on its date, with
something to say.

It is built with [Phaser](https://phaser.io) and has no build step: the game is the files in `gamev2/`.

## Run it

```bash
cd gamev2
python3 -m http.server 8000        # then open http://localhost:8000
```

`?notitle=1&nointro=1` skips the title and the intro; `?date=YYYY-MM-DD` picks the game date.
`node tools/play.js help` plays it in a terminal, with no browser.

## Check it

From `gamev2/`, with Node and Python 3 (nothing to install):

```bash
node tools/test_game.js                 # unit tests, no browser
python3 tools/test_blog_to_npc.py       # the blog pipeline
node tools/play.js check                # the world is still playable
python3 tools/check_generators.py       # the generators still rebuild the committed world (art tools need Pillow: tools/requirements-art.txt)
python3 tools/sync_cities.py --check    # config cities and devhouse.world agree
```

Anything a player can see also has a browser regression: `gamev2/tools/browser/README.md`.

## What is where

| Path | What it is |
|---|---|
| `gamev2/` | The game: `index.html`, `src/` (JavaScript), `config.json` (rooms, NPCs, trips), `tiled/` (the maps), `assets/`, `tools/` (generators, checks, the blog pipeline), `studio/` and `editor/` (in-browser tools), `docs/` |
| `art-source/` | Source art that is not deployed: the tile sheets the `gamev2/tools/extract_*.py` tools cut sprites from, and the team's Pixaki drawings (`art-source/README.md`) |
| `devhouse.world`, `devhouse.tiled-project` | The [Tiled](https://www.mapeditor.org) world and project files: open the project to edit the maps in `gamev2/tiled/` |
| `.claude/skills/` | Agent skills for playing the game from a terminal and for generating or adjusting rooms |
| `docs/workshop/` | Design notes written for individual issues |
| `firebase.json`, `.firebaserc`, `.github/workflows/` | Hosting config and the two workflows below |

## Read next

- `CLAUDE.md`: the rules for working in this repository (`AGENTS.md` points to it).
- `gamev2/CLAUDE.md`: the guide to the game, with an index of the topic files in `gamev2/docs/`.
- `gamev2/docs/working-on-issues.md`: picking up an issue, checking and landing a change.

## Pipelines

- **Deploy GameV2 Canvas** (`.github/workflows/firebase-hosting-gamev2.yml`) publishes `gamev2/` to Firebase
  Hosting on every push to `master` that touches it. The run is green only if the live site serves the commit.
- **Checks** (`.github/workflows/checks.yml`) runs the five checks above on pushes and pull requests. It does
  not gate the deploy.
- Blog posts come from the separate [`devhou-se/www-jp`](https://github.com/devhou-se/www-jp) repository:
  its `game-npc-pipeline` workflow runs `gamev2/tools/blog_to_npc.py` here and commits the new NPC
  (`gamev2/docs/blog-pipeline.md`).

## History

The game began as a Godot 3.6 project that filled this repository's root. It was retired when `gamev2/` went
live and removed in #229; it is all in git history, at commit `b5697496`.
