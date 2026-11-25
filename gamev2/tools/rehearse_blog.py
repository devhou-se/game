#!/usr/bin/env python3
"""rehearse_blog.py — dress rehearsal of the blog → game pipeline (issue #119).

Runs tools/blog_to_npc.py end to end, the way the www-jp game-npc-pipeline
workflow does (one payload per invocation, --summary-out), for a devhouse 3's
worth of synthetic posts: all seven members, Sapporo days and Asahikawa days,
the lead-in before the trip, a day trip, two posts on one day, photos, voices,
a drunk post, early-morning posts (UTC still says yesterday) and a re-run.

Nothing real is touched and nothing leaves the machine:

  - it works in a SCRATCH directory: a copy of config.json plus the
    assets/photos and assets/voice the run produces. The committed
    config.json and assets are fingerprinted before and after;
  - the LLM is --mock (each payload's "mock" says which landmark the post is
    "about"), the photo download and the ElevenLabs call are replaced by
    local stand-ins, `anthropic` cannot be imported and every socket connect
    raises — a network attempt is a failure;
  - the three new members' GitHub logins are not known. Their posts are sent
    from made-up `rehearsal-<name>` logins, first to prove an unmapped author
    is skipped with a warning that says what to fill in, then mapped IN
    MEMORY only so their placements are rehearsed too. A real login in
    AUTHOR_NPCS is used as it is, so this stays valid once they are filled in.

The result is checked twice: against the written config (states, photos,
clips) and through the game's own code — `node tools/play.js --config=…`
resolves every NPC on every day from 19 January to 1 March 2027 and runs the
world check — so what is asserted is what a player would meet.

Run from gamev2/:

  python3 tools/rehearse_blog.py [--keep DIR] [-v]

--keep DIR leaves the scratch directory (config.json, assets/, payloads/,
log.txt) at DIR to look at, or to serve to a browser in place of the real
config. DIR must be new, empty, or a directory an earlier rehearsal kept
(that one is emptied first); anything else is refused, never deleted. Exit status 1 when a check fails. The photo print is rendered for
real when tools/requirements-photos.txt is installed for this python, and by
a stand-in otherwise (the report says which).
"""
import argparse
import contextlib
import datetime
import hashlib
import io
import json
import os
import re
import shutil
import socket
import struct
import subprocess
import sys
import tempfile
import types
import zlib

TOOLS = os.path.dirname(os.path.abspath(__file__))
GV2 = os.path.dirname(TOOLS)
sys.path.insert(0, TOOLS)

import blog_to_npc as b  # noqa: E402
import post_photos  # noqa: E402
import post_voice  # noqa: E402

TRIP = 'devhouse3'
MEMBERS = ['Bailey', 'Damian', 'Dylan', 'Julia', 'Khoi', 'Sam', 'Xander']
FIRST_DAY, LAST_DAY = '2027-01-19', '2027-03-01'      # the lead-in opens … the day after the trip
PHOTO_URL = 'https://rehearsal.invalid/photo-{}.png'   # .invalid never resolves (RFC 2606)


def P(post_id, npc, when, spot, title, lines, photo=False, drunk=False):
    return {'id': str(post_id), 'npc': npc, 'when': when, 'spot': spot, 'title': title,
            'lines': lines, 'photo': photo, 'drunk': drunk}


# The posts, in the order they are published. `when` is the publishing moment
# as GitHub reports it (UTC); the day in Japan is what the game should use.
POSTS = [
    # the lead-in: a travel-day post, on the way to Hokkaido
    P(9000, 'Bailey', '2027-02-12T03:00:00Z', 'Palace · Tokyo Station', 'Rehearsal: on the way',
      ['Rehearsal: one more train and then the snow.', 'See you in Sapporo.']),
    # day one, 08:15 in Sapporo — UTC says the 17th
    P(9001, 'Damian', '2027-02-17T23:15:00Z', 'Sapporo · the Sapporo TV Tower', 'Rehearsal: first morning',
      ['Rehearsal: first morning in Sapporo, and the TV Tower is right there.', 'It tells the time. In red.']),
    P(9002, 'Bailey', '2027-02-18T04:10:00Z', 'Sapporo · the Sapporo Clock Tower', 'Rehearsal: the Clock Tower',
      ['Rehearsal: the Clock Tower is smaller than the photos.', 'Still went in.', 'Worth it.'], photo=True),
    P(9003, 'Dylan', '2027-02-20T02:00:00Z', 'Sapporo · Odori Park', 'Rehearsal: Odori Park',
      ['Rehearsal: Odori Park under a metre of snow.', 'The lanterns are on at four.']),
    # two posts by one author on one day: the second one's spot and photo win
    P(9004, 'Julia', '2027-02-20T03:00:00Z', 'Sapporo · the frozen pond', 'Rehearsal: the frozen pond',
      ['Rehearsal: the pond is frozen solid.', 'I did not test that personally.'], photo=True),
    P(9005, 'Julia', '2027-02-20T09:30:00Z', 'Sapporo · the 7-Eleven', 'Rehearsal: konbini dinner',
      ['Rehearsal: dinner from the 7-Eleven again.', 'No regrets.'], photo=True),
    P(9006, 'Bailey', '2027-02-21T13:00:00Z', 'Sapporo · the Don Takote discount store', 'Rehearsal: laaate night',
      ['Rehearsal: we have beeen to the discount store.', 'I own a penguin hat now.'], drunk=True),
    # the three new members
    P(9007, 'Khoi', '2027-02-22T01:00:00Z', 'Sapporo · the Sapporo Clock Tower', 'Rehearsal: Khoi at the tower',
      ['Rehearsal: Khoi here, at the Clock Tower.', 'Everyone ends up here.']),
    P(9008, 'Sam', '2027-02-22T05:00:00Z', 'Sapporo · the Sapporo TV Tower', 'Rehearsal: Sam up the tower',
      ['Rehearsal: Sam, at the foot of the TV Tower.', 'The view is all white.'], photo=True),
    P(9009, 'Xander', '2027-02-23T06:00:00Z', 'SapporoStation · the platform', 'Rehearsal: the train north',
      ['Rehearsal: Xander on the platform, checking the timetable.', 'Asahikawa in two days.']),
    # the day the group moves: 08:30 on the 25th in Japan — UTC says the 24th
    P(9010, 'Julia', '2027-02-24T23:30:00Z', 'Sapporo · the vending machines', 'Rehearsal: last coffee in Sapporo',
      ['Rehearsal: one last can of coffee before the train.', 'See you up north.']),
    P(9011, 'Bailey', '2027-02-25T07:00:00Z', 'Asahikawa · the bridge over the frozen river', 'Rehearsal: the bridge',
      ['Rehearsal: the river under the bridge is frozen.', 'Asahikawa is colder than Sapporo.'], photo=True),
    P(9012, 'Damian', '2027-02-25T10:00:00Z', 'Asahikawa · ramen alley', 'Rehearsal: ramen alley',
      ['Rehearsal: ramen alley, first night.', 'Shoyu. Obviously.']),
    P(9013, 'Dylan', '2027-02-26T02:00:00Z', 'Asahikawa · the shrine', 'Rehearsal: the shrine',
      ['Rehearsal: the shrine across the river.', 'Very quiet in the snow.'], photo=True),
    P(9014, 'Julia', '2027-02-26T04:00:00Z', 'Asahikawa · the torii gate', 'Rehearsal: the torii',
      ['Rehearsal: a red gate in white snow.', 'I took forty photos.']),
    P(9015, 'Khoi', '2027-02-27T03:00:00Z', 'Asahikawa · ramen alley', 'Rehearsal: more ramen',
      ['Rehearsal: Khoi, back in ramen alley.', 'Miso this time.']),
    # a day trip from Asahikawa
    P(9016, 'Sam', '2027-02-27T05:00:00Z', 'Yukimura · the frozen pond', 'Rehearsal: a day in the snow village',
      ['Rehearsal: Sam, out at the snow village for the day.', 'The pond is a skating rink.']),
    P(9017, 'Xander', '2027-02-28T02:00:00Z', 'Asahikawa · the shrine', 'Rehearsal: last day',
      ['Rehearsal: Xander at the shrine on the last day.', 'Same again next year.']),
    # the evening after the last day (1 March in Japan): still devhouse 3's
    P(9018, 'Sam', '2027-02-28T16:30:00Z', 'Asahikawa · the vending machines', 'Rehearsal: the morning after',
      ['Rehearsal: Sam, the morning after.', 'Hot corn soup from a vending machine.']),
]


# ------------------------------------------------------------------ plumbing

def png_bytes(width, height, pixel):
    """A PNG from pixel(x, y) -> (r, g, b), with nothing but the standard library."""
    rows = b''.join(b'\x00' + bytes(c for x in range(width) for c in pixel(x, y)) for y in range(height))

    def chunk(kind, data):
        return struct.pack('>I', len(data)) + kind + data + struct.pack('>I', zlib.crc32(kind + data))
    return (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0))
            + chunk(b'IDAT', zlib.compress(rows, 6)) + chunk(b'IEND', b''))


def test_card(seed):
    """A photo to import: sky, snow, and a tower whose colour is the post's."""
    hue = [(200, 60, 50), (60, 120, 200), (230, 180, 40), (70, 160, 90)][seed % 4]

    def pixel(x, y):
        if 140 <= x < 180 and 40 <= y < 190:
            return hue
        if y >= 180:
            return (236, 240, 245)
        return (110 + y // 3, 160 + y // 4, 225)
    return png_bytes(320, 240, pixel)


def png_size(path):
    with open(path, 'rb') as f:
        head = f.read(24)
    return struct.unpack('>II', head[16:24]) if head[:8] == b'\x89PNG\r\n\x1a\n' else None


def tree_digest(*paths):
    """A fingerprint of files and directory trees (names and contents)."""
    h = hashlib.sha256()
    for path in paths:
        if os.path.isfile(path):
            h.update(path.encode() + b'\0' + open(path, 'rb').read())
        for root, dirs, files in os.walk(path):
            dirs.sort()
            for name in sorted(files):
                full = os.path.join(root, name)
                h.update(full.encode() + b'\0' + open(full, 'rb').read())
    return h.hexdigest()


def use_photo_renderer(scratch):
    """'real' when photo_pixelize renders the test card on this python,
    otherwise install a stand-in that writes a 160×144 print and say why."""
    probe_in, probe_out = os.path.join(scratch, 'probe-in.png'), os.path.join(scratch, 'probe-out.png')
    try:
        import photo_pixelize
        from pathlib import Path
        open(probe_in, 'wb').write(test_card(0))
        photo_pixelize.crisp_pixelize(Path(probe_in), Path(probe_out))
        if png_size(probe_out) != (160, 144):
            raise ValueError(f'rendered {png_size(probe_out)}, not 160x144')
        return 'real'
    except Exception as e:      # ImportError (no cv2), or a renderer that fails here
        reason = f'{type(e).__name__}: {e}'
        stand_in = types.ModuleType('photo_pixelize')

        def crisp_pixelize(source, destination, *args, **kwargs):
            os.makedirs(os.path.dirname(str(destination)), exist_ok=True)
            seed = len(open(str(source), 'rb').read())
            shade = [(200, 60, 50), (60, 120, 200), (230, 180, 40), (70, 160, 90)][seed % 4]
            open(str(destination), 'wb').write(png_bytes(
                160, 144, lambda x, y: shade if 70 <= x < 90 and 20 <= y < 110 else
                ((236, 240, 245) if y >= 108 else (120, 170, 225))))
        stand_in.crisp_pixelize = crisp_pixelize
        sys.modules['photo_pixelize'] = stand_in
        return f'stand-in ({reason})'
    finally:
        for path in (probe_in, probe_out):
            if os.path.exists(path):
                os.unlink(path)


class Offline:
    """While active: no socket can connect (attempts are counted), the photo
    download and the text-to-speech call are local, `anthropic` cannot be
    imported, and the environment holds rehearsal voice ids and no API key."""

    def __init__(self):
        self.attempts = []
        self.spoken = []        # (voice, text) for every clip "synthesized"
        self.fetched = []

    def __enter__(self):
        self.saved = (socket.socket.connect, socket.create_connection, post_photos.download,
                      post_voice.synthesize, dict(os.environ), sys.modules.get('anthropic', self))
        attempts = self.attempts

        def refuse(*args, **kwargs):
            attempts.append(repr(args[-1] if args else kwargs)[:80])
            raise OSError('rehearsal: the network is off')

        def download(url):
            self.fetched.append(url)
            return test_card(sum(url.encode()))

        def synthesize(text, tts_voice, api_key, model):
            self.spoken.append((tts_voice, text))
            return b'ID3\x03\x00\x00\x00\x00\x00\x0a' + f'rehearsal clip, voice {tts_voice}: {text}'.encode()

        socket.socket.connect = refuse
        socket.create_connection = refuse
        post_photos.download = download
        post_voice.synthesize = synthesize
        sys.modules['anthropic'] = None                       # import anthropic -> ImportError
        for key in [k for k in os.environ if k.startswith(('ELEVENLABS_', 'ANTHROPIC_')) or k == 'GITHUB_ACTIONS']:
            del os.environ[key]
        os.environ['ELEVENLABS_API_KEY'] = 'rehearsal-key'
        for name in MEMBERS:
            os.environ[f'ELEVENLABS_VOICE_{name.upper()}'] = f'rehearsal-{name.lower()}'
        os.environ['ELEVENLABS_VOICE_BAILEY_DRUNK'] = 'rehearsal-bailey-drunk'
        return self

    def __exit__(self, *exc):
        (socket.socket.connect, socket.create_connection, post_photos.download,
         post_voice.synthesize, env, anthropic) = self.saved
        os.environ.clear()
        os.environ.update(env)
        if anthropic is self:
            sys.modules.pop('anthropic', None)
        else:
            sys.modules['anthropic'] = anthropic


def payload_for(post, login):
    """What the workflow's "Fetch post payload" step builds from the issue."""
    content = f"{post['title']}\n\n" + ' '.join(post['lines'])
    if post['photo']:
        content += f"\n\n![photo]({PHOTO_URL.format(post['id'])})"
    return {'post_id': post['id'], 'title': post['title'], 'url': f"https://blog.devhou.se/{post['id']}/",
            'author': login, 'date': post['when'], 'content': content,
            'mock': {'spot': post['spot'], 'dialogue': post['lines'], 'drunk': post['drunk']}}


def run_pipeline(scratch, payload, log):
    """One workflow run: blog_to_npc.py --payload … --mock --summary-out …,
    in the scratch directory. Returns (output, summary)."""
    path = os.path.join(scratch, 'payloads', f"{payload['post_id']}.json")
    summary = os.path.join(scratch, 'summary.json')
    json.dump(payload, open(path, 'w'), indent=1)
    if os.path.exists(summary):
        os.unlink(summary)
    here, argv = os.getcwd(), sys.argv
    out = io.StringIO()
    try:
        os.chdir(scratch)
        sys.argv = ['blog_to_npc.py', '--payload', path, '--mock', '--summary-out', summary]
        with contextlib.redirect_stdout(out):
            status = b.main()
    finally:
        os.chdir(here)
        sys.argv = argv
    text = out.getvalue()
    log.write(f"$ blog_to_npc.py --payload payloads/{payload['post_id']}.json --mock --summary-out summary.json"
              f"   # exit {status}\n{text}\n")
    return text, json.load(open(summary))


NPC_LINE = re.compile(r'(\S+) (\d+),(\d+) (.+?): (\d+) lines(?: "(.*)")?$')


def game_view(config_path, days):
    """{day: [(room, x, y, name, lines, first line)]} as the game resolves it,
    plus the world check's output — through tools/play.js. None without node."""
    node = shutil.which('node')
    if not node:
        return None, None
    script = ''.join(f'date {d}\nnpcs\n' for d in days) + 'check\n'
    env = dict(os.environ, OPENSSL_CONF='/dev/null')
    run = subprocess.run([node, os.path.join(TOOLS, 'play.js'), f'--config={config_path}'],
                         input=script, capture_output=True, text=True, env=env)
    if run.returncode not in (0, 1) or not run.stdout:
        raise RuntimeError(f'play.js failed: {run.stderr.strip() or run.stdout.strip()}')
    view, day, check, in_check = {}, None, [], False
    for line in run.stdout.split('\n'):
        if line.startswith('> date '):
            day = line.split()[2]
            view[day] = []
        elif line.startswith('> check'):
            in_check = True
        elif in_check:
            if line.strip():
                check.append(line)
        elif line.startswith('> ') or line.startswith('on ') or not line.strip() or day is None:
            continue
        else:
            # "Sapporo 38,19 Bailey: 3 lines "Rehearsal: the Clock Tower is…""
            m = NPC_LINE.match(line)
            if m:
                view[day].append((m.group(1), int(m.group(2)), int(m.group(3)), m.group(4),
                                  int(m.group(5)), m.group(6) or ''))
    return view, check


# ------------------------------------------------------------------- the run

def rehearse(scratch, verbose=False):
    results = []

    def check(name, ok, detail=''):
        results.append((name, bool(ok), detail))
        if verbose or not ok:
            print(('ok   ' if ok else 'FAIL ') + name + (f'\n       {detail}' if detail and not ok else ''))
        return bool(ok)

    os.makedirs(os.path.join(scratch, 'payloads'), exist_ok=True)
    os.makedirs(os.path.join(scratch, 'assets', 'photos'), exist_ok=True)
    shutil.copyfile(os.path.join(GV2, 'config.json'), os.path.join(scratch, 'config.json'))
    scratch_config = os.path.join(scratch, 'config.json')
    committed = [os.path.join(GV2, 'config.json'), os.path.join(GV2, 'assets', 'photos'),
                 os.path.join(GV2, 'assets', 'voice')]
    before = tree_digest(*committed)
    log = open(os.path.join(scratch, 'log.txt'), 'w')

    cfg0 = json.load(open(scratch_config))
    trip = next((t for t in cfg0.get('trips', []) if t.get('id') == TRIP), None)
    check('config has the devhouse 3 trip, with its seven members',
          trip and sorted(trip.get('members', [])) == sorted(m.lower() for m in MEMBERS), trip and trip.get('members'))
    if not trip:
        return results, {}
    stays = sorted(trip.get('stays', []), key=lambda s: s['from'])
    check('the trip dates its posts by the clock in Japan ("utcOffset": 9)', trip.get('utcOffset') == 9, trip.get('utcOffset'))

    # who posts as whom: the real login where AUTHOR_NPCS has one, else a rehearsal one
    real = {npc: key for key, npc in b.AUTHOR_NPCS.items() if b.is_login(key)}
    waiting = b.awaiting_login()
    login = {npc: real.get(npc, f'rehearsal-{npc.lower()}') for npc in MEMBERS}
    authors_before = dict(b.AUTHOR_NPCS)
    renderer = use_photo_renderer(scratch)
    spots = b.find_spots(cfg0)
    for post in POSTS:
        check(f"spot offered to the model: {post['spot']}", post['spot'] in spots)
    hokkaido = {'Sapporo · the Sapporo Clock Tower', 'Sapporo · the Sapporo TV Tower', 'Sapporo · Odori Park',
                'Asahikawa · ramen alley', 'Asahikawa · the bridge over the frozen river', 'Asahikawa · the shrine'}
    check('the six landmarks issue #119 names are all rehearsed', hokkaido <= {p['spot'] for p in POSTS},
          sorted(hokkaido - {p['spot'] for p in POSTS}))

    placed = {}        # post id -> the summary record
    with Offline() as offline:
        try:
            # 1. an author nobody maps: skipped, loudly, and nothing is written
            for npc in MEMBERS:
                if npc in real:
                    continue
                sample = next(p for p in POSTS if p['npc'] == npc)
                text, summary = run_pipeline(scratch, payload_for(sample, login[npc]), log)
                check(f'{npc}: a post from an unmapped login is skipped, nothing written',
                      summary == {'placed': []} and open(scratch_config).read() == open(committed[0]).read(), summary)
                check(f'{npc}: the warning says what to add, and who is still waiting',
                      f"'{login[npc]}': '<NPC name>'" in text and 'AUTHOR_NPCS in gamev2/tools/blog_to_npc.py' in text
                      and f'still waiting for a login: {", ".join(waiting)}' in text, text.strip())
            for key, npc in authors_before.items():
                if not b.is_login(key):
                    text, summary = run_pipeline(scratch, payload_for(POSTS[0], key), log)
                    check(f'the placeholder key {key!r} is not an author', summary == {'placed': []}, summary)

            # 2. the posts, one workflow run each (rehearsal logins mapped in memory only)
            for npc in MEMBERS:
                b.AUTHOR_NPCS.setdefault(login[npc], npc)
            for post in POSTS:
                text, summary = run_pipeline(scratch, payload_for(post, login[post['npc']]), log)
                record = (summary.get('placed') or [None])[0]
                room = post['spot'].split(' · ')[0]
                ok = check(f"#{post['id']} {post['npc']} placed at {post['spot']}",
                           record and record['npc'] == post['npc'] and record['post_id'] == post['id']
                           and record['spot'] == post['spot'].split(' · ', 1)[1]
                           and record['room'] == cfg0['rooms'][room].get('name', room)
                           and record['photo'] is post['photo'] and record['voice'] is True
                           and 'ERROR' not in text, record or text.strip())
                if ok:
                    placed[post['id']] = record

            # 3. a re-run of a post changes nothing
            again = next(p for p in POSTS if p['id'] == '9002')
            snapshot = (open(scratch_config).read(), tree_digest(os.path.join(scratch, 'assets')))
            clips = len(offline.spoken)
            run_pipeline(scratch, payload_for(again, login[again['npc']]), log)
            check('re-running a post leaves config, photos and clips exactly as they were',
                  snapshot == (open(scratch_config).read(), tree_digest(os.path.join(scratch, 'assets'))))
            check('… and pays for no new clips', len(offline.spoken) == clips, len(offline.spoken) - clips)
        finally:
            b.AUTHOR_NPCS.clear()
            b.AUTHOR_NPCS.update(authors_before)
    log.close()

    check('no network: nothing tried to connect', not offline.attempts, offline.attempts[:3])
    check('the committed config.json and assets are untouched', tree_digest(*committed) == before)
    check('every photo was "downloaded" from its post (the re-run fetches its own again)', sorted(offline.fetched) == sorted(
        [PHOTO_URL.format(p['id']) for p in POSTS if p['photo']] + [PHOTO_URL.format('9002')]), offline.fetched)

    # ---- what was written -------------------------------------------------
    cfg = json.load(open(scratch_config))
    check('config.json is still written the way the repo keeps it (indent 2, sorted keys)',
          open(scratch_config).read() == json.dumps(cfg, indent=2, sort_keys=True))
    day_of = {p['id']: b.post_date(cfg, {'date': p['when']}) for p in POSTS}
    japan = {p['id']: (datetime.datetime.fromisoformat(p['when'].replace('Z', '+00:00'))
                       + datetime.timedelta(hours=9)).date().isoformat() for p in POSTS}
    check('every post is dated by the day in Japan', day_of == japan,
          {i: (day_of[i], japan[i]) for i in day_of if day_of[i] != japan[i]})
    early = [p['id'] for p in POSTS if p['when'][:10] != day_of[p['id']]]
    check('… including the ones published before 09:00 there (UTC said the day before)', len(early) >= 3, early)

    def state_of(post):
        room = post['spot'].split(' · ')[0]
        npc = b.npc_in_room(cfg['rooms'][room], post['npc'])
        return (npc or {}).get('states', {}).get(day_of[post['id']])

    by_day = {}
    for post in POSTS:
        by_day.setdefault((post['npc'], day_of[post['id']]), []).append(post)
    for (npc, day), posts in sorted(by_day.items()):
        last, st = posts[-1], state_of(posts[-1])
        label = f"{npc} {day} (#{', #'.join(p['id'] for p in posts)})"
        if not check(f'{label}: a state at the last post\'s spot', st and st.get('present') is True, st):
            continue
        lines = [line for p in posts for line in p['lines']]
        check(f'{label}: dialogue is every post\'s lines, in order', st['dialogue'] == lines, st['dialogue'])
        check(f'{label}: "posts" credits each run of lines, with title and url',
              st.get('posts') == [{'id': p['id'], 'lines': len(p['lines']), 'title': p['title'],
                                   'url': f"https://blog.devhou.se/{p['id']}/"} for p in posts], st.get('posts'))
        ax, ay = spots[last['spot']][1:]
        check(f'{label}: stands within two cells of the landmark\'s standing cell',
              max(abs(st['gridX'] - ax), abs(st['gridY'] - ay)) <= 2, (st['gridX'], st['gridY'], ax, ay))
        with_photo = [p for p in posts if p['photo']]
        want_photo = with_photo[-1]['id'] if with_photo else None
        check(f'{label}: photo is {want_photo}', st.get('photo') == want_photo, st.get('photo'))
        drunk = any(p['drunk'] for p in posts)
        check(f'{label}: drunk flag', (st.get('drunk') is True) == drunk, st.get('drunk'))
        tts = f'rehearsal-{npc.lower()}' + ('-drunk' if drunk and npc == 'Bailey' else '')
        voice = post_voice.voice_id_for(npc, day, lines, tts)
        clips = os.path.join(scratch, 'assets', 'voice', voice)
        check(f'{label}: voice {voice}, one clip per line', st.get('voice') == voice and os.path.isdir(clips)
              and sorted(os.listdir(clips)) == [f'{i}.mp3' for i in range(len(lines))],
              (st.get('voice'), os.path.isdir(clips) and os.listdir(clips)))
        # everywhere else they are absent that day
        elsewhere = [room for room, r in b.overworld_rooms(cfg).items()
                     if room != last['spot'].split(' · ')[0]
                     and ((b.npc_in_room(r, npc) or {}).get('states', {}).get(day) or {}).get('present') is True]
        check(f'{label}: placed in one room only', not elsewhere, elsewhere)

    wanted_photos = sorted(p['id'] for posts in by_day.values() for p in [([q for q in posts if q['photo']] or [None])[-1]] if p)
    have = sorted(os.path.splitext(f)[0] for f in os.listdir(os.path.join(scratch, 'assets', 'photos')))
    check('assets/photos holds exactly the prints the states name (a superseded one is pruned)', have == wanted_photos, (have, wanted_photos))
    check('every print is 160×144', all(png_size(os.path.join(scratch, 'assets', 'photos', f'{i}.png')) == (160, 144) for i in have))
    voices = sorted(os.listdir(os.path.join(scratch, 'assets', 'voice')))
    check('assets/voice holds exactly the clip sets the states name (a superseded one is pruned)',
          voices == sorted(post_voice.referenced_voices(cfg)) and len(voices) == len(by_day), (len(voices), len(by_day)))
    check('the drunk post was spoken in the drunk voice',
          any(v == 'rehearsal-bailey-drunk' for v, _ in offline.spoken)
          and all(v != 'rehearsal-bailey-drunk' or 'beeen' in t or 'penguin' in t for v, t in offline.spoken))

    # ---- what a player meets, by the game's own rules ----------------------
    days = []
    d = datetime.date.fromisoformat(FIRST_DAY)
    while d.isoformat() <= LAST_DAY:
        days.append(d.isoformat())
        d += datetime.timedelta(days=1)
    view, world_check = game_view(scratch_config, days)
    if view is None:
        check('node is available to resolve the world the way the game does', False, 'node not found on PATH')
        return results, {'renderer': renderer, 'waiting': waiting}
    check('the world check (node tools/play.js check) finds no problems in the rehearsed config',
          world_check == ['no problems found'], '\n       '.join(world_check[:12]))
    indoors = {k for k, r in cfg['rooms'].items() if r.get('interior')}
    for day in days:
        window = b.trip_window(cfg, day)
        here = [n for n in view[day] if n[0] not in indoors and n[3] in MEMBERS]
        expect = {}
        for npc in MEMBERS:
            said = [p for p in POSTS if p['npc'] == npc and window['from'] <= day_of[p['id']] <= day]
            if said:
                latest = max(day_of[p['id']] for p in said)
                todays = [p for p in said if day_of[p['id']] == latest]
                expect[npc] = (todays[-1]['spot'].split(' · ')[0], todays[0]['lines'][0])
            elif not window['early'] and window['trip']['id'] == TRIP:
                stay = [s for s in stays if s['from'] <= day][-1]['room']
                base = next(n for n in cfg['rooms'][stay]['npcs'] if n['name'] == npc and n.get('stay') == stay)
                expect[npc] = (stay, base['dialogue'][0])
        got = {}
        for room, x, y, name, count, first in here:
            got.setdefault(name, []).append((room, first))
        short = lambda s: s[:70]                                   # play.js prints 70 characters of a line
        ok = (sorted(got) == sorted(expect) and all(len(v) == 1 for v in got.values())
              and all(got[n][0][0] == expect[n][0] and short(got[n][0][1].rstrip('.')) == short(expect[n][1]).rstrip('.')
                      for n in expect))
        check(f'{day}: the game puts {len(expect)} member(s) where the posts (or the base) say', ok,
              {'got': got, 'expected': expect})
        cells = [(room, x, y) for room, x, y, *_ in view[day]]
        check(f'{day}: nobody shares a cell', len(cells) == len(set(cells)),
              sorted(c for c in set(cells) if cells.count(c) > 1))
    return results, {'renderer': renderer, 'waiting': waiting, 'placed': len(placed)}


KEPT = '.gamev2-rehearsal'   # marks a --keep directory as ours to empty next time


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--keep', metavar='DIR', help='leave the scratch directory at DIR: a new or empty directory, or one an earlier rehearsal kept (that one is emptied first)')
    ap.add_argument('-v', '--verbose', action='store_true', help='print every check, not only the failures')
    args = ap.parse_args()

    if args.keep:
        scratch = os.path.abspath(args.keep)
        real, game = os.path.realpath(scratch), os.path.realpath(GV2)
        if os.path.commonpath([real, game]) in (real, game):
            ap.error('--keep must be outside gamev2/ and must not contain it: the rehearsal never writes into the game')
        if os.path.lexists(scratch):
            # only an earlier rehearsal (or an empty directory) is emptied: never somebody's folder
            if not os.path.isdir(scratch) or os.path.islink(scratch):
                ap.error(f'--keep {scratch} is not a directory')
            if os.listdir(scratch) and not os.path.isfile(os.path.join(scratch, KEPT)):
                ap.error(f'--keep {scratch} is not empty and is not an earlier rehearsal (no {KEPT} in it): '
                         'name a new or empty directory')
            shutil.rmtree(scratch)
        os.makedirs(scratch)
        open(os.path.join(scratch, KEPT), 'w').close()
    else:
        scratch = tempfile.mkdtemp(prefix='gamev2-rehearsal-')
    try:
        results, info = rehearse(scratch, verbose=args.verbose)
    finally:
        if not args.keep:
            shutil.rmtree(scratch, ignore_errors=True)

    failed = [r for r in results if not r[1]]
    print(f"blog pipeline rehearsal: {len(results) - len(failed)}/{len(results)} checks passed"
          f" · {info.get('placed', 0)}/{len(POSTS)} posts placed · photo renderer: {info.get('renderer', '?')}"
          + (f' · scratch kept at {scratch}' if args.keep else ''))
    if info.get('waiting'):
        print(f"TO DO before the trip: AUTHOR_NPCS in tools/blog_to_npc.py still has a placeholder for "
              f"{', '.join(info['waiting'])} — until each is replaced by that person's GitHub login their real "
              f"posts are skipped (rehearsed here under made-up logins, mapped in memory only).")
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
