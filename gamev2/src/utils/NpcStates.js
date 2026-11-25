/**
 * NpcStates — dated NPC state snapshots.
 *
 * An NPC in config.json may carry a `states` object keyed by ISO date:
 *
 *   "states": {
 *     "2026-06-30": { "dialogue": ["..."] },
 *     "2026-07-02": { "dialogue": ["..."], "gridX": 26, "gridY": 34 }
 *   }
 *
 * At load, the states dated on-or-before the game date are applied to the
 * base NPC in chronological order — each one is an UPDATE overlaying only the
 * fields it names (so a later dialogue change keeps an earlier position
 * change, and anything never named falls back to the base definition).
 * Viewing "2026-07-01" above shows the 06-30 dialogue at the base position.
 *
 * The game date is ?date=YYYY-MM-DD when given (time travel). Otherwise it is
 * today (device local time) while a trip is on and, between trips, the trip
 * day that today cycles onto: see defaultGameDate. A state of
 * {"present": false} removes the NPC from that date until a later state sets
 * it back.
 *
 * Trips (config.trips, src/utils/Trips.js) scope all of this: only the
 * states dated inside the game date's trip — and, when the trip moves base,
 * inside its current stay — are applied, and a base NPC marked "trip" (and
 * "stay") only exists on that trip's dates. See resolveNpc.
 *
 * A state may also carry "photo": <post id> — a blog-post photo imported to
 * assets/photos/<id>.png by tools/blog_to_npc.py, hung in a frame beside the
 * author in the dialogue box. The pipeline writes photo on every placement
 * (null when the post had none) so an older photo never bleeds forward.
 *
 * Likewise "voice": <voice id> — spoken clips for that state's dialogue, one
 * per line at assets/voice/<id>/<line index>.mp3 (tools/post_voice.py, played
 * by src/Voice.js). Clips belong to the exact dialogue they were generated
 * from, so a state that changes the dialogue without naming a voice clears
 * it rather than inheriting clips for lines that are no longer said.
 *
 * And "posts": [{ id, lines, title?, url? }, ...] — which blog post each run
 * of the state's dialogue lines came from, in dialogue order (the pipeline
 * merges an author's same-day posts into one state). The dialogue box
 * captions each line with its post's title when one is recorded
 * (postForLine below); `tools/blog_to_npc.py --backfill-posts` adds
 * titles to states placed before they were kept. Like voice, posts belong to
 * the dialogue they were written with and are not inherited by a later state
 * that changes it.
 */
/** Today's real date, device local time, as YYYY-MM-DD. */
function todayIso() {
    const d = new Date();
    return d.getFullYear() + '-' +
        String(d.getMonth() + 1).padStart(2, '0') + '-' +
        String(d.getDate()).padStart(2, '0');
}

// Every date with dated content, sorted, and the trips they belong to
// (Trips.of(config)). Set once the config has loaded (see setTripDates);
// empty until then, and for a config with no dated content / no trips.
let tripDates = [];
let loadedTrips = [];
// The real date when the config loaded. NPCs are resolved once, at boot, so
// the default game date must not move on at midnight in a session left open
// (the HUD would name a day whose stories are not the ones showing).
let bootToday = null;

/**
 * Tell the date functions which days have content — the sorted
 * contentChangeDates(config) — and which trips there are. GameScene calls
 * this as soon as config.json is decoded, before anything asks for the game
 * date or resolves an NPC.
 */
function setTripDates(config) {
    tripDates = [...contentChangeDates(config)].sort();
    loadedTrips = Trips.of(config);
    bootToday = todayIso();
}

/**
 * The game date when the URL names none (issues #54, #118).
 *
 * With trips configured (Trips.defaultDate): today while a trip is on —
 * whether or not anyone has posted yet — and otherwise a content day of the
 * most recent trip, cycled: count the days since that trip's last post and
 * wrap at its number of content days, so the day after the last is day one
 * again. Only days that have content are in the cycle, and only one trip's,
 * so two trips are never read as one long span. A visitor therefore always
 * lands on a day of a trip, everyone has that day's story, and coming back
 * tomorrow shows the next one.
 *
 * Without trips the content days are taken as one trip, first day to last
 * (the rule before trips were data).
 *
 * `today` defaults to the real date as it was when the config loaded (the
 * world is resolved once, so the date holds for the session), `dates` to
 * the loaded content days and `trips` to the loaded trips; all are
 * parameters so the mapping can be checked without a clock.
 */
function defaultGameDate(today = bootToday || todayIso(), dates = tripDates, trips = loadedTrips) {
    if (trips.length) return Trips.defaultDate(today, dates, trips);
    if (!dates.length) return today;
    const first = dates[0], last = dates[dates.length - 1];
    if (today >= first && today <= last) return today;
    return Trips.cycle(today, dates);
}

function gameDate() {
    const p = new URLSearchParams(location.search).get('date');
    if (p && /^\d{4}-\d{2}-\d{2}$/.test(p)) return p;
    return defaultGameDate();
}

/**
 * An NPC as it is on `date`, or null when it is not there.
 *
 * `trips` (default: the loaded config's) scopes it to the trip the date
 * belongs to — Trips.windowFor: a base definition marked "trip" (and
 * "stay") is absent outside that trip (and stay), exactly as if it said
 * "present": false, and states dated before the window opens are another
 * trip's history and are skipped. States inside the window apply as ever,
 * so a post still places its author in any room.
 */
function resolveNpc(npcConfig, date, trips = loadedTrips) {
    const scope = trips.length ? Trips.windowFor(trips, date) : null;
    const scoped = !Trips.baseOn(npcConfig, scope);
    if (!npcConfig.states && !scoped) return npcConfig;
    const merged = Object.assign({}, npcConfig);
    delete merged.states;
    if (scoped) merged.present = false;
    // ISO dates compare correctly as strings
    for (const d of Object.keys(npcConfig.states || {}).sort()) {
        if (d > date || (scope && d < scope.from)) continue;
        const state = npcConfig.states[d];
        Object.assign(merged, state);
        if ('dialogue' in state && !('voice' in state)) merged.voice = null;
        if ('dialogue' in state && !('posts' in state)) merged.posts = null;
    }
    if (merged.present === false) return null;
    return merged;
}

/**
 * The blog post dialogue line `lineIndex` came from, or null.
 *
 * `posts` is a resolved state's "posts": [{ id, lines, title?, url? }, ...]
 * in dialogue order, each covering `lines` lines. Only a post with a recorded
 * title is returned — nothing is captioned for states from before titles
 * were kept — and only when the counts add up to the `lineCount` lines being
 * said, so a hand-edited state never credits a line to the wrong post.
 */
function postForLine(posts, lineIndex, lineCount) {
    if (!Array.isArray(posts) || !posts.length) return null;
    const counted = posts.every(p => p && Number.isInteger(p.lines) && p.lines >= 0);
    if (!counted || posts.reduce((n, p) => n + p.lines, 0) !== lineCount) return null;
    let end = 0;
    for (const post of posts) {
        end += post.lines;
        if (lineIndex < end) {
            const titled = typeof post.title === 'string' && post.title.trim() !== '';
            return titled ? post : null;
        }
    }
    return null;
}

/** A post's link, if it is a web address (config is data: nothing else is ever opened). */
function postLink(post) {
    return post && typeof post.url === 'string' && /^https?:\/\//.test(post.url) ? post.url : null;
}

/**
 * Dates on which NPC content changes. The blog pipeline records each accepted
 * post as one or more dated NPC states, so de-duplicating their keys gives the
 * calendar the days that have associated blog content.
 */
function contentChangeDates(config) {
    const dates = new Set();
    for (const room of Object.values((config && config.rooms) || {})) {
        for (const npc of room.npcs || []) {
            for (const date of Object.keys(npc.states || {})) {
                if (/^\d{4}-\d{2}-\d{2}$/.test(date)) dates.add(date);
            }
        }
    }
    return dates;
}

const MONTHS = ['January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December'];

/** "2026-07-02" -> "July 2 2026" (the HUD display format). */
function formatGameDate(iso) {
    const [y, m, d] = iso.split('-').map(Number);
    return `${MONTHS[m - 1]} ${d} ${y}`;
}

/**
 * Navigate to the given game date. The date a clean URL already gives
 * (defaultGameDate) drops the param; any other date — including today's real
 * date once the trip is over — is an explicit choice and goes in ?date=.
 * This reloads, so the comparison uses the real date now, not the boot one.
 */
function setGameDate(iso) {
    const params = new URLSearchParams(location.search);
    if (!iso || iso === defaultGameDate(todayIso())) params.delete('date'); else params.set('date', iso);
    const qs = params.toString();
    // a date hop is an in-game action that happens to reload the page: don't
    // drop the player back on the title screen (one-shot, consumed by
    // TitleScreen.shouldShow on the next load)
    try { sessionStorage.setItem('gamev2_skip_title', '1'); } catch (e) { /* storage blocked */ }
    location.href = location.pathname + (qs ? '?' + qs : '');
}

if (typeof window !== 'undefined') {
    window.gameDate = gameDate;
    window.defaultGameDate = defaultGameDate;
    window.setTripDates = setTripDates;
    window.resolveNpc = resolveNpc;
    window.postForLine = postForLine;
    window.postLink = postLink;
    window.contentChangeDates = contentChangeDates;
    window.formatGameDate = formatGameDate;
    window.setGameDate = setGameDate;
}
