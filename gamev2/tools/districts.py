#!/usr/bin/env python3
"""districts.py — the named areas of every town, for the blog pipeline.

The one authored list of districts (DISTRICTS below) and the step that writes
it into config.json as the top-level `districts`:

  "districts": {"<Room>": [{"key", "name", "description",
                            "bounds": [x0, y0, x1, y1], "stand": [x, y],
                            "spots": ["<landmark label>", ...]}, ...]}

  bounds       the district's rectangle in the room's OWN cells, inclusive
               (a district of the stitched Tokyo city keeps its room's cells,
               like everything else authored)
  stand        the cell somebody placed "in the district" stands nearest to
               (blog_to_npc.area_cell picks a free, ordinary, reachable cell
               inside the bounds, never a road, a door, its front cell or a seam)
  description  one line of what is there, as the placement model reads it
  spots        the named spots (blog_to_npc.LANDMARKS labels) whose standing
               cell lies inside the bounds — worked out here, never authored

tools/blog_to_npc.py offers every district to the placement model beside the
named spots ("Market · Asakusa (area): Senso-ji temple, ..."), so a post that
names an area and no landmark can be placed (issue #219, the city redesign's
step 1: labels only, no map changes). The game itself does not read
`districts` yet.

The names are the redesign plan's going-forward ones wherever that area is on
today's map; the bounds are today's map. An area the plan names that is not
built yet (Shirakawa-go's ryokan, Ueno and Shibuya in Tokyo's Park) has NO district:
add it with the map change that builds it. A room need not be covered edge
to edge, and districts of one room never overlap.

Not listed on purpose: stations and interiors (indoors: the platform is their
one spot).

Run from gamev2/:  python3 tools/districts.py            write config.json `districts`
                   python3 tools/districts.py --report   print each district's spots and where
                                                         seven authors would stand; write nothing
                   python3 tools/districts.py --coverage print where everyone the game shows
                                                         stands on every trip day, and who is in
                                                         no district; write nothing, exit 1 on a
                                                         problem

Everyone the game shows on a trip day (lead-in included) stands inside a
district of their room or on a station's platform; UNCOVERED lists the
exceptions, each with the ticket that ends it.

It is a generator in tools/check_generators.py: a re-run on an unchanged
world writes identical bytes. After a map change that moves a landmark across
a district's edge, or an edit here, run it again. `python3
tools/test_blog_to_npc.py` checks every district (inside its room, no overlap,
somewhere to stand, room for every author).
"""
import datetime
import json
import sys

import blog_to_npc as b

# Rooms that are towns but get no districts. None today: the made-up towns
# this listed (Machi, Inaka, Yukimura) are deleted (issue #68).
UNLABELLED = ()

# Stands that are in no district on purpose, until the ticket named ends them:
# (NPC name, first day of the stand) -> why. Everyone the game shows on a trip
# day stands inside a district of their room or on a station's platform
# (coverage below); tools/test_blog_to_npc.py fails on an uncovered stand that
# is not listed here, and on a line here that matches no uncovered stand.
UNCOVERED = {
    ('Dylan', '2025-11-05'): "post 636 is about Lake Biwa; it waits by Osaka's platform until #382 re-homes it",
}


def d(key, name, description, bounds, stand=None):
    return {'key': key, 'name': name, 'description': description, 'bounds': list(bounds),
            'stand': list(stand or ((bounds[0] + bounds[2]) // 2, (bounds[1] + bounds[3]) // 2))}


# room key -> its districts, in the order they are offered. Bounds are cells
# of the room's own map, [x0, y0, x1, y1] inclusive.
DISTRICTS = {
    # --- Tokyo: one district per room of the stitched city (the room is the district) -----
    'Tokyo': [
        d('imperial-palace', 'Imperial Palace',
          'the moat, stone walls and blue-tiled gate of the palace, its gardens, pond and cherry trees',
          (6, 5, 54, 44), stand=(27, 35)),
    ],
    'Market': [
        d('asakusa', 'Asakusa',
          'Senso-ji temple and its five-storey pagoda, the lantern gate, the stall street up to the temple, '
          'crowds, the Don Takote discount store, an izakaya, konbini',
          (4, 2, 53, 41), stand=(28, 27)),
    ],
    'Palace': [
        d('marunouchi', 'Marunouchi',
          "Tokyo Station's red-brick front and forecourt, the shinkansen, office blocks, Tokyo Tower on the skyline",
          (2, 5, 52, 20), stand=(20, 12)),
    ],
    'Shinjuku': [
        d('shinjuku', 'Shinjuku',
          'the skyscraper district: an avenue of office towers and blocks of flats west of Marunouchi, '
          'a zebra crossing under the signals, vending machines, the bus bay at the end of the avenue',
          (2, 2, 32, 32), stand=(16, 13)),
    ],
    'Park': [
        d('park', 'Park',
          'a city park of gravel walks and trees with a small shrine, a pagoda and a temple bell; it stands in for '
          'Ueno Park and for Shibuya and Meiji Jingu until those are built',
          (4, 3, 52, 37), stand=(30, 18)),
    ],
    'Karuizawa': [
        d('larch-road', 'Larch road',
          "the packed-dirt road in from Tokyo's west gate, through golden larch woods to Shiraito Falls, "
          "where the bus stops and a stall grills corn",
          (10, 5, 46, 36), stand=(30, 33)),
    ],
    # --- Hokkaido ---------------------------------------------------------
    'Sapporo': [
        d('station-front', 'Sapporo Station front',
          'the star-clock station front on its stone-paved plaza: arrivals, the meeting point, the walk out into the snow',
          (21, 6, 33, 19), stand=(26, 15)),
        d('clock-tower', 'Clock Tower block',
          'the Sapporo Clock Tower on dark setts beside a red-brick office block',
          (34, 6, 53, 19), stand=(38, 18)),
        d('odori-park', 'Odori Park',
          'the long snowy boulevard park in the snow festival: the snow castle and sculptures, corn and hot-drink '
          'stalls, the frozen fountain, the Sapporo TV Tower at its east end',
          (2, 23, 53, 30), stand=(21, 27)),
        d('tanukikoji', 'Tanukikoji',
          'the covered shopping arcade on red brick under a glass roof: souvenirs, the crab shop, a drugstore, '
          'the 7-Eleven, in through the tanuki gate',
          (17, 34, 43, 42), stand=(24, 39)),
        d('susukino', 'Susukino',
          'the neon crossing at night: the fox board on the corner building, a karaoke bar, the ramen alley behind '
          'its gate, the streetcar and its stop on a dark tram street',
          (2, 43, 53, 49), stand=(37, 47)),
    ],
    'Asahikawa': [
        d('station-front', 'Station front and Heiwa-dori',
          "Asahikawa Station's glass hall and the pedestrian shopping street out of it: a 7-Eleven, a bookshop, "
          'a sake shop, a bakery, a woodcraft shop, ice sculptures',
          (11, 5, 39, 12), stand=(28, 11)),
        d('ramen-alley', 'Ramen alley',
          'shoyu ramen counters behind a lantern gate, steam, late-night bowls',
          (2, 13, 16, 15), stand=(8, 15)),
        d('riverbank', 'Asahibashi and the riverbank',
          'the green arch bridge over the frozen river, ice fishing, the snowy banks, three Hokkaido houses and '
          'the Asahiyama Zoo gate on the south side',
          (2, 16, 39, 29), stand=(23, 21)),
    ],
    # --- Kansai -----------------------------------------------------------
    'Osaka': [
        d('dotonbori', 'Dotonbori',
          'the neon canal and its bridge, the Dotonbori arch, giant food signs, takoyaki and ramen queues, bars, '
          'the Don Takote discount store and its ferris wheel',
          (2, 9, 47, 23), stand=(30, 17)),
        d('shinsekai', 'Shinsekai',
          'Tsutenkaku Tower, retro arcades and game shops, kushikatsu, gacha machines, lantern streets',
          (2, 29, 47, 44), stand=(22, 40)),
    ],
    # Himeji: walked to from Osaka, the stitched KansaiCity (issue #255)
    'Himeji': [
        d('castle', 'Himeji Castle',
          'the white castle on its hill: over the moat by the bridge and the gate, then three courts climbed as a hairpin to the keep',
          (6, 2, 41, 13), stand=(30, 8)),
        d('kokoen', 'Koko-en garden',
          'the walled garden beside the castle, three rooms in a row: pines and lanterns, the koi pond and its bridge, maples',
          (6, 26, 40, 37), stand=(27, 28)),
    ],
    # Okayama: walked to from Himeji, the west end of KansaiCity (issue #267)
    'Okayama': [
        d('castle', 'Okayama Castle',
          'the black "crow" castle at the water: the keep on the north bank of the river and the gravel court beside it',
          (22, 14, 33, 18), stand=(27, 16)),
        d('momotaro', 'Momotaro Avenue',
          'the avenue in from Himeji and the plaza it ends in on the east bank: the Momotaro statue and a stall of Bizen ware',
          (34, 14, 43, 23), stand=(36, 20)),
        d('korakuen', 'Korakuen garden',
          'the strolling garden inside the bend of the river, over the Tsukimi bridge: open lawn, a hill, a pond, '
          'red-crowned cranes, the castle across the water',
          (3, 22, 28, 37), stand=(18, 30)),
    ],
    # Nara: walked to from Osaka, the east end of KansaiCity (issue #268)
    'Nara': [
        d('todaiji', 'Todaiji',
          'the Great Buddha Hall behind the Nandaimon gate, its gravel court, and the plaza where the avenue ends: '
          'the deer cracker stall',
          (30, 2, 46, 23), stand=(35, 11)),
        d('nara-park', 'Nara Park',
          'the deer park: the lawn and its maples south of the avenue in from Osaka, deer resting on the grass, '
          'the river and its towpath',
          (2, 17, 29, 33), stand=(16, 25)),
        d('kasuga', 'Kasuga Taisha',
          'the vermilion shrine in the cedar wood: the torii, the approach lined with stone lanterns, the hall',
          (30, 24, 46, 37), stand=(40, 35)),
    ],
    # --- Tohoku -----------------------------------------------------------
    'Sendai': [
        d('station-front', 'Sendai Station front',
          'arrivals at Sendai Station, the forecourt, the first steps into town',
          (22, 6, 37, 11), stand=(30, 10)),
        d('aoba-castle', 'Aoba Castle ruins',
          'the hilltop castle ruins: the Masamune statue, the great hall foundations, the view over the city',
          (2, 7, 21, 20), stand=(10, 14)),
        d('downtown', 'Downtown',
          'the city centre: the HUB pub, ramen and izakaya, the 7-Eleven, hotels, the main street',
          (22, 12, 42, 21), stand=(30, 20)),
        d('zuihoden', 'Zuihoden',
          "the black-and-gold mausoleum of Date Masamune, up cedar steps",
          (43, 7, 55, 21), stand=(49, 14)),
        d('nikka', 'Nikka distillery',
          'the whisky distillery: brick kiln house, casks, autumn maples, a tasting',
          (2, 25, 14, 36), stand=(8, 34)),
        d('samurai-quarter', 'Samurai quarter',
          'the old samurai town: earthen walls and gates, townhouses, walled gardens and ponds along a dirt lane',
          (15, 25, 55, 46), stand=(34, 35)),
        d('matsushima', 'Matsushima bay',
          'the bay of pine islets: the cruise boat and its pier, the seaside promenade, sushi and oysters',
          (56, 7, 69, 46), stand=(57, 24)),
    ],
    # --- Kyushu -----------------------------------------------------------
    'Fukuoka': [
        d('hakata-station', 'Hakata Station',
          'the front of Hakata Station: arrivals and goodbyes, the Christmas market and illuminations, ramen shops',
          (28, 3, 44, 10), stand=(36, 9)),
        d('momochi', 'Momochi',
          'Fukuoka Tower, the beach and the sea',
          (6, 6, 15, 23), stand=(11, 20)),
        d('canal-city', 'Canal City',
          'the Canal City shopping mall and its fountain, arcades and shops',
          (9, 24, 28, 32), stand=(18, 31)),
        d('old-hakata', 'Old Hakata',
          'Kushida shrine and the Yamakasa festival float, temples and old townhouses',
          (33, 24, 59, 32), stand=(46, 31)),
        d('nakasu', 'Nakasu',
          'yatai food stalls along the river at night, lanterns, bars and pubs',
          (9, 33, 59, 42), stand=(30, 37)),
        d('dazaifu', 'Dazaifu',
          'Dazaifu Tenmangu: the torii and approach, the arched bridge over the pond, plum trees, the hall with a grove on its roof',
          (33, 43, 59, 56), stand=(46, 52)),
    ],
    # --- Hokuriku ---------------------------------------------------------
    'Kanazawa': [
        d('station-front', 'Station front',
          'Kanazawa Station: arrivals, the forecourt, the bus to Shirakawa-go',
          (20, 5, 37, 11), stand=(28, 11)),
        d('higashi-chaya', 'Higashi Chaya and the temple hill',
          'the old teahouse district: lattice-fronted teahouses, gold leaf shops, the wooded temple hill behind',
          (2, 13, 30, 20), stand=(16, 19)),
        d('katamachi', 'Katamachi',
          'downtown at night: the whisky bar, all-you-can-drink dinners, the 7-Eleven',
          (2, 21, 30, 29), stand=(15, 29)),
        d('castle', 'Castle',
          "Kanazawa Castle: the Ishikawa gate, stone walls, the grounds",
          (38, 7, 58, 20), stand=(48, 20)),
        d('kenrokuen', 'Kenrokuen',
          'the great garden: its pond, the Kotoji stone lantern, roped pines, maples',
          (43, 21, 58, 28), stand=(46, 25)),
        d('nagamachi', 'Nagamachi',
          'the samurai district: earthen walls, the canal and its stone bridge, a samurai house',
          (2, 34, 33, 51), stand=(18, 39)),
        d('teramachi', 'Teramachi',
          'the wood of shrines south of the avenue: a blue-roofed shrine in a clearing among cedars, its stone foxes',
          (35, 34, 57, 50), stand=(46, 45)),
    ],
    'Shirakawago': [
        d('far-bank', 'Far bank and bridge',
          'where the bus stops: the bear warning, the wobbly suspension bridge over the river',
          (1, 4, 15, 28), stand=(6, 15)),
        d('village', 'Village',
          'the gassho thatched farmhouses, the lanes between them, the harvested paddies',
          (16, 7, 35, 28), stand=(22, 14)),
        d('viewpoint', 'Viewpoint',
          'the lookout over the thatched roofs to the snow peaks',
          (27, 3, 35, 6), stand=(31, 5)),
    ],
    'Toyama': [
        d('iwase', 'Iwase port',
          'the port and its observation tower, the sea, the old merchant street, the black ramen shop',
          (10, 2, 42, 16), stand=(24, 15)),
        d('tram-street', 'Tram street',
          'the tram and its stop, the Glass Art Museum, the street through town',
          (10, 17, 42, 23), stand=(28, 18)),
    ],
}


def build(cfg):
    """config `districts` for this world: DISTRICTS with each one's `spots`."""
    spots = b.find_spots(cfg)
    out = {}
    for room_key, listed in DISTRICTS.items():
        if room_key not in cfg['rooms']:
            raise SystemExit(f'districts.py: DISTRICTS names room {room_key!r}, which config.json does not have')
        out[room_key] = []
        for district in listed:
            x0, y0, x1, y1 = district['bounds']
            inside = sorted(spot_id.split(' · ', 1)[1] for spot_id, (room, x, y) in spots.items()
                            if room == room_key and x0 <= x <= x1 and y0 <= y <= y1)
            out[room_key].append(dict(district, spots=inside))
    return out


def report(cfg):
    """Every district as the pipeline sees it, and what is in no district."""
    spots = b.find_spots(cfg)
    for room_key, listed in cfg['districts'].items():
        w, h = b.room_cells(cfg, room_key)[:2]
        print(f"{room_key} \"{cfg['rooms'][room_key].get('name', room_key)}\" {w}x{h}")
        for district in listed:
            x0, y0, x1, y1 = district['bounds']
            taken = []
            for _ in b.AUTHOR_NPCS:          # one cell each, were every author placed here on one day
                cell = b.area_cell(cfg, room_key, district, set(taken))
                if cell is None:
                    break
                taken.append(cell)
            print(f"  {district['name']}  [{x0},{y0} - {x1},{y1}]  stand at {' '.join(f'{x},{y}' for x, y in taken) or 'NOWHERE'}"
                  f"  spots: {', '.join(district['spots']) or '(none)'}")
        loose = sorted(spot_id.split(' · ', 1)[1] + f' ({x},{y})' for spot_id, (room, x, y) in spots.items()
                       if room == room_key and not b.district_at(cfg, room, x, y))
        if loose:
            print(f"  in no district: {', '.join(loose)}")
    missing = [k for k in b.overworld_rooms(cfg) if not b.is_indoors(cfg, k)
               and k not in cfg['districts'] and k not in UNLABELLED]
    if missing:
        print(f"no districts: {', '.join(missing)}")


def coverage(cfg):
    """Where everyone the game shows stands on every trip day, lead-in
    included, as the game resolves it (the izakaya's drinking-game
    opponents left out): rows {'trip', 'name', 'room', 'cell': (x, y),
    'first', 'last', 'days', 'zone', 'posts'} in order of first day. One row
    is a stand: consecutive days of one trip on one cell, until a dated state
    in that room. `zone` is the district's name, 'the platform' in a station,
    or None (an interior, or outdoors in no district). `posts` are the post
    ids of the state dated `first` ([] for a base stand)."""
    rows, current = [], {}
    for trip in sorted(cfg.get('trips') or [], key=lambda t: t['start']):
        day, end = datetime.date.fromisoformat(b.trip_opens(trip)), datetime.date.fromisoformat(trip['end'])
        while day <= end:
            date, yesterday = day.isoformat(), (day - datetime.timedelta(days=1)).isoformat()
            day += datetime.timedelta(days=1)
            window = b.trip_window(cfg, date)
            if window is None or window['trip'] is not trip:
                continue
            for room_key, room in cfg['rooms'].items():
                for npc in room.get('npcs', []):
                    if npc.get('drinkingGameOpponent'):
                        continue
                    present, x, y = b.resolve_pos(npc, date, window)
                    if not present or x is None:
                        continue
                    state = npc.get('states', {}).get(date)
                    key = (trip['id'], npc['name'], room_key)
                    row = current.get(key)
                    if row and row['cell'] == (x, y) and state is None \
                            and row['last'] == yesterday:
                        row['last'], row['days'] = date, row['days'] + 1
                        continue
                    district = b.district_at(cfg, room_key, x, y)
                    zone = district['name'] if district else 'the platform' if room_key in cfg.get('stations', {}) else None
                    row = {'trip': trip['id'], 'name': npc['name'], 'room': room_key, 'cell': (x, y),
                           'first': date, 'last': date, 'days': 1, 'zone': zone,
                           'posts': [str(p['id']) for p in (state or {}).get('posts') or [] if p.get('id') is not None]}
                    rows.append(row)
                    current[key] = row
    return sorted(rows, key=lambda r: r['first'])


def coverage_problems(cfg, rows=None):
    """The lines the --coverage report and the test print: an uncovered stand
    UNCOVERED does not list, and a line of UNCOVERED that is covered now."""
    rows = coverage(cfg) if rows is None else rows
    uncovered = {(r['name'], r['first']): r for r in rows if r['zone'] is None}
    out = []
    for (name, first), r in uncovered.items():
        if (name, first) not in UNCOVERED:
            x, y = r['cell']
            posts = f" (post {', '.join(r['posts'])})" if r['posts'] else ''
            out.append(f"{name} stands in no district at {r['room']} ({x},{y}) from {r['first']} to {r['last']}{posts}: "
                       'grow or add a district in tools/districts.py, move them with blog_to_npc.py --rehome, '
                       'or list the stand in UNCOVERED')
    for name, first in UNCOVERED:
        if (name, first) not in uncovered:
            out.append(f"{name} from {first} is listed in UNCOVERED and is covered now: delete the line")
    return out


def print_coverage(cfg):
    """The --coverage report; returns the problems."""
    rows = coverage(cfg)
    for trip in sorted(cfg.get('trips') or [], key=lambda t: t['start']):
        mine = [r for r in rows if r['trip'] == trip['id']]
        print(f"{trip['id']}  opens {b.trip_opens(trip)}, {trip['start']}..{trip['end']}")
        for r in mine:
            x, y = r['cell']
            zone = r['zone'] or f"IN NO DISTRICT ({UNCOVERED.get((r['name'], r['first']), 'not listed')})"
            posts = f"  post {', '.join(r['posts'])}" if r['posts'] else ''
            print(f"  {r['first']}..{r['last']}  {r['days']:>2}d  {r['name']:<7} {r['room']} ({x},{y})  {zone}{posts}")
        platform = sum(r['days'] for r in mine if r['zone'] == 'the platform')
        none = sum(r['days'] for r in mine if r['zone'] is None)
        print(f"  person-days: {sum(r['days'] for r in mine) - platform - none} in a district, "
              f"{platform} on a platform, {none} in none")
    problems = coverage_problems(cfg, rows)
    for line in problems:
        print(line)
    return problems


def main(argv):
    if '-h' in argv or '--help' in argv:
        print(__doc__.strip())
        return 0
    unknown = [a for a in argv if a not in ('--report', '--coverage')]
    if unknown:
        print(f"unknown option {' '.join(unknown)}; options: --help --report --coverage", file=sys.stderr)
        return 2
    cfg = b.load_config()
    cfg['districts'] = build(cfg)
    if '--report' in argv:
        report(cfg)
        return 0
    if '--coverage' in argv:
        return 1 if print_coverage(cfg) else 0
    b.save_config(cfg)
    print(f"{sum(len(v) for v in cfg['districts'].values())} districts in {len(cfg['districts'])} rooms written to config.json")
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
