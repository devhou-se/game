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