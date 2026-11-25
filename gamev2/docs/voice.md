# Voiced dialogue

Spoken NPC lines: `src/Voice.js`, the mute setting and the `tools/post_voice.py` pipeline step.

A "see X" in the text names a section; if it is not in this file, the index in [`../CLAUDE.md`](../CLAUDE.md) says which file has it.

### Voiced Dialogue (text-to-speech)

NPC dialogue can be read aloud. A resolved NPC state carrying `"voice": <voiceId>` (passed through
`syncNpcPresence` → `NPCManager.spawnNPC` exactly like `"photo"`) has one clip per dialogue line at
`assets/voice/<voiceId>/<lineIndex>.mp3` (0-based index into that state's `dialogue`).

- **Client** (`src/Voice.js`, `scene.voice`): `DialogueManager.updateText()` calls `voice.playLine()` as each
  line is shown (which stops the previous line's clip) and `close()` calls `voice.stop()`. Clips are NOT
  preloaded — the source is set at dialogue time on ONE shared `HTMLAudioElement`, which is created and
  unlocked (10 ms of silence played inside the first key press / tap, capture-phase listeners removed once
  it succeeds) because `playLine()` runs from Phaser's update loop and iOS Safari only lets a
  gesture-played element start from there (the unlock is untested on a real iOS device). An NPC without `voice`, a clip
  that fails to load/decode, or a rejected `play()` is a silent no-op (the only trace of a 404 is the
  browser's own network log line, which is why the pipeline never records a partial clip set).
- **Mute**: the ESC menu's `Voices: ON/OFF` row (flips in place, menu stays open) persists in localStorage
  `gamev2_voice_muted` (`'1'` = muted; default ON). It is the game's shared audio setting — other audio
  features should read `scene.voice.isMuted()` / subscribe with `scene.voice.onMuteChange(fn)`.
- **State merging**: clips belong to the exact lines they were generated from, so in `resolveNpc` a state
  that sets `dialogue` without naming `voice` clears the inherited voice (and `tools/npc_state.py --dialogue`
  drops a state's `voice`).
- **Pipeline** (`tools/post_voice.py`, called by `tools/blog_to_npc.py` after the photo import): with
  `ELEVENLABS_API_KEY` and `ELEVENLABS_VOICE_<NPC>` (e.g. `ELEVENLABS_VOICE_BAILEY`, `_DAMIAN`, `_DYLAN`,
  `_JULIA`, `_KHOI`, `_SAM`, `_XANDER` — the name is derived from the NPC name, so a new author needs no code
  change, only the secret AND a line passing it in the `env:` of www-jp's `game-npc-pipeline.yaml` /
  `game-npc-backfill.yaml`, which list each one by hand) set, each dialogue line is POSTed to the ElevenLabs text-to-speech REST API (stdlib `urllib`)
  and the dated state gets `"voice": "<npc>-<date>-<hash>"`. Optional: `ELEVENLABS_VOICE_<NPC>_DRUNK` (used
  when the LLM's new `drunk` boolean says the post reads as drunk; the state then also carries
  `"drunk": true`) and `ELEVENLABS_MODEL` (default `eleven_multilingual_v2`). Best-effort like photos:
  unconfigured or failing, it logs one `voice: ... — skipped` line and the placement lands with
  `"voice": null`. A clip set is all-or-nothing, and an unchanged re-run reuses the clips on disk.
  After every config write `prune_voices()` deletes clip directories no state references any more, so the
  pipeline workflow must commit `gamev2/assets/voice` (additions and deletions, e.g. `git add -A`) together
  with `config.json` — a recorded `voice` whose clips were not deployed 404s on every line.
  `prune_photos()` (`tools/post_photos.py`) does the same for `assets/photos/<id>.png` prints no state names
  any more (a later same-day post's photo won, the NPC left the room, `--reset`; it also runs when a run
  places nothing, for a post that failed after its photo was imported), so `gamev2/assets/photos`
  must be committed the same way; `test_blog_to_npc.py` fails on an orphaned or missing print.
- **Backfill**: `python3 tools/blog_to_npc.py --voice-backfill [--dry-run]` voices existing dated states
  that have dialogue but no voice (no LLM call, no placement). `--dry-run` prints the line/character
  totals ElevenLabs would bill for.
- **Not live yet**: no API key or cloned voice ids exist, so no state has a `voice` and the game is silent.
