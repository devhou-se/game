extends CanvasLayer
# Speed-boost progress bar. Ported from SpeedBoostUI.cs.

var _progress_bar: ProgressBar
var _duration_label: Label
var _player: Character
var _current_duration: float = 0.0

func _ready():
	_progress_bar = get_node("ProgressBar")
	_duration_label = get_node("ProgressBar/Label")
	_progress_bar.visible = false

func _process(_delta):
	if _progress_bar.visible:
		_duration_label.text = "Zone Energy remaining: %.1fs" % _current_duration

func set_player(player_node: Character):
	_player = player_node

func show_boost_timer(duration: float):
	_current_duration = duration
	_progress_bar.max_value = duration
	_progress_bar.value = duration
	_progress_bar.visible = true
	_duration_label.text = "Zone Energy remaining: %.1fs" % duration

func update_boost_timer(time_left: float):
	_current_duration = time_left
	_progress_bar.value = time_left
	if time_left <= 0:
		_progress_bar.visible = false
