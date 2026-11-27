# Slow loading: a deploy build that bundles the scripts and packs the assets (#244)

## Context

The game has no build step: `gamev2/` is published as it is. A boot makes about **1,309 requests** — 52
scripts, 111 JSON files (`config.json` 3.0 MB, 105 `tiled/*.tmj` 4.7 MB), about 1,143 images (1,041 sprites,
52 photos, 44 ads, 6 others) and 3 fonts — 3.7 MB over the wire. Scripts, `config.json` and the maps carry a
`Date.now()` cache-buster, so a return visit downloads 589 KB again; Time Travel reloads the page
(`NpcStates.js:258`), so that cost is paid in play too. On Android, Phaser loads only 6 files at a time.

Firebase Hosting already serves Brotli, HTTP/2 and ETags, and `create()` takes about 0.4 s. The time goes on
the number of requests (latency × count) and on per-file loader overhead.

Measured here (headless Chrome, software WebGL, CDP throttling; seconds from navigation to the title screen;
"after" is a prototype of this design in a scratch copy, served with Brotli and the headers below):

| Network                             | Today cold | Today warm | After cold | After warm |
|-------------------------------------|-----------:|-----------:|-----------:|-----------:|
| 4G (150 ms, 9 Mbps), Android phone  |       38.4 |        8.3 |        3.5 |        1.5 |
| 4G (150 ms, 9 Mbps), desktop        |       10.7 |        5.2 |        3.5 |        1.7 |
| Cable (28 ms, 5 Mbps)               |        9.6 |        5.5 |        4.9 |        1.5 |
| Unthrottled                         |        5.5 |        5.5 |       ~2.2 |            |

Outcome: the deployed game boots in about ten requests, a return visit downloads only `index.html` (a 304),
and nothing a player sees changes except the wait. Working on the game is unchanged: open `gamev2/index.html`
from a static server, no build. No map data (`config.json`, `tiled/`, `devhouse.world`) is touched.

## Approach

- **A build at deploy time only.** `gamev2/tools/build_dist.js` (node, no dependencies) writes `dist/` at the
  repository root, and Firebase publishes `dist/` instead of `gamev2/`. `dist/` is not committed: committed
  packs would be binary merge conflicts between agents, and the `www-jp` blog pipeline commits
  `gamev2/config.json` and photos directly and cannot be made to rebuild them. `dist/` is a full copy of
  `gamev2/` (the studio, the editor and a loose fallback keep working) plus generated files in `dist/pack/`
  and a rewritten `dist/index.html`.
- **One script bundle**: the 52 files concatenated in `index.html`'s order. No minifier (the tools have no
  dependencies; Brotli takes 820 KB to 207 KB).
- **Three packs, not 1,250 files.** `data.<hash>.json` holds every JSON file preload asks for, parsed
  (3.6 MB, 212 KB Brotli) and an index of the two binary packs; `images.<hash>.bin` is the image files
  preload asks for, end to end (1.5 MB); `photos.<hash>.bin` the NPC photos (0.9 MB). The game hands Phaser
  the parsed JSON objects and `blob:` URLs of slices of the binary packs, so **texture keys, frames and every
  consumer stay exactly as they are**. A GPU texture atlas was rejected for this ticket: the game is built on
  one texture per sprite key (RoomManager, animations, CharacterCreator's pixel reads) and atlases bleed under
  zoom.
- **Photos load after the title screen is up**, in both modes. They are 38% of the image bytes, are seen
  only in a dialogue, and a new blog post should not invalidate the sprite pack. `DialogueManager` already
  shows no photo when the texture is missing.
- **The build packs what the game asks for.** It runs the game's own `preload()` code in a node `vm` with a
  recording loader, so there is no second list of assets to keep in step. (This leaves out 521 sprite PNGs,
  768 KB, that no `spriteMetadata` entry names.)
- **Content-hashed names, cached for ever.** `/pack/**` gets `immutable`; `index.html` gets `no-cache`
  (revalidated, a 304 when unchanged). The `Date.now()` busters remain only in the unbuilt game.
- **Preload hints** in the built `index.html` start both boot packs while Phaser and the bundle are still
  downloading (0.17 s instead of 0.93 s on 4G; Chrome reuses the response for Phaser's request).
- **Loader settings** (both modes): `maxParallelDownloads: 32` (Phaser's desktop default; Android's 6 cost
  2 s even with packs) and `imageLoadType: 'HTMLImageElement'` (skips an XHR-to-blob hop per image; halves
  the load phase at zero latency).

## Changes

Work in this order; each step leaves the checks green. Suggested commits: one per numbered step,
`gamev2: <what> (#244)`.

1. **The game loads through `Assets`; photos load after boot; loader settings.**
   - `gamev2/src/utils/Assets.js` (new; in `index.html`'s list before `SpriteSystem.js`; add it to
     `tools/test_game.js`'s load list if the tests need it) — see Data and interfaces.
   - `gamev2/src/GameScene.js`: split `preload()`.
     - `preload()` keeps the progress handler, the three `load.font` calls (plain URLs) and the
       `JapaneseFont.load` hook, then: if `window.GAME_BUILD`, `load.json('pack-data', build.data)` and
       `load.binary('pack-images', build.images)`; when both `filecomplete-*` events have fired,
       `Assets.install(...)` then `this.queueAssets()`. If either fails (`loaderror` for those keys), call
       `queueAssets()` once without installing: the loose files are in `dist/`. Without `GAME_BUILD`, call
       `queueAssets()` directly.
     - `queueAssets()` is the rest of today's body with every path wrapped: `load.json(key, Assets.json(path))`
       and `load.image(key, Assets.url(path, bust))`; `bust` is true where there is a `?t=` on an image today
       (`japan.png`, item icons, portraits). `?maps=config` still skips the `.tmj` files. The photo loop
       moves out.
     - `queuePhotos(config)` is the photo loop (`photo-<id>` ← `Assets.url('assets/photos/<id>.png')`).
       `loadPhotos()`, called at the end of `create()` after `hideLoader()`: packed → `load.binary` of
       `build.photos`, on its `filecomplete` `Assets.installPhotos(buffer)` and `queuePhotos`; loose →
       `queuePhotos`; then `this.load.start()`. It must not move the loader bar or call `JapaneseFont.load`
       again (the existing hook is `once`).
     - Progress: `updateLoader` already keeps a high-water mark. Packed: 0.7 × the download fraction of
       `pack-images` (`fileprogress`) + 0.3 × the loader's `progress`; loose: as today.
     - On each loader `complete`, `Assets.release()`; after the boot pass also remove `pack-data` and
       `pack-images` from the caches.
   - `gamev2/src/systems/SpriteSystem.js` `loadSpriteAssets`: its three URLs go through `Assets.url`.
   - `gamev2/src/game.js`: `loader: { maxParallelDownloads: 32, imageLoadType: 'HTMLImageElement' }`.
2. **The build.**
   - `gamev2/index.html`: `<!-- build:head -->` as the first line inside `<head>`; the script-list block
     between `<!-- build:scripts -->` and `<!-- /build:scripts -->`. The list keeps its `'src/X.js',` form
     (tests read it).
   - `gamev2/tools/build_dist.js` — `node tools/build_dist.js [--out <dir>] [--commit <sha>]`, run from
     `gamev2/`; default out `../dist`, default commit `git rev-parse HEAD` or `dev`. Exports
     `build({ out, commit, copy = true })`. It:
     1. refuses an `out` that is the repository root, `gamev2/` or inside `gamev2/`; empties and recreates it;
     2. if `copy`, copies `gamev2/` into it, skipping dotfiles, `node_modules` and `__pycache__`;
     3. reads the script list between the markers and writes the files in order, each under a `// src/<file>`
        line and joined with `\n;\n`, to `pack/game.<hash>.js`;
     4. records the loads: a `vm` context with `Phaser = { Scene: class {} }`, a recording `Assets`
        (`json`/`url` note the path and return it) and a stub `load` (`on`, `once`, `font`, `image`,
        `spritesheet`, `json`; `json` reads the file and fires `filecomplete-json-<key>`), `textures.exists`
        false; load `SpriteSystem.js` and `GameScene.js`, run `queueAssets()` then `queuePhotos(config)`.
        Fail the build if a recorded file is missing or if an image or JSON path did not come through `Assets`;
     5. writes `pack/images.<hash>.bin`, `pack/photos.<hash>.bin` (files in sorted path order), then
        `pack/data.<hash>.json` (format below); `<hash>` is the first 12 hex digits of the file's SHA-256;
     6. writes `index.html`: `<!-- build:head -->` becomes
        `<link rel="preload" as="fetch" crossorigin href="pack/data.<hash>.json">` and the same for the images
        pack; the scripts block becomes
        `<script>window.GAME_BUILD = {"commit":…,"data":…,"images":…,"photos":…};</script>` and
        `<script src="pack/game.<hash>.js"></script>`.
     The same inputs and commit give byte-identical output.
   - `.gitignore`: `dist/`.
3. **The deploy publishes the build.**
   - `firebase.json`: `"public": "dist"` and the headers below.
   - `.github/workflows/firebase-hosting-gamev2.yml`: after checkout, `actions/setup-node@v4` (node 24, as
     in `checks.yml`) and `node tools/build_dist.js --commit "$GITHUB_SHA"` with `working-directory: gamev2`.
     Both verify steps `cmp` against `dist/index.html` (it carries the commit, so the check now holds for
     every commit). The authoritative step also fetches the `data` pack URL named in `dist/index.html` with
     `curl -sfI` and fails unless `cache-control` contains `immutable`. Path filters unchanged.
   - `gamev2/tools/tests/repo-layout.test.js`: the hosting assertion becomes `'dist'`, plus the header rules.
4. **Docs**: `README.md` (line 8, Pipelines), root `CLAUDE.md` (overview, CI/CD), `gamev2/CLAUDE.md` ("No
   Build Process", the new-JS-files rule, a rule that every load in the scene goes through `Assets`),
   `gamev2/docs/architecture.md` (`Assets.js` in the file map; a short "Loading and the deploy build"
   section, with its row in `gamev2/CLAUDE.md`'s index), `gamev2/docs/working-on-issues.md` and
   `gamev2/tools/browser/README.md` (how to build and serve `dist/` to check the built game). They say: no
   build to develop; the deploy builds `dist/`; a manual `firebase deploy` needs the build first.

## Data and interfaces

`Assets` (global, like the other `utils`):

- `Assets.json(path)` → the parsed object from the pack, else `` `${path}?t=${Date.now()}` ``. Phaser's
  `load.json` accepts either.
- `Assets.url(path, bust = false)` → a `blob:` URL (type `image/png`) of the file's slice of the images or
  photos pack, else `path` (with `?t=` if `bust`). Blob URLs it makes are remembered.
- `Assets.install(data, buffer)`, `Assets.installPhotos(buffer)`; `Assets.release()` revokes the remembered
  blob URLs and drops the buffers and the JSON map (it keeps the photos index until the photos are installed).

`window.GAME_BUILD = { commit, data, images, photos }` — the last three are URLs relative to `index.html`.
Set only in the built `index.html`; its absence is the unbuilt game.

`pack/data.<hash>.json`:
`{ "json": { "<path>": <parsed JSON> }, "images": { "<path>": [offset, length] }, "photos": { … } }`, paths
as the game writes them (`config.json`, `tiled/tokyo.tmj`, `assets/sprites/x.png`).

`firebase.json` hosting entry (site and `ignore` unchanged):

```json
"public": "dist",
"headers": [
  { "source": "/pack/**", "headers": [{ "key": "Cache-Control", "value": "public, max-age=31536000, immutable" }] },
  { "source": "/", "headers": [{ "key": "Cache-Control", "value": "no-cache" }] },
  { "source": "/index.html", "headers": [{ "key": "Cache-Control", "value": "no-cache" }] }
]
```

Everything else keeps Firebase's one-hour default. No change to `config.json`, saves or URLs players use.

## Tests

- New `gamev2/tools/tests/build.test.js` (builds into a temp directory with `copy: false`, removes it after):
  the built index has no `src/` script tag and no `Date.now`, and names exactly the files in `pack/`; file
  names match their content hashes; the bundle has every listed file once, in order, and compiles
  (`new vm.Script`); every packed JSON deep-equals its source and every image and photo slice is byte-equal to
  its file; the recorder saw 3 fonts and nothing else outside `Assets`; photos are only in the photos pack and
  every `npc.photo` is there; two builds are identical; a bad `--out` is refused.
- `Assets` cases (same file or its own): unbuilt → busted path / plain path; installed → the object and a
  blob URL per call (stub `URL.createObjectURL`); `release()` revokes them.
- Source `index.html` has both markers and the list between them; existing `includes('src/X.js')` tests pass.
- Run from `gamev2/`: `node tools/test_game.js`, `python3 tools/test_blog_to_npc.py`,
  `node tools/play.js check`, `python3 tools/check_generators.py`, `python3 tools/sync_cities.py --check`.
- Browser (needs the `workshop/needs:browser` label): `tools/browser/regress.js` against `gamev2/` **and**
  against a served `dist/`. In the built game check by hand, desktop and a phone size: no console errors;
  each pack requested once; a dialogue with a photo shows it; reload is served from cache; `?maps=config`
  boots; with `pack/` deleted from a copy of `dist/` the game still boots from the loose files.
- After the merge, on the live site: the response headers of `/` and a `/pack/` file, and a cold and a warm
  load on a real phone.

## Risks and open questions

- **Not checkable here**: Firebase's header globs and the real network. The workflow's `immutable` check
  catches a rule that does not match; the fallback is the default one-hour cache, never a broken game.
- **Preload reuse was measured in Chrome only.** If Safari or Firefox fetch a pack twice, drop the hints
  (they are worth about 0.7 s on 4G) rather than tune them.
- **The built and unbuilt games differ in how they load.** The recorder test and running the regression on
  both keep them together; a load added outside `Assets` fails the build test.
- **Concatenation**: no file uses `'use strict'` or relies on being its own script today; the `vm.Script`
  test and the regression on `dist/` cover it.
- **A photo can be missing** from a dialogue opened in the first second after the title screen on a slow
  connection; it appears the next time. Accepted.
- **An open tab across a deploy** keeps working (everything is in memory after boot; the photos pack of the
  old release may 404, which only means no photos until reload).
- A manual `firebase deploy` without the build publishes a stale or missing `dist/`; the docs say so.
- The `www-jp` pipeline is unaffected: it commits under `gamev2/`, and the deploy that follows builds.
- Left out on purpose: a texture atlas (would remove the last ~1 s of per-image decode and upload),
  minification, and deleting the 521 unused sprite files.
