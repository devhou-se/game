class_name Character extends CharacterBody2D
# Grid-based movement using a buffered input + ShapeCast lookahead.
# Ported from Character.cs.

const GRID_SIZE := 16.0
const SPEED := 48.0
const BUFFER_TIME_MAX := 0.05
# Walk/idle cycles play at the SpriteFrames' own fps (10, matching gamev2).
# Kept constant on purpose: movement boost/shift speeds the character up,
# but never the animation playback.

var _speed_multiplier := 1.0
var _speed_duration_remaining := 0.0
var _shift_multiplier := 1.0

var _target_position: Vector2
var _buffered_vector := Vector2.ZERO
var _buffer_time_remaining := 0.0

var _shape_cast: ShapeCast2D
var _animated_sprite: AnimatedSprite2D
var _collider: CollisionShape2D

var _current_animation := "idle"
var _current_direction := ""
var _current_flip := false
var _animation_vector := Vector2.ZERO

const DIRECTION_ANIMATIONS := {
	Vector2.LEFT: "_side",
	Vector2.RIGHT: "_side",
	Vector2.UP: "_back",
	Vector2.DOWN: "",
}
const DIRECTION_FLIP := {
	Vector2.LEFT: true,
	Vector2.RIGHT: false,
	Vector2.UP: false,
	Vector2.DOWN: false,
}

func _ready():
	_shape_cast = get_node("ShapeCast2D")
	_animated_sprite = get_node("AnimatedSprite2D")
	_collider = get_node("CollisionShape2D")
	_animated_sprite.speed_scale = 1.0
	_target_position = position

func teleport(pos: Vector2) -> void:
	position = pos
	_target_position = pos

func apply_speed_boost(multiplier: float, duration: float) -> void:
	_speed_multiplier = multiplier
	_speed_duration_remaining = duration

func set_shift_multiplier(value: float) -> void:
	_shift_multiplier = value

# Buffer an input direction (replaces C# InputVector setter).
func set_input_vector(value: Vector2) -> void:
	_buffered_vector = value
	_buffer_time_remaining = BUFFER_TIME_MAX

func _process(delta):
	_process_speed_boost(delta)

func _process_speed_boost(delta):
	if _speed_duration_remaining <= 0:
		_speed_multiplier = 1.0
		return
	_speed_duration_remaining -= delta

func _physics_process(delta):
	_process_buffer()
	_process_move(delta)
	_update_animation()
	_process_input(delta)
	var anim_name := _current_animation + _current_direction
	if _animated_sprite.animation != anim_name or not _animated_sprite.is_playing():
		_animated_sprite.play(anim_name)
	_animated_sprite.flip_h = _current_flip

func _process_move(delta: float):
	var path := _target_position - position
	var step: float = delta * SPEED * _speed_multiplier * _shift_multiplier
	var distance := path.length()
	if path == Vector2.ZERO or step > distance:
		position = _target_position
		_collider.position = Vector2.ZERO
		return
	var direction := path.normalized()
	position += direction * step
	_collider.position -= direction * step

func _update_animation():
	if _animation_vector == Vector2.ZERO:
		return
	_current_direction = DIRECTION_ANIMATIONS[_animation_vector]
	_current_animation = "idle" if position == _target_position else "walk"
	_current_flip = DIRECTION_FLIP[_animation_vector]

func _process_buffer():
	if position != _target_position:
		return
	if _buffered_vector == Vector2.ZERO:
		return
	_animation_vector = _buffered_vector
	var target_vector := _buffered_vector * GRID_SIZE
	var new_target := position + target_vector
	_shape_cast.target_position = target_vector
	_shape_cast.force_shapecast_update()
	if _shape_cast.is_colliding():
		var c = _shape_cast.get_collider(0)
		if c and c.has_method("bump"):
			c.bump(self)
		_buffered_vector = Vector2.ZERO
		return
	_target_position = new_target
	_collider.position += target_vector
	_buffered_vector = Vector2.ZERO

func _process_input(delta):
	if _buffer_time_remaining <= 0:
		_buffered_vector = Vector2.ZERO
	else:
		_buffer_time_remaining -= delta
