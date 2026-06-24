class_name DayNightController extends Node
# Day/night CanvasModulate tint, weather, and street lights. Ported from DayNightController.cs.

@export var day_duration: float = 86400.0
@export var day_color: Color = Color(1.0, 1.0, 1.0, 1.0)
@export var night_color: Color = Color(0.15, 0.15, 0.3, 1.0)
@export var dawn_dusk_color: Color = Color(1.0, 0.6, 0.4, 1.0)
@export var use_tokyo_real_time: bool = true

signal time_changed(time_of_day, current_hour)
signal weather_changed(weather)

var _time: float = 0.0
var _current_hour: float = 0.0
var _weather_effects := ["Sunny", "Cloudy", "Rainy"]
var _current_weather := "Sunny"
var _weather_transition_time: float = 0.0
var _weather_duration: float = 3600.0

var _canvas_modulate: CanvasModulate
var _game_controller: GameController

var _lights_parent: Node2D
var _lights_enabled := false

var _rain_particles: CPUParticles2D
var _cloud_particles: CPUParticles2D
var _last_debug_time: float = 0.0

func _ready():
	_game_controller = get_node_or_null("/root/Main/GameController")
	_canvas_modulate = CanvasModulate.new()
	_canvas_modulate.name = "DayNightCanvasModulate"
	get_tree().root.call_deferred("add_child", _canvas_modulate)

	if use_tokyo_real_time:
		_initialize_tokyo_time()
	else:
		_time = (8.0 / 24.0) * day_duration

	_change_weather()

	_lights_parent = Node2D.new()
	_lights_parent.name = "DayNightLights"
	call_deferred("_add_lights_parent")
	call_deferred("_setup_weather_particles")

func _process(delta):
	if use_tokyo_real_time:
		_update_tokyo_time()
	else:
		_time += delta
		if _time >= day_duration:
			_time = 0.0
	_current_hour = (_time / day_duration) * 24.0
	_update_lighting()
	_update_weather(delta)
	_update_game_controller_time()

func _initialize_tokyo_time():
	var t := _get_tokyo_time()
	var hour: float = t.hour + (t.minute / 60.0)
	_time = (hour / 24.0) * day_duration

func _update_tokyo_time():
	var t := _get_tokyo_time()
	var hour: float = t.hour + (t.minute / 60.0) + (t.second / 3600.0)
	_time = (hour / 24.0) * day_duration

func _get_tokyo_time() -> Dictionary:
	# Tokyo is UTC+9.
	var unix := Time.get_unix_time_from_system() + 9 * 3600
	return Time.get_datetime_dict_from_unix_time(int(unix))

func _update_lighting():
	var color := day_color
	var debug_interval := 60.0 if use_tokyo_real_time else 2.0
	if _time - _last_debug_time >= debug_interval:
		_last_debug_time = _time
		print("DayNight: Hour=%.1f, Weather=%s, Night=%s" % [_current_hour, _current_weather, _lights_enabled])

	if _current_hour >= 21.0 or _current_hour < 5.0:
		color = night_color
		_set_lights_enabled(true)
	elif _current_hour >= 5.0 and _current_hour < 7.0:
		var t := (_current_hour - 5.0) / 2.0
		color = night_color.lerp(dawn_dusk_color, t * 0.7)
		if t > 0.7:
			var t2 := (t - 0.7) / 0.3
			color = dawn_dusk_color.lerp(day_color, t2)
		_set_lights_enabled(t < 0.5)
	elif _current_hour >= 7.0 and _current_hour < 17.0:
		color = day_color
		_set_lights_enabled(false)
	elif _current_hour >= 17.0 and _current_hour < 21.0:
		var t := (_current_hour - 17.0) / 4.0
		if t < 0.5:
			color = day_color.lerp(dawn_dusk_color, t / 0.5)
		else:
			color = dawn_dusk_color.lerp(night_color, (t - 0.5) / 0.5)
		_set_lights_enabled(t > 0.7)

	color = _apply_weather_effects(color)
	if _canvas_modulate != null and is_instance_valid(_canvas_modulate):
		_canvas_modulate.color = color
	else:
		ensure_canvas_modulate()
		if _canvas_modulate != null:
			_canvas_modulate.color = color

func _apply_weather_effects(base_color: Color) -> Color:
	match _current_weather:
		"Cloudy":
			base_color.r *= 0.85
			base_color.g *= 0.85
			base_color.b *= 0.9
		"Rainy":
			base_color.r *= 0.7
			base_color.g *= 0.7
			base_color.b *= 0.8
	return base_color

func _update_weather(delta):
	_weather_transition_time += delta
	if _weather_transition_time >= _weather_duration:
		_change_weather()
		_weather_transition_time = 0.0

func _change_weather():
	var new_weather := _current_weather
	while new_weather == _current_weather:
		new_weather = _weather_effects[randi() % _weather_effects.size()]
	_current_weather = new_weather
	_update_weather_particles()
	weather_changed.emit(_current_weather)

func _setup_weather_particles():
	var rect := get_viewport().get_visible_rect()

	_rain_particles = CPUParticles2D.new()
	_rain_particles.name = "RainParticles"
	_rain_particles.amount = 200
	_rain_particles.lifetime = 2.0
	_rain_particles.preprocess = 0.5
	_rain_particles.speed_scale = 2.0
	_rain_particles.emitting = false
	_rain_particles.direction = Vector2(0.1, 1)
	_rain_particles.spread = 5.0
	_rain_particles.initial_velocity_min = 270.0
	_rain_particles.initial_velocity_max = 300.0
	_rain_particles.linear_accel_min = 50.0
	_rain_particles.linear_accel_max = 50.0
	_rain_particles.scale_amount_min = 1.5
	_rain_particles.scale_amount_max = 2.0
	_rain_particles.color = Color(0.6, 0.7, 0.9, 0.6)
	_rain_particles.emission_shape = CPUParticles2D.EMISSION_SHAPE_RECTANGLE
	_rain_particles.emission_rect_extents = Vector2(rect.size.x / 2, 10)
	_rain_particles.position = Vector2(rect.size.x / 2, -10)
	_rain_particles.z_index = 100
	get_parent().call_deferred("add_child", _rain_particles)

	_cloud_particles = CPUParticles2D.new()
	_cloud_particles.name = "CloudParticles"
	_cloud_particles.amount = 30
	_cloud_particles.lifetime = 20.0
	_cloud_particles.preprocess = 10.0
	_cloud_particles.speed_scale = 0.3
	_cloud_particles.emitting = false
	_cloud_particles.direction = Vector2(1, 0)
	_cloud_particles.spread = 20.0
	_cloud_particles.initial_velocity_min = 10.0
	_cloud_particles.initial_velocity_max = 20.0
	_cloud_particles.scale_amount_min = 35.0
	_cloud_particles.scale_amount_max = 50.0
	_cloud_particles.color = Color(0.8, 0.8, 0.8, 0.2)
	_cloud_particles.emission_shape = CPUParticles2D.EMISSION_SHAPE_RECTANGLE
	_cloud_particles.emission_rect_extents = Vector2(rect.size.x, 100)
	_cloud_particles.position = Vector2(rect.size.x / 2, 100)
	_cloud_particles.z_index = 90
	get_parent().call_deferred("add_child", _cloud_particles)

func _update_weather_particles():
	if _rain_particles != null:
		_rain_particles.emitting = _current_weather == "Rainy"
	if _cloud_particles != null:
		_cloud_particles.emitting = _current_weather == "Cloudy"

func _update_game_controller_time():
	if _game_controller == null:
		return
	var time_of_day: int
	if _current_hour >= 21.0 or _current_hour < 5.0:
		time_of_day = GameController.TimeOfDay.NIGHT
	elif _current_hour >= 5.0 and _current_hour < 7.0:
		time_of_day = GameController.TimeOfDay.MORNING
	elif _current_hour >= 7.0 and _current_hour < 17.0:
		time_of_day = GameController.TimeOfDay.DAY
	else:
		time_of_day = GameController.TimeOfDay.EVENING
	_game_controller.set_time(time_of_day)
	time_changed.emit(time_of_day, _current_hour)

func _set_lights_enabled(enabled: bool):
	if _lights_enabled == enabled:
		return
	_lights_enabled = enabled
	if _lights_parent == null:
		return
	var weather_intensity := 1.0
	if _current_weather == "Rainy":
		weather_intensity = 1.3
	elif _current_weather == "Cloudy":
		weather_intensity = 1.1
	for child in _lights_parent.get_children():
		if child is Sprite2D:
			child.visible = enabled
			if enabled:
				child.modulate = Color(weather_intensity, weather_intensity, weather_intensity, 0.5)
		elif child is Light2D:
			child.enabled = enabled
			if enabled:
				child.energy = weather_intensity

func get_current_hour() -> float:
	return _current_hour

func get_time_of_day() -> int:
	return _game_controller.get_time() if _game_controller != null else GameController.TimeOfDay.DAY

func get_current_weather() -> String:
	return _current_weather

func is_night_time() -> bool:
	return _lights_enabled

func _add_lights_parent():
	if get_parent() != null:
		get_parent().add_child(_lights_parent)

func ensure_canvas_modulate():
	if not is_inside_tree():
		push_error("DayNightController: Not in tree yet, cannot ensure CanvasModulate")
		return
	var tree := get_tree()
	if tree == null or tree.root == null:
		push_error("DayNightController: Tree or Root is null")
		return
	for child in tree.root.get_children():
		if child is CanvasModulate and child != _canvas_modulate:
			child.queue_free()
	if _canvas_modulate == null or not is_instance_valid(_canvas_modulate):
		_canvas_modulate = CanvasModulate.new()
		_canvas_modulate.name = "DayNightCanvasModulate"
		tree.root.add_child(_canvas_modulate)
		print("Recreated CanvasModulate")

func add_light(pos: Vector2, energy: float = 1.0, color = null):
	if _lights_parent == null:
		push_error("DayNightController: lights_parent is null, cannot add light")
		return
	var light_sprite := Sprite2D.new()
	light_sprite.position = pos
	var image := Image.create(64, 64, false, Image.FORMAT_RGBA8)
	var center := Vector2(32, 32)
	var base_color: Color = color if color != null else Color(1.0, 0.9, 0.7, 1.0)
	for x in range(64):
		for y in range(64):
			var dist := center.distance_to(Vector2(x, y))
			var alpha: float = clampf(1.0 - (dist / 32.0), 0.0, 1.0)
			alpha = alpha * alpha
			var pixel_color := base_color
			pixel_color.a = alpha * energy
			image.set_pixel(x, y, pixel_color)
	var texture := ImageTexture.create_from_image(image)
	light_sprite.texture = texture
	light_sprite.scale = Vector2(3, 3)
	light_sprite.modulate = Color(1, 1, 1, 0.5)
	light_sprite.visible = _lights_enabled
	light_sprite.z_index = 10
	_lights_parent.add_child(light_sprite)

func setup_street_lights(_scene: Node2D):
	for x in range(-600, 601, 200):
		for y in range(-600, 601, 200):
			var pos := Vector2(x, y)
			var energy := 0.7 + randf() * 0.3
			var color := Color(1.0, 0.9 + randf() * 0.1, 0.6 + randf() * 0.2, 1.0)
			add_light(pos, energy, color)
	add_light(Vector2(0, -100), 1.2, Color(1.0, 0.95, 0.8))
	add_light(Vector2(-150, 50), 1.0, Color(1.0, 0.9, 0.7))
	add_light(Vector2(150, 50), 1.0, Color(1.0, 0.9, 0.7))
	print("Added %d street lights to the scene" % _lights_parent.get_child_count())
