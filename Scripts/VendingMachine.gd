extends StaticBody2D
# Vending machine that dispenses speed-boost cans. Ported from VendingMachine.cs.

@export var drink_can_scene: PackedScene
@export var can_spawn_offset: float = 32.0
@export var max_cans: int = 3
@export var cooldown_time: float = 2.0

signal can_dispensed

var _current_cans: int = 0
var _cooldown_timer: float = 0.0
var _player_nearby: bool = false
var _animated_sprite: AnimatedSprite2D
var _interaction_area: Area2D
var _prompt_label: Label

func _ready():
	if has_node("AnimatedSprite2D"):
		_animated_sprite = get_node("AnimatedSprite2D")
	_create_interaction_area()
	_create_prompt_label()
	if drink_can_scene == null:
		drink_can_scene = load("res://Scenes/DrinkCan.tscn")

func _create_interaction_area():
	_interaction_area = Area2D.new()
	_interaction_area.name = "InteractionArea"
	var collision_shape := CollisionShape2D.new()
	var rect_shape := RectangleShape2D.new()
	rect_shape.size = Vector2(96, 96)  # was extents 48 (half-size) in Godot 3
	collision_shape.shape = rect_shape
	_interaction_area.add_child(collision_shape)
	add_child(_interaction_area)
	_interaction_area.body_entered.connect(_on_body_entered)
	_interaction_area.body_exited.connect(_on_body_exited)

func _create_prompt_label():
	_prompt_label = Label.new()
	_prompt_label.name = "PromptLabel"
	_prompt_label.text = "Press SPACE to buy drink"
	_prompt_label.add_theme_color_override("font_color", Color.WHITE)
	_prompt_label.add_theme_color_override("font_shadow_color", Color.BLACK)
	_prompt_label.add_theme_constant_override("shadow_offset_x", 1)
	_prompt_label.add_theme_constant_override("shadow_offset_y", 1)
	_prompt_label.position = Vector2(-60, -40)
	_prompt_label.visible = false
	add_child(_prompt_label)

func _process(delta):
	if _cooldown_timer > 0:
		_cooldown_timer -= delta
	if _player_nearby and _prompt_label != null:
		_prompt_label.visible = _cooldown_timer <= 0 and _current_cans < max_cans

func _on_body_entered(body):
	if body is Player:
		_player_nearby = true
		if _prompt_label != null:
			_prompt_label.visible = _cooldown_timer <= 0 and _current_cans < max_cans

func _on_body_exited(body):
	if body is Player:
		_player_nearby = false
		if _prompt_label != null:
			_prompt_label.visible = false

# Called by the player's interaction system.
func interact(_player):
	_dispense_can()

func _dispense_can():
	if _cooldown_timer > 0 or _current_cans >= max_cans or drink_can_scene == null:
		print("VendingMachine: Cannot dispense - on cooldown or max cans reached")
		return
	var can = drink_can_scene.instantiate()
	if can == null:
		push_error("VendingMachine: Failed to instance DrinkCan")
		return
	can.global_position = global_position + Vector2.DOWN * can_spawn_offset
	get_parent().add_child(can)
	_current_cans += 1
	_cooldown_timer = cooldown_time
	if _animated_sprite != null:
		_animated_sprite.play("dispense")
	can.tree_exited.connect(_on_can_collected)
	can_dispensed.emit()
	print("VendingMachine: Dispensed can! Total: %d/%d" % [_current_cans, max_cans])

func _on_can_collected():
	_current_cans = max(0, _current_cans - 1)
	print("VendingMachine: Can collected! Remaining: %d/%d" % [_current_cans, max_cans])
