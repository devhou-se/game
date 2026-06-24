extends Character
# Player input → buffered grid movement. Ported from Player.cs.

func _physics_process(delta):
	var input_vector := _get_input_vector()
	if input_vector != Vector2.ZERO:
		set_input_vector(input_vector)
	super._physics_process(delta)

func _get_input_vector() -> Vector2:
	var v := Vector2.ZERO
	if Input.is_action_pressed("ui_left"):
		v.x -= 1
	if Input.is_action_pressed("ui_right"):
		v.x += 1
	if Input.is_action_pressed("ui_up"):
		v.y -= 1
	if Input.is_action_pressed("ui_down"):
		v.y += 1
	set_shift_multiplier(4.0 if Input.is_action_pressed("ui_shift") else 1.0)
	# Cancel diagonals (matches Player.cs).
	if v.length() > 1:
		return Vector2.ZERO
	return v
