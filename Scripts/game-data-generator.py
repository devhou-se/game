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