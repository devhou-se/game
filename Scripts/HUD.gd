extends CanvasLayer
# Heads-up display: time + weather readout. Ported from HUD.cs.

var _name_input: LineEdit
var _stamina_bar: ProgressBar
var _energy_bar: ProgressBar
var _time_label: Label
var _weather_label: Label
var _player: Player

func _ready():
	var base := "MarginContainer/CenterContainer/HBoxContainer"
	if has_node(base + "/Stamina"):
		_stamina_bar = get_node(base + "/Stamina")
	if has_node(base + "/Energy"):
		_energy_bar = get_node(base + "/Energy")
	if has_node(base + "/InfoPanel/HBoxContainer2/TimeLabel"):
		_time_label = get_node(base + "/InfoPanel/HBoxContainer2/TimeLabel")
	if has_node(base + "/InfoPanel/HBoxContainer2/WeatherLabel"):
		_weather_label = get_node(base + "/InfoPanel/HBoxContainer2/WeatherLabel")
	if has_node(base + "/LineEdit"):
		_name_input = get_node(base + "/LineEdit")
		_name_input.text_submitted.connect(_on_name_entered)
	elif has_node("LineEdit"):
		_name_input = get_node("LineEdit")
		_name_input.text_submitted.connect(_on_name_entered)
	call_deferred("_find_player")

func _find_player():
	var players := get_tree().get_nodes_in_group("player")
	if players.size() > 0:
		_player = players[0] as Player
		if _player != null and _player.has_signal("stamina_changed"):
			_player.connect("stamina_changed", _on_stamina_changed)

func _process(_delta):
	var dnc: DayNightController = null
	if get_node_or_null("/root/Main") != null:
		var main := get_node("/root/Main")
		if main.get_parent() != null:
			dnc = main.get_parent().get_node_or_null("DayNightController")
	if dnc == null and Global.controller != null:
		dnc = Global.controller.get_day_night_controller()
	if dnc != null and _time_label != null:
		var hour := dnc.get_current_hour()
		var display_hour := int(floor(hour)) % 12
		if display_hour == 0:
			display_hour = 12
		var minute := int((hour - floor(hour)) * 60)
		var ampm := "PM" if hour >= 12 else "AM"
		_time_label.text = "%d:%02d %s" % [display_hour, minute, ampm]
		if _weather_label != null:
			_weather_label.text = dnc.get_current_weather() + " :)"

func _on_name_entered(text: String):
	print("User entered name: " + text)
	Global.player_name = text

func _on_stamina_changed(current: float, maximum: float):
	if _stamina_bar != null:
		_stamina_bar.max_value = maximum
		_stamina_bar.value = current
