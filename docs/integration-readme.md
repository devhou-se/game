# www-jp Blog to Game Integration

> **Current pipeline (gamev2).** The live game is the Phaser project in `gamev2/`, and its blog
> integration is `gamev2/tools/blog_to_npc.py`. Everything below the "Legacy" heading — and all of
> `integration-setup-guide.md` — describes the retired Godot-era design (OpenAI personality profiles,
> GCS-hosted audio, `character_manager.gd`), none of which exists in gamev2.

## How it works today

A new devhou.se blog post moves its author's NPC and gives them new dialogue:

1. The `game-npc-pipeline` workflow in the **www-jp** repository (not this one) checks out this repo and
   runs, from `gamev2/`, `python3 tools/blog_to_npc.py --payload post.json` with the post as
   `{"post_id", "title", "author", "date", "content"}` (`author` is the GitHub login), then commits the
   result. Pushing to master deploys via `.github/workflows/firebase-hosting-gamev2.yml`.
2. **Text**: one Claude call (`MODEL` in the tool, structured JSON output) reads the post and returns the
   spot the author should stand at (one of the landmarks found in the overworld rooms), 3-4 first-person
   dialogue lines, and whether the post reads as drunk. Lines are trimmed to 160 characters on a
   sentence/word boundary, never mid-word.
3. **Photo** (optional, best-effort): the post's first image becomes a 160x144 pixel-art print in
   `gamev2/assets/photos/<post_id>.png` (`tools/post_photos.py`).
4. **Voice** (optional, best-effort): with `ELEVENLABS_API_KEY` and `ELEVENLABS_VOICE_<NPC>` set, each
   line is spoken by ElevenLabs into `gamev2/assets/voice/<voice id>/<line>.mp3` (`tools/post_voice.py`).
   Unconfigured, the placement lands silent.
5. **Placement**: the result is written to `gamev2/config.json` as a dated NPC state
   (`present`, `gridX`/`gridY`, `dialogue`, `photo`, `voice`, `posts`) in the chosen room, and
   `present: false` on that date in every other room. Two posts by one author on the same day share the
   state: the later post's spot wins and its lines follow the earlier post's (8 lines a day at most);
   `posts` records which lines came from which post, so re-running a post replaces only its own lines.
6. **Runtime**: `gamev2/src/utils/NpcStates.js` resolves each NPC to the game date (today, or
   `?date=YYYY-MM-DD` / the in-game date picker), so the author stands at the spot and says the lines
   from the post's date on. The dialogue box (`src/DialogueManager.js`) shows the lines — Japanese
   included — with the photo framed beside the speaker and the clip for each line played if there is one.

Secrets (held by the www-jp workflow): `ANTHROPIC_API_KEY`; optionally `ELEVENLABS_API_KEY` and the
`ELEVENLABS_VOICE_*` voice ids. Authors map to NPCs in `AUTHOR_NPCS` in the tool.

Test without keys or network, from `gamev2/`:

```bash
python3 tools/blog_to_npc.py --payload post.json --mock --dry-run   # canned LLM reply, nothing written
python3 tools/test_blog_to_npc.py                                   # unit checks
```

Not ported from the Godot design: generated personality profiles/traits, bilingual dialogue options, and
the 180+ generated collision responses. gamev2 has no consumer for them.

## Legacy (Godot-era) integration

The rest of this file is kept for reference only.

This integration automatically converts blog posts from the www-jp repository into interactive NPCs in the game.

## Features

- Automatically processes new blog posts via webhooks
- Generates character traits based on post content
- Creates dialogue options in both English and Japanese
- Synthesizes voice audio using ElevenLabs
- Stores audio files in Google Cloud Storage
- Updates game data and triggers deployment

## Required Secrets

To use this integration, you need to set up the following secrets in your GitHub repository:

1. `OPENAI_API_KEY` - For generating character data and translations
2. `ELEVENLABS_API_KEY` - For voice synthesis
3. `GCS_BUCKET` - The name of your Google Cloud Storage bucket
4. `GCS_CREDENTIALS` - JSON credentials for your GCS service account
5. `CF_API_TOKEN` - For Cloudflare Pages deployment (if using Cloudflare)
6. `CF_ACCOUNT_ID` - Your Cloudflare account ID (if using Cloudflare)

## Testing the Integration

You can test the integration by simulating a webhook with:

```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"event_type":"new_post","client_payload":{"post_id":"123","title":"Test Post","author":"testuser","date":"2025-03-19T12:00:00Z","content":"This is a test post content."}}' \
  -H "Authorization: token YOUR_GITHUB_PAT" \
  "https://api.github.com/repos/YOUR_USERNAME/YOUR_GAME_REPO/dispatches"
```

Replace YOUR_GITHUB_PAT, YOUR_USERNAME, and YOUR_GAME_REPO with your actual values.

## Godot Setup

1. Add the character_manager.gd as an autoload script in your project settings
2. Create a dialogue bubble scene that accepts text input
3. Use the npc_controller.gd script for blog post NPCs
4. Update AUDIO_BASE_URL in character_manager.gd with your actual GCS bucket URL

## Troubleshooting

If you encounter issues:

1. Check the Actions tab for workflow logs
2. Verify your API keys and credentials
3. Make sure the GCS bucket has appropriate permissions
4. Check the NPC scripts for compatibility with your Godot version