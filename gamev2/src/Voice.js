/**
 * Voice — spoken NPC dialogue, and the game's shared audio settings.
 *
 * A resolved NPC state may carry "voice": <voiceId> (written by
 * tools/blog_to_npc.py next to "photo"): the clip for dialogue line N lives
 * at assets/voice/<voiceId>/<N>.mp3 (N is the 0-based index into the state's
 * dialogue array). DialogueManager calls playLine() as each line is shown and
 * stop() on close; playLine() always stops the previous clip first.
 *
 * Clips are NOT preloaded: the source is set when the line appears and the
 * browser's HTTP cache covers replays. Every clip goes through ONE shared
 * HTMLAudioElement, created and "unlocked" (a few ms of silence played and
 * paused) inside the first real key press / tap. playLine() itself runs from
 * Phaser's update loop, not inside the input event, and iOS Safari only lets
 * an element that a gesture has already played start again from there.
 *
 * Everything here is best-effort: an NPC without a voice, a missing or
 * undecodable clip, or a rejected play() just means the line is read
 * silently.
 *
 * The mute setting ("Voices: ON/OFF" in the ESC menu) persists in
 * localStorage under gamev2_voice_muted and defaults to ON (not muted). Other
 * audio features should honour it too: read isMuted() and subscribe with
 * onMuteChange().
 */
class Voice {
    constructor() {
        this.muted = false;
        try { this.muted = localStorage.getItem(Voice.STORE_KEY) === '1'; } catch (e) { /* no storage */ }
        this.audio = null;        // the one shared HTMLAudioElement (made on first gesture / first clip)
        this.current = null;      // that element while a line's clip is loading or playing, else null
        this.gen = 0;             // bumped by every playLine()/stop(), so stale callbacks can tell
        this.unlocked = false;
        this.unlocking = false;
        this.listeners = [];

        if (typeof window !== 'undefined' && typeof Audio !== 'undefined') {
            this.unlock = this.unlock.bind(this);
            Voice.GESTURES.forEach(ev => window.addEventListener(ev, this.unlock, true));
        }
    }

    isMuted() {
        return this.muted;
    }

    setMuted(muted) {
        this.muted = !!muted;
        try { localStorage.setItem(Voice.STORE_KEY, this.muted ? '1' : '0'); } catch (e) { /* play on */ }
        if (this.muted) this.stop();
        this.listeners.forEach(fn => fn(this.muted));
    }

    toggleMuted() {
        this.setMuted(!this.muted);
        return this.muted;
    }

    /** fn(muted) is called whenever the mute setting changes. */
    onMuteChange(fn) {
        this.listeners.push(fn);
    }

    clipUrl(voiceId, lineIndex) {
        return `assets/voice/${encodeURIComponent(voiceId)}/${lineIndex}.mp3`;
    }

    element() {
        if (!this.audio && typeof Audio !== 'undefined') {
            const audio = this.audio = new Audio();
            const drop = () => { this.current = null; };
            audio.addEventListener('ended', drop);
            audio.addEventListener('error', drop);   // missing / undecodable clip: stay silent
        }
        return this.audio;
    }

    /**
     * Gesture handler (capture phase, so it runs inside the key press / tap
     * itself): play a moment of silence on the shared element so later
     * play() calls from the game loop are allowed. Retried on each gesture
     * until one is accepted, then the listeners are removed.
     */
    unlock() {
        if (this.unlocked || this.unlocking) return;
        const audio = this.element();
        if (this.current) {
            // a line already owns the element: if it is audibly running the
            // element is as unlocked as it gets, otherwise try again later
            if (!audio.paused) this.finishUnlock();
            return;
        }
        const gen = this.gen;
        const settle = ok => {
            this.unlocking = false;
            if (ok) this.finishUnlock();
            if (this.gen !== gen) return;   // a line took the element over meanwhile
            audio.pause();
            audio.removeAttribute('src');
            audio.load();
        };
        this.unlocking = true;
        audio.src = Voice.SILENCE;
        const started = audio.play();
        if (started && started.then) started.then(() => settle(true), () => settle(false));
        else settle(true);
    }

    finishUnlock() {
        this.unlocked = true;
        Voice.GESTURES.forEach(ev => window.removeEventListener(ev, this.unlock, true));
    }

    /**
     * Speak dialogue line `lineIndex` of voice `voiceId`, replacing whatever
     * was playing. A falsy voiceId (NPC has no voice) or a muted game just
     * stops the previous clip. Returns the audio element, or null.
     */
    playLine(voiceId, lineIndex) {
        this.stop();
        if (!voiceId || this.muted) return null;
        const audio = this.element();
        if (!audio) return null;

        const gen = ++this.gen;
        audio.src = this.clipUrl(voiceId, lineIndex);
        this.current = audio;

        // play() rejects when the clip fails to load, when autoplay is
        // blocked, or when stop() interrupts it — none of which matter
        const started = audio.play();
        if (started && started.catch) {
            started.catch(() => { if (this.gen === gen) this.current = null; });
        }
        return audio;
    }

    stop() {
        const audio = this.current;
        if (!audio) return;
        this.gen++;
        this.current = null;
        audio.pause();
        // drop the source so a clip still downloading is aborted
        audio.removeAttribute('src');
        audio.load();
    }
}

Voice.STORE_KEY = 'gamev2_voice_muted';
Voice.GESTURES = ['pointerdown', 'pointerup', 'touchend', 'click', 'keydown'];
// 10 ms of 8-bit silence
Voice.SILENCE = 'data:audio/wav;base64,UklGRnQAAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YVAAAACAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgA==';
