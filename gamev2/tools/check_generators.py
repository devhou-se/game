#!/usr/bin/env python3
"""check_generators.py — a room generator re-run on an unchanged world must
leave config.json byte-identical (issue #107).

The generated rooms also collect edits their generator did not make: the blog
pipeline's NPC states, a shop door wired by another generator, a surgical fix
through /adjust-game. A generator that does not know about such an edit drops
it the next time it runs. This runs every room generator on its own, in a
scratch copy of the project (the real config.json is never written), and
fails if the copy's config.json changed — naming the rooms and cells, so the
edit can be folded back into the generator (or kept by it, the way NPCs are).

Run from gamev2/:  python3 tools/check_generators.py [generator ...]
                   python3 tools/check_generators.py generate_osaka

Exit 0 when every generator reproduces the committed world, 1 otherwise.
Needs no Pillow. A new room generator belongs in GENERATORS.
"""
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
    'generate_machi', 'generate_inaka', 'generate_yukimura', 'generate_osaka',
    'generate_sapporo', 'generate_asahikawa',
    'generate_konbinis', 'generate_discount_stores', 'generate_stations',
]
# what a generator reads, relative to gamev2/ (config.json is copied per run)
INPUTS = ['tools', 'tiled/prefabs', 'assets/sprites']


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
    with tempfile.TemporaryDirectory(prefix='check_generators_') as work:
        for rel in INPUTS:
            shutil.copytree(os.path.join(root, rel), os.path.join(work, rel),
                            ignore=shutil.ignore_patterns('__pycache__'))
        scratch = os.path.join(work, 'config.json')
        for name in names:
            open(scratch, 'w').write(committed)
            run = subprocess.run([sys.executable, f'tools/{name}.py'], cwd=work,
                                 stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            if run.returncode != 0:
                last = (run.stdout.strip().splitlines() or ['no output'])[-1]
                failures[name] = [f'exited {run.returncode}: {last}']
                continue
            regenerated = open(scratch).read()
            if regenerated != committed:
                failures[name] = describe(json.loads(committed), json.loads(regenerated))
    return failures


def main(argv):
    names = [a[:-3] if a.endswith('.py') else a for a in argv] or GENERATORS
    unknown = [n for n in names if n not in GENERATORS]
    if unknown:
        print(f'unknown generator(s) {unknown}; expected some of {GENERATORS}')
        return 2
    failures = check(names)
    for name in names:
        if name not in failures:
            print(f'ok    {name}.py reproduces config.json')
            continue
        print(f'DRIFT {name}.py would change config.json:')
        for line in failures[name]:
            print(f'        {line}')
    if failures:
        print('\nA generator no longer rebuilds the committed world. Fold the difference into the\n'
              'generator (or have it keep what it does not own) - do not re-run it over the room.')
    return 1 if failures else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
