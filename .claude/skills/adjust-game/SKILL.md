---
name: adjust-game
description: Make a specific requested change to the gamev2 world — "replace room X with Y", "I don't like building X, use Y instead", "move the pond", "remove those lanterns", "the plaza is too big", "swap the torii", "put the shop somewhere else". Surgical counterpart to generate-room; makes exactly the stated adjustment (and its collision/door/transporter consequences), nothing else. Use whenever the user expresses dissatisfaction with, or requests a change to, an existing room, object, NPC, connection, or world layout.
---

# Adjust the game world as specified

You are making a TARGETED change to the Phaser game in `gamev2/` (run
everything from that directory). The prime directive: **make the change the
user asked for, exactly, and nothing else** — then prove both halves (the
change landed; nothing else moved).

## 1. Find the source of truth for what's changing

This decides HOW you edit. Getting it wrong either loses the change on the
next regen or breaks determinism.

- **Generated rooms** (a `tools/generate_<slug>.py` mentions the room — grep
  for the room name in `tools/`): edit the GENERATOR script, re-run it, and
  regenerate the room's `.tmj`. Never hand-edit config.json for these; a
  re-run would wipe your change. NPC changes for these rooms go in the
  generator too (`rg.make_npc(..., states=...)`), not `npc_state.py`.
- **Ported rooms** (Tokyo, Market, Park, Palace — no generator): config.json
  is the map source; edit it with a small python script (serialization is
  ALWAYS `json.dumps(cfg, indent=2, sort_keys=True)`, NO trailing newline),
  then `python3 tools/config_to_tiled.py <Room>`.
- **Prefab art/collision/doors** (`tiled/prefabs/*.tmj`, seeded by
  `tools/make_prefabs.py`): change the spec in make_prefabs.py and re-run it
  (keeps the file regenerable), then re-run every generator that stamps that
  prefab. Ported rooms don't use prefabs — their objects are edited in place.
- **NPCs** in ported rooms: `tools/npc_state.py` for dated changes; direct
  config edit for base fields.
- **Connections/doors**: transporters live in each room's config AND its
  `.tmj` Meta layer — the game reads the TMJ, so regenerate the `.tmj` of
  EVERY room whose transporters you touch.
- **World layout** (`devhouse.world` at repo root): map offsets in pixels,
  64px cells; keep connecting roads aligned across seams; interiors stay out.

## 2. Locate every instance before editing

Objects are sprites + colliders + sometimes doors/transporters, spread across
layers. Find them all first:

```python
import json
cfg = json.load(open('config.json'))
pal = cfg['tilePalette']
key = lambda i: pal[i] if isinstance(i, int) else i
for rk, r in cfg['rooms'].items():
    for L in r['layers']:
        hits = [(xy, key(i)) for xy, i in L['tiles'].items()
                if key(i).startswith('<family>')]
        if hits: print(rk, L['name'], L.get('collision'), hits)
```

When removing/moving/replacing an object, its gk_blank colliders move with it
— collision must keep matching the visuals (invisible walls and walk-through
objects are the two classic failure modes; both have happened in this repo).
Removing a prefab-stamped object in a generated room = remove the
`b.stamp(...)` call; everything (sprites, colliders, doors) goes with it.
If sprite sizes differ when swapping A→B, re-anchor so the FEET line up
(bottom rows), not the top-left.

## 3. Make the change, then prove minimality

- Apply the edit (generator change + re-run, or config edit script).
- `git diff --stat` and eyeball the actual diff: does it touch ONLY what the
  request implies? For generated rooms, the generator re-run must reproduce
  everything else byte-identically — any unexpected churn means your edit has
  side effects; fix before proceeding.
- Requested-change checklist: if the user said "replace X with Y", X must be
  GONE (zero placements found by the locator scan) and Y present at the same
  spots; if "move", old cells free / new cells occupied.

## 4. Verify like generate-room does (never skip)

1. `python3 tools/qa_port.py --room <Room>` for every touched room — 0 errors.
2. `python3 tools/config_to_tiled.py <Room>` for every touched room (and any
   room whose transporters changed).
3. Render before/after: `/Applications/Tiled.app/Contents/MacOS/tmxrasterizer
   tiled/<room>.tmj /tmp/after.png` — LOOK at it; confirm the change reads
   visually and nothing else shifted.
4. In-browser (server usually on :8000): rooms load with zero console errors;
   config<->tmj parity IDENTICAL; walk to the changed spot (held-key events,
   ~400ms/cell) and screenshot it; collision-probe the changed cells via
   `!scene.collisionSystem.checkTileCollision([{x,y}])` — blocked where solid,
   free where open. If a door/transporter changed, walk through it both ways.
5. If the room is in `devhouse.world` and its size/position changed, update
   the world file and rasterize it.

## 5. Interpretation rules

- Do exactly what was asked. Don't "improve" adjacent things you happen to
  notice; mention them in the summary instead.
- If the request is ambiguous between a small set of readings (e.g. "building
  X" could be two buildings), pick the most likely, state the interpretation
  explicitly in your summary, and make the change easy to flip.
- "Replace room X with Y": keep X's inbound connections working — find every
  transporter in other rooms targeting X and point them at sensible cells in
  Y; regenerate those rooms' tmjs too. Remove X from devhouse.world if it's
  gone; add Y.
- A gotcha ledger lives in `gamev2/tiled/README.md` and the memory notes
  (pond has no edge-w piece; interiors want light-concrete floors; rooms are
  min 20x15; `pagoda-floor` is a roof texture; overlay UIs must swallow the
  keypress that opened them).

## 6. Ship

Commit directly to master (no attribution, no PRs, no branches) with a
message that states the adjustment in the user's terms plus what it entailed
mechanically; push. Tell the user where to look in-game to see the change.
