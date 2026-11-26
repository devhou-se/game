# Hand-off notes (26 Nov 2026) — delete this folder before the branch lands

This branch is issue #218 (San Franbourne, two airports, the flight) as built and self-verified by its
implementer on master 8bdc34ac. It has NOT been rebased onto current master, reviewed or landed.

To finish it:
1. Rebase onto master. `gamev2/config.json`, `gamev2/tiled/`, `devhouse.world` and `gamev2/assets/map` will
   conflict (the tile palette is positional): take master's side for those paths, resolve the source
   conflicts by hand (likely `tools/generate_stations.py`, `tools/check_generators.py`,
   `tools/generate_konbinis.py`, `src/utils/Interactions.js`, `tools/tests/japan-map.test.js`,
   `tools/tests/hud-phone-layout.test.js`, `tools/roomgen.py`), then replay the map data with
   `sanfranbourne_apply.sh <checkout root>`.
2. Run the five checks in gamev2/CLAUDE.md plus `tools/browser/regress.js`.
3. One review as a player (Tokyo Station -> Haneda -> flight -> the city and back), then land and close #218.

The other scripts here replay or roll out map data and were only on one laptop:
- `lobbies_apply.sh <Town>...`  tower lobbies (#216); Osaka is done.
- `shrines_apply.sh <Room>...`  shrine worship halls (#212); Tokyo, Market, Park are done.
- `houses_apply.sh <Town>...`   house interiors (#208); six towns are done.
- `kanazawa_apply.sh`           the Kanazawa region (#68), already on master; kept for reference.
They were written to be run from a private `.agent-queue/items/` folder: check the paths at the top of
each before running.

`city-redesign-plan.md` is the full audit and plan behind the reply on #210.
