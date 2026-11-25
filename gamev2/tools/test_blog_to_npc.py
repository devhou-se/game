#!/usr/bin/env python3
"""test_blog_to_npc.py — unit checks for the blog → game pipeline.

Run from gamev2/:  python3 tools/test_blog_to_npc.py

No network, no API keys, nothing written: posts go through process_post in
--mock mode (canned LLM response) with dry_run, against an in-memory copy of
config.json.
"""
import contextlib
import copy
import io
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import blog_to_npc as b  # noqa: E402
import config_to_tiled as c2t  # noqa: E402
import post_photos  # noqa: E402


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
        elif room_key in stations:
            assert set(by_room.get(room_key, {})) == {'the platform'}, (room_key, by_room.get(room_key))
        else:
            assert 'the platform' not in by_room.get(room_key, {}), room_key
            assert by_room.get(room_key), f'{room_key} is outdoors and offers nowhere to stand'
    indoor_labels = {label for _, label, _, options in map(b.landmark_fields, b.LANDMARKS)
                     if options.get('indoors')}
    assert indoor_labels == {'the platform'}, indoor_labels

    # a landmark that names one town is offered there and nowhere else, even
    # where another town is built from the same sprites
    assert 'the old-town lane' in by_room['Machi']
    assert [r for r in by_room if 'the old-town lane' in by_room[r]] == ['Machi']
    assert 'ramen alley' in by_room['Asahikawa']
    for prefix, label, _, options in map(b.landmark_fields, b.LANDMARKS):
        for room_key in options.get('rooms', ()):
            assert room_key in cfg['rooms'], f'{label}: no room {room_key!r}'
            assert label in by_room.get(room_key, {}), f'{label} is not found in {room_key}'
        if 'rooms' in options:
            offered = {r for r in by_room if label in by_room[r]}
            assert offered == set(options['rooms']), (label, offered)
    # ... and that lane filter is doing something: the sprites are in both towns
    def has_tile(room_key, prefix):
        return any(key.startswith(prefix) for layer in cfg['rooms'][room_key]['layers']
                   for key in b.decode_tiles(cfg, layer).values())
    assert has_tile('Machi', 'machiya-') and has_tile('Asahikawa', 'machiya-')

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
        assert cell in reach[room_key], f'{spot_id}: {cell} cannot be walked to'
        # four authors can be at one spot on one day without anyone being walled in
        taken = set()
        for _ in b.AUTHOR_NPCS:
            c = b.walkable_near(cfg, room_key, x, y, taken)
            assert c in reach[room_key], f'{spot_id}: {c} (with {sorted(taken)} taken) cannot be walked to'
            taken.add(c)

    # a station's platform spot keeps clear of the train doors and where you arrive
    for room_key in stations:
        st = cfg['stations'][room_key]
        cell = b.walkable_near(cfg, room_key, *by_room[room_key]['the platform'])
        keep_clear = [tuple(c) for c in st.get('board', [])] + [tuple(st['arrive'])]
        assert all(max(abs(cell[0] - cx), abs(cell[1] - cy)) > 2 for cx, cy in keep_clear), (room_key, cell)


def test_landmark_rules():
    """landmark_applies on a made-up world: outdoors, a station, an interior."""
    cfg = {'rooms': {'Machi': {}, 'Other': {}, 'MachiStation': {}, 'Shop': {'interior': True}},
           'stations': {'MachiStation': {}}}
    plain, lane, platform = {}, {'rooms': ('Machi',)}, {'indoors': True}
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
                                                    '6,6': 'machiya-a_0_0'}}]}
    for room in cfg['rooms'].values():
        room.update(tiles)
    assert b.find_spots(cfg) == {
        'Machi · the vending machines': ('Machi', 3, 4),
        'Other · the vending machines': ('Other', 3, 4),
        'Machi · the old-town lane': ('Machi', 8, 11),
        'MachiStation · the platform': ('MachiStation', 3, 4),
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
    # a trip opens a fortnight before it starts (the lead-in): its posts, nobody at the base yet
    assert b.trip_window(cfg, '2027-02-03')['trip']['id'] == 'devhouse2'
    lead = b.trip_window(cfg, '2027-02-10')
    assert (lead['trip']['id'], lead['early'], lead['from']) == ('devhouse3', True, '2027-02-04'), lead
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


if __name__ == '__main__':
    config = b.load_config()
    test_trim_line()
    test_merge_same_day()
    test_same_day_posts(config)
    test_landmark_rules()
    test_spots(config)
    test_post_source(config)
    test_backfill_posts()
    test_shipped_posts(config)
    test_photos(config)
    test_authors(config)
    test_trips(config)
    test_shipped_dialogue(config)
    test_tiled_ids_stable()
    print('ok')
