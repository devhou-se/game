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