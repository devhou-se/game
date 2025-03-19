# Game Repository Integration Setup Guide

This guide provides step-by-step instructions for implementing the www-jp blog to game integration in your Godot-based game repository. When properly configured, this system will automatically convert blog posts into interactive NPCs with dialogue and voice synthesis.

## Table of Contents

1. [Overview](#overview)
2. [Repository Structure](#repository-structure)
3. [Workflow Files](#workflow-files)
4. [Required Scripts](#required-scripts)
5. [Godot Project Configuration](#godot-project-configuration)
6. [Configuring Secrets](#configuring-secrets)
7. [Testing the Integration](#testing-the-integration)
8. [Troubleshooting](#troubleshooting)

## Overview

The integration system works as follows:

1. When a new blog post is created in the www-jp repository:
   - A webhook notification is sent to your game repository
   - The notification includes the post ID, title, author, date, and content

2. Your game repository then:
   - Processes the post content to generate character attributes
   - Creates dialogue options based on post content (in English and Japanese)
   - Generates voice audio using ElevenLabs API
   - Stores audio files in Google Cloud Storage
   - Updates game data files with new character information
   - Triggers a build and deployment of the game

## Repository Structure

Your game repository should include these components:

```
game-repository/
├── .github/
│   └── workflows/
│       ├── process-blog-post.yaml
│       └── build-deploy.yaml
├── scripts/
│   ├── requirements.txt
│   ├── game-data-generator.py
│   ├── voice-synthesis.py
│   └── gcs-uploader.py
├── data/
│   ├── characters/
│   └── audio/
└── [your Godot project files]
```

## Workflow Files

### 1. Process Blog Post Workflow

Create a file at `.github/workflows/process-blog-post.yaml`:

```yaml
name: Process Blog Post

on:
  repository_dispatch:
    types: [new_post]
    
jobs:
  process-game-data:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4
        
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.10"
          
      - name: Install dependencies
        run: pip install -r scripts/requirements.txt
        
      - name: Extract post data
        id: extract-data
        run: |
          echo '${{ toJson(github.event.client_payload) }}' > post_data.json
          POST_ID=$(jq -r '.post_id' post_data.json)
          POST_AUTHOR=$(jq -r '.author' post_data.json)
          echo "post_id=$POST_ID" >> $GITHUB_OUTPUT
          echo "post_author=$POST_AUTHOR" >> $GITHUB_OUTPUT
          
      - name: Generate game data
        run: python scripts/game-data-generator.py
        env:
          POST_DATA_FILE: post_data.json
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
          
      - name: Generate audio
        run: python scripts/voice-synthesis.py
        env:
          ELEVENLABS_API_KEY: ${{ secrets.ELEVENLABS_API_KEY }}
          POST_ID: ${{ steps.extract-data.outputs.post_id }}
          POST_AUTHOR: ${{ steps.extract-data.outputs.post_author }}
          
      - name: Upload audio to GCS
        run: python scripts/gcs-uploader.py
        env:
          GCS_BUCKET: ${{ secrets.GCS_BUCKET }}
          GCS_CREDENTIALS: ${{ secrets.GCS_CREDENTIALS }}
          POST_ID: ${{ steps.extract-data.outputs.post_id }}
          
      - name: Update game data
        run: |
          mkdir -p data/characters/
          mkdir -p data/audio/
          cp generated/character-${{ steps.extract-data.outputs.post_id }}.json data/characters/
          cp generated/audio-refs-${{ steps.extract-data.outputs.post_id }}.json data/audio/
          
      - name: Commit changes
        run: |
          git config user.name "GitHub Actions"
          git config user.email "actions@github.com"
          git add data/characters/ data/audio/
          git commit -m "Add game data for post #${{ steps.extract-data.outputs.post_id }}"
          git push
```

### 2. Build and Deploy Workflow

Create a file at `.github/workflows/build-deploy.yaml`:

```yaml
name: Build and Deploy Game

on:
  push:
    branches:
      - main
    paths:
      - 'data/characters/**'
      - 'data/audio/**'
      
jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4
        
      - name: Setup Godot
        uses: chickensoft-games/setup-godot@v1
        with:
          version: 4.2.1
          export-templates: true
          
      - name: Build WASM
        run: |
          mkdir -p build/web
          godot --headless --export-release "Web" build/web/index.html
          
      - name: Deploy to hosting
        uses: cloudflare/wrangler-action@v3
        with:
          apiToken: ${{ secrets.CF_API_TOKEN }}
          accountId: ${{ secrets.CF_ACCOUNT_ID }}
          command: pages deploy build/web --project-name=game
```

## Required Scripts

### 1. Python Dependencies

Create a file at `scripts/requirements.txt`:

```
openai>=1.0.0
google-cloud-storage>=2.7.0
requests>=2.28.0
elevenlabs>=0.2.24
```

### 2. Game Data Generator

Create a file at `scripts/game-data-generator.py`:

```python
#!/usr/bin/env python3
import os
import json
import openai
import random

# Set up OpenAI API
openai.api_key = os.environ.get("OPENAI_API_KEY")

# Load post data
post_data_file = os.environ.get("POST_DATA_FILE", "post_data.json")
with open(post_data_file, 'r') as f:
    post_data = json.load(f)

post_id = post_data.get("post_id")
post_title = post_data.get("title")
post_author = post_data.get("author")
post_content = post_data.get("content")

# Generate character traits using OpenAI
def generate_character_traits():
    response = openai.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a character designer for a pixel art game. Generate character traits based on the blog post content."},
            {"role": "user", "content": f"Generate character traits based on this blog post:\nTitle: {post_title}\nContent: {post_content}\n\nProvide a JSON object with these fields:\n- personality (5 adjectives)\n- interests (5 items)\n- movement_pattern (one of: 'wander', 'stationary', 'patrol')\n- appearance (brief description)\n- location_preference (one of: 'town_center', 'beach', 'market', 'park', 'library')"}
        ]
    )
    
    result = response.choices[0].message.content
    # Extract JSON from the response
    try:
        # Find JSON in the response
        json_start = result.find('{')
        json_end = result.rfind('}') + 1
        json_str = result[json_start:json_end]
        return json.loads(json_str)
    except Exception as e:
        print(f"Error parsing JSON: {e}")
        # Return fallback traits
        return {
            "personality": ["friendly", "curious", "thoughtful", "creative", "calm"],
            "interests": ["technology", "travel", "photography", "writing", "food"],
            "movement_pattern": "wander",
            "appearance": "Casual outfit with a camera and notebook",
            "location_preference": "town_center"
        }

# Generate dialogue options using OpenAI
def generate_dialogue():
    response = openai.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a dialogue writer for a pixel art game. Generate dialogue based on the blog post content."},
            {"role": "user", "content": f"Generate dialogue options based on this blog post:\nTitle: {post_title}\nContent: {post_content}\n\nProvide a JSON object with these categories:\n- greetings (3 short phrases)\n- topics (5 topics with 3 dialogue lines each)\n- reactions (3 each for: happy, sad, surprised, curious)\n\nKeep each dialogue line under 100 characters. Make them sound conversational."}
        ]
    )
    
    result = response.choices[0].message.content
    # Extract JSON from the response
    try:
        # Find JSON in the response
        json_start = result.find('{')
        json_end = result.rfind('}') + 1
        json_str = result[json_start:json_end]
        return json.loads(json_str)
    except Exception as e:
        print(f"Error parsing JSON: {e}")
        # Return fallback dialogue
        return {
            "greetings": ["Hello there!", "Nice to meet you.", "Welcome!"],
            "topics": {
                "topic1": ["This is a fallback dialogue line.", "Second fallback line.", "Third fallback line."],
                "topic2": ["Another fallback dialogue.", "More fallback dialogue.", "Yet more fallback."]
            },
            "reactions": {
                "happy": ["That's great!", "I'm glad to hear that.", "Wonderful!"],
                "sad": ["I'm sorry to hear that.", "That's unfortunate.", "I hope things get better."],
                "surprised": ["Really?", "I didn't expect that!", "That's surprising!"],
                "curious": ["Tell me more.", "How interesting!", "I'd like to know more about that."]
            }
        }

# Translate dialogue to Japanese
def translate_dialogue(dialogue):
    # Prepare dialogue for translation
    all_lines = []
    
    # Add greetings
    for greeting in dialogue["greetings"]:
        all_lines.append(greeting)
    
    # Add topics
    for topic, lines in dialogue["topics"].items():
        all_lines.extend(lines)
    
    # Add reactions
    for emotion, reactions in dialogue["reactions"].items():
        all_lines.extend(reactions)
    
    # Translate all lines at once
    response = openai.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a translator who specializes in Japanese. Translate each line to natural, conversational Japanese."},
            {"role": "user", "content": f"Translate each of these lines to Japanese. Return a JSON array with the translated lines in the same order:\n\n{json.dumps(all_lines)}"}
        ]
    )
    
    result = response.choices[0].message.content
    
    try:
        # Find JSON in the response
        json_start = result.find('[')
        json_end = result.rfind(']') + 1
        json_str = result[json_start:json_end]
        translated_lines = json.loads(json_str)
        
        # Rebuild the dialogue structure with translations
        translated_dialogue = {"en": dialogue, "ja": {}}
        
        # Copy English structure
        translated_dialogue["ja"]["greetings"] = []
        translated_dialogue["ja"]["topics"] = {}
        translated_dialogue["ja"]["reactions"] = {}
        
        # Get translations from the array
        index = 0
        
        # Add greetings
        for _ in range(len(dialogue["greetings"])):
            translated_dialogue["ja"]["greetings"].append(translated_lines[index])
            index += 1
        
        # Add topics
        for topic, lines in dialogue["topics"].items():
            translated_dialogue["ja"]["topics"][topic] = []
            for _ in range(len(lines)):
                translated_dialogue["ja"]["topics"][topic].append(translated_lines[index])
                index += 1
        
        # Add reactions
        for emotion, reactions in dialogue["reactions"].items():
            translated_dialogue["ja"]["reactions"][emotion] = []
            for _ in range(len(reactions)):
                translated_dialogue["ja"]["reactions"][emotion].append(translated_lines[index])
                index += 1
        
        return translated_dialogue
    
    except Exception as e:
        print(f"Error parsing translated JSON: {e}")
        # Return original dialogue without translations
        return {"en": dialogue, "ja": dialogue}

# Main process
def main():
    # Generate character traits
    traits = generate_character_traits()
    
    # Generate dialogue
    dialogue = generate_dialogue()
    
    # Translate dialogue
    translated_dialogue = translate_dialogue(dialogue)
    
    # Create character data
    character_data = {
        "post_id": post_id,
        "author": post_author,
        "title": post_title,
        "traits": traits,
        "dialogue": translated_dialogue,
        "created_at": post_data.get("date")
    }
    
    # Ensure output directory exists
    os.makedirs("generated", exist_ok=True)
    
    # Save character data to file
    with open(f"generated/character-{post_id}.json", 'w') as f:
        json.dump(character_data, f, indent=2)
    
    print(f"Generated character data for post #{post_id} by {post_author}")

if __name__ == "__main__":
    main()
```

### 3. Voice Synthesis Script

Create a file at `scripts/voice-synthesis.py`:

```python
#!/usr/bin/env python3
import os
import json
import requests
from elevenlabs import generate, save
from elevenlabs.client import ElevenLabs

# Set up ElevenLabs API
api_key = os.environ.get("ELEVENLABS_API_KEY")
client = ElevenLabs(api_key=api_key)

# Get post information
post_id = os.environ.get("POST_ID")
post_author = os.environ.get("POST_AUTHOR")

# Define voice mapping - ensure you have access to these voices
# or substitute with voices available in your ElevenLabs subscription
VOICE_MAPPING = {
    # Default voices
    "default_en_male": "Adam",
    "default_en_female": "Rachel",
    "default_ja_male": "Takumi",
    "default_ja_female": "Hiroto",
    
    # Custom mappings for specific authors
    "bailey": "Daniel",
    "alex": "Thomas",
    "jordan": "Rachel"
}

def get_voice_for_author(author):
    """Get the appropriate voice for the author"""
    if author.lower() in VOICE_MAPPING:
        return VOICE_MAPPING[author.lower()]
    
    # Default to a generic voice based on username characteristics
    # This is a simplified approach - you might want more sophisticated logic
    username_length = len(author)
    if username_length % 2 == 0:
        return VOICE_MAPPING["default_en_male"]
    else:
        return VOICE_MAPPING["default_en_female"]

def generate_audio_files():
    """Generate audio files for dialogue lines"""
    # Load character data
    try:
        with open(f"generated/character-{post_id}.json", 'r') as f:
            character_data = json.load(f)
    except FileNotFoundError:
        print(f"Character data file not found for post #{post_id}")
        return
    
    # Create output directories
    os.makedirs(f"generated/audio/{post_id}/en", exist_ok=True)
    os.makedirs(f"generated/audio/{post_id}/ja", exist_ok=True)
    
    # Get the appropriate voice
    voice_name = get_voice_for_author(post_author)
    
    # Track audio files and their corresponding text
    audio_refs = {
        "en": {},
        "ja": {}
    }
    
    # Process English dialogue
    dialogue_en = character_data["dialogue"]["en"]
    
    # Generate audio for greetings
    audio_refs["en"]["greetings"] = []
    for i, greeting in enumerate(dialogue_en["greetings"]):
        filename = f"generated/audio/{post_id}/en/greeting_{i}.mp3"
        
        # Generate and save audio
        audio = generate(
            text=greeting,
            voice=voice_name,
            model="eleven_multilingual_v2"
        )
        save(audio, filename)
        
        audio_refs["en"]["greetings"].append({
            "text": greeting,
            "file": f"audio/{post_id}/en/greeting_{i}.mp3"
        })
    
    # Generate audio for topics
    audio_refs["en"]["topics"] = {}
    for topic, lines in dialogue_en["topics"].items():
        audio_refs["en"]["topics"][topic] = []
        for i, line in enumerate(lines):
            filename = f"generated/audio/{post_id}/en/topic_{topic}_{i}.mp3"
            
            # Generate and save audio
            audio = generate(
                text=line,
                voice=voice_name,
                model="eleven_multilingual_v2"
            )
            save(audio, filename)
            
            audio_refs["en"]["topics"][topic].append({
                "text": line,
                "file": f"audio/{post_id}/en/topic_{topic}_{i}.mp3"
            })
    
    # Generate audio for reactions
    audio_refs["en"]["reactions"] = {}
    for emotion, reactions in dialogue_en["reactions"].items():
        audio_refs["en"]["reactions"][emotion] = []
        for i, reaction in enumerate(reactions):
            filename = f"generated/audio/{post_id}/en/reaction_{emotion}_{i}.mp3"
            
            # Generate and save audio
            audio = generate(
                text=reaction,
                voice=voice_name,
                model="eleven_multilingual_v2"
            )
            save(audio, filename)
            
            audio_refs["en"]["reactions"][emotion].append({
                "text": reaction,
                "file": f"audio/{post_id}/en/reaction_{emotion}_{i}.mp3"
            })
    
    # Process Japanese dialogue
    dialogue_ja = character_data["dialogue"]["ja"]
    
    # For Japanese, use a Japanese voice
    ja_voice = VOICE_MAPPING.get("default_ja_male")
    
    # Generate audio for Japanese greetings
    audio_refs["ja"]["greetings"] = []
    for i, greeting in enumerate(dialogue_ja["greetings"]):
        filename = f"generated/audio/{post_id}/ja/greeting_{i}.mp3"
        
        # Generate and save audio
        audio = generate(
            text=greeting,
            voice=ja_voice,
            model="eleven_multilingual_v2"
        )
        save(audio, filename)
        
        audio_refs["ja"]["greetings"].append({
            "text": greeting,
            "file": f"audio/{post_id}/ja/greeting_{i}.mp3"
        })
    
    # Generate audio for Japanese topics
    audio_refs["ja"]["topics"] = {}
    for topic, lines in dialogue_ja["topics"].items():
        audio_refs["ja"]["topics"][topic] = []
        for i, line in enumerate(lines):
            filename = f"generated/audio/{post_id}/ja/topic_{topic}_{i}.mp3"
            
            # Generate and save audio
            audio = generate(
                text=line,
                voice=ja_voice,
                model="eleven_multilingual_v2"
            )
            save(audio, filename)
            
            audio_refs["ja"]["topics"][topic].append({
                "text": line,
                "file": f"audio/{post_id}/ja/topic_{topic}_{i}.mp3"
            })
    
    # Generate audio for Japanese reactions
    audio_refs["ja"]["reactions"] = {}
    for emotion, reactions in dialogue_ja["reactions"].items():
        audio_refs["ja"]["reactions"][emotion] = []
        for i, reaction in enumerate(reactions):
            filename = f"generated/audio/{post_id}/ja/reaction_{emotion}_{i}.mp3"
            
            # Generate and save audio
            audio = generate(
                text=reaction,
                voice=ja_voice,
                model="eleven_multilingual_v2"
            )
            save(audio, filename)
            
            audio_refs["ja"]["reactions"][emotion].append({
                "text": reaction,
                "file": f"audio/{post_id}/ja/reaction_{emotion}_{i}.mp3"
            })
    
    # Save audio references
    with open(f"generated/audio-refs-{post_id}.json", 'w') as f:
        json.dump(audio_refs, f, indent=2)
    
    print(f"Generated audio files for post #{post_id}")

if __name__ == "__main__":
    generate_audio_files()
```

### 4. Google Cloud Storage Uploader

Create a file at `scripts/gcs-uploader.py`:

```python
#!/usr/bin/env python3
import os
import json
import base64
from tempfile import NamedTemporaryFile
from google.cloud import storage

# Get post ID
post_id = os.environ.get("POST_ID")

# Setup GCS client
gcs_credentials_json = os.environ.get("GCS_CREDENTIALS")
gcs_bucket_name = os.environ.get("GCS_BUCKET")

def upload_to_gcs():
    """Upload audio files to Google Cloud Storage"""
    # Create a temporary file for credentials
    with NamedTemporaryFile(mode='w', delete=False) as temp:
        temp.write(gcs_credentials_json)
        temp_name = temp.name
    
    try:
        # Setup GCS client
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = temp_name
        storage_client = storage.Client()
        bucket = storage_client.bucket(gcs_bucket_name)
        
        # Load audio references
        with open(f"generated/audio-refs-{post_id}.json", 'r') as f:
            audio_refs = json.load(f)
        
        # Upload English audio files
        for category in ["greetings", "reactions"]:
            if category == "greetings":
                for item in audio_refs["en"][category]:
                    local_path = f"generated/{item['file']}"
                    remote_path = item['file']
                    blob = bucket.blob(remote_path)
                    blob.upload_from_filename(local_path)
            elif category == "reactions":
                for emotion, reactions in audio_refs["en"][category].items():
                    for item in reactions:
                        local_path = f"generated/{item['file']}"
                        remote_path = item['file']
                        blob = bucket.blob(remote_path)
                        blob.upload_from_filename(local_path)
        
        # Upload English topic audio files
        for topic, items in audio_refs["en"]["topics"].items():
            for item in items:
                local_path = f"generated/{item['file']}"
                remote_path = item['file']
                blob = bucket.blob(remote_path)
                blob.upload_from_filename(local_path)
        
        # Upload Japanese audio files
        for category in ["greetings", "reactions"]:
            if category == "greetings":
                for item in audio_refs["ja"][category]:
                    local_path = f"generated/{item['file']}"
                    remote_path = item['file']
                    blob = bucket.blob(remote_path)
                    blob.upload_from_filename(local_path)
            elif category == "reactions":
                for emotion, reactions in audio_refs["ja"][category].items():
                    for item in reactions:
                        local_path = f"generated/{item['file']}"
                        remote_path = item['file']
                        blob = bucket.blob(remote_path)
                        blob.upload_from_filename(local_path)
        
        # Upload Japanese topic audio files
        for topic, items in audio_refs["ja"]["topics"].items():
            for item in items:
                local_path = f"generated/{item['file']}"
                remote_path = item['file']
                blob = bucket.blob(remote_path)
                blob.upload_from_filename(local_path)
        
        print(f"Uploaded audio files to GCS bucket '{gcs_bucket_name}'")
    
    finally:
        # Clean up the temporary file
        if os.path.exists(temp_name):
            os.unlink(temp_name)

if __name__ == "__main__":
    upload_to_gcs()
```

## Godot Project Configuration

### 1. Character Manager Script

Create a file in your Godot project at `scripts/character_manager.gd`:

```gdscript
extends Node

# Audio base URLs
const AUDIO_BASE_URL = "https://storage.googleapis.com/[YOUR-BUCKET-NAME]"

# Character data
var characters = {}
var audio_refs = {}

# Current language
var current_language = "en"

func _ready():
    # Load all character data
    load_characters()
    
    # Connect language change signal
    # You'll need to implement this signal in your game
    # For example: settings.connect("language_changed", self, "_on_language_changed")

# Load all character data from files
func load_characters():
    characters = {}
    audio_refs = {}
    
    var dir = Directory.new()
    if dir.open("res://data/characters/") == OK:
        dir.list_dir_begin(true)
        var file_name = dir.get_next()
        while file_name != "":
            if not dir.current_is_dir() and file_name.ends_with(".json"):
                var character_file = "res://data/characters/" + file_name
                var audio_file = "res://data/audio/audio-refs-" + file_name.split("-")[1]
                
                var character_data = load_json_file(character_file)
                var audio_data = load_json_file(audio_file)
                
                if character_data and audio_data:
                    var post_id = character_data.post_id
                    characters[post_id] = character_data
                    audio_refs[post_id] = audio_data
            
            file_name = dir.get_next()

# Load JSON file
func load_json_file(file_path):
    var file = File.new()
    var error = file.open(file_path, File.READ)
    if error != OK:
        print("Error opening file: ", file_path)
        return null
    
    var content = file.get_as_text()
    file.close()
    
    var json = JSON.parse(content)
    if json.error != OK:
        print("Error parsing JSON: ", file_path)
        return null
    
    return json.result

# Get all character IDs
func get_character_ids():
    return characters.keys()

# Get character data by ID
func get_character(id):
    if characters.has(id):
        return characters[id]
    return null

# Get audio URL for character dialogue
func get_audio_url(character_id, category, key = null, index = 0):
    if not audio_refs.has(character_id):
        return ""
    
    var lang = current_language
    
    if category == "greeting":
        if index < audio_refs[character_id][lang]["greetings"].size():
            var file_path = audio_refs[character_id][lang]["greetings"][index]["file"]
            return AUDIO_BASE_URL + "/" + file_path
    
    elif category == "topic" and key != null:
        if audio_refs[character_id][lang]["topics"].has(key):
            if index < audio_refs[character_id][lang]["topics"][key].size():
                var file_path = audio_refs[character_id][lang]["topics"][key][index]["file"]
                return AUDIO_BASE_URL + "/" + file_path
    
    elif category == "reaction" and key != null:
        if audio_refs[character_id][lang]["reactions"].has(key):
            if index < audio_refs[character_id][lang]["reactions"][key].size():
                var file_path = audio_refs[character_id][lang]["reactions"][key][index]["file"]
                return AUDIO_BASE_URL + "/" + file_path
    
    return ""

# Get text for character dialogue
func get_dialogue_text(character_id, category, key = null, index = 0):
    if not characters.has(character_id):
        return ""
    
    var lang = current_language
    var dialogue = characters[character_id]["dialogue"][lang]
    
    if category == "greeting":
        if index < dialogue["greetings"].size():
            return dialogue["greetings"][index]
    
    elif category == "topic" and key != null:
        if dialogue["topics"].has(key):
            if index < dialogue["topics"][key].size():
                return dialogue["topics"][key][index]
    
    elif category == "reaction" and key != null:
        if dialogue["reactions"].has(key):
            if index < dialogue["reactions"][key].size():
                return dialogue["reactions"][key][index]
    
    return ""

# Change current language
func set_language(lang):
    if lang in ["en", "ja"]:
        current_language = lang

# Callback for language changes
func _on_language_changed(new_language):
    set_language(new_language)
```

### 2. NPC Controller Script

Create a file in your Godot project at `scripts/npc_controller.gd`:

```gdscript
extends Node2D

# Character properties
export var character_id = ""
export var dialogue_bubble_scene: PackedScene

# Movement properties
var movement_pattern = "wander"
var location_preference = "town_center"
var movement_speed = 50
var wander_radius = 100
var initial_position = Vector2.ZERO
var target_position = Vector2.ZERO
var moving = false

# Dialogue properties
var dialogue_bubble = null
var current_dialogue = ""
var current_audio_player = null

# Character Manager reference
onready var character_manager = get_node("/root/CharacterManager")

func _ready():
    # Save initial position
    initial_position = global_position
    
    # Load character data
    if character_id and character_manager:
        var character = character_manager.get_character(character_id)
        if character:
            # Set up movement based on character traits
            movement_pattern = character.traits.movement_pattern
            location_preference = character.traits.location_preference
            
            # Randomize speed slightly
            movement_speed = rand_range(40, 60)
            
            # Set up initial dialogue - random greeting
            var greeting_index = int(rand_range(0, 3))
            current_dialogue = character_manager.get_dialogue_text(character_id, "greeting", null, greeting_index)
            
            # Create dialogue bubble
            dialogue_bubble = dialogue_bubble_scene.instance()
            add_child(dialogue_bubble)
            dialogue_bubble.set_text(current_dialogue)
            dialogue_bubble.visible = false
            
            # Play greeting audio
            var audio_url = character_manager.get_audio_url(character_id, "greeting", null, greeting_index)
            if audio_url:
                play_audio(audio_url)
    
    # Start movement behavior
    start_movement()

func _process(delta):
    if movement_pattern != "stationary" and moving:
        # Move towards target position
        var direction = target_position - global_position
        if direction.length() > 5:
            global_position += direction.normalized() * movement_speed * delta
        else:
            # Reached target, stop moving
            moving = false
            # Wait before moving again
            yield(get_tree().create_timer(rand_range(3, 8)), "timeout")
            start_movement()

# Start NPC movement based on pattern
func start_movement():
    match movement_pattern:
        "wander":
            # Pick a random point within wander radius
            var angle = rand_range(0, 2 * PI)
            var distance = rand_range(0, wander_radius)
            target_position = initial_position + Vector2(cos(angle), sin(angle)) * distance
            moving = true
        
        "patrol":
            # Patrol between points - implement your own logic here
            pass
        
        "stationary":
            # Don't move
            moving = false

# Interact with NPC - called when player initiates interaction
func interact():
    # Show dialogue bubble
    if dialogue_bubble:
        dialogue_bubble.visible = true
        
        # Choose a random topic
        var character = character_manager.get_character(character_id)
        var topics = character.dialogue[character_manager.current_language].topics.keys()
        var random_topic = topics[int(rand_range(0, topics.size()))]
        var line_index = int(rand_range(0, 3))
        
        # Set dialogue text
        current_dialogue = character_manager.get_dialogue_text(character_id, "topic", random_topic, line_index)
        dialogue_bubble.set_text(current_dialogue)
        
        # Play audio
        var audio_url = character_manager.get_audio_url(character_id, "topic", random_topic, line_index)
        if audio_url:
            play_audio(audio_url)
        
        # Hide bubble after a delay
        yield(get_tree().create_timer(5.0), "timeout")
        dialogue_bubble.visible = false

# Play audio from URL
func play_audio(url):
    # Stop current audio if playing
    if current_audio_player and current_audio_player.is_playing():
        current_audio_player.stop()
    
    # Create audio player if needed
    if not current_audio_player:
        current_audio_player = AudioStreamPlayer.new()
        add_child(current_audio_player)
    
    # Load and play audio
    var http_request = HTTPRequest.new()
    add_child(http_request)
    http_request.connect("request_completed", self, "_on_audio_request_completed")
    http_request.request(url)

# Handle audio request completion
func _on_audio_request_completed(result, response_code, headers, body):
    if result == HTTPRequest.RESULT_SUCCESS and response_code == 200:
        var stream = AudioStreamMP3.new()
        stream.data = body
        current_audio_player.stream = stream
        current_audio_player.play()
```

## Configuring Secrets

Add these secrets to your game repository:

1. `OPENAI_API_KEY`
   - Required for generating character data and translating dialogue
   - Get from: https://platform.openai.com/api-keys

2. `ELEVENLABS_API_KEY`
   - Required for voice synthesis
   - Get from: https://elevenlabs.io/app/api-key

3. `GCS_BUCKET`
   - Name of your Google Cloud Storage bucket
   - Format: `your-bucket-name` (without gs:// prefix)

4. `GCS_CREDENTIALS`
   - Service account JSON credentials for GCS
   - Format: Complete JSON credential file contents

5. `CF_API_TOKEN`
   - Cloudflare API token for deploying to Pages
   - Required if using Cloudflare for hosting

6. `CF_ACCOUNT_ID`
   - Your Cloudflare account ID
   - Required if using Cloudflare for hosting

### Setting Up GCS

1. Create a GCS bucket:
   - Go to Google Cloud Console -> Storage -> Buckets
   - Click "Create Bucket"
   - Name your bucket and configure settings
   - Set appropriate permissions and CORS configuration

2. Create a service account:
   - Go to IAM & Admin -> Service Accounts
   - Create a new service account with "Storage Object Admin" role
   - Create and download a JSON key

3. Format the JSON key:
   - Use the entire JSON file contents as the GCS_CREDENTIALS secret

## Testing the Integration

Once everything is set up, you can test the integration:

1. Create a test blog post in the www-jp repository
2. Monitor the GitHub Actions tab in your game repository
3. The "Process Blog Post" workflow should trigger automatically
4. Check the workflow logs for any errors
5. Verify that character data and audio files are generated
6. Check the game after it's built and deployed

For manual testing, you can create a new file in your game repository to simulate receiving a webhook:

```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"event_type":"new_post","client_payload":{"post_id":"123","title":"Test Post","author":"testuser","date":"2025-03-19T12:00:00Z","content":"This is a test post content."}}' \
  -H "Authorization: token YOUR_GITHUB_PAT" \
  "https://api.github.com/repos/YOUR_USERNAME/YOUR_GAME_REPO/dispatches"
```

## Troubleshooting

### Common Issues

1. **Webhook Not Received**
   - Check the repository dispatch event configuration
   - Verify that the GAME_REPO_TOKEN has the correct permissions
   - Check GitHub Actions logs in www-jp repository

2. **Character Generation Fails**
   - Verify OpenAI API key is valid
   - Check for rate limiting or quota issues
   - Review Python script error messages

3. **Audio Generation Fails**
   - Verify ElevenLabs API key is valid
   - Check that the specified voices exist in your account
   - Look for error messages in the workflow logs

4. **GCS Upload Fails**
   - Verify GCS credentials are correct
   - Check bucket permissions
   - Ensure the service account has the right roles

5. **Game Build Fails**
   - Check Godot export configuration
   - Verify project structure and required files
   - Review build logs for specific error messages