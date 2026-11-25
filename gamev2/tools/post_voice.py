#!/usr/bin/env python3
"""post_voice.py — speak an NPC's dialogue with ElevenLabs text-to-speech.

Each dialogue line of a dated NPC state is sent to the ElevenLabs REST API in
its author's voice and saved to assets/voice/<voice id>/<line index>.mp3.
blog_to_npc.py records the clip set on the state as "voice": "<voice id>",
and the dialogue box plays the clip for each line as it is shown
(src/Voice.js).

Configuration is all environment variables:

  ELEVENLABS_API_KEY            the API key (xi-api-key)
  ELEVENLABS_VOICE_<NPC>        ElevenLabs voice id for an NPC, by upper-cased
                                NPC name: ELEVENLABS_VOICE_BAILEY, _DAMIAN,
                                _DYLAN, _JULIA
  ELEVENLABS_VOICE_<NPC>_DRUNK  optional second voice id, used when the LLM
                                judged the post to read as drunk (falls back
                                to the sober voice when unset)
  ELEVENLABS_MODEL              optional TTS model id
                                (default eleven_multilingual_v2)

Voice is strictly best-effort, like photos: with no key or no voice id for the
author the step logs one line and returns None, and any API failure does the
same, so the NPC placement always lands. A clip set is all-or-nothing — if any
line fails, the lines already written are removed and no "voice" is recorded,
so the game never asks for a clip that is not there.

The voice id is <npc>-<date>-<hash of the lines and the voice used>, so clips
can never be paired with dialogue other than the lines they were made from,
and re-running an unchanged post reuses the clips already on disk instead of
paying for them again. When the lines or the voice do change the old directory
is orphaned; prune_voices() (run by blog_to_npc.py after every config write)
deletes clip directories no state references any more.
"""
import hashlib
import json
import os
import shutil
import urllib.error
import urllib.parse
import urllib.request

API_URL = 'https://api.elevenlabs.io/v1/text-to-speech/{voice}?output_format=mp3_44100_128'
DEFAULT_MODEL = 'eleven_multilingual_v2'
VOICE_DIR = 'assets/voice'


def elevenlabs_voice(npc_name, drunk=False):
    """The configured ElevenLabs voice id for an NPC, or None. The drunk voice
    is optional per author and falls back to the sober one."""
    base = f'ELEVENLABS_VOICE_{npc_name.upper()}'
    return (drunk and os.environ.get(f'{base}_DRUNK')) or os.environ.get(base) or None


def voice_id_for(npc_name, date, dialogue, tts_voice):
    """Directory name for a clip set: stable for the same lines in the same
    voice, different as soon as either changes."""
    digest = hashlib.sha1(json.dumps([tts_voice, dialogue]).encode()).hexdigest()[:8]
    return f'{npc_name.lower()}-{date}-{digest}'


def synthesize(text, tts_voice, api_key, model):
    """One ElevenLabs text-to-speech call -> mp3 bytes."""
    req = urllib.request.Request(
        API_URL.format(voice=urllib.parse.quote(tts_voice, safe='')),
        data=json.dumps({'text': text, 'model_id': model}).encode(),
        headers={
            'xi-api-key': api_key,
            'Content-Type': 'application/json',
            'Accept': 'audio/mpeg',
            'User-Agent': 'devhouse-game-pipeline',
        },
        method='POST',
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = resp.read()
    if not data:
        raise ValueError('empty audio response')
    return data


def voice_dialogue(npc_name, date, dialogue, drunk=False, out_dir=VOICE_DIR, dry_run=False):
    """Generate one clip per dialogue line. Returns the voice id
    (assets/voice/<id>/<line>.mp3) or None when unconfigured or failed."""
    api_key = os.environ.get('ELEVENLABS_API_KEY')
    tts_voice = elevenlabs_voice(npc_name, drunk)
    if not api_key or not tts_voice:
        missing = 'ELEVENLABS_API_KEY' if not api_key else f'ELEVENLABS_VOICE_{npc_name.upper()}'
        print(f'  voice: {missing} not set — skipped')
        return None

    mood = 'drunk' if drunk and os.environ.get(f'ELEVENLABS_VOICE_{npc_name.upper()}_DRUNK') else 'sober'
    voice_id = voice_id_for(npc_name, date, dialogue, tts_voice)
    dest = os.path.join(out_dir, voice_id)
    chars = sum(len(line) for line in dialogue)
    if dry_run:
        print(f'  voice: would speak {len(dialogue)} lines ({chars} chars, {mood}) -> {dest}/')
        return voice_id

    paths = [os.path.join(dest, f'{i}.mp3') for i in range(len(dialogue))]
    if all(os.path.exists(p) for p in paths):
        print(f'  voice: {dest}/ already has all {len(dialogue)} clips — reused')
        return voice_id

    model = os.environ.get('ELEVENLABS_MODEL') or DEFAULT_MODEL
    try:
        os.makedirs(dest, exist_ok=True)
        for line, path in zip(dialogue, paths):
            data = synthesize(line, tts_voice, api_key, model)
            with open(path, 'wb') as f:
                f.write(data)
    except Exception as e:
        # clean up first: nothing below may leave a partial clip set behind
        shutil.rmtree(dest, ignore_errors=True)
        detail = f'{type(e).__name__}: {e}'
        if isinstance(e, urllib.error.HTTPError):
            # the API explains itself in the body (bad voice id, quota, ...)
            try:
                detail += ' ' + e.read(300).decode('utf-8', 'replace')
            except Exception:
                pass   # the body is a nicety; the connection may be gone
        print(f'  voice: text-to-speech failed ({detail}) — skipped')
        return None

    print(f'  voice: {len(dialogue)} lines ({chars} chars, {mood}) -> {dest}/')
    return voice_id


def referenced_voices(node):
    """Every "voice" id named anywhere in a config (base NPC defs + states)."""
    found = set()
    if isinstance(node, dict):
        for key, value in node.items():
            if key == 'voice' and isinstance(value, str):
                found.add(value)
            else:
                found |= referenced_voices(value)
    elif isinstance(node, list):
        for value in node:
            found |= referenced_voices(value)
    return found


def prune_voices(cfg, out_dir=VOICE_DIR):
    """Delete clip directories no state in the config points at any more
    (lines regenerated, voice id changed, --reset, dialogue hand-edited) so
    superseded clips are not deployed forever. Returns the removed ids."""
    if not os.path.isdir(out_dir):
        return []
    keep = referenced_voices(cfg)
    removed = []
    for name in sorted(os.listdir(out_dir)):
        path = os.path.join(out_dir, name)
        if os.path.isdir(path) and not os.path.islink(path) and name not in keep:
            shutil.rmtree(path, ignore_errors=True)
            removed.append(name)
    if removed:
        print(f'voice: removed {len(removed)} superseded clip set(s): {", ".join(removed)}')
    return removed
