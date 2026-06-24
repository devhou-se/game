extends MarginContainer
# Main menu (procedural UI). Ported from Menu.cs.

var _name_input: LineEdit

func _ready():
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)

	var background := TextureRect.new()
	background.texture = load("res://Assets/menu.jpeg")
	background.stretch_mode = TextureRect.STRETCH_SCALE
	background.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	background.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	add_child(background)

	var main_container := VBoxContainer.new()
	add_child(main_container)
	main_container.set_anchors_preset(Control.PRESET_CENTER)
	main_container.size_flags_horizontal = Control.SIZE_FILL
	main_container.size_flags_vertical = Control.SIZE_FILL
	main_container.add_theme_constant_override("separation", 10)

	var margin_container := MarginContainer.new()
	margin_container.add_theme_constant_override("margin_top", 50)
	main_container.add_child(margin_container)

	var button_container := VBoxContainer.new()
	margin_container.add_child(button_container)
	button_container.set_anchors_preset(Control.PRESET_CENTER)
	button_container.size_flags_horizontal = Control.SIZE_FILL
	button_container.size_flags_vertical = Control.SIZE_FILL
	button_container.add_theme_constant_override("separation", 10)

	var name_label := Label.new()
	name_label.text = "Enter your name:"
	name_label.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	button_container.add_child(name_label)

	_name_input = LineEdit.new()
	_name_input.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	_name_input.text_submitted.connect(_on_name_entered)
	button_container.add_child(_name_input)

	var play_button := _create_button("Play", button_container)
	var quit_button := _create_button("Quit", button_container)
	play_button.pressed.connect(_on_play_pressed)
	quit_button.pressed.connect(_on_quit_pressed)

func _create_button(text: String, parent: Node) -> Button:
	var button := Button.new()
	button.text = text
	button.custom_minimum_size = Vector2(200, 50)
	button.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	parent.add_child(button)
	return button

func _on_name_entered(text: String):
	print("User entered name: " + text)
	Global.player_name = text

func _on_play_pressed():
	_on_name_entered(_name_input.text)
	get_tree().change_scene_to_file("res://Scenes/Main.tscn")

func _on_quit_pressed():
	get_tree().quit()
