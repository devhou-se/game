#!/usr/bin/env python3
"""npc_state.py — add/update dated NPC states in config.json.

States are updates: at load the game applies every state dated on-or-before
the current game date in chronological order over the NPC's base definition
(?date=YYYY-MM-DD to time-travel; defaults to today).

Usage (from gamev2/):
  python3 tools/npc_state.py <Room> <Npc> --list
  python3 tools/npc_state.py <Room> <Npc> <YYYY-MM-DD> \
      [--dialogue "line 1" "line 2" ...] [--pos X,Y] [--sprite <base>] \
      [--absent | --present]
  python3 tools/npc_state.py <Room> <Npc> <YYYY-MM-DD> --delete

Examples:
  python3 tools/npc_state.py Tokyo Bailey 2026-07-26 --dialogue "Back from holidays!"
  python3 tools/npc_state.py Tokyo Bailey 2026-07-28 --pos 26,34
  python3 tools/npc_state.py Machi Dylan 2026-08-01 --absent
"""
import argparse, json, re, sys

ap = argparse.ArgumentParser()
ap.add_argument('room'); ap.add_argument('npc'); ap.add_argument('date', nargs='?')
ap.add_argument('--dialogue', nargs='+')
ap.add_argument('--pos')
ap.add_argument('--sprite')
ap.add_argument('--absent', action='store_true')
ap.add_argument('--present', action='store_true')
ap.add_argument('--delete', action='store_true')
ap.add_argument('--list', action='store_true', dest='list_')
args = ap.parse_args()

cfg = json.load(open('config.json'))
room = cfg['rooms'].get(args.room) or sys.exit(f'no room {args.room!r}; have {list(cfg["rooms"])}')
npc = next((n for n in room['npcs'] if n['name'].lower() == args.npc.lower()), None) \
    or sys.exit(f'no NPC {args.npc!r} in {args.room}; have {[n["name"] for n in room["npcs"]]}')

if args.list_:
    print(f'{npc["name"]} base: pos ({npc["gridX"]},{npc["gridY"]}), dialogue {npc["dialogue"]}')
    for d, st in sorted(npc.get('states', {}).items()):
        print(f'  {d}: {json.dumps(st)}')
    sys.exit(0)

if not args.date or not re.fullmatch(r'\d{4}-\d{2}-\d{2}', args.date):
    sys.exit('need a date as YYYY-MM-DD (or --list)')

states = npc.setdefault('states', {})
if args.delete:
    states.pop(args.date, None)
    if not states: del npc['states']
    print(f'deleted state {args.date}')
else:
    st = states.setdefault(args.date, {})
    if args.dialogue: st['dialogue'] = args.dialogue
    if args.pos:
        x, y = map(int, args.pos.split(','))
        st['gridX'], st['gridY'] = x, y
    if args.sprite:
        st['sprite'] = f'{args.sprite}_front'
        st['directionalSprites'] = {'up': f'{args.sprite}_back', 'down': f'{args.sprite}_front',
                                    'left': '', 'right': f'{args.sprite}_side'}
    if args.absent: st['present'] = False
    if args.present: st['present'] = True
    if not st: sys.exit('nothing to set — pass --dialogue/--pos/--sprite/--absent/--present')
    print(f'{npc["name"]} @ {args.date}: {json.dumps(st)}')

open('config.json', 'w').write(json.dumps(cfg, indent=2, sort_keys=True))
