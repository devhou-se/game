#!/usr/bin/env python3
"""check_distinct.py — is each city still as much its own as it was?

The measure from the city audit (issues #210, #219): how much of a city's art
it shares with another city, and how much is used nowhere else. Three numbers
per city, over its outdoor rooms (a stitched city's districts count as one
city; stations and interiors are left out): the tiles of their layers, and the
cars that run their streets (a room's `tramways`: a tram or a cable car is
drawn by src/AmbientTrams.js and not as a tile, and is the city's art all the
same, issue #264):

  buildings   the highest Jaccard overlap of its BUILDING sprites with any
              other city's (shared / all of the pair; 7-Eleven excluded)
  sprites     the same over every sprite, ground and shared kit included
  own         the share of its building and scenery sprites (no ground, no
              shared kit) that no other city uses

A "sprite" is a tile family: autotile pieces, sheet frames and top / bottom
halves fold into one name (`grass-autotile_edge-n` -> `grass-autotile`,
`torii-red-top` + `-feet` -> `torii-red`, `building-roof-blue` -> `house-blue`).

The targets a city passes at (the redesign plan's rule 1):

  buildings <= 0.25     sprites <= 0.40     own >= one third

Today's cities miss them by design until each is rebuilt, so this check does
not fail on the targets. It fails (exit 1) only when a city is WORSE than the
numbers recorded in tools/distinct_baseline.json: a higher overlap or a lower
own share. A city that is not in the baseline (a new town) is printed with
its numbers against the targets and does not fail the check: record it.

Run from gamev2/:  python3 tools/check_distinct.py            the table, and the verdict
                   python3 tools/check_distinct.py --update   record today's numbers as the baseline
                                                              (after a rebuild made a city better,
                                                              or a new town landed: say why in the commit)

A new town's own landmark art counts as building sprites once its prefix is
in LANDMARK_ART below.
"""
import json
import os
import re
import sys

TARGETS = {'buildings': 0.25, 'sprites': 0.40, 'own': 1 / 3}
BASELINE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'distinct_baseline.json')
# pieces shared on purpose: not counted for or against a city's own art
KIT = re.compile(r'^(seven-eleven|7-11-sign|.*vending-machine|road-|crossing-|traffic-light|train-track|'
                 r'station-|train-|gk_blank)')
# art drawn for one place: a building sprite
LANDMARK_ART = re.compile(
    r'(asahikawa-|ramen-banner|canal-|dazaifu-|fukuoka-|hakata-|yatai-|dotonbori-|tsutenkaku|sapporo-|'
    r'sendai-(zuihoden|masamune|pub|kiln|gate|barrels)|matsushima-|tokyo-station|tokyo-tower|kanazawa-|karuizawa-|'
    r'shirakawa-(?!paddy)|toyama-(?!tram-rail)|devhouse-|himeji-|kansai-|okayama-|nara-|'
    # Asahikawa (issue #219, stage B): building prefixes only - `heiwa-`, `ramen-` or `zoo-` alone would
    # count the paving, Sapporo's ramen-alley-lanterns and the props
    r'heiwa-shop-|ramen-(shoyu|narrow|miso)-front|asahibashi-|hokkaido-house-|zoo-(gate|ticket-booth))')
TEMPLE_KIT = re.compile(
    r'(shrine|red-shrine|red-centre-roof|red-pagoda|red-small-pagoda|pagoda-|temple-|blue-wall|'
    r'blue-short-wall|blue-shrine|torii-|fox-statue|kirin-statue|bell-|blue-bell|castle-wall)')
# a number moves by less than this from rounding alone
EPS = 0.005


def family(key):
    """The sprite a tile key is a piece of."""
    k = re.sub(r'_(center|edge-[nsew]|corner-[ns][ew]|inner-[ns][ew])$', '', key)
    k = re.sub(r'_\d+_\d+$', '', k)
    k = k.replace('gravel_autotile', 'gravel-autotile')
    m = re.match(r'building-(rafter|tier|roof)-(\w+)$', k)
    if m:
        return 'house-' + m.group(2)
    if re.match(r'building-entrance-\d', k):
        return 'house-entrance'
    snow = '-snow' if k.endswith('-snow') else ''
    if snow:
        k = k[:-5]
    m = re.match(r'(.*?)-(top|bottom|feet|base|base-shadow)(-\d+)?$', k)
    if m:
        k = m.group(1)
    return k + snow


def is_building(fam):
    """A building sprite: a house, machiya, high-rise, the discount store,
    the shrine / temple kit, or a named landmark. Not the 7-Eleven (kit)."""
    return bool(fam.startswith(('house-', 'machiya-', 'highrise-', 'midrise-')) or fam == 'discount-store'
                or TEMPLE_KIT.match(fam) or LANDMARK_ART.match(fam))


def towns(cfg):
    """{city name: [outdoor room keys]} — a stitched city's districts under
    the city's name, any other outdoor room under its own key."""
    stations = set(cfg.get('stations') or {})
    city_of = {}
    for city in (cfg.get('cities') or {}).values():
        for m in city.get('rooms', []):
            city_of[m['room']] = city.get('name') or m['room']
    out = {}
    for key, room in cfg['rooms'].items():
        if room.get('interior') or key in stations:
            continue
        out.setdefault(city_of.get(key, key), []).append(key)
    return out


def sprite_sets(cfg, rooms):
    """(all sprites, building sprites, buildings + scenery) of some rooms:
    what their layers hold and the cars on their `tramways`."""
    pal = cfg.get('tilePalette') or []
    sprites, ground = set(), set()
    for key in rooms:
        for line in cfg['rooms'][key].get('tramways') or []:
            if line.get('sprite'):
                sprites.add(family(line['sprite']))
        for layer in cfg['rooms'][key].get('layers', []):
            if layer.get('collision'):
                continue
            for v in (layer.get('tiles') or {}).values():
                fam = family(pal[v] if isinstance(v, int) else v)
                if fam == 'house-entrance':
                    continue
                sprites.add(fam)
                if layer['name'] in ('Floor', 'Water'):
                    ground.add(fam)
    buildings = {f for f in sprites if is_building(f)}
    objects = {f for f in sprites if not KIT.match(f) and f not in ground}
    return sprites, buildings, objects


def jaccard(a, b):
    return len(a & b) / len(a | b) if a | b else 0.0


def measure(cfg):
    """{city: {'buildings', 'sprites', 'own', 'like'}} for every live city:
    its worst building overlap (and with whom: 'like'), its worst all-sprite
    overlap, and the share of its buildings and scenery that are its own."""
    sets = {city: sprite_sets(cfg, rooms) for city, rooms in towns(cfg).items()}
    out = {}
    for city, (sprites, buildings, objects) in sets.items():
        others = [c for c in sets if c != city]
        worst = max(others, key=lambda c: jaccard(buildings, sets[c][1]), default=None)
        elsewhere = set().union(*[sets[c][2] for c in others]) if others else set()
        out[city] = {
            'buildings': round(jaccard(buildings, sets[worst][1]) if worst else 0.0, 3),
            'like': worst,
            'sprites': round(max((jaccard(sprites, sets[c][0]) for c in others), default=0.0), 3),
            'own': round(len(objects - elsewhere) / len(objects) if objects else 0.0, 3),
        }
    return out


def worse(now, base):
    """The ways `now` (one city's numbers) is worse than its baseline: a list
    of sentences, empty when it is no worse."""
    out = []
    for key, word in (('buildings', 'building overlap'), ('sprites', 'sprite overlap')):
        if now[key] > base[key] + EPS:
            out.append(f'{word} {now[key]:.2f}, was {base[key]:.2f}')
    if now['own'] < base['own'] - EPS:
        out.append(f"own art {now['own']:.0%}, was {base['own']:.0%}")
    return out


def passes(now):
    return (now['buildings'] <= TARGETS['buildings'] + EPS and now['sprites'] <= TARGETS['sprites'] + EPS
            and now['own'] >= TARGETS['own'] - EPS)


def check(cfg, baseline):
    """(lines to print, cities that got worse) for a config against a baseline
    {city: {'buildings', 'sprites', 'own'}}."""
    now = measure(cfg)
    lines = [f"{'city':<12} {'buildings':>9} {'(most like)':<14} {'sprites':>7} {'own':>5}   against the targets, and the baseline",
             f"{'target':<12} {'<= ' + format(TARGETS['buildings'], '.2f'):>9} {'':<14} "
             f"{'<= ' + format(TARGETS['sprites'], '.2f'):>7} {'>= 33%':>5}"]
    failed = []
    for city, n in now.items():
        base = baseline.get(city)
        verdict = 'passes' if passes(n) else 'below target'
        if base is None:
            verdict += ' - NOT in the baseline: record it (--update)'
        else:
            bad = worse(n, base)
            if bad:
                failed.append(city)
                verdict += ' - WORSE than the baseline: ' + '; '.join(bad)
        lines.append(f"{city:<12} {n['buildings']:>9.2f} {'(' + str(n['like']) + ')':<14} {n['sprites']:>7.2f} {n['own']:>5.0%}   {verdict}")
    gone = sorted(set(baseline) - set(now))
    if gone:
        lines.append(f"in the baseline but not in the world: {', '.join(gone)} (--update drops them)")
    return lines, failed


def main(argv):
    if '-h' in argv or '--help' in argv:
        print(__doc__.strip())
        return 0
    unknown = [a for a in argv if a != '--update']
    if unknown:
        print(f"unknown option {' '.join(unknown)}; options: --help --update", file=sys.stderr)
        return 2
    cfg = json.load(open('config.json'))
    if '--update' in argv:
        now = {city: {k: n[k] for k in ('buildings', 'sprites', 'own')} for city, n in measure(cfg).items()}
        open(BASELINE, 'w').write(json.dumps(now, indent=2, sort_keys=True) + '\n')
        print(f'{len(now)} cities recorded in tools/distinct_baseline.json')
        return 0
    baseline = json.load(open(BASELINE)) if os.path.exists(BASELINE) else {}
    lines, failed = check(cfg, baseline)
    print('\n'.join(lines))
    if failed:
        print(f"\n{', '.join(failed)}: less its own than recorded. Give the city art of its own instead of another "
              "city's, or, if the change is meant, record it: python3 tools/check_distinct.py --update")
        return 1
    print('\nno city is worse than the baseline (tools/distinct_baseline.json)')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
