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
	call_deferred("_place_bailey_at_vending_machine")

func _place_bailey_at_vending_machine():
	NPCLocationManager.place_npc(_level, "Bailey", "World", "vending machine")

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
	_setup_scene_day_night(scene)

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
