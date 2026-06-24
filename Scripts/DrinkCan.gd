extends Area2D
# Collectible speed-boost can with weather/time glow. Ported from DrinkCan.cs.

@export var speed_boost_multiplier: float = 2.0
@export var speed_boost_duration: float = 5.0

var _sprite: Sprite2D
var _light: Node2D
var _current_weather := "Sunny"
var _current_time_of_day: int = GameController.TimeOfDay.DAY

func _ready():
	body_entered.connect(_on_body_entered)
	_sprite = get_node("Sprite")
	if has_node("Light2D"):
		_light = get_node("Light2D")
		if _light is PointLight2D:
			_light.texture = _create_radial_gradient_texture(128)
		_light.visible = false
	call_deferred("_connect_to_weather_system")

func _connect_to_weather_system():
	var dnc = get_node_or_null("/root/Main/DayNightController")
	if dnc == null:
		dnc = get_tree().root.get_node_or_null("Main/DayNightController")
	if dnc != null:
		dnc.weather_changed.connect(_on_weather_changed)
		dnc.time_changed.connect(_on_time_changed)
		_current_weather = dnc.get_current_weather()
		_current_time_of_day = dnc.get_time_of_day()
		_update_light()

func _on_weather_changed(weather: String):
	_current_weather = weather
	_update_light()

func _on_time_changed(time_of_day, _current_hour):
	_current_time_of_day = time_of_day
	_update_light()

func _update_light():
	if _light == null:
		return
	var should_glow := (_current_weather == "Cloudy" or _current_weather == "Rainy"
		or _current_time_of_day == GameController.TimeOfDay.EVENING
		or _current_time_of_day == GameController.TimeOfDay.NIGHT)
	_light.visible = should_glow
	if _sprite != null:
		if should_glow:
			_sprite.modulate = Color(1.3, 1.3, 1.3, 1.0)
		else:
			_sprite.modulate = Color(1.0, 1.0, 1.0, 1.0)

func _on_body_entered(body):
	if body is Character:
		body.apply_speed_boost(speed_boost_multiplier, speed_boost_duration)
		_flash_and_jiggle()

func _flash_and_jiggle():
	var flash := create_tween()
	flash.tween_property(_sprite, "modulate:a", 0.0, 0.1)
	flash.tween_property(_sprite, "modulate:a", 1.0, 0.1)
	var jiggle := create_tween()
	jiggle.tween_property(_sprite, "scale", Vector2(1.2, 0.8), 0.1)
	jiggle.tween_property(_sprite, "scale", Vector2(0.8, 1.2), 0.1)
	jiggle.tween_property(_sprite, "scale", Vector2(1, 1), 0.1)

func _create_radial_gradient_texture(size: int) -> ImageTexture:
	var image := Image.create(size, size, false, Image.FORMAT_RGBA8)
	var center := size / 2.0
	var max_radius := center
	for y in range(size):
		for x in range(size):
			var dx := x - center
			var dy := y - center
			var distance := sqrt(dx * dx + dy * dy)
			var normalized: float = clampf(distance / max_radius, 0, 1)
			var alpha := 1.0 - normalized
			image.set_pixel(x, y, Color(1, 1, 1, alpha))
	return ImageTexture.create_from_image(image)
