class_name EnvironmentController extends Node2D
# Ambient particle effects reacting to day/night, weather, wind. Ported from
# EnvironmentController.cs. Particle child nodes are optional; logic is null-guarded.

var _fireflies: CPUParticles2D
var _butterflies: CPUParticles2D
var _water_reflections: CPUParticles2D
var _leaf_particles: CPUParticles2D
var _time: float = 0.0
var _wind_influence := Vector2.ZERO
var _day_night_controller: DayNightController

func _ready():
	_fireflies = get_node_or_null("Fireflies")
	_butterflies = get_node_or_null("Butterflies")
	_water_reflections = get_node_or_null("WaterReflections")
	_leaf_particles = get_node_or_null("LeafParticles")
	var main = get_node_or_null("/root/Main")
	if main != null and main.get_parent() != null:
		_day_night_controller = main.get_parent().get_node_or_null("DayNightController")
	var wind_controller = get_node_or_null("/root/Main/WindController")
	if wind_controller != null and wind_controller.has_signal("wind_changed"):
		wind_controller.connect("wind_changed", _on_wind_changed)
	if _day_night_controller != null:
		_day_night_controller.time_changed.connect(_on_time_changed)
		_day_night_controller.weather_changed.connect(_on_weather_changed)
	_setup_initial_states()

func _process(delta):
	_time += delta
	_update_particle_effects()

func _setup_initial_states():
	if _fireflies != null: _fireflies.emitting = false
	if _butterflies != null: _butterflies.emitting = true
	if _water_reflections != null: _water_reflections.emitting = true
	if _leaf_particles != null: _leaf_particles.emitting = false

func _update_particle_effects():
	if _day_night_controller == null:
		return
	var is_night: bool = _day_night_controller.is_night_time()
	var weather: String = _day_night_controller.get_current_weather()
	if _fireflies != null:
		_fireflies.emitting = is_night and (weather == "Sunny" or weather == "Cloudy")
		if _fireflies.emitting:
			var pulse := (sin(_time * 2) + 1) * 0.5
			_fireflies.scale_amount_min = 2 + pulse
			_fireflies.scale_amount_max = 2 + pulse
			var color: Color = _fireflies.color
			color.a = 0.7 + pulse * 0.3
			_fireflies.color = color
			_fireflies.direction = _wind_influence
	if _butterflies != null:
		_butterflies.emitting = not is_night and (weather == "Sunny" or weather == "Cloudy")
		if _butterflies.emitting:
			_butterflies.direction = _wind_influence
			var v := 30 + _wind_influence.length() * 20
			_butterflies.initial_velocity_min = v
			_butterflies.initial_velocity_max = v
	if _leaf_particles != null:
		_leaf_particles.emitting = weather == "Rainy" or _wind_influence.length() > 0.3
		if _leaf_particles.emitting:
			_leaf_particles.direction = _wind_influence
			var v := 40 + _wind_influence.length() * 50
			_leaf_particles.initial_velocity_min = v
			_leaf_particles.initial_velocity_max = v
	if _water_reflections != null:
		_water_reflections.amount = 50 if weather == "Sunny" else 30
		var v := 5 + _wind_influence.length() * 10
		_water_reflections.initial_velocity_min = v
		_water_reflections.initial_velocity_max = v
		_water_reflections.direction = _wind_influence

func _on_wind_changed(strength, direction):
	_wind_influence = direction * strength

func _on_time_changed(_time_of_day, _current_hour):
	pass

func _on_weather_changed(weather):
	print("Weather changed to: %s" % weather)
