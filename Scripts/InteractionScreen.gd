extends Control
# NPC dialogue box. Ported from InteractionScreen.cs.

signal interaction_completed(npc_name)

var _dialogue_text: RichTextLabel
var _name_label: Label
var _continue_button: Button
var _click_indicator: Label

var _dialogue_lines: Array = []
var _current_line_index := 0
var _npc_name := ""

func _ready():
	_dialogue_text = get_node("DialogueBox/DialogueText")
	_name_label = get_node("CharacterDisplay/NameLabel")
	_continue_button = get_node("DialogueBox/ContinueButton")
	_click_indicator = get_node("DialogueBox/ClickIndicator")
	_dialogue_text.bbcode_enabled = true
	_continue_button.pressed.connect(_on_continue_pressed)
	set_process_input(true)
	# Keep processing while the game is paused.
	process_mode = Node.PROCESS_MODE_ALWAYS
	visible = false

func _input(event):
	if not visible:
		return
	if event is InputEventKey and event.pressed:
		if event.keycode == KEY_SPACE or event.keycode == KEY_ENTER:
			_on_continue_pressed()

func show_interaction(npc, _last_scene := ""):
	_npc_name = npc.npc_name
	_dialogue_lines = Array(npc.dialogue_lines)
	_current_line_index = 0
	_name_label.text = _npc_name
	_show_current_line()
	visible = true
	get_tree().paused = true

func _show_current_line():
	if _current_line_index < _dialogue_lines.size():
		_dialogue_text.text = _dialogue_lines[_current_line_index]
		if _current_line_index < _dialogue_lines.size() - 1:
			_click_indicator.text = "Click to continue..."
			_continue_button.text = "Continue"
		else:
			_click_indicator.text = "Click to close"
			_continue_button.text = "Close"

func _on_continue_pressed():
	_current_line_index += 1
	if _current_line_index < _dialogue_lines.size():
		_show_current_line()
	else:
		_close_interaction()

func _close_interaction():
	queue_free()
	get_tree().paused = false
