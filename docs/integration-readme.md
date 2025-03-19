# www-jp Blog to Game Integration

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