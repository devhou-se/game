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