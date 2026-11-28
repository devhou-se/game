# art-source

Source art for the game in `gamev2/`. Nothing here is loaded by the game or deployed with it: the deploy
publishes `gamev2/` only.

## `GuttyKreum/`

The tile sheets that `gamev2/tools/extract_*.py` cut sprites from (they read them as `../art-source/...`,
run from `gamev2/`). They come from GuttyKreum's Japanese pixel-art packs, which were bought for this project.
The author's terms (`Licence.txt` of the Halloween pack, in history, see below): the packs may be used and
modified in free and commercial projects, and may **not be redistributed or resold**. So do not copy these
sheets into `gamev2/` (everything there is published) or anywhere else; only the sprites the tools cut from
them ship.

Only the 14 sheets a tool reads are kept, with each pack's `Readme.txt`:

| Sheet | Read by |
|---|---|
| `DotonboriCity_v3/RPGMakerVXAce/GK_DB_F.png` | `extract_dotonbori.py` |
| `DotonboriCity_v3/RPGMakerVXAce/GK_DB_B.png` | `extract_city.py` |
| `Osaka_V5/RPGMakerVXAce/GK_Osaka_C_2.png` | `extract_city.py` |
| `JapaneseCity_Complete_v7_1/RPGMakerVXAce/GK_JC_C_2.png` | `extract_city.py` |
| `JapaneseCity_Complete_v7_1/RPGMakerVXAce/GK_JC_B_2.png` | `extract_street.py`, `extract_house_interior.py` |
| `TemplesandShrinesv2/RPGMakerVXAce/GK_TS_A5.png` | `extract_street.py` |
| `TemplesandShrinesv2/MainTileMap/MainTileMap.png` | `extract_shrine.py` (the shrine roof) |
| `TemplesShrines_v2/Non-RPGMaker_Tilemap/Main_Tilemap.png` | `extract_shrine.py` (the garland rope), `generate_sendai_art.py` (the roof of Zuihoden) |
| `UrbanAccessoriesv2/Tilemap.png` | `extract_street.py` |
| `Train_Stationv8/Tilemaps/Non-RPGMaker/Maintilemap.png` | `extract_train.py`, `extract_station.py` |
| `TrainInteriors_v1/preview1.png`, `preview2.png`, `preview3.png` | `extract_train_interior.py` |
| `TrainInteriors_v1/RPGMakerVXAce/GK_TI_A5.png` | `extract_house_interior.py` |

`gamev2/tools/tests/repo-layout.test.js` checks that this folder holds exactly the sheets the tools name.

### Bringing another sheet back

The rest of the packs (and the other art of the old Godot project: `Assets/Modern_Exteriors_RPG_Maker_MV`,
`Assets/Tiles`, `Assets/sprites`, ...) were removed from the tree in #229 and are in git history: commit
`b5697496` has them all. To use another sheet:

```bash
git ls-tree -r --name-only b5697496 -- Assets/GuttyKreum/<pack>/      # what the pack holds
mkdir -p "art-source/GuttyKreum/<pack>/<dir>"
git show "b5697496:Assets/GuttyKreum/<pack>/<dir>/<file>.png" > "art-source/GuttyKreum/<pack>/<dir>/<file>.png"
```

Keep the path it had under `Assets/GuttyKreum/`, then add it to `SHEETS` in
`gamev2/tools/tests/repo-layout.test.js` and to the table above.

## `line-art/`

The line drawings of three landmarks, as they were the game's sprites before #70: `tokyo-station_0_0.png`
(2624x512), `tokyo-tower_0_0.png` (512x960) and `tsutenkaku_0_0.png` (512x832). Black lines, white fill, one
red (the tower's centre panel, Tsutenkaku's sign), pixel-doubled. They are the old sprites byte for byte:

```bash
git show 422b40ec:gamev2/assets/sprites/<key>.png > art-source/line-art/<key>.png
```

`gamev2/tools/generate_tokyo_art.py` and `gamev2/tools/generate_tsutenkaku.py` paint them (through
`gamev2/tools/line_art.py`, which reads them as `../art-source/line-art/...`, run from `gamev2/`): the game's
sprite is the drawing with colour laid on, its outline and lines unchanged (#271;
`gamev2/tools/tests/landmark-placeholders.test.js` compares the two). The Tokyo two are the team's Pixaki
drawings doubled: `pixaki/Landmarks/Tokyo Station.pixaki/images/preview.png` cropped at (32,32) and
`Tokyo Tower.pixaki/images/preview.png` cropped at (32,0). Tsutenkaku's was drawn by an earlier
`generate_tsutenkaku.py`. A change to one of these changes its sprite's outline, so it must still fit the
map: the same test holds the sprites to what Palace, Park and Osaka rely on.

## `pixaki/`

The team's own drawings, made in Pixaki: characters (front, back and side views), landmarks (Tokyo Station,
Tokyo Tower), konbini fronts and signs, a pavement tile. Each `*.pixaki` folder is one document
(`document.json`, its layer images and a cached preview). They are original work, kept as source; no tool
reads them.
