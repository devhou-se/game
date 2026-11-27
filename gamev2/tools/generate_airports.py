#!/usr/bin/env python3
"""generate_airports.py — the airport interiors + the flight registry (issue #218).

The only way between Japan and the home city is by air. Each end has an
airport, built from ONE template (airport_interior), top to bottom:

  the back wall      windows onto the apron, THE GATE (the jet-bridge door) in
                     the middle and the departures board beside it: bump either
                     and the board opens with the flights (src/StationPicker.js
                     in flight mode; one Interactions rule, `flights`)
  the gate lounge    carpet, banks of seats, and THE PUB against the west wall:
                     back shelf, counter with taps, stools - bump it and the bar
                     list opens (Shop.VENUES.pub: the izakaya's drinks and food)
  the security line  two scanner arches you walk through; the x-ray belts and
                     tube railing close the rest of the row
  the check-in hall  desks, the 7-Eleven kiosk (the station's booth and its
                     rule: the konbini list), benches, trolleys, a tactile path
  the front wall     with the way out in the middle

Both airports are `interior` rooms with `shopEnabled: false`: no day/night
grade, never offered to the blog pipeline, and neither the kiosk nor the pub
stamps the Stamp Card (a station's kiosk does not either).

Config `airports` is the registry src/AirTravel.js reads:
  serves   the room the airport belongs to (its town, for the Map and labels)
  label    what the flights board calls it; left out when it is just the name
           of the room it serves (so the home city's name lives in ONE place:
           rooms.<city>.name)
  order    its place on the board
  arrive   where you stand after a flight: in front of the gate
  entry    where a door from outside puts you

HanedaAirport is reached by train: its way out leads to HanedaStation
("Haneda Airport" on the departures board, tools/generate_stations.py), whose
stairs lead back in. The home airport opens onto the city by a door.

Art: tools/generate_sanfranbourne_art.py (airport-*), plus the station's
floors, railing, kiosk, benches, planters and front wall. Idempotent; keeps
nothing (nobody is ever placed in an airport). Run from gamev2/ after the art
tool and before generate_stations.py / generate_sanfranbourne.py:
    python3 tools/generate_airports.py
    python3 tools/config_to_tiled.py HanedaAirport SanFranbourneAirport
    node tools/play.js lint HanedaAirport SanFranbourneAirport
"""
import roomgen as rg

W, H = 36, 22
CX = W // 2 - 1                 # the gate and the way out are cells CX, CX+1
SECURITY_ROW = 8
BAR = (2, 3)                    # the pub: 5x3, bumped from the lounge side
KIOSK = (W - 8, 10)             # the 7-Eleven: 4x3


def layout():
    """Where everything in an airport is (cells)."""
    return dict(w=W, h=H, gate=[CX, 0], board=[CX + 3, 0],
                arrive=[CX, 2],                         # in front of the gate
                scanners=[CX, CX + 1],
                mats=[[CX, H - 1], [CX + 1, H - 1]],    # the way out
                entry=[CX, H - 4])                      # where a door from outside puts you


# The flights board lists airports in THIS order (written as `order`).
# `out`: where the way out leads - (room, cell). The cell must be the one the
# other side's generator lands you on going the other way.
AIRPORTS = {
    'HanedaAirport': dict(name='Haneda Airport', label='Tokyo', serves='Palace',
                          out=('HanedaStation', None)),         # None: that station's `entry`
    'SanFranbourneAirport': dict(name='Tullafrisco Airport', serves='SanFranbourne',
                                 out=('SanFranbourne', [9, 13])),   # in front of the terminal's doors
}


def airport_interior():
    L = layout()
    b = rg.Builder(W, H)

    def place(layer, x, y, sprite, solid=()):
        b.place(layer, x, y, f'{sprite}_0_0', solid)

    # ---- floors: carpet airside, the station's pale concourse landside
    for x in range(W):
        for y in range(H):
            b.put('Floor', x, y, 'airport-carpet_0_0' if y < SECURITY_ROW else 'station-concourse_0_0')

    # ---- the back wall: the gate in the middle, the board beside it, windows
    taken = {}
    place('Collidables', L['gate'][0], 0, 'airport-gate', rg.block(2, 2))
    place('Collidables', L['board'][0], 0, 'airport-board', rg.block(2, 2))
    taken.update({L['gate'][0] + i: 1 for i in range(2)}); taken.update({L['board'][0] + i: 1 for i in range(2)})
    for x in (2, 5, 8, 11, 23, 26, 29, 32):
        place('Collidables', x, 0, 'airport-window', rg.block(2, 2))
        taken.update({x: 1, x + 1: 1})
    for x in range(W):
        if x not in taken:
            place('Collidables', x, 0, 'airport-wall', rg.block(1, 2))

    # ---- the gate lounge: the pub on the west wall, seats facing the gate
    place('Collidables', *BAR, 'airport-bar', rg.block(5, 3))
    for x in (9, 12, 22, 25):
        place('Collidables', x, 5, 'airport-seats', rg.block(3, 1))
    for x in (10, 23):
        place('Collidables', x, 3, 'airport-seats', rg.block(3, 1))
    place('Collidables', W - 4, 2, 'station-planter-a', [(0, 1), (1, 1)])
    place('Collidables', W - 3, 5, 'airport-trolley', rg.block(1, 1))

    # ---- the security line: arches in the middle (walk-through, like a ticket
    #      gate: on `Other`, no collider), x-ray belts either side, railing
    closed = {}
    for x in L['scanners']:
        b.put('Other', x, SECURITY_ROW - 1, 'airport-security_0_0')
        closed[x] = 'arch'
    for x in (L['scanners'][0] - 3, L['scanners'][-1] + 1):
        place('Collidables', x, SECURITY_ROW - 1, 'airport-xray', rg.block(3, 2))
        closed.update({x + i: 'xray' for i in range(3)})
    b.railing_row(SECURITY_ROW, closed)

    # ---- the check-in hall
    for x in (3, 7, 11):
        place('Collidables', x, 10, 'airport-checkin', rg.block(3, 2))
    place('Collidables', *KIOSK, 'station-kiosk', rg.block(4, 3))
    last = H - 3
    for y in range(SECURITY_ROW + 1, last + 1):         # the tactile path from the arches to the way out
        b.put('Over Floor', CX, y, f"station-tactile-{'stop' if y in (SECURITY_ROW + 1, last) else 'v'}_0_0")
    b.put('Tops', CX, last, 'station-exit-sign_0_0')
    for x in (CX - 3, CX + 3):
        place('Collidables', x, last - 1, 'station-planter-a' if x < CX else 'station-planter-b', [(0, 1), (1, 1)])
    for x in (5, W - 9):
        place('Collidables', x, 15, 'station-bench', [(0, 1), (1, 1)])
    for x in (10, W - 13):
        place('Collidables', x, 14, 'station-pillar', [(0, 1)])
    for x in (1, 2, W - 2):
        place('Collidables', x, last, 'airport-trolley', rg.block(1, 1))
    place('Collidables', W - 4, last - 2, 'station-board-map', [(0, 2), (1, 2)])

    # ---- the front wall, the way out in the middle
    for x in range(W):
        if x not in (CX, CX + 1):
            place('Collidables', x, H - 2, 'station-wall-front', [(0, 0), (0, 1)])
    b.put('Over Floor', CX, H - 2, 'station-stairs_0_0')
    return b, L


def main():
    cfg = rg.load_config()
    L = layout()
    for key, spec in AIRPORTS.items():
        b, _ = airport_interior()
        room, cell = spec['out']
        if cell is None:                                # a station: its entry cell (small: 11,11)
            cell = cfg.get('stations', {}).get(room, {}).get('entry', [11, 11])
        cfg['rooms'][key] = b.room(spec['name'], transporters=[
            rg.transporter(mx, my, room, cell[0], cell[1], hidden=True) for (mx, my) in L['mats']])
        cfg['rooms'][key]['interior'] = True
        cfg['rooms'][key]['shopEnabled'] = False        # no konbini shelves here; not a Stamp Card store
    cfg['airports'] = {
        key: {'serves': spec['serves'], 'order': order,
              **({'label': spec['label']} if spec.get('label') else {}),
              'arrive': L['arrive'], 'entry': L['entry']}
        for order, (key, spec) in enumerate(AIRPORTS.items())
    }
    rg.save_config(cfg)
    print('airports:', {k: v['serves'] for k, v in cfg['airports'].items()})


if __name__ == '__main__':
    main()
