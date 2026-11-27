#!/usr/bin/env python3
"""check_generators.py — a generator re-run on an unchanged world must leave
what is committed as it is: config.json for the room generators (issue #107),
the Tiled maps for config_to_tiled.py, and the sprites and prefabs for the
art tools (issue #186). Text is compared byte for byte, a PNG by its decoded
pixels (issue #230).

The generated rooms also collect edits their generator did not make: the blog
pipeline's NPC states, a shop door wired by another generator, a surgical fix
through /adjust-game. A generator that does not know about such an edit drops
it the next time it runs. This runs every room generator on its own, in a
scratch copy of the project (the real config.json is never written), and
fails if the copy's config.json changed — naming the rooms and cells, so the
edit can be folded back into the generator (or kept by it, the way NPCs are).

The same holds one step on: `config_to_tiled` re-seeds every room that has a
tiled/<room>.tmj and fails if a map changed (a config edit whose map was not
re-seeded, or a map edited by hand), if a tiled/*.tmj has no room, or if a
room has no map (unmatched_maps, issue #243: a removed building's map left
behind, a new room never seeded), and each art / prefab tool must rebuild
the committed assets/sprites and tiled/prefabs. Whatever a tool writes under
OUTPUTS is compared, so a room generator that touched a sprite fails too.

A PNG is the same when it decodes to the same picture (same_picture): the
bytes of the file also depend on the zlib that Pillow was built with, so the
same pixels are written as a different file from one machine to the next.
What Pillow draws can differ between versions too (a curve or a slanted line
a pixel off), and that is drift like any other: the summary names the Pillow
that ran, and docs/generators-and-checks.md the versions known to rebuild
the committed art.

Run from gamev2/:  python3 tools/check_generators.py [generator ...]
                   python3 tools/check_generators.py generate_osaka config_to_tiled

Exit 0 when every generator reproduces the committed world, 1 otherwise.
The room generators and config_to_tiled need no Pillow. The art tools do:
without it they are listed as skipped, not as ok — run the check with a
python3 that has Pillow to cover them. The two that draw Japanese text
(FONT_TOOLS) are skipped the same way where no Japanese system font is
readable (a sandboxed shell, a machine without one): the glyphs decide the
pixels, so no stand-in font would rebuild the committed art. A new room
generator belongs in GENERATORS, a new art tool in ART_TOOLS.
"""
import filecmp
import json
import os
import shutil
import subprocess
import sys
import tempfile

# Every tool that builds rooms into config.json. Each must be a no-op here on
# its own: a town generator runs its own fence / track passes (Builder.finish)
# and keeps what it does not own (NPCs, signage, another generator's door).
GENERATORS = [
    'generate_osaka',
    'generate_sapporo', 'generate_asahikawa', 'generate_sendai',
    'generate_fukuoka',
    'generate_airports', 'generate_sanfranbourne',
    'generate_konbinis', 'generate_discount_stores', 'generate_stations',
    'generate_izakaya', 'generate_houses', 'generate_shrines', 'generate_palace', 'generate_chikagai',
    'generate_temple', 'generate_pagodas', 'generate_devhouses',
    'generate_pub', 'generate_distillery', 'generate_mall', 'generate_tower_deck',
]
GENERATORS += ['generate_kanazawa', 'generate_shirakawago', 'generate_toyama']     # Hokuriku (issue #68)
# config `districts` from tools/districts.py: last, it reads where the landmarks of every room stand (issue #219)
GENERATORS += ['districts']
# config_to_tiled.py, run over every room that has a committed tiled/*.tmj
TILED = 'config_to_tiled'
# Tools that draw sprites / prefabs (and register them in config.json). They
# need Pillow; the extract_* ones read the source sheets in ../art-source, and
# generate_cast the character creator's tables (src/CharacterCreator.js).
ART_TOOLS = [
    'make_prefabs', 'generate_hokkaido', 'generate_sendai_art', 'generate_tsutenkaku',
    'generate_discount_art', 'generate_cooler_art', 'make_snow_tiles',
    'make_road_tiles', 'generate_ads', 'generate_cast', 'extract_city',
    'extract_dotonbori', 'extract_shrine', 'extract_street', 'extract_train',
    'extract_train_interior', 'extract_station', 'generate_station_art',
    'generate_fukuoka_art', 'extract_house_interior', 'generate_house_art', 'generate_shrine_art', 'generate_palace_art',
    'generate_temple_art', 'generate_pagoda_art',
    'make_japan_map',
    'generate_sanfranbourne_art',
]
ART_TOOLS += ['generate_hokuriku_art']
ART_TOOLS += ['generate_sapporo_art']        # Sapporo's own art (issue #219)
ART_TOOLS += ['generate_chikagai_art']       # the underground arcades and their street entrances
ART_TOOLS += ['generate_konbini_art']        # the 7-Eleven interiors' kit (issue #221)
ART_TOOLS += ['generate_pub_art']            # the Sendai pub's interior, and the frame its neighbours share (issue #217)
ART_TOOLS += ['generate_distillery_art']     # the distillery's tasting bar in Sendai (issue #217)
ART_TOOLS += ['generate_mall_art']           # Canal City's atrium in Fukuoka (issue #217)
ART_TOOLS += ['generate_devhouse_art']       # the two Devhouses and what stands in them (issue #69)
ART_TOOLS += ['generate_tower_deck_art']     # Fukuoka Tower's observation deck and the lift's view (issue #242)
ART_TOOLS += ['generate_wheel_art']          # Osaka: the gondola you board and the view from the wheel (issue #242)
# the art tools that also need a Japanese system font (generate_ads.find_font)
FONT_TOOLS = ['generate_ads', 'extract_city']
CHECKS = GENERATORS + [TILED] + ART_TOOLS
# what a tool reads and may write, relative to gamev2/ — copied to the scratch
# project once (plus config.json), compared and put back after every run
OUTPUTS = ['tiled', 'assets/sprites', 'assets/ads', 'assets/map']
# (fonts: generate_station_art sets its signs in the game's own pixel fonts)
INPUTS = ['tools', 'src/CharacterCreator.js', 'fonts'] + OUTPUTS


def pillow_version():
    """The Pillow this python3 has, as '13.0.0'; None without it."""
    try:
        import PIL
        return PIL.__version__
    except ImportError:
        return None


def have_pillow():
    return pillow_version() is not None


def have_jp_font():
    """Whether generate_ads.find_font finds a font it can read (needs Pillow)."""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import generate_ads
    try:
        generate_ads.find_font()
        return True
    except SystemExit:
        return False


def skips(names, pillow, font):
    """{tool: why it cannot be checked here} for the art tools among `names`:
    all of them without Pillow, the FONT_TOOLS without a Japanese font."""
    if not pillow:
        return {n: 'needs Pillow' for n in names if n in ART_TOOLS}
    return {} if font else {n: 'needs a Japanese system font' for n in names if n in FONT_TOOLS}


def tiled_rooms(root='.'):
    """Rooms of config.json that have a committed tiled/<room>.tmj."""
    rooms = json.load(open(os.path.join(root, 'config.json')))['rooms']
    return [r for r in rooms if os.path.exists(os.path.join(root, 'tiled', r.lower() + '.tmj'))]


def unmatched_maps(root='.'):
    """Where config.json's rooms and the top level of tiled/ are out of step:
    ['tiled/x.tmj has no room in config.json: delete it', ...] for each map
    whose name is no room's key in lower case, then ['room X has no
    tiled/x.tmj: run config_to_tiled.py X', ...] for each room without a map.
    tiled/prefabs/ is not looked at."""
    rooms = json.load(open(os.path.join(root, 'config.json')))['rooms']
    tiled = os.path.join(root, 'tiled')
    maps = sorted(f[:-4] for f in os.listdir(tiled) if f.endswith('.tmj') and os.path.isfile(os.path.join(tiled, f)))
    keys = {r.lower() for r in rooms}
    return [f'tiled/{m}.tmj has no room in config.json: delete it' for m in maps if m not in keys] + \
           [f'room {r} has no tiled/{r.lower()}.tmj: run config_to_tiled.py {r}' for r in rooms if r.lower() not in maps]


def files_under(base, rel):
    """Paths (relative to base) of every file under base/rel."""
    out = set()
    for d, dirs, names in os.walk(os.path.join(base, rel)):
        dirs[:] = [x for x in dirs if x != '__pycache__']
        out.update(os.path.relpath(os.path.join(d, n), base) for n in names)
    return out


def same_picture(a, b):
    """Whether two PNG files decode to the same picture: the same size and the
    same RGBA pixels. The file's bytes are not compared — they depend on the
    zlib Pillow was built with (issue #230). False for anything that is not a
    PNG Pillow can read, and without Pillow."""
    if not (a.lower().endswith('.png') and b.lower().endswith('.png')):
        return False
    try:
        from PIL import Image
        with Image.open(a) as ia, Image.open(b) as ib:
            return ia.size == ib.size and ia.convert('RGBA').tobytes() == ib.convert('RGBA').tobytes()
    except Exception:       # no Pillow, or not a picture it can read: not known to be the same
        return False


def restore(root, work):
    """Differences under OUTPUTS between the scratch project and the committed
    one, as ['tiled/x.tmj changed', ...] — and the scratch copy put back the
    way it was, so the next tool starts from the committed files. A PNG whose
    bytes differ and whose pixels do not is put back and not reported."""
    out = []
    for rel in OUTPUTS:
        a, b = files_under(root, rel), files_under(work, rel)
        for f in sorted(a | b):
            src, dst = os.path.join(root, f), os.path.join(work, f)
            if f not in a:
                out.append(f'{f} ADDED')
                os.remove(dst)
            elif f not in b or not filecmp.cmp(src, dst, shallow=False):
                if f not in b:
                    out.append(f'{f} REMOVED')
                elif not same_picture(src, dst):
                    out.append(f'{f} changed')
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.copyfile(src, dst)
    return out


def describe(before, after, limit=8):
    """Human-readable differences between two configs: rooms added / removed,
    and per room the keys and layer cells that changed."""
    out = []
    pal = after.get('tilePalette', [])
    name = lambda i: pal[i] if isinstance(i, int) and 0 <= i < len(pal) else i
    for key in sorted(set(before) | set(after)):
        if key != 'rooms' and before.get(key) != after.get(key):
            out.append(f'top-level `{key}` changed')
    ra, rb = before.get('rooms', {}), after.get('rooms', {})
    for room in sorted(set(ra) | set(rb)):
        a, b = ra.get(room), rb.get(room)
        if a == b:
            continue
        if a is None or b is None:
            out.append(f'room {room} ' + ('ADDED' if a is None else 'REMOVED'))
            continue
        for key in sorted(set(a) | set(b)):
            if a.get(key) == b.get(key):
                continue
            if key != 'layers':
                out.append(f'{room}.{key} changed')
                continue
            la = {l['name']: l.get('tiles', {}) for l in a['layers']}
            lb = {l['name']: l.get('tiles', {}) for l in b['layers']}
            for layer in sorted(set(la) | set(lb)):
                ta, tb = la.get(layer, {}), lb.get(layer, {})
                cells = sorted((c for c in set(ta) | set(tb) if ta.get(c) != tb.get(c)),
                               key=lambda c: [int(v) for v in c.split(',')][::-1])
                if cells:
                    shown = ', '.join(f'({c}) {name(ta.get(c))} -> {name(tb.get(c))}' for c in cells[:limit])
                    more = f', +{len(cells) - limit} more' if len(cells) > limit else ''
                    out.append(f'{room} layer {layer}: {len(cells)} cell(s) — committed -> regenerated: {shown}{more}')
            if [(l['name'], l.get('z'), l.get('collision')) for l in a['layers']] != \
               [(l['name'], l.get('z'), l.get('collision')) for l in b['layers']]:
                out.append(f'{room}.layers order / properties changed')
    return out or ['formatting only (same data, different bytes)']


def check(names, root='.'):
    """Run each generator in a scratch copy of `root` (a gamev2 directory).
    Returns {generator: [difference, ...]} for the ones that are not a no-op."""
    committed = open(os.path.join(root, 'config.json')).read()
    failures = {}
    with tempfile.TemporaryDirectory(prefix='check_generators_') as top:
        # the scratch project sits one level down so that ../art-source (the
        # sheets the extract_* tools cut sprites from) resolves beside it
        work = os.path.join(top, 'gamev2')
        source_art = os.path.abspath(os.path.join(root, '..', 'art-source'))
        if os.path.isdir(source_art):
            os.symlink(source_art, os.path.join(top, 'art-source'))
        for rel in INPUTS:
            src, dst = os.path.join(root, rel), os.path.join(work, rel)
            if os.path.isdir(src):
                shutil.copytree(src, dst, ignore=shutil.ignore_patterns('__pycache__'))
            else:
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.copyfile(src, dst)
        scratch = os.path.join(work, 'config.json')
        for name in names:
            open(scratch, 'w').write(committed)
            args = tiled_rooms(work) if name == TILED else []
            run = subprocess.run([sys.executable, f'tools/{name}.py'] + args, cwd=work,
                                 stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            files = restore(root, work)     # also after a crash: it may have written some
            # a map without a room, a room without a map: no re-seed shows either
            unmatched = unmatched_maps(root) if name == TILED else []
            if run.returncode != 0:
                last = (run.stdout.strip().splitlines() or ['no output'])[-1]
                failures[name] = [f'exited {run.returncode}: {last}'] + unmatched
                continue
            regenerated = open(scratch).read()
            if unmatched:
                failures[name] = unmatched
            if regenerated != committed:
                failures[name] = failures.get(name, []) + describe(json.loads(committed), json.loads(regenerated))
            if files:
                more = [f'+{len(files) - 12} more file(s)'] if len(files) > 12 else []
                failures[name] = failures.get(name, []) + files[:12] + more
    return failures


def main(argv):
    names = [a[:-3] if a.endswith('.py') else a for a in argv] or CHECKS
    unknown = [n for n in names if n not in CHECKS]
    if unknown:
        print(f'unknown generator(s) {unknown}; expected some of {CHECKS}')
        return 2
    pillow = have_pillow()
    skipped = skips(names, pillow, pillow and have_jp_font())
    failures = check([n for n in names if n not in skipped])
    what = lambda n: ('the Tiled maps' if n == TILED else
                      'the sprites and prefabs' if n in ART_TOOLS else 'config.json')
    for name in names:
        if name in skipped:
            print(f'skip  {name}.py {skipped[name]} - NOT checked')
        elif name not in failures:
            print(f'ok    {name}.py reproduces {what(name)}')
        else:
            crashed = failures[name][0].startswith('exited ')
            print(f'FAIL  {name}.py did not finish:' if crashed else
                  f'DRIFT {name}.py would change {what(name)}:')
            for line in failures[name]:
                print(f'        {line}')
    if failures:
        print('\nA generator no longer rebuilds the committed world. Fold the difference into the\n'
              'generator (or have it keep what it does not own) - do not re-run it over the room.\n'
              'For a Tiled map: python3 tools/config_to_tiled.py <Room> after the config edit.')
        if any(n in ART_TOOLS for n in failures):
            print(f'The art tools ran on Pillow {pillow_version()}. A sprite drawn a pixel off by another Pillow\n'
                  'shows as drift too: docs/generators-and-checks.md lists the versions that rebuild the art.')
    if skipped:
        print(f'\n{len(skipped)} art tool(s) not checked: ' +
              ('this python3 has no Pillow. Run the check with one that does.' if not pillow else
               'no Japanese system font is readable here (generate_ads.find_font). '
               'Run the check where the system fonts are.'))
    return 1 if failures else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
