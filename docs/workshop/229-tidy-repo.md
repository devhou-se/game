# Tidy repo: remove the Godot project, leave gamev2 as the repository (#229)

## Context

The live game is `gamev2/` (Phaser, no build step, deployed to game.devhou.se). The repository root still
holds the retired Godot 3.6 project around it: about 18,700 of 20,871 tracked files (`Assets/` 16,820,
`.import/`, `.mono/`, `Scenes/`, `Scripts/`, `addons/`, `TeamFolders/`, the C# solution, Godot-era scripts and
docs, a retired deploy workflow). `gamev2/` depends on it in exactly one way: seven `tools/extract_*.py` art
tools cut sprites from 14 tile sheets (1.1 MB) and one Godot tileset file under `Assets/`.

Outcome: the root holds the game, its source art, the Tiled world files, deploy config and docs, and nothing
else; docs and pipelines describe what is there; the checks run in CI. Nothing a player sees changes, and no
map data (`gamev2/config.json`, `gamev2/tiled/`, `devhouse.world`, `gamev2/assets/`) is touched.

## Approach

- **`gamev2/` stays where it is; the root is emptied around it.** Hoisting it to the root would break the
  `game-npc-pipeline` workflow in `devhou-se/www-jp` (it checks this repository out, runs from `gamev2/` and
  commits `gamev2/config.json`, `gamev2/assets/photos`, `gamev2/assets/voice`; it cannot be changed from here),
  every branch in flight, and several hundred `gamev2/...` paths in docs, skills and tests, for no gain to the
  player. So `devhouse.world`, `devhouse.tiled-project`, `firebase.json` (`public: gamev2`) and the deploy
  path filter keep their paths.
- **Source art moves to `art-source/` at the root, trimmed to what is used.** It stays outside `gamev2/`
  because everything under `gamev2/` is published by the deploy and the sheets are purchased GuttyKreum packs.
  Only the 14 sheets the tools read are kept (plus the packs' `Readme.txt`); the rest of the packs remain in
  git history. Being a sibling of `gamev2/`, the tools' cwd-relative paths change only in the directory name.
- **The team's own Pixaki drawings are kept** (`some-assets/`, 546 files, 2.8 MB) as `art-source/pixaki/`:
  they are original work, not Godot. `Assets/some-assets/` is a strict subset of it (checked by hash) and goes.
- **`extract_shrine.py` stops reading the Godot tileset**: the two crop boxes it looked up in
  `Assets/Tilemap/GuttyKreum.tres` become constants in the tool.
- **The Godot porting tools go with the project** (`doport.py`, `render_godot.py`, `render_rect.py` read
  `Scenes/*.tscn`); `autotile.py` stays (`config_to_tiled.py` imports it).
- **A Checks workflow** runs the five no-browser checks on pushes and pull requests. Today nothing runs them.
- History is not rewritten. The last commit that has the Godot project is recorded in the README.

## Changes

Work in this order; each step leaves the checks green. Suggested commits: one per numbered step,
`gamev2: <what> (#229)`.

### 1. Source art

Before starting, note `BASE=$(git merge-base HEAD origin/master)`; it is the "last commit with the Godot
project" quoted in the READMEs below.

- `git mv` these from `Assets/GuttyKreum/` to `art-source/GuttyKreum/`, same relative path (bytes unchanged):
  - `DotonboriCity_v3/RPGMakerVXAce/GK_DB_F.png`, `DotonboriCity_v3/RPGMakerVXAce/GK_DB_B.png`
  - `Osaka_V5/RPGMakerVXAce/GK_Osaka_C_2.png`
  - `JapaneseCity_Complete_v7_1/RPGMakerVXAce/GK_JC_C_2.png`, `.../GK_JC_B_2.png`
  - `TemplesandShrinesv2/RPGMakerVXAce/GK_TS_A5.png`, `TemplesandShrinesv2/MainTileMap/MainTileMap.png`
  - `TemplesShrines_v2/Non-RPGMaker_Tilemap/Main_Tilemap.png`
  - `UrbanAccessoriesv2/Tilemap.png`
  - `Train_Stationv8/Tilemaps/Non-RPGMaker/Maintilemap.png`
  - `TrainInteriors_v1/preview1.png`, `preview2.png`, `preview3.png`, `TrainInteriors_v1/RPGMakerVXAce/GK_TI_A5.png`
  - and `Readme.txt` of `DotonboriCity_v3`, `JapaneseCity_Complete_v7_1`, `Osaka_V5`, `TemplesShrines_v2`,
    `Train_Stationv8`, `UrbanAccessoriesv2` (the packs' terms).
- `git mv` `some-assets/Pixaki/*` and `some-assets/711 - style 1.pixaki` into `art-source/pixaki/`; delete
  the `*.import` files among them.
- Add `art-source/README.md`: what the folder is (the sheets `gamev2/tools/extract_*.py` cut from; purchased
  packs, not deployed, not to be redistributed; `pixaki/` is the team's drawings), and how to bring another
  sheet back: `git show <BASE>:Assets/GuttyKreum/<pack>/<file> > art-source/GuttyKreum/<pack>/<file>`, then
  add it to the list in `gamev2/tools/tests/repo-layout.test.js`.
- `gamev2/tools/extract_city.py`, `extract_dotonbori.py`, `extract_house_interior.py`, `extract_station.py`,
  `extract_street.py`, `extract_train.py`, `extract_train_interior.py`: `../Assets/` becomes `../art-source/`
  in the path constants and docstrings. No other change.
- `gamev2/tools/extract_shrine.py`: remove `TRES` and `tile_source()`. Add
  `GK = '../art-source/GuttyKreum/'`, `ROOF_ATLAS = GK + 'TemplesandShrinesv2/MainTileMap/MainTileMap.png'`,
  and make `SPRITES = {'shrine-top_0_0': ('shrine-top', (1888, 96, 2048, 288), (1920, 160, 2016, 352))}`
  (display name, crop box, box of `shrine-building` beneath it; these are the values the tileset held).
  `ATLAS = GK + 'TemplesShrines_v2/Non-RPGMaker_Tilemap/Main_Tilemap.png'`. `main()` uses them; the
  "widen tile" message and the docstring name the constants instead of the tileset. Output must not change.
- `gamev2/tools/check_generators.py` (`check()`, and the comment above `ART_TOOLS`): the scratch symlink is
  `art-source` instead of `Assets` (`source_art = .../'..'/'art-source'`; `os.symlink(source_art, top/'art-source')`).
- `gamev2/tools/generate_house_art.py`, `extract_house_interior.py` docstrings: "no pack in ../Assets" becomes
  "none of the GuttyKreum packs".
- Add the first test of `repo-layout.test.js` (see Tests).

### 2. Remove the Godot project and what only served it

`git rm -r` (nothing below is read by `gamev2/` after step 1):

- `Assets/` (the rest), `.import/`, `.mono/`, `Scenes/`, `Scripts/`, `addons/`, `TeamFolders/`, `some-assets/`
  (what is left), root `tools/`
- `project.godot`, `export_presets.cfg`, `icon.png`, `icon.png.import`, `game.sln`, `game.csproj`,
  `game.sln.DotSettings.user`, `Folder.DotSettings.user`, `Directory.Build.props`, `generate_grid.py`,
  `generate_single_tile.py`
- `PROJECT_STRUCTURE.md`, `GIT_GUIDE_FOR_BEGINNERS.md`, `docs/integration-setup-guide.md`,
  `docs/integration-readme.md` (after step 4 moves its current part)
- `.github/workflows/firebase-hosting-merge.yml`, `.firebase/` (a tracked deploy cache)
- `gamev2/tools/doport.py`, `render_godot.py`, `render_rect.py`; `gamev2/CLEANUP_SUMMARY.md`,
  `gamev2/REFACTORING_COMPLETE.md` (stale one-off reports); `gamev2/tools/__pycache__/` (17 tracked `.pyc`
  that every check run dirties; `git rm --cached`)

Root afterwards: `.claude/`, `.github/`, `art-source/`, `docs/workshop/`, `gamev2/`, `.firebaserc`,
`.gitignore`, `AGENTS.md`, `CLAUDE.md`, `README.md`, `devhouse.tiled-project`, `devhouse.world`, `firebase.json`.

### 3. Config and pipelines

- `.gitignore`, replaced: `.DS_Store`, `.idea/`, `__pycache__/`, `*.pyc`, `node_modules/`, `.firebase/`,
  `.playwright-mcp/`.
- `firebase.json`: drop the `devhouse-80936` / `public` entry (the Godot export). `hosting` stays an array
  with the one `devhouse-game-canvas` / `gamev2` entry, unchanged.
- `.github/workflows/firebase-hosting-gamev2.yml`: add `firebase.json` and the workflow's own path to
  `on.push.paths`. Nothing else.
- New `.github/workflows/checks.yml`, name `Checks`: on `push` to `master`, `pull_request` and
  `workflow_dispatch`; push and pull_request filtered to `gamev2/**`, `art-source/**`, `devhouse.world`,
  `.github/workflows/checks.yml`. One job on `ubuntu-latest`, `actions/checkout@v4`, `actions/setup-node@v4`
  (node 24), `actions/setup-python@v5` (3.13), working directory `gamev2`, one step per check:
  `node tools/test_game.js`, `python3 tools/test_blog_to_npc.py`, `node tools/play.js check`,
  `python3 tools/check_generators.py`, `python3 tools/sync_cities.py --check`. Pillow is deliberately not
  installed: the art check compares PNG bytes, which differ between Pillow versions, so on the runner the art
  tools are listed as `skip` (exit 0). Say so in a comment. It does not gate the deploy.

### 4. Docs

- `README.md` (root, now one line), rewritten for people: what the game is and the link; run it
  (`cd gamev2 && python3 -m http.server 8000`); the five checks; layout (`gamev2/`, `art-source/`,
  `devhouse.world` + `devhouse.tiled-project`, `.claude/skills/`, `docs/workshop/`); where to read next
  (`CLAUDE.md`, `gamev2/CLAUDE.md`, `gamev2/docs/`); deploy and Checks workflows; blog posts come from
  `devhou-se/www-jp`; one History line: the Godot project was removed in #229 and is in history at `<BASE>`.
- `CLAUDE.md` (root): remove the Godot paragraph and the "do not delete `Assets/`" rule (one sentence instead:
  removed in #229, in history); add `art-source/` to "Where things are"; in CI/CD drop the retired workflow
  and add Checks; the `AGENTS.md` sentence becomes "`AGENTS.md` sends agents that read that file here".
  The git workflow section is not changed.
- New `AGENTS.md`: a few lines pointing at `CLAUDE.md` and `gamev2/CLAUDE.md` as the rules for every agent.
  (`CLAUDE.md` says it exists; it never did. A pointer cannot drift from the rules.)
- `gamev2/docs/blog-pipeline.md`: new first section "How a post becomes an NPC", moved from the "How it works
  today" part of `docs/integration-readme.md` (the www-jp workflow, text, photo, voice, placement, runtime,
  secrets, the two test commands); drop its Godot paragraphs. `gamev2/CLAUDE.md`: add that title to the
  `blog-pipeline.md` index row.
- `gamev2/tiled/README.md`: "Porting more Godot .tscn maps" becomes "Seeding a room's map from config" and
  keeps the `config_to_tiled.py` and `play.js lint` steps; one sentence says the four Tokyo districts were
  ported once from the Godot project with tools that were removed with it (#229). Delete the
  `Scenes/osaka/osaka_outside.tscn` gotcha. The shrine note says the roof's rect is in `tools/extract_shrine.py`.
- `gamev2/docs/landmarks-and-towns.md`: delete the "legacy `Scenes/osaka/...`" sentence; `../Assets` becomes
  the GuttyKreum packs. `gamev2/docs/buildings-and-street-props.md`: `../Assets/GuttyKreum` becomes
  `../art-source/GuttyKreum`. `gamev2/docs/generators-and-checks.md`: one sentence that the `extract_*` tools
  read `../art-source`. `gamev2/docs/working-on-issues.md` section 7: one line that the Checks workflow runs
  on every push and pull request.
- Comments that name removed files are reworded to "the Godot port" (history stays, the pointer goes):
  `gamev2/tools/autotile.py`, `config_to_tiled.py`, `generate_tsutenkaku.py`, `generate_osaka.py`,
  `gamev2/editor/core/Config.js`.

## Data and interfaces

- No change to `config.json`, `tiled/`, `devhouse.world`, `devhouse.tiled-project`, any sprite, save data or
  URL. `gamev2/` paths are unchanged, so the www-jp pipeline is unaffected.
- New directory contract: `art-source/GuttyKreum/<pack>/...` is what `extract_*.py` reads as
  `../art-source/...` from `gamev2/`; `check_generators.py` links it beside its scratch copy.
- `firebase.json` declares one site. The `Deploy GameV2 Canvas` workflow and its secret are unchanged.

## Tests

New `gamev2/tools/tests/repo-layout.test.js` (same shape as `madeup-towns.test.js`; found by name):

1. *The source art the extract tools name is in art-source (#229)*: with `SHEETS` = the 14 paths above,
   the `.png` files under `../art-source/GuttyKreum` are exactly `SHEETS`; in every `tools/extract_*.py`,
   each quoted string that ends in `.png`, contains `/` and does not start with `assets/` is, once a leading
   `../art-source/GuttyKreum/` is stripped, a member of `SHEETS`; each sheet's basename appears in at least
   one extract tool; `check_generators.py` contains `'art-source'`.
2. *Nothing points at the removed Godot project (#229)* (lands with step 4): `project.godot`, `game.sln` and
   `.github/workflows/firebase-hosting-merge.yml` do not exist; `AGENTS.md` exists; no `.py`, `.js`, `.md`,
   `.html` under `gamev2/` (not `node_modules`, not this test file), nor root `CLAUDE.md`, `AGENTS.md`,
   `README.md`, `firebase.json`, `.claude/skills/*/SKILL.md`, `.github/workflows/*.yml`, matches
   `/\bAssets\b|Scenes\/|\.tscn|\.tres|doport|render_godot|render_rect|parse_godot|PORT_SCENE|project\.godot|some-assets|TeamFolders/`.
   (`art-source/README.md` and `docs/workshop/` are out of scope: they quote the old paths on purpose.)

Run, from `gamev2/`, all green (they were on this branch before the change: 317 passed / ok / no problems /
room and map checks ok / 7 rooms in sync):

```bash
node tools/test_game.js && python3 tools/test_blog_to_npc.py && node tools/play.js check \
  && python3 tools/check_generators.py && python3 tools/sync_cities.py --check
```

The art tools need Pillow, which the container lacks; `python3 -m venv /tmp/pv && /tmp/pv/bin/pip install pillow`
works. `check_generators.py` under that Pillow reports byte `DRIFT` even before this change (encoder
differences), so verify pixels instead, before and after: copy `gamev2/` and `art-source/` side by side into a
temp directory, run the seven tools `extract_dotonbori`, `extract_shrine`, `extract_street`, `extract_train`,
`extract_train_interior`, `extract_station`, `extract_house_interior` there, and compare every
`assets/sprites/*.png` with the committed one as decoded RGBA, and `config.json` as parsed JSON. Expected,
as measured on the base: all seven exit 0, 0 sprites differ in pixels, config data equal. This is what proves
the inlined shrine boxes. `extract_city` also needs a Japanese system font and cannot run here; test 1 covers
its paths. Report the result in the summary.

Also confirm `git status` is clean after running the checks (no tracked `.pyc` left), and
`git diff --stat origin/master -- gamev2/config.json gamev2/tiled gamev2/assets devhouse.world` is empty.
No browser run is needed: nothing a player can see changes.

## Risks and open questions

- **Clone size does not shrink**: the 106 MB of art stays in history. Rewriting history is out of scope.
- **Branches in flight** that edit `check_generators.py`, the docs above or `.gitignore` get small textual
  conflicts; none of the data files are touched. Land this between map changes, not across one.
- **The Checks workflow cannot be run from the pipeline's container**; its first run is on the pull request.
  The five commands pass here on Linux with node 24 and python 3.13 without Pillow, which is what it pins.
- **The old Firebase site `devhouse-80936`** keeps serving the last Godot build until it is disabled in the
  Firebase console; that is the owner's to do.
- **On the owner's machine** a byte-exact `check_generators.py` with the usual Pillow should still report `ok`
  for the `extract_*` tools, since the sheets are moved unchanged; worth one run after merge.
- Choices made here that the owner may want otherwise (none blocks the work):
  1. `gamev2/` is not hoisted to the root (reasons in Approach). Doing it later needs a change in www-jp first.
  2. The unused GuttyKreum sheets, `Modern_Exteriors`, `Tiles` and the other Godot art leave the tree
     (recoverable from `<BASE>`); the Pixaki drawings stay.
  3. `CLAUDE.md` and `working-on-issues.md` still say "commit to master, no pull requests" while Workshop
     works on branches and pull requests. Not changed here.
  4. Checks do not gate the deploy; a red Checks run is a signal, the deploy still goes out.
