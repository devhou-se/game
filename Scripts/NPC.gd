class_name NPC extends Character
# Wandering NPC with name label, dialogue, and bump-to-talk. Ported from NPC.cs.

@export var cares_about_bailey_butler_being_in_the_office: bool = false
@export var enable_full_interaction: bool = true
@export var npc_name: String = ""
@export var dialogue_lines: PackedStringArray = PackedStringArray([
	"Hello there!",
	"Nice to meet you.",
	"How can I help you today?",
])

const MOVE_WAIT_TIME := 3.0
const VECTORS := [Vector2.LEFT, Vector2.RIGHT, Vector2.UP, Vector2.DOWN]

var _is_bailey_butler_in_the_office := false
var _text_time_left := 0.0
var _control: Control
var _interaction_screen_scene: PackedScene
var _next_move_wait_time := 3.0
var _http: HTTPRequest

func _ready():
	super._ready()
	_control = get_node("Control")
	_interaction_screen_scene = load("res://Scenes/InteractionScreen.tscn")
	var name_label: Label = get_node("Title")
	name_label.text = npc_name
	# Use this person's sprite if one exists (Assets/people/<name>.tres).
	var sf_path := "res://Assets/people/%s.tres" % npc_name.to_lower()
	if ResourceLoader.exists(sf_path):
		_animated_sprite.sprite_frames = load(sf_path)
	_check_if_bailey_butler_is_in_the_office()

func _process(delta):
	super._process(delta)
	_next_move_wait_time -= delta
	if _text_time_left > 0:
		_text_time_left -= delta
		if _text_time_left <= 0:
			_control.visible = false

func _physics_process(delta):
	_update_input_vector()
	super._physics_process(delta)

# Bumper interface (duck-typed via has_method("bump") in Character).
func bump(bumper):
	if not (bumper is Player):
		return
	if Global.conversation_cooldown > 0:
		return
	if _text_time_left > 0:
		return
	if enable_full_interaction and _interaction_screen_scene:
		var interaction_screen = _interaction_screen_scene.instantiate()
		var ui_layer = get_node_or_null("/root/Main/UI")
		if ui_layer:
			ui_layer.add_child(interaction_screen)
		else:
			get_tree().current_scene.add_child(interaction_screen)
		interaction_screen.show_interaction(self)
		interaction_screen.tree_exiting.connect(_on_conversation_ended)

func _on_conversation_ended():
	Global.conversation_cooldown = 1.0

func _update_input_vector():
	if _next_move_wait_time > 0:
		return
	_next_move_wait_time = MOVE_WAIT_TIME
	var index := randi() % VECTORS.size()
	set_input_vector(VECTORS[index])

func _check_if_bailey_butler_is_in_the_office():
	_http = HTTPRequest.new()
	add_child(_http)
	_http.request_completed.connect(_on_office_check_completed)
	var err := _http.request("http://isbaileybutlerintheoffice.today/raw")
	if err != OK:
		push_warning("Office check request failed to start")

func _on_office_check_completed(_result, _response_code, _headers, body: PackedByteArray):
	var text := body.get_string_from_utf8().strip_edges()
	_is_bailey_butler_in_the_office = (text == "yes")
