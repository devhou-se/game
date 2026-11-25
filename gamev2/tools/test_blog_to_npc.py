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
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import blog_to_npc as b  # noqa: E402


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
    assert room == room_b and st['posts'] == [{'id': '1', 'lines': 2}, {'id': '2', 'lines': 2}]
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


def test_shipped_dialogue(cfg):
    """Nothing in config.json is over the limit or cut mid-word at it."""
    for room_key, room in cfg['rooms'].items():
        for npc in room.get('npcs', []):
            for date, st in npc.get('states', {}).items():
                for line in st.get('dialogue') or []:
                    where = f'{room_key} {npc["name"]} {date}: {line!r}'
                    assert len(line) <= b.MAX_LINE_CHARS, where
                    assert len(line) < b.MAX_LINE_CHARS or line[-1] in '.!?…。！？', where


if __name__ == '__main__':
    config = b.load_config()
    test_trim_line()
    test_merge_same_day()
    test_same_day_posts(config)
    test_shipped_dialogue(config)
    print('ok')
