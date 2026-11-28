#!/usr/bin/env python3
"""test_blog_to_npc.py — unit checks for the blog → game pipeline.

Run from gamev2/:  python3 tools/test_blog_to_npc.py

No network, no API keys, nothing written: posts go through process_post in
--mock mode (canned LLM response) with dry_run, against an in-memory copy of
config.json.
"""
import contextlib
import copy
import datetime
import io
import json
import os
import struct
import sys
import tempfile
import zlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import blog_to_npc as b  # noqa: E402
import check_distinct  # noqa: E402
import check_generators  # noqa: E402
import config_to_tiled as c2t  # noqa: E402
import post_photos  # noqa: E402
import districts  # noqa: E402
import sync_cities  # noqa: E402


def test_trim_line():
    limit = b.MAX_LINE_CHARS
    assert b.trim_line('  Short   and\nsweet. ') == 'Short and sweet.'
    assert b.trim_line('x' * limit) == 'x' * limit            # exactly at the limit: untouched

    # ends on the last complete sentence when one closes in the back half
    two = 'A' * 99 + '. ' + 'Going back for round two, cigars in hand and no regrets at all, honestly, none'
    assert len(two) > limit
    assert b.trim_line(two) == 'A' * 99 + '.'

    # no sentence end to fall back to: last whole word + ellipsis, never mid-word
    words = ' '.join(['gorgeous'] * 40)
    out = b.trim_line(words)
    assert len(out) <= limit and out.endswith('gorgeous…'), out
    assert all(w == 'gorgeous' for w in out[:-1].split()), out

    # a full stop inside a number or early in the line is not a sentence end
    early = 'Hi. ' + ' '.join(['word'] * 60)
    assert b.trim_line(early).endswith('word…')
    decimal = ' '.join(['word'] * 30) + ' 3.5 ' + ' '.join(['word'] * 30)
    assert not b.trim_line(decimal).endswith('3.')

    # the dangling comma before the cut goes, the ellipsis stays inside the limit
    comma = 'w' * 150 + ', andthensomemorewordsafterit'
    assert b.trim_line(comma) == 'w' * 150 + '…'

    # Japanese: sentence end, then 、 clause, then a plain cut — always <= limit
    ja = 'あ' * 100 + '。' + 'い' * 100
    assert b.trim_line(ja) == 'あ' * 100 + '。'
    ja = 'あ' * 120 + '、' + 'い' * 100
    assert b.trim_line(ja) == 'あ' * 120 + '…'
    ja = 'あ' * 300
    assert b.trim_line(ja) == 'あ' * (limit - 1) + '…'

    # an abbreviation's full stop is not a sentence end
    for abbr in ('Mr. Smith', 'e.g. Smith', 'St. Kilda'):
        line = 'We did it. ' + 'x ' * 60 + abbr + ' went on and on and on about the trains for hours'
        out = b.trim_line(line)
        assert len(out) <= limit and out.endswith('…') and abbr in out and not out.endswith(' …'), out
    assert b.trim_line('x ' * 60 + 'I said no. ' + 'y ' * 40).endswith('I said no.')

    for line in (two, words, early, decimal, comma, ja):
        assert len(b.trim_line(line)) <= limit

    assert b.clean_dialogue(['a', '  ', 'b', 'c', 'd', 'e']) == ['a', 'b', 'c', 'd']


def post(post_id, author='baely', date='2031-03-04', title=None):
    return {'post_id': post_id, 'author': author, 'date': date,
            'title': title or f'post {post_id}', 'content': 'no pictures here'}


def placements(cfg, npc_name, date):
    """[(room, state)] for every room holding a state for this NPC on date."""
    out = []
    for room_key, room in b.overworld_rooms(cfg).items():
        npc = b.npc_in_room(room, npc_name)
        if npc and date in npc.get('states', {}):
            out.append((room_key, npc['states'][date]))
    return out


def ids(state):
    return [p['id'] for p in state['posts']]


def place(cfg, p, spot_id, spots):
    """process_post in mock mode, with the mock's spot choice pinned."""
    with contextlib.redirect_stdout(io.StringIO()):
        record, _ = b.process_post(cfg, p, spots, [spot_id], mock=True, dry_run=True)
    assert record, f'post {p["post_id"]} was not placed'
    return record


def test_same_day_posts(base_cfg):
    cfg = copy.deepcopy(base_cfg)
    spots = b.find_spots(cfg)
    by_room = {}
    for spot_id, (room_key, _, _) in sorted(spots.items()):
        by_room.setdefault(room_key, spot_id)
    assert len(by_room) >= 2, 'need landmarks in two rooms'
    (room_a, spot_a), (room_b, spot_b) = list(by_room.items())[:2]
    date = '2031-03-04'

    def live():
        return [(r, st) for r, st in placements(cfg, 'Bailey', date) if st.get('present')]

    # one post: placed in room A, 2 mock lines, its id recorded
    place(cfg, post(1), spot_a, spots)
    (room, st), = live()
    assert room == room_a and ids(st) == ['1'] and len(st['dialogue']) == 2
    first = list(st['dialogue'])

    # the same post again (workflow re-run): replaced, not stacked
    place(cfg, post(1), spot_a, spots)
    (room, st), = live()
    assert ids(st) == ['1'] and st['dialogue'] == first

    # a second post the same day, in another room: its spot wins, both posts'
    # lines are kept in order, and room A keeps nothing but "absent"
    place(cfg, post(2), spot_b, spots)
    (room, st), = live()
    assert room == room_b and st['posts'] == [{'id': '1', 'lines': 2, 'title': 'post 1'},
                                              {'id': '2', 'lines': 2, 'title': 'post 2'}]
    assert st['dialogue'][:2] == first and 'post 2' in st['dialogue'][2] and len(st['dialogue']) == 4
    assert dict(placements(cfg, 'Bailey', date))[room_a] == {'present': False}

    # more posts than the day has room for: capped, the oldest lines go first
    for n in (3, 4, 5):
        place(cfg, post(n), spot_b, spots)
    (room, st), = live()
    assert len(st['dialogue']) == b.MAX_DAY_LINES
    assert 'post 5' in st['dialogue'][-2] and ids(st) == ['2', '3', '4', '5']   # post 1 has no lines left
    assert not any('post 1!' in line for line in st['dialogue'])

    # re-running a post of a merged day replaces only its own lines (they move
    # to the end, as the post processed last) and keeps the other posts'
    before = list(st['dialogue'])
    place(cfg, post(3), spot_a, spots)
    (room, st), = live()
    assert room == room_a and ids(st) == ['2', '4', '5', '3']
    assert st['dialogue'] == before[0:2] + before[4:8] + before[2:4]
    assert dict(placements(cfg, 'Bailey', date))[room_b] == {'present': False}
    # ... and re-running a post whose lines the cap already dropped adds it
    # back as the latest without wiping the day
    place(cfg, post(1), spot_a, spots)
    (room, st), = live()
    assert ids(st) == ['4', '5', '3', '1'] and len(st['dialogue']) == b.MAX_DAY_LINES

    # the next day starts clean; another author's same-day post is untouched by all this
    place(cfg, post(6, date='2031-03-05'), spot_a, spots)
    (_, nxt), = [(r, s) for r, s in placements(cfg, 'Bailey', '2031-03-05') if s.get('present')]
    assert ids(nxt) == ['6'] and len(nxt['dialogue']) == 2
    place(cfg, post(7, author='jughents'), spot_b, spots)
    (_, julia), = [(r, s) for r, s in placements(cfg, 'Julia', date) if s.get('present')]
    assert ids(julia) == ['7'] and len(julia['dialogue']) == 2

    # a state from before "posts" existed is replaced, as it always was
    legacy = copy.deepcopy(base_cfg)
    place(legacy, post(8), spot_a, spots)
    (_, st), = [(r, s) for r, s in placements(legacy, 'Bailey', date) if s.get('present')]
    del st['posts']
    place(legacy, post(9), spot_a, spots)
    (_, st), = [(r, s) for r, s in placements(legacy, 'Bailey', date) if s.get('present')]
    assert ids(st) == ['9'] and len(st['dialogue']) == 2 and 'post 9' in st['dialogue'][0]


def rooms_on(cfg, npc_name, date):
    """Overworld rooms the game shows the NPC in on date: resolved inside the
    date's trip window, as the game does (whereabouts, below, with cells)."""
    window = b.trip_window(cfg, date)
    return [room_key for room_key, room in b.overworld_rooms(cfg).items()
            if b.npc_in_room(room, npc_name)
            and b.resolve_pos(b.npc_in_room(room, npc_name), date, window)[0]]


def test_rehome(base_cfg):
    """--rehome moves a placement to another spot and keeps what the post gave
    it; the room left behind and the later history stay consistent (#121)."""
    cfg = copy.deepcopy(base_cfg)
    spots = b.find_spots(cfg)
    platform = 'TokyoStation · the platform'
    outdoor = [s for s, (room_key, _, _) in sorted(spots.items()) if not b.is_indoors(cfg, room_key)]
    target = outdoor[0]
    target_room = spots[target][0]
    later = next(s for s in outdoor if spots[s][0] != target_room)
    d1, d2, d3 = '2031-03-04', '2031-03-05', '2031-03-06'

    place(cfg, post(1, date=d1), platform, spots)           # Bailey, on the platform
    place(cfg, post(2, date=d3), later, spots)              # ... who moves on two days later
    assert b.placement_room(cfg, 'Bailey', d1) == 'TokyoStation'
    assert b.stay_end(cfg, 'Bailey', d1) == d3 and b.stay_end(cfg, 'Bailey', d3) is None
    before = dict(b.npc_in_room(cfg['rooms']['TokyoStation'], 'Bailey')['states'][d1])

    # someone else is already recorded as arriving at the same landmark the
    # next day, while Bailey would still be standing there
    place(cfg, post(3, author='jughents', date=d2), target, spots)
    julia = b.resolve_pos(b.npc_in_room(cfg['rooms'][target_room], 'Julia'), d2, b.trip_window(cfg, d2))[1:]
    assert julia not in b.occupied_cells(cfg, target_room, d1, 'Bailey')     # one day alone would miss her
    assert julia in b.occupied_during(cfg, target_room, d1, 'Bailey')

    # ... but a later trip's days are not part of the stay: that trip starts
    # everyone from its base again, so a devhouse 2 placement is not there
    trip_cfg = copy.deepcopy(base_cfg)
    old_day, new_day = '2025-11-17', '2027-02-20'
    assert b.trip_window(trip_cfg, new_day)['from'] > old_day
    was = b.occupied_during(trip_cfg, target_room, old_day, 'Dylan')
    place(trip_cfg, post(4, author='jughents', date=new_day), target, spots)
    assert b.npc_in_room(trip_cfg['rooms'][target_room], 'Julia')['states'][new_day]['present'] is True
    assert b.occupied_during(trip_cfg, target_room, old_day, 'Dylan') == was

    with contextlib.redirect_stdout(io.StringIO()):
        changes = b.rehome(cfg, 'Bailey', d1, target, spots)
    assert changes[0].startswith(f'Bailey {d1}: TokyoStation'), changes[0]
    assert b.placement_room(cfg, 'Bailey', d1) == target_room
    st = b.npc_in_room(cfg['rooms'][target_room], 'Bailey')['states'][d1]
    cell = (st['gridX'], st['gridY'])
    assert st['present'] is True and cell != julia, (cell, julia)
    assert cell == b.walkable_near(cfg, target_room, *spots[target][1:],
                                   b.occupied_during(cfg, target_room, d1, 'Bailey'))
    for key in ('dialogue', 'posts', 'photo'):                               # the post's content went along
        assert st.get(key) == before.get(key), key
    assert st['posts'][0]['id'] == '1' and len(st['dialogue']) == 2
    # the platform keeps nothing but "absent", and each day has her in one room
    assert b.npc_in_room(cfg['rooms']['TokyoStation'], 'Bailey')['states'][d1] == {'present': False}
    assert rooms_on(cfg, 'Bailey', d1) == [target_room]
    assert rooms_on(cfg, 'Bailey', d2) == [target_room]
    assert rooms_on(cfg, 'Bailey', d3) == [spots[later][0]]

    # within a room it is a plain move; again leaves it where it is
    with contextlib.redirect_stdout(io.StringIO()):
        b.rehome(cfg, 'Bailey', d1, target, spots)
    again = b.npc_in_room(cfg['rooms'][target_room], 'Bailey')['states'][d1]
    assert (again['gridX'], again['gridY']) == cell and again['dialogue'] == before['dialogue']

    # ... and to another spot in the same room it changes the cell and nothing
    # else (#190): no "voice" key on a state that had none, no extra states
    # in the other rooms
    del again['voice']
    nearby = next(s for s in outdoor if spots[s][0] == target_room and b.walkable_near(
        cfg, target_room, *spots[s][1:], b.occupied_during(cfg, target_room, d1, 'Bailey')) != cell)
    untouched = copy.deepcopy(cfg)
    with contextlib.redirect_stdout(io.StringIO()):
        changes = b.rehome(cfg, 'Bailey', d1, nearby, spots)
    assert len(changes) == 1 and changes[0].startswith(f'Bailey {d1}: {target_room}'), changes
    moved = b.npc_in_room(cfg['rooms'][target_room], 'Bailey')['states'][d1]
    assert (moved['gridX'], moved['gridY']) != cell and 'voice' not in moved
    moved['gridX'], moved['gridY'] = cell
    assert cfg == untouched, 'a same-room rehome changed more than the cell'

    # nothing to move, or nowhere to move it: refused, config untouched
    snapshot = json.dumps(cfg, sort_keys=True)
    for args in (('Bailey', '2031-01-01', target), ('Bailey', d1, 'Nowhere · the moon'),
                 ('Nobody', d1, target)):
        try:
            b.rehome(cfg, *args, spots)
        except ValueError:
            pass
        else:
            raise AssertionError(f'rehome{args} should have been refused')
    assert json.dumps(cfg, sort_keys=True) == snapshot


# issue #121: posts about somewhere else that were parked on a platform before
# #73. The only thing pinned is that they are not back on one - a day that is
# rebuilt (--reset, a re-run of its post) may land anywhere else, or nowhere.
OFF_THE_PLATFORM = [('Julia', '2025-11-03'), ('Damian', '2025-11-05'), ('Dylan', '2025-11-02'),
                    ('Dylan', '2025-11-05'), ('Bailey', '2025-11-16'), ('Dylan', '2025-11-01'),
                    ('Julia', '2025-11-12')]

# issue #263: the two posts about Karuizawa stand there, moved off Tokyo
# Station's platform by --rehome once the place was built (#260, #262):
# (NPC, date) -> (spot, cell, post)
IN_KARUIZAWA = {
    ('Damian', '2025-11-01'): ('Karuizawa · Shiraito Falls', (13, 8), '544'),
    ('Julia', '2025-11-02'): ('Karuizawa · the corn stall', (21, 8), '572'),
}


def test_shipped_whereabouts(cfg):
    """config.json's history is consistent across rooms: on every dated day
    each NPC is present in at most one room and no two share a cell; and the
    #121 placements are outdoors, with the station they left saying absent."""
    rooms = b.overworld_rooms(cfg)
    dates = sorted({d for room in rooms.values() for n in room.get('npcs', []) for d in n.get('states', {})}
                   | {d for t in cfg.get('trips') or [] for d in
                      [t['start'], t['end']] + [st['from'] for st in t.get('stays') or []]})
    names = sorted({n['name'] for room in rooms.values() for n in room.get('npcs', [])})
    for date in dates:
        for name in names:
            here = rooms_on(cfg, name, date)
            assert len(here) <= 1, f'{name} is in {here} on {date}'
        window = b.trip_window(cfg, date)
        for room_key, room in rooms.items():
            taken = {}
            for n in room.get('npcs', []):
                present, x, y = b.resolve_pos(n, date, window)
                if present:
                    assert (x, y) not in taken, f'{room_key} {date}: {n["name"]} and {taken[(x, y)]} share {(x, y)}'
                    taken[(x, y)] = n['name']
    # nobody's dated placement is inside a sprite — under a canopy, bell roof
    # or gate beam, or on the head of a statue or vending machine (#183, #189:
    # the resolver keeps off those cells, and so do the placements made before it did)
    for room_key, room in cfg['rooms'].items():
        behind = b.overhead_cells(cfg, room_key, standing=True)
        for n in room.get('npcs', []):
            for date, state in n.get('states', {}).items():
                if state.get('present') is not False and state.get('gridX') is not None:
                    assert (state['gridX'], state['gridY']) not in behind, \
                        f'{room_key} {date}: {n["name"]} stands inside a sprite at {(state["gridX"], state["gridY"])}'
    for name, date in OFF_THE_PLATFORM:
        for station in cfg['stations']:
            npc = b.npc_in_room(cfg['rooms'][station], name)
            assert npc is None or npc.get('states', {}).get(date, {'present': False}) == {'present': False}, \
                f'{name} {date}: {station} holds the placement again'
        room_key = b.placement_room(cfg, name, date)
        if room_key is not None:
            assert not b.is_indoors(cfg, room_key), f'{name} {date} ({room_key})'
            assert rooms_on(cfg, name, date) == [room_key], f'{name} {date} ({room_key})'

    # the Karuizawa days (#263): at the spot the post is about, with what the
    # post gave them, Tokyo Station saying absent; and --rehome to the same
    # spot again would leave them on the same cell
    spots = b.find_spots(cfg)
    for (name, date), (spot, cell, post_id) in IN_KARUIZAWA.items():
        assert spots[spot][0] == 'Karuizawa' and rooms_on(cfg, name, date) == ['Karuizawa'], (name, date, rooms_on(cfg, name, date))
        state = b.npc_in_room(cfg['rooms']['Karuizawa'], name)['states'][date]
        assert (state['gridX'], state['gridY']) == cell, (name, date, state['gridX'], state['gridY'])
        assert [p['id'] for p in state['posts']] == [post_id] and state['photo'] == post_id and len(state['dialogue']) == 4
        assert cell not in b.doorway_cells(cfg, 'Karuizawa'), f'{name} {date}: {cell} is a door or in front of one'
        assert b.npc_in_room(cfg['rooms']['TokyoStation'], name)['states'][date] == {'present': False}
        for station in cfg['stations']:
            assert station not in rooms_on(cfg, name, date)
        again = copy.deepcopy(cfg)
        with contextlib.redirect_stdout(io.StringIO()):
            b.rehome(again, name, date, spot, spots)
        assert b.npc_in_room(again['rooms']['Karuizawa'], name)['states'][date] == state, f'{name} {date}: a second --rehome moved it'
    # ... and the day after, each is with the others again and Karuizawa is empty
    for (name, date) in IN_KARUIZAWA:
        nxt = (datetime.date.fromisoformat(date) + datetime.timedelta(days=1)).isoformat()
        assert 'Karuizawa' not in rooms_on(cfg, name, nxt), (name, nxt)


def test_shipped_coverage(cfg):
    """Everyone the game shows on a trip day stands inside a district of
    their room or on a station's platform (districts.coverage, #383), and
    districts.UNCOVERED lists exactly the stands that do not."""
    def npc(name, x, y, **kw):
        return dict({'name': name, 'gridX': x, 'gridY': y}, **kw)
    made = {
        'trips': [{'id': 't1', 'start': '2025-01-10', 'end': '2025-01-20', 'lead': 3, 'members': ['a', 'b']},
                  {'id': 't2', 'start': '2025-03-01', 'end': '2025-03-05', 'lead': 2, 'members': ['c']}],
        'stations': {'TownStation': {}},
        'districts': {'Town': [{'key': 'square', 'name': 'Square', 'bounds': [0, 0, 4, 4]}]},
        'rooms': {
            'Town': {'npcs': [
                npc('A', 2, 2, trip='t1', states={'2025-01-12': {'gridX': 2, 'gridY': 2, 'posts': [{'id': '5'}]},
                                                  '2025-01-15': {'gridX': 2, 'gridY': 2, 'posts': [{'id': '6'}]}}),
                npc('B', 5, 2, trip='t1'),
                npc('C', 1, 1, trip='t2')]},
            'TownStation': {'npcs': [npc('S', 1, 1, trip='t1')]},
            'Shop': {'interior': True, 'npcs': [npc('I', 1, 1, trip='t1'),
                                                npc('O', 2, 1, trip='t1', drinkingGameOpponent=True)]},
        },
    }
    rows = districts.coverage(made)
    by = lambda name: [r for r in rows if r['name'] == name]
    assert [(r['first'], r['last'], r['days'], r['posts']) for r in by('A')] == [
        ('2025-01-07', '2025-01-11', 5, []), ('2025-01-12', '2025-01-14', 3, ['5']), ('2025-01-15', '2025-01-20', 6, ['6'])]
    assert all(r['zone'] == 'Square' and r['trip'] == 't1' and r['cell'] == (2, 2) for r in by('A'))
    assert [(r['zone'], r['first']) for r in by('B')] == [(None, '2025-01-07')]
    assert [(r['zone'], r['room']) for r in by('S')] == [('the platform', 'TownStation')]
    assert [(r['zone'], r['room']) for r in by('I')] == [(None, 'Shop')]
    assert by('O') == []
    assert [(r['first'], r['last'], r['trip'], r['zone']) for r in by('C')] == [('2025-03-01', '2025-03-05', 't2', 'Square')]
    assert [r['first'] for r in rows] == sorted(r['first'] for r in rows)
    kept = districts.UNCOVERED
    try:
        districts.UNCOVERED = {('B', '2025-01-07'): 'waits for a district', ('A', '2025-01-07'): 'stale'}
        problems = districts.coverage_problems(made)
        assert len(problems) == 2, problems
        assert problems[0].startswith('I stands in no district at Shop (1,1) from 2025-01-07 to 2025-01-20:'), problems
        assert problems[1] == 'A from 2025-01-07 is listed in UNCOVERED and is covered now: delete the line', problems
    finally:
        districts.UNCOVERED = kept

    # the shipped world
    rows = districts.coverage(cfg)
    problems = districts.coverage_problems(cfg, rows)
    assert problems == [], '\n'.join(problems)
    for trip in cfg['trips']:
        seen = {r['name'].lower() for r in rows if r['trip'] == trip['id']}
        assert set(trip['members']) <= seen, (trip['id'], set(trip['members']) - seen)
    assert not any(cfg['rooms'][r['room']].get('interior') for r in rows), [r for r in rows if cfg['rooms'][r['room']].get('interior')]


def test_merge_same_day():
    p10, p11 = {'id': '10', 'lines': 2}, {'id': '11', 'lines': 1}
    earlier = {'dialogue': ['a', 'b'], 'photo': '10', 'posts': [p10], 'drunk': True}
    assert b.merge_same_day(earlier, 11, ['c'], None, False) == (['a', 'b', 'c'], '10', True, [p10, p11])
    assert b.merge_same_day(earlier, 11, ['c'], '11', False)[1] == '11'      # later photo wins
    assert b.merge_same_day(None, 11, ['c'], None, False) == (['c'], None, False, [p11])
    assert b.merge_same_day(earlier, None, ['c'], None, False) == (['c'], None, False, None)
    # a re-run of one post of a merged day: only its own lines are replaced
    both = {'dialogue': ['a', 'b', 'c'], 'photo': None, 'posts': [p10, p11]}
    assert b.merge_same_day(both, 10, ['A'], None, False) == (['c', 'A'], None, False, [p11, {'id': '10', 'lines': 1}])
    assert b.merge_same_day(both, 11, ['C', 'D'], None, False)[0] == ['a', 'b', 'C', 'D']
    # a state whose counts do not add up (hand-edited) or without them is replaced outright
    for bad in ({'dialogue': ['a', 'b', 'c'], 'posts': [p10]}, {'dialogue': ['a'], 'posts': ['10']}, {'dialogue': ['a']}):
        assert b.merge_same_day(bad, 11, ['c'], None, False) == (['c'], None, False, [p11])
    assert earlier['posts'] == [{'id': '10', 'lines': 2}]                    # inputs are not mutated


def test_spots(cfg):
    """What find_spots offers, over every room (issues #73, #100)."""
    spots = b.find_spots(cfg)
    stations = set(cfg.get('stations', {}))
    assert stations, 'config has no stations'
    by_room = {}
    for spot_id, (room_key, x, y) in spots.items():
        assert spot_id.startswith(room_key + ' · '), spot_id
        by_room.setdefault(room_key, {})[spot_id.split(' · ', 1)[1]] = (x, y)

    # interiors are opt-in: a konbini or the izakaya is never offered, and a
    # station offers its platform and none of the props standing on it
    for room_key, room in cfg['rooms'].items():
        if room.get('interior'):
            assert room_key not in by_room, f'{room_key} is an interior but offers {by_room[room_key]}'
        elif room.get('blog') is False:
            # closed to the pipeline (issue #218): the home city and Haneda's rail stop are on no trip,
            # so their torii, 7-Eleven, vending machines and platform are never offered
            assert room_key not in by_room, f'{room_key} is closed to the blog but offers {by_room[room_key]}'
            assert room_key not in b.overworld_rooms(cfg), room_key
        elif room_key in stations:
            assert set(by_room.get(room_key, {})) == {'the platform'}, (room_key, by_room.get(room_key))
        else:
            assert 'the platform' not in by_room.get(room_key, {}), room_key
            assert by_room.get(room_key), f'{room_key} is outdoors and offers nowhere to stand'
    closed = {k for k, r in cfg['rooms'].items() if r.get('blog') is False}
    assert closed == {'SanFranbourne', 'HanedaStation'}, closed
    assert not any(k in by_room for k in cfg.get('airports', {})), 'an airport offers a spot'
    indoor_labels = {label for _, label, _, options in map(b.landmark_fields, b.LANDMARKS)
                     if options.get('indoors')}
    assert indoor_labels == {'the platform'}, indoor_labels

    # a landmark that names one town is offered there and nowhere else, even
    # where another town is built from the same sprites
    assert 'the Nagamachi samurai lane' in by_room['Kanazawa']
    assert [r for r in by_room if 'the Nagamachi samurai lane' in by_room[r]] == ['Kanazawa']
    assert 'ramen alley' in by_room['Asahikawa']
    for prefix, label, _, options in map(b.landmark_fields, b.LANDMARKS):
        for room_key in options.get('rooms', ()):
            assert room_key in cfg['rooms'], f'{label}: no room {room_key!r}'
            assert label in by_room.get(room_key, {}), f'{label} is not found in {room_key}'
        if 'rooms' in options:
            # ...nowhere else, unless another row carries the same label for another town: Sapporo's
            # `ramen alley` hangs on Susukino's ramen gate, Asahikawa's on its own lantern gate
            # (issue #219). An unscoped row counts for the towns that hold its sprite
            offered = {r for r in by_room if label in by_room[r]}
            expected = set()
            for other_prefix, other_label, _, other in map(b.landmark_fields, b.LANDMARKS):
                if other_label == label:
                    expected |= set(other['rooms']) if 'rooms' in other else {
                        r for r in by_room if any(key.startswith(other_prefix) for layer in cfg['rooms'][r]['layers']
                                                  for key in b.decode_tiles(cfg, layer).values())}
            assert offered == expected, (label, offered, expected)
    # the two ramen alleys: each town's own, at its own sprite
    assert by_room['Sapporo']['ramen alley'] == (25, 47), by_room['Sapporo']['ramen alley']
    assert sorted(r for r in by_room if 'ramen alley' in by_room[r]) == ['Asahikawa', 'Sapporo']
    # ... and that filter is doing something: the gate's sprite is in both towns
    def has_tile(room_key, prefix):
        return any(key.startswith(prefix) for layer in cfg['rooms'][room_key]['layers']
                   for key in b.decode_tiles(cfg, layer).values())
    assert has_tile('Kanazawa', 'sendai-gate_') and has_tile('Sendai', 'sendai-gate_')

    # every spot is somewhere an author can stand and the player can walk up
    # to: a free cell at the landmark's standing cell or within two of it
    # (Market's fox statues stand in a fenced garden: the visitor is put
    # outside the fence), that is connected to one of the room's ways in
    reach = {}
    for spot_id, (room_key, x, y) in sorted(spots.items()):
        cell = b.walkable_near(cfg, room_key, x, y)
        assert cell is not None, f'{spot_id}: nowhere to stand near ({x},{y})'
        assert max(abs(cell[0] - x), abs(cell[1] - y)) <= 2, f'{spot_id}: ({x},{y}) resolves to far-off {cell}'
        if room_key not in reach:
            reach[room_key] = b.reachable_cells(cfg, room_key)
            # None = "no way in, so no filter": an outdoor room must never be that (issue #124)
            assert reach[room_key] is not None, f'{room_key} has no way in to judge its spots from'
        assert cell in reach[room_key], f'{spot_id}: {cell} cannot be walked to'
        # four authors can be at one spot on one day without anyone being walled in
        taken = set()
        for _ in b.AUTHOR_NPCS:
            c = b.walkable_near(cfg, room_key, x, y, taken)
            assert c in reach[room_key], f'{spot_id}: {c} (with {sorted(taken)} taken) cannot be walked to'
            # ... or being stood under a canopy or roof, which hides them (issue #183)
            assert c not in b.overhead_cells(cfg, room_key), f'{spot_id}: {c} is under an overhead sprite'
            taken.add(c)
    SAKURA = 'Osaka'
    # the sakura canopy is 3x2 from its tile cell, the trunk under its middle:
    # the spot is the ground in front of the trunk, not the canopy's corner
    canopy = next((x, y) for layer in cfg['rooms'][SAKURA]['layers'] if layer['name'] == 'Tops'
                  for xy, key in b.decode_tiles(cfg, layer).items() if key.startswith('sakura-large-top')
                  for x, y in [map(int, xy.split(','))])
    under = {(canopy[0] + i, canopy[1] + j) for i in range(3) for j in range(2)}
    assert under <= b.overhead_cells(cfg, SAKURA), sorted(under - b.overhead_cells(cfg, SAKURA))
    assert by_room[SAKURA]['the sakura trees'] == (canopy[0] + 1, canopy[1] + 3)
    # a landmark with a stand cell is anchored on a tile whose stand cell is in
    # the open, where the room has one — Market's first sakura has the 7-Eleven
    # in front of its trunk and its second the roof of a high-rise, which sent
    # the visitor round the back of the store (#189)
    def sprite_cell(room_key, layer_name, prefix):
        return {(x, y) for layer in cfg['rooms'][room_key]['layers'] if layer['name'] == layer_name
                for xy, key in b.decode_tiles(cfg, layer).items() if key.startswith(prefix)
                for x, y in [map(int, xy.split(','))]}
    for room_key, at in by_room.items():
        if 'the sakura trees' not in at:
            continue
        x, y = at['the sakura trees']
        assert (x - 1, y - 3) in sprite_cell(room_key, 'Tops', 'sakura-large-top'), (room_key, x, y)
        stands = [(cx + 1, cy + 3) for cx, cy in sprite_cell(room_key, 'Tops', 'sakura-large-top')]
        behind = b.overhead_cells(cfg, room_key, standing=True)
        in_open = [c for c in stands if c not in behind and b.walkable_near(cfg, room_key, *c) == c]
        assert not in_open or (x, y) in in_open, f'{room_key}: sakura spot ({x},{y}) is not in the open, {in_open} are'
    market = by_room['Market']['the sakura trees']
    assert b.walkable_near(cfg, 'Market', *market) == market
    store = next(iter(sprite_cell('Market', 'Collidables', 'seven-eleven')))
    assert not (store[0] - 1 <= market[0] <= store[0] + 3 and store[1] - 1 <= market[1] <= store[1] + 3), (market, store)
    assert {(store[0] + i, store[1] + j) for i in range(3) for j in range(4)} <= b.overhead_cells(cfg, 'Market', standing=True)
    assert b.overhead_cells(cfg, 'Market') < b.overhead_cells(cfg, 'Market', standing=True)
    # ... and with nowhere in the open the first tile stays (checked above)
    # the 7-Eleven's visitor stands on the pavement at its front, beside the
    # door — not behind the store, nor on the cell shoppers step out onto (#184)
    stores = [room_key for room_key in by_room if 'the 7-Eleven' in by_room[room_key]]
    assert {'Market', 'Park', 'Sapporo'} <= set(stores), stores
    for room_key in stores:
        door = next((t['gridX'], t['gridY']) for t in cfg['rooms'][room_key]['transporters']
                    if t['targetRoom'].startswith('Konbini')
                    and max(abs(t['gridX'] - by_room[room_key]['the 7-Eleven'][0]), abs(t['gridY'] - by_room[room_key]['the 7-Eleven'][1])) <= 2)
        cell = b.walkable_near(cfg, room_key, *by_room[room_key]['the 7-Eleven'])
        assert cell == (door[0] - 1, door[1] + 1), f'{room_key}: 7-Eleven door {door}, visitor at {cell}'
    # no spot stands its visitor inside a sprite: under a roof or gate beam, or
    # on the head of a statue or vending machine, which collide only at the
    # base (Palace's vending machines, Market's torii)
    for spot_id, (room_key, x, y) in spots.items():
        cell = b.walkable_near(cfg, room_key, x, y)
        assert cell not in b.overhead_cells(cfg, room_key, standing=True), f'{spot_id}: {cell} is inside a sprite'
    # a cell inside a standing sprite is taken before one under a roof, when nothing is open
    statues = copy.deepcopy(cfg)
    w, h = b.room_cells(statues, SAKURA)[:2]
    statues['rooms'][SAKURA]['layers'].append(
        {'name': 'Statues', 'z': 5, 'tiles': {f'{x},{y}': 'shrub-small-circle_0_0' for x in range(w) for y in range(h)}})
    cell = b.walkable_near(statues, SAKURA, *canopy)
    assert cell is not None and cell not in b.overhead_cells(statues, SAKURA), cell
    # with nowhere open in range a covered cell still does (better hidden than unplaced)
    roofed = copy.deepcopy(cfg)
    tops = next(layer for layer in roofed['rooms'][SAKURA]['layers'] if layer['name'] == 'Tops')
    w, h = b.room_cells(roofed, SAKURA)[:2]
    tops['tiles'] = {f'{x},{y}': 'sakura-large-top_0_0' for x in range(w) for y in range(h)}
    assert b.walkable_near(roofed, SAKURA, *canopy) is not None

    # a station's platform spot keeps clear of the train doors and where you arrive
    for room_key in stations:
        if cfg['rooms'][room_key].get('blog') is False:      # offers no platform spot (checked above)
            continue
        st = cfg['stations'][room_key]
        cell = b.walkable_near(cfg, room_key, *by_room[room_key]['the platform'])
        keep_clear = [tuple(c) for c in st.get('board', [])] + [tuple(st['arrive'])]
        assert all(max(abs(cell[0] - cx), abs(cell[1] - cy)) > 2 for cx, cy in keep_clear), (room_key, cell)


def test_city_reach(cfg):
    """Spot reachability in the stitched Tokyo city (issue #124).

    The game merges the districts of config `cities` into one room and drops
    the seam transporters between them; blog_to_npc floods that city with a
    small port of the merge (city_districts / city_reachable). It is pinned
    here, for EVERY cell of every room, to `node tools/play.js reach`, which
    floods the room built by the game's own src/systems/CityStitcher.js."""
    import json
    import shutil
    import subprocess
    city = cfg['cities']['TokyoCity']
    names = [m['room'] for m in city['rooms']]
    assert names == ['Tokyo', 'Market', 'Palace', 'Park', 'Karuizawa', 'Shinjuku'], names

    # the layout: offsets from the union's top-left, sizes from the rooms
    districts = b.city_districts(cfg, 'Market')
    assert [d[0] for d in districts] == names
    assert min(d[1] for d in districts) == 0 and min(d[2] for d in districts) == 0
    assert dict((d[0], d[1:3]) for d in districts)['Tokyo'] == (48, 1), districts     # Karuizawa is the 48 columns west of it
    assert b.city_districts(cfg, 'Sendai') is None and b.city_districts(cfg, 'KonbiniMarket1') is None
    for name in names:
        assert b.city_districts(cfg, name) == districts

    # Tokyo has seams and one door of its own, into its shrine hall (#212; it
    # had none before) - and is still judged (it used to fall back to "no
    # filter"); nobody is judged from the seams alone. Since #215 also the two
    # tower doors of the palace, both into its one audience hall
    assert [t['targetRoom'] for t in cfg['rooms']['Tokyo']['transporters']
            if t['targetRoom'] not in names] == ['ShrineTokyo1', 'PalaceHallTokyo1', 'PalaceHallTokyo1']
    reach = {name: b.reachable_cells(cfg, name) for name in names}
    for name in names:
        assert reach[name], f'{name}: nothing reachable'
        w, h, floored, blocked = b.room_cells(cfg, name)
        assert all(0 <= x < w and 0 <= y < h for x, y in reach[name]), name
    px, py = cfg['player']['startX'], cfg['player']['startY']
    assert (px, py) in reach['Tokyo']

    # the stitch decides ownership: a cell two districts share is walkable or
    # not by the LATER one's map. Block Palace's copy of a shared cell and the
    # same cell, seen from Market, is no longer somewhere to stand.
    at = {d[0]: d for d in districts}
    shared = None
    for x, y in sorted(reach['Palace']):
        mx, my = x + at['Palace'][1] - at['Market'][1], y + at['Palace'][2] - at['Market'][2]
        if 0 <= mx < at['Market'][3] and 0 <= my < at['Market'][4]:
            shared = (x, y, mx, my)
            break
    assert shared, 'Market and Palace share no walkable cell'
    assert shared[2:] in reach['Market']
    cut = copy.deepcopy(cfg)
    colliders = next(l for l in cut['rooms']['Palace']['layers'] if l.get('collision'))
    colliders['tiles'][f'{shared[0]},{shared[1]}'] = next(iter(colliders['tiles'].values()))
    assert shared[2:] not in b.reachable_cells(cut, 'Market'), shared
    assert b.walkable_near(cut, 'Market', *shared[2:]) != shared[2:]
    # ...and someone standing on it in Palace occupies it for Market too
    cfg2 = copy.deepcopy(cfg)
    cfg2['rooms']['Palace']['npcs'].append(dict(b.hidden_base_def('Zed', shared[0], shared[1]), present=True))
    assert shared[2:] in b.occupied_cells(cfg2, 'Market', '2025-11-01', 'nobody')
    assert shared[2:] not in b.occupied_cells(cfg, 'Market', '2025-11-01', 'nobody')

    # without the city block the districts are judged alone, as before
    alone = copy.deepcopy(cfg)
    del alone['cities']
    assert b.city_districts(alone, 'Market') is None
    assert (58, 22) in b.reachable_cells(alone, 'Tokyo')     # seeded by its seam transporter again

    # the pin: every cell of every room, python against the game's stitcher
    node = shutil.which('node')
    assert node, 'node is needed to pin blog_to_npc reachability to the game (tools/play.js reach)'
    here = os.path.dirname(os.path.abspath(__file__))
    out = subprocess.run([node, os.path.join(here, 'play.js'), 'reach'], capture_output=True, text=True,
                         env=dict(os.environ, OPENSSL_CONF='/dev/null'), check=True).stdout
    game = {room: {tuple(map(int, c.split(','))) for c in cells} for room, cells in json.loads(out).items()}
    assert set(game) == set(cfg['rooms'])
    checked = 0
    for room_key in b.overworld_rooms(cfg):
        mine = b.reachable_cells(cfg, room_key)
        assert mine is not None, room_key
        w, h, _, _ = b.room_cells(cfg, room_key)
        diff = sorted((mine ^ game[room_key]))
        assert not diff, (f'{room_key}: blog_to_npc and the game disagree on {len(diff)} cell(s), e.g. {diff[:8]} '
                          f'(python-only: {sorted(mine - game[room_key])[:4]}, game-only: {sorted(game[room_key] - mine)[:4]})')
        checked += w * h
    assert checked > 20000, checked


def test_landmark_rules():
    """landmark_applies on a made-up world: outdoors, a station, an interior."""
    cfg = {'rooms': {'Sendai': {}, 'Other': {}, 'SendaiStation': {}, 'Shop': {'interior': True}},
           'stations': {'SendaiStation': {}},
           # find_spots weighs a stand cell against the room's floor (#189)
           'game': {'gridSize': 64, 'worldWidth': 640, 'worldHeight': 640}}
    plain, lane, platform = {}, {'rooms': ('Sendai',)}, {'indoors': True}
    assert [b.landmark_applies(cfg, r, plain) for r in cfg['rooms']] == [True, True, False, False]
    assert [b.landmark_applies(cfg, r, lane) for r in cfg['rooms']] == [True, False, False, False]
    assert [b.landmark_applies(cfg, r, platform) for r in cfg['rooms']] == [False, False, True, True]
    assert b.landmark_fields(('a-', 'A')) == ('a-', 'A', (0, 0), {})
    assert b.landmark_fields(('a-', 'A', (1, 2))) == ('a-', 'A', (1, 2), {})
    assert b.landmark_fields(('a-', 'A', lane)) == ('a-', 'A', (0, 0), lane)
    assert b.landmark_fields(('a-', 'A', (1, 2), lane)) == ('a-', 'A', (1, 2), lane)

    # find_spots on it: the shop offers nothing even to an 'indoors' landmark
    # (the pipeline keeps no books in `interior` rooms), the station only that
    tiles = {'layers': [{'name': 'Other', 'tiles': {'3,4': 'white-vending-machine-top_0_0',
                                                    '6,6': 'sendai-pub_0_0'}}]}
    for room in cfg['rooms'].values():
        room.update(tiles)
    assert b.find_spots(cfg) == {
        'Sendai · the vending machines': ('Sendai', 3, 4),
        'Other · the vending machines': ('Other', 3, 4),
        'Sendai · the HUB pub': ('Sendai', 9, 11),
        'SendaiStation · the platform': ('SendaiStation', 3, 4),
    }


def test_post_source(base_cfg):
    """A placement records the post's title, and its url when the payload has one."""
    cfg = copy.deepcopy(base_cfg)
    spots = b.find_spots(cfg)
    spot = sorted(spots)[0]
    date = '2031-03-04'

    def state():
        (_, st), = [(r, s) for r, s in placements(cfg, 'Bailey', date) if s.get('present')]
        return st

    place(cfg, dict(post(1, title='  Ramen,\n again '), url='https://devhou.se/posts/1'), spot, spots)
    assert state()['posts'] == [{'id': '1', 'lines': 2, 'title': 'Ramen, again',
                                 'url': 'https://devhou.se/posts/1'}]
    # a second post the same day keeps the first one's title and url
    place(cfg, post(2, title='Trains'), spot, spots)
    assert state()['posts'] == [
        {'id': '1', 'lines': 2, 'title': 'Ramen, again', 'url': 'https://devhou.se/posts/1'},
        {'id': '2', 'lines': 2, 'title': 'Trains'}]
    # a url that is not a web address is not recorded; nor is a blank title
    assert b.post_entry(3, 1, '  ', 'javascript:alert(1)') == {'id': '3', 'lines': 1}
    assert b.post_entry(3, 1, None, None) == {'id': '3', 'lines': 1}
    assert b.post_entry(3, 1, 'T', 'http://x.test/3') == {'id': '3', 'lines': 1, 'title': 'T', 'url': 'http://x.test/3'}


def test_backfill_posts():
    def npc(name, states):
        return {'name': name, 'states': states}
    cfg = {'rooms': {
        'A': {'npcs': [
            npc('Bailey', {
                # already has "posts": titles are filled in per id
                '2031-01-01': {'dialogue': ['a', 'b', 'c'], 'photo': None,
                               'posts': [{'id': '10', 'lines': 2}, {'id': '11', 'lines': 1, 'title': 'old'}]},
                # no "posts": the photo is the post id
                '2031-01-02': {'dialogue': ['a', 'b'], 'photo': '12'},
                # neither: the one post by baely that day
                '2031-01-03': {'dialogue': ['a'], 'photo': None},
                # two posts that day and nothing to tell them apart: left alone
                '2031-01-04': {'dialogue': ['a'], 'photo': None},
                # not a placement
                '2031-01-05': {'present': False},
                '2031-01-06': {'present': False, 'dialogue': ['a'], 'photo': '12'},
                # a post the list does not know
                '2031-01-07': {'dialogue': ['a'], 'photo': '99'},
            }),
            npc('Julia', {'2031-01-03': {'dialogue': ['j'], 'photo': None}}),
            {'name': 'Shopkeeper', 'dialogue': ['hi']},
        ]},
    }}
    entries = [
        {'id': 10, 'title': 'Ten', 'url': 'https://b.test/10'},
        {'id': '11', 'title': 'Eleven'},
        {'id': 12, 'title': 'Twelve', 'url': 'https://b.test/12'},
        {'id': 13, 'title': 'Thirteen', 'url': 'https://b.test/13', 'author': 'Baely', 'date': '2031-01-03T09:00:00Z'},
        {'id': 14, 'title': 'Fourteen', 'author': 'baely', 'date': '2031-01-04'},
        {'id': 15, 'title': 'Fifteen', 'author': 'baely', 'date': '2031-01-04'},
        {'id': 16, 'title': 'Sixteen', 'author': 'nobody', 'date': '2031-01-03'},
        {'title': 'no id'}, 'junk',
    ]
    before = copy.deepcopy(cfg)
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        changed = b.backfill_posts(cfg, entries)
    st = cfg['rooms']['A']['npcs'][0]['states']
    assert changed == 3, out.getvalue()
    assert st['2031-01-01']['posts'] == [{'id': '10', 'lines': 2, 'title': 'Ten', 'url': 'https://b.test/10'},
                                         {'id': '11', 'lines': 1, 'title': 'Eleven'}]
    assert st['2031-01-02']['posts'] == [{'id': '12', 'lines': 2, 'title': 'Twelve', 'url': 'https://b.test/12'}]
    assert st['2031-01-03']['posts'] == [{'id': '13', 'lines': 1, 'title': 'Thirteen', 'url': 'https://b.test/13'}]
    for date in ('2031-01-04', '2031-01-05', '2031-01-06', '2031-01-07'):
        assert st[date] == before['rooms']['A']['npcs'][0]['states'][date], date
    assert cfg['rooms']['A']['npcs'][1:] == before['rooms']['A']['npcs'][1:]     # Julia: nobody listed for her
    # nothing but "posts" changed anywhere
    for date, state in st.items():
        was = before['rooms']['A']['npcs'][0]['states'][date]
        assert {k: v for k, v in state.items() if k != 'posts'} == {k: v for k, v in was.items() if k != 'posts'}
    assert '14, 15' in out.getvalue() and 'left alone' in out.getvalue()
    assert 'matched nothing: 14, 15, 16' in out.getvalue(), out.getvalue()
    # a second run finds nothing left to do
    with contextlib.redirect_stdout(io.StringIO()):
        assert b.backfill_posts(cfg, entries) == 0
    # a listed post with a null (or missing) title or url keeps what the state already records
    with contextlib.redirect_stdout(io.StringIO()):
        assert b.backfill_posts(cfg, [{'id': 10, 'title': None, 'url': 'https://b.test/ten'},
                                      {'id': 11, 'url': None}, {'id': 12, 'title': '', 'url': None}]) == 1
    assert st['2031-01-01']['posts'] == [{'id': '10', 'lines': 2, 'title': 'Ten', 'url': 'https://b.test/ten'},
                                         {'id': '11', 'lines': 1, 'title': 'Eleven'}]
    assert st['2031-01-02']['posts'] == [{'id': '12', 'lines': 2, 'title': 'Twelve', 'url': 'https://b.test/12'}]
    st['2031-01-01']['posts'][0]['url'] = 'https://b.test/10'
    # the backfilled "posts" are what merge_same_day expects: a re-run of post 12 replaces its lines
    assert b.merge_same_day(st['2031-01-02'], 12, ['x'], None, False, title='Twelve!') == (
        ['x'], None, False, [{'id': '12', 'lines': 1, 'title': 'Twelve!'}])


def test_shipped_posts(cfg):
    """Every "posts" in config.json adds up to its dialogue (the game captions
    lines by these counts) and no title was made up for a state without one."""
    for room_key, room in cfg['rooms'].items():
        for npc in room.get('npcs', []):
            for date, st in npc.get('states', {}).items():
                made_by = st.get('posts')
                if made_by is None:
                    continue
                where = f'{room_key} {npc["name"]} {date}'
                assert sum(p['lines'] for p in made_by) == len(st['dialogue']), where
                assert all(str(p['id']) == p['id'] for p in made_by), where
def test_photos(cfg):
    """Every shipped print is referenced and every referenced print exists;
    prune_photos removes exactly the prints no state points at."""
    shipped = {os.path.splitext(f)[0] for f in os.listdir(post_photos.PHOTO_DIR)
               if f.endswith('.png')}
    wanted = post_photos.referenced_photos(cfg)
    assert shipped - wanted == set(), f'orphaned photos: {sorted(shipped - wanted)}'
    assert wanted - shipped == set(), f'missing photos: {sorted(wanted - shipped)}'

    fake = {'rooms': {'A': {'npcs': [
        {'name': 'Bailey', 'photo': '1', 'states': {
            '2031-01-01': {'photo': '2'}, '2031-01-02': {'photo': None},
            '2031-01-03': {'photo': 3}}}]}}}
    assert post_photos.referenced_photos(fake) == {'1', '2', '3'}
    with tempfile.TemporaryDirectory() as tmp:
        for name in ('1.png', '2.png', '3.png', '4.png', '5.png', 'README.md'):
            open(os.path.join(tmp, name), 'w').close()
        os.mkdir(os.path.join(tmp, '6.png'))
        with contextlib.redirect_stdout(io.StringIO()) as out:
            assert post_photos.prune_photos(fake, tmp) == ['4', '5']
            assert post_photos.prune_photos(fake, tmp) == []
        assert 'removed 2 superseded' in out.getvalue()
        assert sorted(os.listdir(tmp)) == ['1.png', '2.png', '3.png', '6.png', 'README.md']
    assert post_photos.prune_photos(fake, os.path.join(tmp, 'gone')) == []

    # a run that places nothing still prunes: a post that fails after its
    # photo was imported must not leave the print behind
    def fails_after_import(cfg, post, *args, **kwargs):
        open(os.path.join(post_photos.PHOTO_DIR, '9.png'), 'w').close()
        raise RuntimeError('boom')
    here, argv, real = os.getcwd(), sys.argv, b.process_post
    with tempfile.TemporaryDirectory() as tmp:
        try:
            os.chdir(tmp)
            os.makedirs(post_photos.PHOTO_DIR)
            open(os.path.join(post_photos.PHOTO_DIR, '7.png'), 'w').close()
            json.dump({'rooms': {'A': {'npcs': [{'name': 'Bailey', 'photo': '7'}]}}}, open('config.json', 'w'))
            json.dump({'post_id': 9}, open('post.json', 'w'))
            before = open('config.json').read()
            b.process_post, sys.argv = fails_after_import, ['blog_to_npc.py', '--payload', 'post.json']
            with contextlib.redirect_stdout(io.StringIO()) as out:
                assert b.main() == 0
            assert 'ERROR RuntimeError: boom' in out.getvalue(), out.getvalue()
            assert os.listdir(post_photos.PHOTO_DIR) == ['7.png'], os.listdir(post_photos.PHOTO_DIR)
            assert open('config.json').read() == before
        finally:
            b.process_post, sys.argv = real, argv
            os.chdir(here)


def test_authors(cfg):
    """Blog author login -> NPC: mapped authors resolve (any case), placeholder
    entries can never match, and an unmapped author's post is skipped with a
    warning that names the login and where to add it."""
    assert b.npc_for_author('baely') == 'Bailey' and b.npc_for_author(' Jughents ') == 'Julia'
    assert b.npc_for_author('nobody-here') is None and b.npc_for_author('') is None and b.npc_for_author(None) is None

    # what a login can and cannot be
    for ok in ('baely', 'dbut2', 'a', 'a-b', 'x' * 39, 'khoi_acme', 'a-b_c', 'some-app[bot]'):
        assert b.is_login(ok), ok
    for bad in ('', '<khoi github login>', 'two words', 'a--b', '-a', 'a-', 'x' * 40, 'Upper', '_a', 'todo:khoi',
                'a b', '<a>', 'a[bot]x', '[bot]'):
        assert not b.is_login(bad), bad

    # every placeholder key is unmatchable — even when a post's author field
    # is, verbatim, the placeholder text
    table = {'baely': 'Bailey', '<khoi github login>': 'Khoi', '<sam github login>': 'Sam'}
    assert b.awaiting_login(table) == ['Khoi', 'Sam']
    assert b.npc_for_author('<khoi github login>', table) is None
    assert b.npc_for_author('khoi', table) is None                 # the NPC's name is not their login
    assert b.awaiting_login({'baely': 'Bailey'}) == []
    # an Enterprise Managed User login (underscore) maps like any other
    assert b.npc_for_author('Khoi_Acme', {'khoi_acme': 'Khoi'}) == 'Khoi'
    assert b.awaiting_login({'khoi_acme': 'Khoi'}) == []
    for key in b.AUTHOR_NPCS:
        assert b.is_login(key) or (key.startswith('<') and key.endswith('>')), key
        assert b.npc_for_author(key) == (b.AUTHOR_NPCS[key] if b.is_login(key) else None), key

    # every NPC the table names can be created: it has a full sprite set
    for npc in b.AUTHOR_NPCS.values():
        for d in ('front', 'back', 'side'):
            assert f'{npc.lower()}_{d}' in cfg['spriteMetadata'], f'{npc}: no {d} sprite'

    # the warning names the login, the file, and who is still waiting
    w = b.unmapped_author_warning(42, 'newperson', table)
    assert w.startswith('WARNING: #42:') and "'newperson': '<NPC name>'" in w, w
    assert 'AUTHOR_NPCS' in w and 'blog_to_npc.py' in w and 'Khoi, Sam' in w, w
    assert 'waiting' not in b.unmapped_author_warning(42, 'newperson', {'baely': 'Bailey'})

    # end to end: an unmapped author is skipped loudly and nothing is placed;
    # the same post under a mapped login lands
    saved = dict(b.AUTHOR_NPCS)
    try:
        b.AUTHOR_NPCS.clear()
        b.AUTHOR_NPCS.update(table)
        work = copy.deepcopy(cfg)
        spots = b.find_spots(work)
        post = {'post_id': 77, 'title': 't', 'author': 'NewPerson', 'date': '2031-04-01', 'content': 'hello'}
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            record, usage = b.process_post(work, post, spots, sorted(spots), mock=True, dry_run=True)
        assert record is None and usage is None and work == cfg
        assert "WARNING: #77: blog author 'newperson' is not mapped" in out.getvalue(), out.getvalue()
        assert 'still waiting for a login: Khoi, Sam' in out.getvalue(), out.getvalue()

        # the login arrives: replace the placeholder and the post is placed —
        # for someone who had no NPC in that room before (hidden base def)
        del b.AUTHOR_NPCS['<khoi github login>']
        b.AUTHOR_NPCS['newperson'] = 'Khoi'
        with contextlib.redirect_stdout(io.StringIO()):
            record, _ = b.process_post(work, post, spots, sorted(spots), mock=True, dry_run=True)
        assert record and record['npc'] == 'Khoi' and record['date'] == '2031-04-01', record
        here = [(r, s) for r, s in placements(work, 'Khoi', '2031-04-01') if s.get('present')]
        assert len(here) == 1 and here[0][1]['dialogue'], here
    finally:
        b.AUTHOR_NPCS.clear()
        b.AUTHOR_NPCS.update(saved)


def test_post_date(cfg):
    """A post's day is the day where the trip is, when the trip says how far
    ahead of UTC that is (issue #119); otherwise the UTC date, as ever."""
    day = lambda when, c=cfg: b.post_date(c, {'date': when})
    trip = next(t for t in cfg['trips'] if t['id'] == 'devhouse3')
    assert trip.get('utcOffset') == 9, 'devhouse 3 is in Japan'
    assert all('utcOffset' not in t for t in cfg['trips'] if t['id'] == 'devhouse2'), \
        'devhouse 2 history was written with UTC dates: an offset would re-date a re-run post'
    # 08:30 in Asahikawa on the day the group moves there: UTC still says the 24th
    assert day('2027-02-24T23:30:00Z') == '2027-02-25'
    assert day('2027-02-24T14:59:59Z') == '2027-02-24' and day('2027-02-24T15:00:00Z') == '2027-02-25'
    # the first morning of the trip, and a post from the road in the lead-in
    assert day('2027-02-17T23:15:00+00:00') == '2027-02-18'
    assert day('2027-02-11T20:00:00Z') == '2027-02-12'
    # the first hours of the first lead-in day are still devhouse 2's day in UTC
    assert day('2027-01-18T16:00:00Z') == '2027-01-19' and day('2027-01-18T14:59:00Z') == '2027-01-18'
    # any zone is the same moment
    assert day('2027-02-18T08:15:00+09:00') == '2027-02-18' and day('2027-02-18T10:15:00+11:00') == '2027-02-18'
    # nothing to convert: a bare date, a time with no zone, a trip with no offset, no trips
    assert day('2027-02-20') == '2027-02-20' and day('2027-02-20T23:30:00') == '2027-02-20'
    assert day('2025-11-11T23:30:00Z') == '2025-11-11'
    assert day('2027-02-24T23:30:00Z', {'trips': []}) == '2027-02-24'
    assert day('2027-02-24T23:30:00Z', {'trips': [dict(trip, utcOffset=True)]}) == '2027-02-24'
    assert day('2027-02-24T23:30:00Z', {'trips': [dict(trip, utcOffset=-10)]}) == '2027-02-24'
    assert day(None) == '' and day('2027-02-2') == '2027-02-2'
    # … and what is not a date is skipped, not placed under a made-up day
    spots = b.find_spots(cfg)
    for bad in (None, '2027-02-2', 'next Tuesday', '2027-02-30T99:00:00Z'):
        work, out = copy.deepcopy(cfg), io.StringIO()
        with contextlib.redirect_stdout(out):
            record, _ = b.process_post(work, dict(post(1), date=bad), spots, sorted(spots), mock=True, dry_run=True)
        assert record is None and work == cfg and 'bad date' in out.getvalue(), (bad, out.getvalue())
    # … by the backfill too: an impossible day is not a day to match a state on
    assert b.post_date(cfg, {'date': '2027-02-30T01:00:00Z'}) == '2027-02-30' and not b.is_day('2027-02-30')
    # end to end: the early-morning post lands on the Asahikawa day
    work = copy.deepcopy(cfg)
    record = place(work, dict(post(2), date='2027-02-24T23:30:00Z'), 'Asahikawa · the Asahiyama Zoo gate', spots)
    assert record['date'] == '2027-02-25', record
    assert [r for r, st in placements(work, 'Bailey', '2027-02-25') if st.get('present')] == ['Asahikawa']
    assert placements(work, 'Bailey', '2027-02-24') == []


def test_mock_steer(cfg):
    """--mock takes its spot, lines and drunk flag from the payload's "mock"
    (tools/rehearse_blog.py sends each post where it is about)."""
    ids_ = ['A · one', 'B · two']
    plain, usage = b.generate(post(1), 'Bailey', ids_, mock=True)
    assert usage is None and plain['spot'] == 'A · one' and plain['drunk'] is False and len(plain['dialogue']) == 2
    steered, _ = b.generate(dict(post(1), mock={'spot': 'B · two', 'dialogue': ['hi'], 'drunk': True, 'other': 1}),
                            'Bailey', ids_, mock=True)
    assert steered == {'spot': 'B · two', 'dialogue': ['hi'], 'drunk': True}, steered
    part, _ = b.generate(dict(post(1), mock={'drunk': True}), 'Bailey', ids_, mock=True)
    assert part == dict(plain, drunk=True)
    assert b.generate(dict(post(1), mock='B · two'), 'Bailey', ids_, mock=True)[0] == plain
    # a steered spot that is not on offer is refused like any model answer
    work, spots, out = copy.deepcopy(cfg), b.find_spots(cfg), io.StringIO()
    with contextlib.redirect_stdout(out):
        record, _ = b.process_post(work, dict(post(3), mock={'spot': 'Nowhere · at all'}), spots, sorted(spots),
                                   mock=True, dry_run=True)
    assert record is None and work == cfg and 'unusable content' in out.getvalue()


def test_not_in_the_way(cfg):
    """A placement never seals off part of the map or the people in it
    (issue #119: Asahikawa's ramen alley was one cell wide)."""
    # walls_in on a hand-drawn lane: x 0..6 on row 1, an alcove at (3,0), a yard 2x2 at the east end
    lane = {(x, 1) for x in range(7)} | {(3, 0)} | {(5, 2), (6, 2)}
    assert b.walls_in((2, 1), lane), 'the middle of a one-cell lane'
    assert not b.walls_in((3, 0), lane), 'the alcove off it'
    assert not b.walls_in((0, 1), lane), 'the end of a dead end seals nothing'
    assert not b.walls_in((6, 2), lane) and not b.walls_in((6, 1), lane), 'the yard can be walked round'
    assert b.walls_in((4, 1), lane), 'the mouth of the yard'
    assert b.walls_in((3, 0), {(3, 0)}), 'nowhere to be walked up to from'
    open_ground = {(x, y) for x in range(5) for y in range(5)}
    assert not any(b.walls_in(c, open_ground) for c in open_ground)
    cross = {(2, y) for y in range(5)} | {(x, 2) for x in range(5)}
    assert b.walls_in((2, 2), cross), 'the middle of a crossroads'

    # walkable_near on the same lane as a room: the landmark's cell is the lane, so the alcove it is
    floor = {f'{x},{y}': 'f' for x, y in lane}
    tiny = {'game': {'gridSize': 64, 'worldWidth': 7 * 64, 'worldHeight': 3 * 64},
            'rooms': {'A': {'layers': [{'name': 'Floor', 'tiles': floor}],
                            'transporters': [{'gridX': 0, 'gridY': 1, 'targetRoom': 'A', 'targetX': 1, 'targetY': 1}]}}}
    assert b.walkable_near(tiny, 'A', 3, 1) == (3, 0)
    # with somebody in the alcove already the next person goes where they wall nobody in
    second = b.walkable_near(tiny, 'A', 3, 1, {(3, 0)})
    assert second in {(5, 2), (6, 2), (6, 1), (5, 1)}, second
    # … and never beside someone whose only way to be reached is that cell
    corner = {'game': tiny['game'], 'rooms': {'A': {
        'layers': [{'name': 'Floor', 'tiles': {f'{x},{y}': 'f' for x in range(7) for y in range(3)}},
                   {'name': 'Walls', 'collision': True, 'tiles': {'5,1': 'w', '6,1': 'w', '5,0': 'w'}}],
        'transporters': tiny['rooms']['A']['transporters']}}}
    # (6,0) is a pocket nobody can get to; (6,2) is reached along row 2 only
    assert b.walkable_near(corner, 'A', 6, 0) != (6, 0)
    assert b.walkable_near(corner, 'A', 5, 2, {(6, 2)}) != (5, 2), 'would leave (6,2) unreachable'

    # an alley one cell wide between two yards (what Asahikawa's ramen alley was until it was rebuilt two
    # cells wide, issue #219): seven posts about it stand in the yards, and the alley stays one walk
    alley = {(x, 2) for x in range(3, 10)} | {(x, y) for x in (0, 1, 2, 10, 11, 12) for y in range(5)}
    town = {'game': {'gridSize': 64, 'worldWidth': 13 * 64, 'worldHeight': 5 * 64},
            'rooms': {'A': {'layers': [{'name': 'Floor', 'tiles': {f'{x},{y}': 'f' for x, y in alley}}],
                            'transporters': [{'gridX': 0, 'gridY': 0, 'targetRoom': 'A', 'targetX': 1, 'targetY': 1}]}}}
    room, x, y = 'A', 6, 2
    region = b.walk_region(town, room)
    assert b.walls_in((x, y), region), 'the middle of the alley is in the way'
    taken = set()
    for _ in b.AUTHOR_NPCS:
        cell = b.walkable_near(town, room, x, y, taken)
        assert cell is not None and not b.walls_in(cell, region - taken), (cell, sorted(taken))
        assert cell[1] != 2 or not 3 <= cell[0] <= 9, f'{cell} is in the alley'
        taken.add(cell)
    # the shipped alley: anybody can be stood on any cell of its south row
    region = b.walk_region(cfg, 'Asahikawa')
    for ax in range(2, 17):
        assert (ax, 15) in region and not b.walls_in((ax, 15), region), f'Asahikawa ({ax}, 15) is refused'
    spots = b.find_spots(cfg)
    # every spot, seven deep: nobody walls anything in, and everyone can be walked up to
    for spot_id, (room, x, y) in sorted(spots.items()):
        region, taken = b.walk_region(cfg, room), set()
        for _ in b.AUTHOR_NPCS:
            cell = b.walkable_near(cfg, room, x, y, taken)
            assert cell is not None, f'{spot_id}: nowhere left to stand with {sorted(taken)} taken'
            assert not b.walls_in(cell, region - taken), (spot_id, cell)
            taken.add(cell)
        for cx, cy in taken:
            assert any(n in region and n not in taken for n in ((cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1))), \
                f'{spot_id}: {(cx, cy)} cannot be walked up to with {sorted(taken)} there'
    # Odori Park is a spot of its own, on the path down the middle of the park
    assert spots['Sapporo · Odori Park'][0] == 'Sapporo' and 26 <= spots['Sapporo · Odori Park'][2] <= 27, spots['Sapporo · Odori Park']
    assert [s for s in spots if s.endswith('· Odori Park')] == ['Sapporo · Odori Park']


def test_shipped_dialogue(cfg):
    """Nothing in config.json is over the limit or cut mid-word at it."""
    for room_key, room in cfg['rooms'].items():
        for npc in room.get('npcs', []):
            for date, st in npc.get('states', {}).items():
                for line in st.get('dialogue') or []:
                    where = f'{room_key} {npc["name"]} {date}: {line!r}'
                    assert len(line) <= b.MAX_LINE_CHARS, where
                    assert len(line) < b.MAX_LINE_CHARS or line[-1] in '.!?…。！？', where


def whereabouts(cfg, npc_name, date):
    """[(room, x, y)] — everywhere the game shows this NPC on date (the
    izakaya's opponent is a fixture, not the travelling NPC)."""
    window = b.trip_window(cfg, date)
    out = []
    for room_key, room in cfg['rooms'].items():
        npc = b.npc_in_room(room, npc_name)
        if npc is None or npc.get('drinkingGameOpponent'):
            continue
        present, x, y = b.resolve_pos(npc, date, window)
        if present:
            out.append((room_key, x, y))
    return out


def test_trips(base_cfg):
    """Trip-scoped base NPCs and dated states compose (issues #118, #131):
    before a trip's first post its members stand at the trip's base, a post
    moves its author as usual, a new stay starts from base again, and none of
    it shows on another trip's dates."""
    cfg = copy.deepcopy(base_cfg)
    spots = b.find_spots(cfg)

    def spot_in(room_key, label=None):
        return next(s for s, (r, _, _) in sorted(spots.items()) if r == room_key and (label is None or label in s))

    def base(room_key, name):
        npc = b.npc_in_room(cfg['rooms'][room_key], name)
        return (room_key, npc['gridX'], npc['gridY'])

    seven = ('Bailey', 'Damian', 'Dylan', 'Julia', 'Khoi', 'Sam', 'Xander')
    trips = {t['id']: t for t in cfg['trips']}
    assert trips['devhouse3']['members'] == [n.lower() for n in seven]
    assert all('james' not in t['members'] for t in cfg['trips'])
    assert b.trip_window(cfg, '2027-02-20')['stay']['room'] == 'Sapporo'
    assert b.trip_window(cfg, '2027-02-25')['from'] == '2027-02-25'
    assert b.trip_window(cfg, '2026-11-25')['trip']['id'] == 'devhouse2'
    assert b.trip_window({'rooms': {}}, '2027-02-20') is None
    # a trip opens before it starts (the lead-in — a fortnight, or its `lead` days: 30 for devhouse 3, #170):
    # its posts, nobody at the base yet
    assert trips['devhouse3'].get('lead') == 30
    assert b.trip_window(cfg, '2027-01-18')['trip']['id'] == 'devhouse2'
    early = b.trip_window(cfg, '2027-01-19')
    assert (early['trip']['id'], early['early'], early['from']) == ('devhouse3', True, '2027-01-19'), early
    no_lead = copy.deepcopy(cfg)
    del next(t for t in no_lead['trips'] if t['id'] == 'devhouse3')['lead']
    assert b.trip_window(no_lead, '2027-02-03')['trip']['id'] == 'devhouse2' and b.trip_window(no_lead, '2027-02-04')['from'] == '2027-02-04'
    lead = b.trip_window(cfg, '2027-02-10')
    assert (lead['trip']['id'], lead['early'], lead['from']) == ('devhouse3', True, '2027-01-19'), lead
    assert b.trip_window(cfg, '2027-02-18')['early'] is False and b.trip_window(cfg, '2025-09-01')['early'] is False
    cfg_l = copy.deepcopy(cfg)
    for name in seven:
        assert whereabouts(cfg_l, name, '2027-02-10') == [], name
    place(cfg_l, post(900, date='2027-02-10'), spot_in('Tokyo'), spots)       # a post on the way there
    assert [r for r, _, _ in whereabouts(cfg_l, 'Bailey', '2027-02-10')] == ['Tokyo']
    assert [r for r, _, _ in whereabouts(cfg_l, 'Bailey', '2027-02-17')] == ['Tokyo']
    assert whereabouts(cfg_l, 'Bailey', '2027-02-18') == [base('Sapporo', 'Bailey')]     # day one: at the base
    assert whereabouts(cfg_l, 'Bailey', '2025-11-02') == whereabouts(cfg, 'Bailey', '2025-11-02')

    # before any devhouse 3 post: everyone at the base, Sapporo then Asahikawa
    for name in seven:
        assert whereabouts(cfg, name, '2027-02-20') == [base('Sapporo', name)], name
        assert whereabouts(cfg, name, '2027-02-26') == [base('Asahikawa', name)], name
    # ...and the three new members are nowhere on a devhouse 2 date
    for name in ('Khoi', 'Sam', 'Xander'):
        assert whereabouts(cfg, name, '2025-11-02') == [], name
    before = {name: whereabouts(cfg, name, '2025-11-02') for name in seven}
    assert all(len(before[n]) == 1 for n in ('Bailey', 'Damian', 'Dylan', 'Julia')), before

    # Bailey's first devhouse 3 post moves him, off everybody else's cell
    place(cfg, post(901, date='2027-02-20'), spot_in('Sapporo', 'Clock Tower'), spots)
    (room, x, y), = whereabouts(cfg, 'Bailey', '2027-02-20')
    assert room == 'Sapporo' and (room, x, y) != base('Sapporo', 'Bailey')
    others = {whereabouts(cfg, n, '2027-02-20')[0] for n in seven if n != 'Bailey'}
    assert (room, x, y) not in others and len(others) == 6
    assert whereabouts(cfg, 'Bailey', '2027-02-19') == [base('Sapporo', 'Bailey')]      # the day before: still base
    assert whereabouts(cfg, 'Bailey', '2027-02-24') == [(room, x, y)]                   # stays put until the group moves
    # the group moves base: he is in Asahikawa with the rest, though his last post was Sapporo
    assert whereabouts(cfg, 'Bailey', '2027-02-25') == [base('Asahikawa', 'Bailey')]
    # a post from Asahikawa moves him there
    place(cfg, post(902, date='2027-02-26'), spot_in('Asahikawa'), spots)
    (room2, x2, y2), = whereabouts(cfg, 'Bailey', '2027-02-26')
    assert room2 == 'Asahikawa' and (room2, x2, y2) != base('Asahikawa', 'Bailey')
    # a post from a room that is another trip's home still places him (and only there)
    place(cfg, post(903, date='2027-02-27'), spot_in('Tokyo'), spots)
    (room3, _, _), = whereabouts(cfg, 'Bailey', '2027-02-27')
    assert room3 == 'Tokyo'
    assert whereabouts(cfg, 'Bailey', '2027-02-26') == [(room2, x2, y2)]
    # a room he had never been in gets a hidden base def, as ever
    fresh = next(r for r in sorted({r for r, _, _ in spots.values()})
                 if b.npc_in_room(cfg['rooms'][r], 'Khoi') is None)
    cfg_k = copy.deepcopy(cfg)
    cell = b.walkable_near(cfg_k, fresh, *spots[spot_in(fresh)][1:],
                           b.occupied_cells(cfg_k, fresh, '2027-02-21', 'Khoi'))
    assert any('hidden base def' in c for c in b.apply(cfg_k, 'Khoi', '2027-02-21', fresh, *cell, ['hello']))
    assert [r for r, _, _ in whereabouts(cfg_k, 'Khoi', '2027-02-21')] == [fresh]
    assert whereabouts(cfg_k, 'Khoi', '2027-02-25') == [base('Asahikawa', 'Khoi')]
    assert whereabouts(cfg_k, 'Khoi', '2025-11-02') == []

    # nobody else moved, and devhouse 2 is exactly as it was
    for name in seven:
        if name != 'Bailey':
            assert whereabouts(cfg, name, '2027-02-27') == [base('Asahikawa', name)], name
        assert whereabouts(cfg, name, '2025-11-02') == before[name], name
    # every dated day so far belongs to exactly one trip, and its base cast is still valid data
    for room_key in ('Sapporo', 'Asahikawa'):
        for npc in base_cfg['rooms'][room_key]['npcs']:
            assert npc.get('trip') == 'devhouse3' and npc.get('stay') == room_key, (room_key, npc['name'])
            assert npc.get('present') is not False and len(npc['dialogue']) >= 2


def test_tiled_ids_stable():
    """config_to_tiled keeps every sprite's tile id when a room gains or loses
    sprites, so a map change does not renumber the whole .tmj (#108)."""
    import json
    # a fresh room is numbered in sorted order, as before
    assert c2t.assign_ids({'b', 'a', 'c'}, {}) == {'a': 0, 'b': 1, 'c': 2}
    # a new sprite goes after the highest id, wherever it sorts
    prev = {'b': 0, 'd': 1, 'f': 2}
    assert c2t.assign_ids({'a', 'b', 'd', 'e', 'f'}, prev) == {'b': 0, 'd': 1, 'f': 2, 'a': 3, 'e': 4}
    # a dropped sprite leaves a gap; nothing else moves and no id is shared
    kid = c2t.assign_ids({'b', 'f', 'z'}, prev)
    assert kid == {'b': 0, 'f': 2, 'z': 3}, kid
    # the image path round-trips to the key, collider marker included
    assert c2t.sprite_key('../assets/sprites/collider-marker.png') == 'gk_blank'
    assert c2t.sprite_key('../assets/sprites/gravel-autotile_edge-n.png') == 'gravel-autotile_edge-n'
    assert c2t.previous_ids('tiled/no-such-room.tmj') == {}
    # every shipped map: ids unique, and re-deriving them from the file itself
    # with one extra sprite leaves all existing ids alone
    tiled = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'tiled')
    for name in sorted(os.listdir(tiled)):
        if not name.endswith('.tmj'):
            continue
        path = os.path.join(tiled, name)
        tiles = json.load(open(path))['tilesets'][0]['tiles']
        prev = c2t.previous_ids(path)
        assert len(prev) == len(tiles) == len(set(prev.values())), name
        kid = c2t.assign_ids(set(prev) | {'!new-sprite'}, prev)
        new = kid.pop('!new-sprite')
        assert kid == prev and new == max(prev.values()) + 1, name


def test_tiled_maps_in_sync():
    """check_generators covers the Tiled maps: every room's committed .tmj is
    what config_to_tiled writes for it, and a map that drifted is named (#186)."""
    cg = check_generators
    root = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
    rooms = cg.tiled_rooms(root)
    assert 'Tokyo' in rooms and 'Market' in rooms and len(rooms) >= 30, rooms
    assert cg.TILED in cg.CHECKS and set(cg.GENERATORS) < set(cg.CHECKS)
    assert cg.check([cg.TILED], root) == {}, 'a tiled/*.tmj is out of step with config.json'
    # restore() names what a tool changed / added / removed and puts it back
    with tempfile.TemporaryDirectory() as tmp:
        a, w = os.path.join(tmp, 'a'), os.path.join(tmp, 'w')
        for base in (a, w):
            for rel in cg.OUTPUTS:
                os.makedirs(os.path.join(base, rel))
            for rel, text in (('tiled/one.tmj', '1'), ('tiled/two.tmj', '2')):
                open(os.path.join(base, rel), 'w').write(text)
        assert cg.restore(a, w) == []
        open(os.path.join(w, 'tiled/one.tmj'), 'w').write('edited')
        os.remove(os.path.join(w, 'tiled/two.tmj'))
        open(os.path.join(w, 'assets/sprites/new.png'), 'w').write('x')
        assert cg.restore(a, w) == ['tiled/one.tmj changed', 'tiled/two.tmj REMOVED',
                                    'assets/sprites/new.png ADDED']
        assert cg.restore(a, w) == [] and open(os.path.join(w, 'tiled/one.tmj')).read() == '1'


def test_generator_check_skips():
    """check_generators covers generate_ads and generate_cast, and lists a tool
    it cannot run here as skipped rather than failed: every art tool without
    Pillow (#193). None waits on a system font: the ads (#279) and the Don
    Takote sign (#346) are set in the game's own PixelMplus12."""
    cg = check_generators
    assert {'generate_ads', 'generate_cast', 'extract_city'} < set(cg.ART_TOOLS)
    assert not hasattr(cg, 'FONT_TOOLS') and not hasattr(cg, 'have_jp_font')
    assert 'assets/ads' in cg.OUTPUTS and 'src' in cg.INPUTS and 'fonts' in cg.INPUTS
    assert cg.skips(cg.CHECKS, True) == {}
    assert sorted(cg.skips(cg.CHECKS, False)) == sorted(cg.ART_TOOLS)
    assert cg.skips(['generate_osaka', cg.TILED], False) == {}
    for tool in ('extract_city.py', 'generate_ads.py'):     # no system font is looked for any more
        src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), tool)).read()
        assert 'find_font' not in src and '/System/Library/Fonts' not in src, tool


def png_bytes(rows, level=9):
    """A small RGBA PNG of `rows` (lists of (r, g, b, a)), deflated at `level`."""
    def chunk(kind, data):
        return struct.pack('>I', len(data)) + kind + data + struct.pack('>I', zlib.crc32(kind + data))
    raw = b''.join(b'\0' + bytes(v for px in row for v in px) for row in rows)
    return (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', len(rows[0]), len(rows), 8, 6, 0, 0, 0))
            + chunk(b'IDAT', zlib.compress(raw, level)) + chunk(b'IEND', b''))


def test_generator_check_pictures():
    """check_generators compares a PNG by its decoded pixels, not its bytes:
    the same picture deflated by another zlib is not drift, a changed pixel
    or size is (#230). Without Pillow it cannot decode, so bytes decide."""
    cg = check_generators
    assert (cg.pillow_version() is not None) == cg.have_pillow()
    red, blue, clear = (200, 30, 30, 255), (30, 30, 200, 255), (0, 0, 0, 0)
    rows = [[red] * 16, [blue] * 16, [clear] * 16, [red, blue] * 8]
    committed, recompressed = png_bytes(rows, 9), png_bytes(rows, 0)
    assert committed != recompressed
    pixel = png_bytes(rows[:3] + [[blue, red] * 8])
    hidden = png_bytes(rows[:2] + [[(9, 9, 9, 0)] * 16] + rows[3:])     # the colour under a clear pixel is data too
    size = png_bytes(rows + [[clear] * 16])
    with tempfile.TemporaryDirectory() as tmp:
        a, w = os.path.join(tmp, 'a'), os.path.join(tmp, 'w')
        for base in (a, w):
            for rel in cg.OUTPUTS:
                os.makedirs(os.path.join(base, rel))
        rel = 'assets/sprites/one.png'
        other = 'tiled/one.tmj'                 # a .tmj is text: bytes decide, whatever is in it
        for f in (rel, other):
            open(os.path.join(a, f), 'wb').write(committed)

        def rerun(data, f=rel):
            open(os.path.join(w, rel), 'wb').write(committed)
            open(os.path.join(w, other), 'wb').write(committed)
            open(os.path.join(w, f), 'wb').write(data)
            out = cg.restore(a, w)
            assert open(os.path.join(w, f), 'rb').read() == committed, 'the scratch copy was not put back'
            return out

        assert rerun(committed) == []
        assert rerun(recompressed, other) == [f'{other} changed']
        for data in (pixel, hidden, size, b'not a picture', committed[:40]):
            assert rerun(data) == [f'{rel} changed'], data[:40]
        same = os.path.join(w, 'same.png')
        open(same, 'wb').write(recompressed)
        if cg.have_pillow():
            assert rerun(recompressed) == [], 'the same pixels in other bytes were reported as drift'
            assert cg.same_picture(os.path.join(a, rel), same)
        else:
            assert rerun(recompressed) == [f'{rel} changed']
            assert not cg.same_picture(os.path.join(a, rel), same)
        assert not cg.same_picture(os.path.join(a, other), os.path.join(a, other))      # not a PNG by name


def test_sync_cities_anywhere():
    """sync_cities finds config.json and devhouse.world from its own place in
    the repo, not from the working directory (#193)."""
    gv2 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    assert sync_cities.CONFIG == os.path.join(gv2, 'config.json')
    assert sync_cities.WORLD == os.path.join(os.path.dirname(gv2), 'devhouse.world')
    here = os.getcwd()
    with tempfile.TemporaryDirectory() as tmp:
        os.chdir(tmp)
        try:
            cells = sync_cities.world_cells()
            sync_cities.check()             # exits if config and world disagree
        finally:
            os.chdir(here)
    assert cells['tokyo'] and cells['market'], sorted(cells)


# the four placements issue #219 moved to the place each post is about: (NPC, date) -> (room, cell)
REPLACED_219 = {
    ('Bailey', '2025-11-01'): ('Market', (26, 17)),         # Senso-ji: the foot of the hall's steps
    ('Julia', '2025-11-01'): ('Market', (49, 30)),          # four Don Quijotes: beside the Don Takote's doors
    ('Dylan', '2025-11-01'): ('Market', (6, 38)),           # the izakaya night: beside its door, not in front
    ('Damian', '2025-11-12'): ('Okayama', (13, 27)),        # Hakata to Okayama: Korakuen's lawn beside the first crane (issues #267, #276; it was Hakata's platform)
    ('Damian', '2025-11-14'): ('Nara', (35, 10)),           # the day in Nara: in front of the Great Buddha Hall (issue #268; it was Osaka's canal bank)
}


def test_districts(cfg):
    """config `districts` (tools/districts.py, issue #219): every town's named
    areas, offered to the placement model beside the named spots."""
    # in step with the one authored list, and it covers every outdoor town that is staying
    assert cfg.get('districts') == districts.build(cfg), 'config districts are stale: python3 tools/districts.py'
    outdoor = [k for k in b.overworld_rooms(cfg) if not b.is_indoors(cfg, k)]
    assert sorted(cfg['districts']) == sorted(k for k in outdoor if k not in districts.UNLABELLED), \
        sorted(set(outdoor) ^ set(cfg['districts']))
    assert set(districts.UNLABELLED) <= set(outdoor), 'a deleted town is still listed as unlabelled'
    assert not {'Machi', 'Inaka', 'Yukimura'} & (set(cfg['rooms']) | set(cfg['districts'])), 'a made-up town is back (#68)'
    assert 'districts' in check_generators.GENERATORS
    spots, areas = b.find_spots(cfg), b.find_areas(cfg)
    assert len(areas) == sum(len(v) for v in cfg['districts'].values()) >= 30
    for room_key, listed in cfg['districts'].items():
        w, h = b.room_cells(cfg, room_key)[:2]
        assert len({d['key'] for d in listed}) == len({d['name'] for d in listed}) == len(listed), room_key
        for d in listed:
            where = f"{room_key} / {d['name']}"
            x0, y0, x1, y1 = d['bounds']
            assert 0 <= x0 <= x1 < w and 0 <= y0 <= y1 < h, f'{where}: bounds {d["bounds"]} in a {w}x{h} room'
            assert x0 <= d['stand'][0] <= x1 and y0 <= d['stand'][1] <= y1, f'{where}: stand {d["stand"]} outside the bounds'
            assert d['description'].strip() == d['description'] and '\n' not in d['description'] and 20 <= len(d['description']) <= 200, where
            # its spots are the landmarks standing inside it - worked out, so they cannot go stale silently
            inside = sorted(label for label, (x, y) in ((i.split(' · ', 1)[1], c[1:]) for i, c in spots.items() if c[0] == room_key)
                            if x0 <= x <= x1 and y0 <= y <= y1)
            assert d['spots'] == inside, (where, d['spots'], inside)
            assert b.district_at(cfg, room_key, *d['stand']) is d
            # no two districts of a room overlap
            for other in listed:
                if other is not d:
                    ox0, oy0, ox1, oy1 = other['bounds']
                    assert x1 < ox0 or ox1 < x0 or y1 < oy0 or oy1 < y0, f"{where} overlaps {other['name']}"
            # every author can be placed in it on one day: seven different cells, each inside the bounds,
            # walked to, not a door, the cell in front of one or a seam, not on the room's edge, in the open
            reach, doors, plain = b.reachable_cells(cfg, room_key), b.doorway_cells(cfg, room_key), b.plain_cells(cfg, room_key)
            behind, taken = b.overhead_cells(cfg, room_key, standing=True), []
            for _ in b.AUTHOR_NPCS:
                cell = b.area_cell(cfg, room_key, d, set(taken))
                assert cell is not None, f'{where}: nowhere to stand with {taken} taken'
                assert x0 <= cell[0] <= x1 and y0 <= cell[1] <= y1 and cell in reach and cell not in taken, (where, cell)
                assert cell not in doors and cell not in behind and 0 < cell[0] < w - 1 and 0 < cell[1] < h - 1, (where, cell)
                taken.append(cell)
            assert taken[0] in plain, f'{where}: the first to arrive stands on a road or a stair at {taken[0]}'
            assert b.area_id(room_key, d) in areas
    # a station and an interior have no districts, and an area is never mistaken for a named spot
    assert not any(b.is_indoors(cfg, room) for room, _ in areas.values())
    assert not set(areas) & set(spots) and all(i.endswith(b.AREA) for i in areas)
    both = b.all_spots(cfg)
    assert set(both) == set(areas) | set(spots) and all(both[i] == spots[i] for i in spots)
    # Sapporo's park is both: the spot under its lanterns, and the park
    assert 'Sapporo · Odori Park' in spots and 'Sapporo · Odori Park (area)' in areas

    # the Tokyo districts go by their real names; the room keys are what they were (#219)
    names = {k: cfg['rooms'][k]['name'] for k in ('Tokyo', 'Market', 'Palace', 'Park')}
    assert names == {'Tokyo': 'Imperial Palace', 'Market': 'Asakusa', 'Palace': 'Marunouchi', 'Park': 'Park'}, names
    for key, name in names.items():
        assert [d['name'] for d in cfg['districts'][key]] == [name], key
    assert cfg['cities']['TokyoCity']['name'] == 'Tokyo' and cfg['rooms']['TokyoStation']['name'] == 'Tokyo Station'
    # an interior names its host by the host's display name
    assert cfg['rooms']['KonbiniMarket1']['name'] == '7-Eleven · Asakusa 1'
    assert cfg['rooms']['DonTakoteMarket']['name'] == 'Don Takote · Asakusa'
    assert cfg['rooms']['HouseMarket1']['name'] == 'House · Asakusa 1'
    assert cfg['rooms']['ShrineMarket1']['name'] == 'Shrine · Asakusa'
    assert cfg['rooms']['ShrineTokyo1']['name'] == 'Palace Shrine'      # its own name: the host's is too long for a phone's bar
    assert cfg['rooms']['KonbiniPark1']['name'] == '7-Eleven · Park 1'
    # what a post about Asakusa or the palace names is a spot of that district
    for room_key, label, cell in (('Market', 'Senso-ji temple', (26, 17)), ('Market', 'the temple gate', (26, 24)),
                                  ('Market', 'the izakaya', (6, 38)), ('Tokyo', 'the Imperial Palace gate', (28, 34)),
                                  ('Tokyo', 'the palace moat', (20, 33))):
        assert spots[f'{room_key} · {label}'] == (room_key, *cell), (label, spots.get(f'{room_key} · {label}'))
        assert b.walkable_near(cfg, room_key, *cell) == cell and label in cfg['districts'][room_key][0]['spots']
    izakaya = next(t for t in cfg['rooms']['Market']['transporters'] if t['targetRoom'] == 'Izakaya')
    assert (izakaya['gridX'], izakaya['gridY']) == (7, 37) and (6, 38) not in b.doorway_cells(cfg, 'Market')

    # what the model reads: a named spot with its district, a district with its description
    ids_ = sorted(both)
    offer = b.offer_lines(cfg, ids_).split('\n')
    assert len(offer) == len(ids_) and all(line.startswith(f'- {i}') for line, i in zip(offer, ids_))
    asakusa = cfg['districts']['Market'][0]
    assert f"- Market · Asakusa (area): {asakusa['description']}" in offer
    assert '- Market · Senso-ji temple (in Asakusa)' in offer and '- Tokyo · the palace moat (in Imperial Palace)' in offer
    assert '- Sapporo · the Don Takote discount store' in offer, 'a spot in no district is offered bare'
    assert '- TokyoStation · the platform' in offer
    assert 'Senso-ji' in asakusa['description'] and 'Ueno' in cfg['districts']['Park'][0]['description']

    # a post that names an area and no landmark is placed in that district: on ordinary ground inside
    # its bounds, and the next author the same day beside them, not on them
    post_ = dict(post(900, date='2031-03-04', title='A slow day'),
                 content='We dropped the bags and spent the whole afternoon wandering around Asakusa. Too many people.')
    assert b.named_area(post_, ids_) == 'Market · Asakusa (area)'
    assert b.named_area(post(901), ids_) is None and b.named_area(dict(post_, content='Asakusabashi'), ids_) is None
    assert b.named_area(dict(post_, content='Odori Park at night, then the Park again'), ids_) == 'Sapporo · Odori Park (area)'
    assert b.generate(post_, 'Bailey', ids_, mock=True)[0]['spot'] == 'Market · Asakusa (area)'
    assert b.generate(post(901), 'Bailey', ids_, mock=True)[0]['spot'] == ids_[0]
    work, out = copy.deepcopy(cfg), io.StringIO()
    with contextlib.redirect_stdout(out):
        record, _ = b.process_post(work, post_, both, ids_, mock=True, dry_run=True)
        second, _ = b.process_post(work, dict(post_, post_id=902, author='dbut2'), both, ids_, mock=True, dry_run=True)
    assert record and record['room'] == 'Asakusa' and record['spot'] == 'Asakusa (area)', (record, out.getvalue())
    cells = []
    for name in ('Bailey', 'Dylan'):
        (room_key, state), = [(r, st) for r, st in placements(work, name, '2031-03-04') if st.get('present')]
        cell = (state['gridX'], state['gridY'])
        x0, y0, x1, y1 = asakusa['bounds']
        assert room_key == 'Market' and x0 <= cell[0] <= x1 and y0 <= cell[1] <= y1, (name, room_key, cell)
        assert cell in b.plain_cells(cfg, 'Market') and cell not in b.doorway_cells(cfg, 'Market'), (name, cell)
        assert cell in b.reachable_cells(cfg, 'Market'), (name, cell)
        cells.append(cell)
    assert cells[0] == both['Market · Asakusa (area)'][1:] and cells[1] != cells[0] and second, cells
    # ... and a placement can be re-homed to a district by hand
    with contextlib.redirect_stdout(io.StringIO()):
        b.rehome(work, 'Bailey', '2031-03-04', 'Fukuoka · Nakasu (area)', both)
    (room_key, state), = [(r, st) for r, st in placements(work, 'Bailey', '2031-03-04') if st.get('present')]
    assert room_key == 'Fukuoka' and b.district_at(cfg, 'Fukuoka', state['gridX'], state['gridY'])['key'] == 'nakasu'

    # the ground an area never uses: road, rails, crossings, stairs, a bridge deck
    plain = b.plain_cells(cfg, 'Market')
    assert (2, 43) not in plain and (26, 16) not in plain and (26, 17) in plain      # the avenue, the hall's steps, the paving below them
    assert (12, 11) not in b.plain_cells(cfg, 'Shirakawago'), 'the suspension bridge deck'
    assert {(7, 37), (7, 38), (6, 37), (8, 37), (7, 36)} <= b.doorway_cells(cfg, 'Market')
    # a district with no ordinary cell left takes a road cell before it gives up - and nothing else
    far = cfg['districts']['Shirakawago'][0]
    assert far['key'] == 'far-bank'
    crowd = set()
    for _ in b.AUTHOR_NPCS:
        crowd.add(b.area_cell(cfg, 'Shirakawago', far, crowd))
    assert None not in crowd and crowd - b.plain_cells(cfg, 'Shirakawago'), 'the bus bay is a road stub'
    assert not any((x, 11) in crowd for x in range(10, 16)), 'never the bridge deck'
    sealed = dict(far, bounds=[20, 29, 30, 31])                     # solid ground: nowhere at all
    assert b.area_cell(cfg, 'Shirakawago', sealed) is None

    # the four placements the plan found in the wrong place stand where their post is about
    for (name, date), (room_key, cell) in REPLACED_219.items():
        assert rooms_on(cfg, name, date) == [room_key], (name, date, rooms_on(cfg, name, date))
        state = b.npc_in_room(cfg['rooms'][room_key], name)['states'][date]
        assert (state['gridX'], state['gridY']) == cell and state['dialogue'], (name, date, state.get('gridX'), state.get('gridY'))
        assert cell not in b.doorway_cells(cfg, room_key), f'{name} {date}: {cell} is a door or in front of one'
    for name, date in REPLACED_219:
        for room_key in ('Tokyo', 'Park'):
            st = (b.npc_in_room(cfg['rooms'][room_key], name) or {}).get('states', {}).get(date)
            assert st in (None, {'present': False}), f'{name} {date}: {room_key} still holds {st}'


def test_distinct():
    """tools/check_distinct.py: the audit's measure, and the "no worse than
    the baseline" rule (issue #219)."""
    cd = check_distinct
    assert cd.family('grass-autotile_edge-n') == 'grass-autotile' and cd.family('torii-red-feet_0_0') == 'torii-red'
    assert cd.family('building-roof-blue_0_0') == 'house-blue' and cd.family('building-entrance-2_0_0') == 'house-entrance'
    assert cd.family('tree-3-top-snow_0_0') == 'tree-3-snow' and cd.family('sapporo-clock-tower_0_0') == 'sapporo-clock-tower'
    assert cd.is_building('house-blue') and cd.is_building('sapporo-clock-tower') and cd.is_building('highrise-glass')
    assert cd.is_building('shrine-building') and not cd.is_building('seven-eleven') and not cd.is_building('tree-3')
    assert cd.jaccard({1, 2}, {2, 3}) == 1 / 3 and cd.jaccard(set(), set()) == 0

    def room(tiles, **more):
        return dict({'layers': [{'name': 'Floor', 'tiles': {'0,0': 'grass-autotile_center'}},
                                {'name': 'Collidables', 'tiles': {f'{i},1': t for i, t in enumerate(tiles)}},
                                {'name': 'Colliders', 'collision': True, 'tiles': {'0,1': 'gk_blank'}}]}, **more)
    world = {'tilePalette': [], 'stations': {'AStation': {}}, 'cities': {'AB': {'name': 'Ab', 'rooms': [{'room': 'A1'}, {'room': 'A2'}]}},
             'rooms': {
                 'A1': room(['house-blue_0_0', 'tokyo-tower_0_0']), 'A2': room(['tree-1-top_0_0', 'seven-eleven_0_0']),
                 'B': room(['house-blue_0_0', 'house-red_0_0', 'tree-1-base_0_0']),
                 'C': room(['sapporo-clock-tower_0_0', 'tree-9_0_0']),
                 'AStation': room(['house-red_0_0']), 'Shop': room(['house-red_0_0'], interior=True),
                 'D': room(['tokyo-tower_0_0', 'tree-9_0_0'])}}
    assert cd.towns(world) == {'Ab': ['A1', 'A2'], 'B': ['B'], 'C': ['C'], 'D': ['D']}
    got = cd.measure(world)
    assert sorted(got) == ['Ab', 'B', 'C', 'D'], 'every town is judged (none is exempt now the made-up towns are deleted)'
    # Ab's buildings {house-blue, tokyo-tower}: B shares one of three, D one of two
    assert got['Ab']['buildings'] == 0.5 and got['Ab']['like'] == 'D' and got['B']['buildings'] == 0.333
    # its buildings and scenery {house-blue, tokyo-tower, tree-1}: none its own (the 7-Eleven is kit, grass is ground)
    assert got['Ab']['own'] == 0 and got['B']['own'] == 0.333 and got['C'] == {'buildings': 0.0, 'like': 'Ab', 'sprites': 0.5, 'own': 0.5}
    assert cd.passes({'buildings': 0.25, 'sprites': 0.4, 'own': 0.334}) and not cd.passes({'buildings': 0.26, 'sprites': 0.4, 'own': 0.5})
    assert not cd.passes({'buildings': 0.1, 'sprites': 0.1, 'own': 0.3})
    # no worse than the baseline: equal is fine, better is fine, a higher overlap or a lower own share fails
    base = {c: {k: n[k] for k in ('buildings', 'sprites', 'own')} for c, n in got.items()}
    lines, failed = cd.check(world, base)
    assert failed == [] and len(lines) == 6 and 'below target' in lines[2], lines
    assert cd.worse(got['B'], dict(base['B'], buildings=0.9, own=0.1)) == []
    assert cd.worse(got['B'], dict(base['B'], buildings=0.2)) == ['building overlap 0.33, was 0.20']
    assert cd.worse(got['B'], dict(base['B'], sprites=0.1, own=0.5)) == ['sprite overlap 0.50, was 0.10', 'own art 33%, was 50%']
    borrowed = copy.deepcopy(world)
    borrowed['rooms']['B']['layers'][1]['tiles']['9,1'] = 'sapporo-clock-tower_0_0'      # B takes C's landmark
    lines, failed = cd.check(borrowed, base)
    assert failed == ['B', 'C'], (failed, lines)
    assert any(line.startswith('C ') and 'WORSE than the baseline: building overlap 0.33, was 0.00; own art 0%, was 50%' in line for line in lines), lines
    # a car on a room's `tramways` is drawn by AmbientTrams and not as a tile, and is the town's art all the
    # same: taking it off the map and onto its rails changes no number (issue #264: #245 did that to Toyama's
    # tram and San Franbourne's cable car and tram, and four cities read as worse)
    parked = copy.deepcopy(world)
    parked['rooms']['B']['layers'][1]['tiles']['9,1'] = 'toyama-tram_0_0'
    running = copy.deepcopy(world)
    running['rooms']['B']['tramways'] = [{'row': 1, 'from': 0, 'to': 9, 'sprite': 'toyama-tram_0_0', 'shuttle': True}]
    assert cd.measure(running) == cd.measure(parked) != got
    assert cd.sprite_sets(running, ['B']) == cd.sprite_sets(parked, ['B'])
    assert 'toyama-tram' in cd.sprite_sets(running, ['B'])[1], 'a landmark car is a building sprite, as its tile was'
    assert cd.measure(running)['B']['own'] == 0.5 and cd.check(running, base)[1] == [], 'B has art of its own now'
    lines, failed = cd.check(world, cd.measure(running))        # and a town that loses its car altogether is worse
    assert 'B' in failed and any(line.startswith('B ') and 'own art 33%, was 50%' in line for line in lines), (failed, lines)
    # a town the baseline has not heard of is reported, never failed; one that is gone is named
    lines, failed = cd.check(world, {'Ab': base['Ab'], 'B': base['B'], 'Gone': base['B']})
    assert failed == [] and any('NOT in the baseline' in line for line in lines if line.startswith('C '))
    assert lines[-1].startswith('in the baseline but not in the world: Gone')
    # the committed baseline is this world's cities, and each is recorded with the three numbers
    real = json.load(open(cd.BASELINE))
    cfg = b.load_config()
    assert sorted(real) == sorted(cd.measure(cfg)), (sorted(real), sorted(cd.measure(cfg)))
    assert all(sorted(v) == ['buildings', 'own', 'sprites'] for v in real.values())
    # every car declared in the committed world is counted for its city
    cars = {(city, cd.family(line['sprite'])) for city, rooms in cd.towns(cfg).items() for key in rooms
            for line in cfg['rooms'][key].get('tramways') or []}
    assert cars and all(car in cd.sprite_sets(cfg, cd.towns(cfg)[city])[2] for city, car in cars), cars
    assert cd.TARGETS == {'buildings': 0.25, 'sprites': 0.40, 'own': 1 / 3}


if __name__ == '__main__':
    config = b.load_config()
    test_trim_line()
    test_merge_same_day()
    test_same_day_posts(config)
    test_rehome(config)
    test_shipped_whereabouts(config)
    test_shipped_coverage(config)
    test_landmark_rules()
    test_spots(config)
    test_city_reach(config)
    test_post_source(config)
    test_backfill_posts()
    test_shipped_posts(config)
    test_photos(config)
    test_authors(config)
    test_trips(config)
    test_post_date(config)
    test_mock_steer(config)
    test_not_in_the_way(config)
    test_shipped_dialogue(config)
    test_tiled_ids_stable()
    test_tiled_maps_in_sync()
    test_generator_check_skips()
    test_generator_check_pictures()
    test_sync_cities_anywhere()
    test_districts(config)
    test_distinct()
    print('ok')
