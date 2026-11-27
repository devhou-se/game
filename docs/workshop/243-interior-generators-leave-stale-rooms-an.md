# Design: the interior generators clean up after a removed building (#243)

## Context

An interior room belongs to a building in a town: `HouseAsahikawa2` to the second house of Asahikawa,
`ShrineFukuoka1` to a shrine hall, `KonbiniMarket3` to a 7-Eleven. When the building is taken out of the town
and the generators are re-run, three things are left behind today:

| Leftover | Where it comes from |
|---|---|
| `gamev2/tiled/<room>.tmj` of a room that no longer exists | `generate_houses.py` and `generate_pagodas.py` delete the room from `config.json` and nothing deletes its map |
| a `gk_blank` collider on the old door cell | `roomgen.shut_door` always writes one, also when the cell is now open ground or outside a resized room |
| the room itself, with no door into it | `generate_shrines.py`, `generate_konbinis.py` and `generate_discount_stores.py` never prune |

Buildings are numbered per town in (y, x) order, so removing one renumbers the rest and the leftover is the
highest-numbered room, not the one that was removed. The city redesign (#219) removes many houses, towers and
shrines, and each of these is deleted by hand.

The committed world is clean today (105 rooms, 105 maps, every interior reachable), so this change touches
**no room and no map**: it changes what the tools do the next time a building goes.

Outcome: after removing a building and re-running the town's generator (if it has one) and the interior
generator, `config.json` has no room for it, `tiled/` has no map for it, the host has no door and no collider
left on its old cell, and `check_generators.py` fails if a map and a room are ever out of step again.

## Approach

Three small pieces in `tools/roomgen.py`, used by every interior generator that numbers its rooms per town;
plus one more thing `check_generators.py` looks at.

1. **`shut_door` only seals a doorway that is still there.** It always drops the kind's transporter on the
   cell. It writes the collider only when a building of that kind still has its door on the cell
   (`house_door_at` with the kind's `OWNED_DOORS` sprites) and no other transporter is left on the cell. A
   house that is skipped, or the second door of a tower's pair, still stands, so it is sealed exactly as now and
   a re-run stays a no-op. A cell whose building is gone, a cell outside the room, and a doorway another kind
   now uses are left alone. It never removes a collider.
2. **`drop_stale`, a new helper run after a generator has built a host's rooms.** It shuts every door in the
   host that leads into a room of the generator's prefix from a cell the run did not just open, and deletes
   the rooms the run did not build. Working from the host's transporters rather than from the stale room's
   marker also catches the removed building's old door when renumbering has left it pointing into a live
   room (a ported host edited by hand, where no town generator rebuilt the transporter list), and needs no
   marker, so it serves konbinis and discount stores as they are.
3. **`save_config` deletes the map of every room that was loaded and is not saved.** One place covers
   houses, lobbies, shops, pagodas, shrines, konbinis, discount stores and any later generator, and
   `--dry-run` (which never saves) deletes nothing.
4. **`check_generators.py`** fails, under its `config_to_tiled` entry, for a `tiled/*.tmj` with no room and
   for a room with no map. Today it only regenerates the maps of rooms that have one, so neither is seen.

Konbini rooms get no ownership marker: their keys are `Konbini<Host><n>` and the generator has a fixed host
list, so a key pattern says whose a room is without rewriting 13 committed rooms.

`generate_discount_stores.py` is not named in the ticket but has the identical gap (`DonTakote<Host>`), and
the fix is the same three lines, so it is included. The single-building generators (palace, temple, pub,
distillery, mall, chikagai, devhouses) assert that their building exists, which is loud already; they are not
changed.

## Changes

### `gamev2/tools/roomgen.py`

- `load_config`: also record the room keys as loaded, in a module-level `_rooms_loaded` (a set, replaced on
  every load, like `_house_doors`).
- `save_config(cfg=None, path='config.json')`: after writing the config, for every key in `_rooms_loaded`
  that is not in `cfg['rooms']`, delete `<directory of path>/tiled/<key.lower()>.tmj` and print
  `deleted  tiled/<name>.tmj`. Skip a key whose lower-case name is also a live room's; ignore a file that is
  not there. **If `tiled` is a symlink, delete nothing** and print `kept     tiled/<name>.tmj (tiled is a
  symlink)`: eight test helpers link the committed `tiled/` into a scratch project and prune rooms there.
  Returns nothing, as now.
- `shut_door(host_room, cell, prefix)`, same signature:
  1. drop the transporters on `cell` whose `targetRoom` starts with `prefix` (as now);
  2. `sprites = OWNED_DOORS[prefix][1]` if the prefix has a row, else nothing (do not fall through to
     `house_door_at`'s house default);
  3. write `Colliders[cell] = pidx('gk_blank')` only if `sprites`, `house_door_at(host_room, x, y, sprites)`
     and no transporter remains on `cell`.
- New `drop_stale(cfg, host, prefix, opened, stale)`, beside `shut_door`; returns report lines:
  - for each transporter of `cfg['rooms'][host]` whose `targetRoom` starts with `prefix` and whose cell is
    not in `opened` (door cells, tuples or lists): `shut_door(room, cell, prefix)`, and a line
    `shut     <host> door (x, y) - it led into <target>; no <prefix> door is there now`;
  - for each key in `stale`: `del cfg['rooms'][key]`, and a line
    `removed  <key> - nothing in <host> claims it any more`, with `, and its NPCs went with it: <names>`
    when the room held any.
- Docstrings of all four say the above. `keep_house_doors` is not changed: a deleted room has no marker and a
  renumbered room's marker names its new cell, so it restores neither.

### `gamev2/tools/generate_houses.py` (houses, lobbies, shops)

In `apply`: remove the pre-build loop ("rooms of this town from an earlier run that no house claims any
more"). After the `for h in houses` loop:

```python
stale = [k for k, r in cfg['rooms'].items() if (r.get(marker) or {}).get('host') == host and k not in built]
lines += rg.drop_stale(cfg, host, prefix, [c for h in houses if h['key'] in built for c in h['doors']], stale)
```

The two `rg.shut_door` calls inside the loop (a skipped house, the unopened door of a pair) stay. `main`
already prints the lines and already skips `save_config` on `--dry-run`. Docstring: a removed building's room,
map and door go on the next run.

### `gamev2/tools/generate_pagodas.py`

Same replacement in its `apply(host)`: the pre-build prune loop goes, `rg.drop_stale(cfg, host, PREFIX,
<doors opened>, <rooms with the pagoda marker for host that were not built>)` follows the build loop and its
lines join the report. `tests/pagodas.test.js` asserts the source text `rg.shut_door(room, cell, PREFIX)`;
keep that call for skipped pagodas and unopened doors, or update the assertion if the line moves.

### `gamev2/tools/generate_shrines.py`

- `HOSTS = ARGS or wired_hosts()` becomes: the wired hosts, then any host named by a `shrine` marker that is
  not already listed (in `cfg['rooms']` order). A town that lost its only hall has no door left and is
  otherwise never visited. On the committed world the list is unchanged.
- After the build loop, before `save_config`, for each host in `HOSTS`:
  `rg.drop_stale(cfg, host, PREFIX, [doors of this host's halls], [k for k, r in cfg['rooms'].items() if
  (r.get('shrine') or {}).get('host') == host and k not in built])`; print the lines.

### `gamev2/tools/generate_konbinis.py`

After the build loop, for each host in `HOSTS`: `rg.drop_stale(cfg, host, 'Konbini', [doors of this host's
stores], [k for k in cfg['rooms'] if re.fullmatch(f'Konbini{re.escape(host)}\\d+', k) and k not in
new_rooms])`; print the lines. `Konbini` has no `OWNED_DOORS` row, so nothing is sealed: the old door cell
just loses its transporter. The legacy `cfg['rooms'].pop('Konbini', None)` stays (its map, if any, now goes
with it).

### `gamev2/tools/generate_discount_stores.py`

The same in `main`, with prefix `DonTakote` and stale keys matching `DonTakote<host>\d*`.

### `gamev2/tools/check_generators.py`

- New `unmatched_maps(root)`: `['tiled/x.tmj has no room in config.json: delete it', ...]` for each top-level
  `tiled/*.tmj` whose name is not a room key lower-cased, then `['room X has no tiled/x.tmj: run
  config_to_tiled.py X', ...]` for each room without one. `tiled/prefabs/` is not looked at.
- `check()`: when the name is `TILED`, put `unmatched_maps(root)` in front of that entry's differences (the
  entry fails if either list is non-empty). No new name in `CHECKS`, no new flag.
- A generator that deletes a map on an unchanged world already shows as `tiled/x.tmj REMOVED`: `check()`
  copies `tiled/` into its scratch project as a real directory.

### Docs

- `gamev2/docs/generators-and-checks.md`: `check_generators.py` (the two new failures); "Interior building
  blocks" layer 2 (`shut_door`'s rule, `drop_stale`, `save_config` deleting maps); "What a new interior has
  to decide" (a generator that numbers rooms per town calls `drop_stale`).
- `gamev2/docs/landmarks-and-towns.md`: House interiors (the sentence "which also deletes the rooms no house
  claims any more": and their maps, and the old door), "Konbini interiors per host", "Shrine worship halls"
  (removing one: re-run the generator; nothing to delete by hand).

## Data and interfaces

- No schema, config or palette change; no room, map or sprite changes. `config.json` and `tiled/` are
  byte-identical after the change.
- `roomgen.save_config` gains a side effect (deleting maps of dropped rooms, never through a symlink).
  `roomgen.shut_door` keeps its signature and seals less. `roomgen.drop_stale` is new.
  `check_generators.unmatched_maps` is new.
- Generator output gains `removed`, `shut` and `deleted` lines. After a prune the host's own map still needs
  `python3 tools/config_to_tiled.py <Host>`, which the generators already tell you to run.

## Tests

New `gamev2/tools/tests/stale-interiors.test.js`. Its scratch helper differs from the others: `tiled/` is a
real directory (copy the top-level `.tmj` files, link `tiled/prefabs`), `tools` and `assets` are links,
`config.json` is a copy. Each case edits the scratch config, runs the generator there and reads the result.

1. **Houses**: in a town with three or more houses, take the first house's door sprite out of Collidables
   and its transporter out of the host (what a town rebuild leaves), run `generate_houses.py <Town>`. The
   highest-numbered `House<Town><n>` and its map are gone, every other map is still there, the old door cell
   has no collider and no transporter, and every `House` door of the town leads to the room whose marker
   `door` is that cell.
2. The same with the transporter left in place (a ported host edited by hand): same result.
3. **Shrines**: remove Fukuoka's hall at door (38,30), run `generate_shrines.py Fukuoka`: `ShrineFukuoka2`
   and its map are gone, `ShrineFukuoka1`'s marker door is (47,48), Fukuoka has one `Shrine` door. Remove
   Asahikawa's only hall and its transporter, run with no argument: `ShrineAsahikawa1` and its map are gone.
4. **Konbinis**: remove Market's first 7-Eleven, run `generate_konbinis.py Market`: `KonbiniMarket6` and its
   map are gone and the five doors lead to `KonbiniMarket1`-`5` in (y, x) order. Remove Sapporo's only store:
   `KonbiniSapporo1` is gone.
5. **Discount stores**: remove Sapporo's store, run `generate_discount_stores.py Sapporo`:
   `DonTakoteSapporo` and its map are gone.
6. `generate_houses.py <Town> --dry-run` on case 1's config writes neither the config nor a map.
7. A second run after each prune changes nothing.
8. With `tiled` as a symlink, a prune leaves the linked map in place and says so.

Changed tests:

- `tests/generator-blocks.test.js`, the `shut_door` case: rewrite for the new rule with prefix `House` and a
  `building-entrance-1_0_0` sprite on the host. A standing door is sealed and its transporter dropped; with
  the sprite gone the transporter is dropped and no collider written; a cell that keeps another kind's
  transporter is not sealed (the old assertion "sealed, kept" described the bug); a cell outside the room
  gets nothing; an unknown prefix drops its transporter and seals nothing.
- `tests/check-generators.test.js`: `unmatched_maps` on a tmp project with one extra map and one room
  without a map names both, and returns `[]` for the committed world.
- `tests/pagodas.test.js`: the source-text assertion, if the line it quotes moved.

Run from `gamev2/`; all must pass, and `git status` must show no change under `config.json` or `tiled/`:

```bash
node tools/test_game.js
python3 tools/test_blog_to_npc.py
node tools/play.js check
python3 tools/check_generators.py
python3 tools/sync_cities.py --check
```

No browser is needed: nothing a player can see changes.

## Risks and open questions

- **`save_config` now deletes files.** It only deletes maps of rooms it loaded and no longer saves, under the
  config's own directory, and never through a symlink. The symlink rule exists for the tests; a test that
  wants deletion must use a real `tiled/`.
- **A pruned room's NPCs go with it.** None of these rooms holds an NPC today; the `removed` line names
  them. `generate_shrines.py` carries NPCs by room key, so after renumbering they stay with the key, not the
  hall (as before this change).
- **Transporters are matched by key prefix** (`House`, `Shrine`, `Konbini`, ...), as `shut_door` and
  `find_houses` already do. Verified on the committed world: all 70 such doors sit in their own host, on
  their room's marker cell.
- **Not cleaned**: a stray collider an earlier run already left in a map (it cannot be told from a wanted
  one; none is known); room keys quoted in docs or tests after a renumbering; a host room deleted outright
  (`generate_houses.py` stops with a `KeyError`, which is loud).
- **Order of a host's transporters** can differ from today's only in a run that actually prunes; the no-op
  run is unchanged, which `check_generators.py` confirms.
- No decision is needed from the owner. Including `generate_discount_stores.py` goes one generator beyond
  the three the ticket names; drop that section if it is not wanted.
