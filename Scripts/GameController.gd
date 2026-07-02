class_name GameController extends Node
# Scene flow + day/night setup. Ported from GameController.cs.

enum TimeOfDay { MORNING, DAY, EVENING, NIGHT }

var _player: Character
var _current_player: Character
var _level: Node2D
var _level_parent: Node2D
var _day_night_controller
var _cool_down := 0.0
var _time_of_day: int = TimeOfDay.MORNING

func _ready():
	Global.controller = self
	_level_parent = get_node("../CurrentLevel")
	_player = load("res://Scenes/Player.tscn").instantiate()
	_initialize_day_night_system()
	goto("World")

func _process(delta):
	if _cool_down > 0.0:
		_cool_down -= delta

func goto(scene: String):
	if _cool_down > 0.0:
		return
	_cool_down = 0.2
	if _current_player != null:
		var parent = _current_player.get_parent()
		if parent:
			parent.remove_child(_current_player)
	if _level != null:
		_level.queue_free()
	var ls: PackedScene = load("res://Scenes/%s.tscn" % scene)
	_level = ls.instantiate()
	_level_parent.add_child(_level)
	var y_sort = _level.get_node("Characters")
	if _current_player == null:
		_current_player = _player
	y_sort.add_child(_player)
	_player.teleport(Vector2.ZERO)
	_apply_scene_scale(_level)
	_setup_scene_day_night(scene)

func _apply_scene_scale(level: Node) -> void:
	# Match gamev2's pixel scale: each grid cell renders at 64 screen px and the
	# character is one cell tall, whatever the scene's tile resolution (16 or 32).
	var tile_size := 16.0
	var tml := _find_tilemap_layer(level)
	if tml and tml.tile_set:
		tile_size = float(tml.tile_set.tile_size.x)
	var zoom := 64.0 / tile_size
	var char_scale := tile_size / 64.0
	var cam: Camera2D = _player.get_node_or_null("Camera2D")
	if cam:
		cam.zoom = Vector2(zoom, zoom)
	var chars := level.get_node_or_null("Characters")
	if chars:
		for c in chars.get_children():
			_scale_character(c, char_scale)

func _scale_character(c: Node, s: float) -> void:
	var spr = c.get_node_or_null("AnimatedSprite2D")
	if spr:
		spr.scale = Vector2(s, s)
		# Centre the sprite on its cell, matching gamev2's anchorY 0.5.
		spr.position.y = 0.0
	var tag = c.get_node_or_null("NameTag")
	if tag:
		# Tuck the badge just above the head (head top sits at -24*s).
		tag.position.y = -40.0 * s
		tag.scale = Vector2(s, s)

func _find_tilemap_layer(node: Node) -> TileMapLayer:
	if node is TileMapLayer:
		return node
	for ch in node.get_children():
		var r := _find_tilemap_layer(ch)
		if r:
			return r
	return null

func get_time() -> int:
	return _time_of_day

func set_time(t: int) -> void:
	_time_of_day = t

func _initialize_day_night_system():
	_day_night_controller = DayNightController.new()
	_day_night_controller.name = "DayNightController"
	get_parent().call_deferred("add_child", _day_night_controller)

func _setup_scene_day_night(scene_name: String):
	var outdoor_scenes := ["World", "Town", "tokyo_overworld"]
	var is_outdoor := false
	for s in outdoor_scenes:
		if scene_name.to_lower() == s.to_lower():
			is_outdoor = true
			break
	if is_outdoor and _day_night_controller != null:
		call_deferred("_setup_scene_lighting", _level)
		var environment_controller = EnvironmentController.new()
		environment_controller.name = "EnvironmentController"
		_level.call_deferred("add_child", environment_controller)
		call_deferred("_ensure_scene_canvas_modulate")

func _setup_scene_lighting(scene):
	if _day_night_controller != null and scene != null:
		_day_night_controller.setup_street_lights(scene)

func _ensure_scene_canvas_modulate():
	if _day_night_controller != null:
		_day_night_controller.ensure_canvas_modulate()

func get_day_night_controller():
	return _day_night_controller

func is_night_time() -> bool:
	return _day_night_controller.is_night_time() if _day_night_controller != null else false

func get_current_weather() -> String:
	return _day_night_controller.get_current_weather() if _day_night_controller != null else "Sunny"
