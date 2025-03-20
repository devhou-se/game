extends AnimatedSprite

var grid_size = 16
var is_moving = false
var target_position = Vector2.ZERO
var speed = 50
var max_stamina = 100
var stamina_regen = 20
var stamina = 0
var stamina_drain = 1
var sprint_speed = 100
var last_direction = "down"  # Track last direction for idle state
var particles
var footstep_player: AudioStreamPlayer2D
var sprite: AnimatedSprite
var wind_influence = Vector2.ZERO
var wind_resistance = 0.0

func _ready():
	position = position.snapped(Vector2.ONE * grid_size)
	target_position = position
	sprite = $AnimatedSprite
	sprite.play("idle")  # Default idle front
	
	# Setup sprint particles
	particles = CPUParticles2D.new()
	particles.emitting = false
	particles.amount = 8
	particles.lifetime = 0.4
	particles.explosiveness = 0.1
	particles.direction = Vector2(0, 1)
	particles.gravity = Vector2(0, 0)
	particles.initial_velocity = 20
	particles.scale_amount = 2
	add_child(particles)
	
	# Setup footstep sounds
	footstep_player = AudioStreamPlayer2D.new()
	footstep_player.volume_db = -10
	add_child(footstep_player)
	
	# Connect to wind controller
	var wind_controller = get_node("/root/Main/WindController")
	if wind_controller:
		wind_controller.connect("wind_changed", self, "_on_wind_changed")

func update_animation(direction: String, is_walking: bool):
	# Update particles position based on direction and wind
	var particle_offset = Vector2.ZERO
	match direction:
		"left":
			particle_offset = Vector2(16, 8)
			particles.direction = Vector2(1, 0) + wind_influence
		"right":
			particle_offset = Vector2(-16, 8)
			particles.direction = Vector2(-1, 0) + wind_influence
		"up":
			particle_offset = Vector2(0, 16)
			particles.direction = Vector2(0, 1) + wind_influence
		"down":
			particle_offset = Vector2(0, -16)
			particles.direction = Vector2(0, -1) + wind_influence
	
	particles.position = particle_offset
	
	var animation_prefix = "walk" if is_walking else "idle"
	
	match direction:
		"left":
			play(animation_prefix + "_side")
			flip_h = true
		"right":
			play(animation_prefix + "_side")
			flip_h = false
		"up":
			play(animation_prefix + "_back")
		"down":
			play(animation_prefix)  # Using default animations for front
	
	last_direction = direction

func play_footstep():
	if !footstep_player.playing:
		# Adjust footstep sound based on wind strength
		footstep_player.pitch_scale = rand_range(0.8, 1.2) * (1.0 - wind_resistance * 0.3)
		footstep_player.play()

func _process(delta):
	# Handle stamina and sprint
	if Input.is_action_pressed("ui_shift") and stamina > 0:
		speed = sprint_speed * (1.0 - wind_resistance * 0.5)  # Reduce sprint speed in strong winds
		stamina = max(0, stamina - stamina_drain * delta * (1.0 + wind_resistance))  # Drain stamina faster in wind
		particles.emitting = is_moving
	else:
		speed = speed * (1.0 - wind_resistance * 0.3)  # Reduce base speed less in wind
		stamina = min(max_stamina, stamina + stamina_regen * delta)
		particles.emitting = false
	
	if is_moving:
		var move_direction = (target_position - position).normalized()
		# Add wind influence to movement
		var wind_effect = wind_influence * wind_resistance
		var final_direction = (move_direction + wind_effect).normalized()
		var collision = move_and_collide(final_direction * speed * delta)
		
		if position.distance_to(target_position) < 1:
			position = target_position
			is_moving = false
			# When stopping, play idle animation for last direction
			update_animation(last_direction, false)
		else:
			# Continue normal movement
			if position.distance_to(target_position) < 1:
				position = target_position
				is_moving = false
				update_animation(last_direction, false)
		
		# Adjust footstep frequency based on wind resistance
		var step_interval = 400 if speed <= base_speed else 250
		step_interval *= (1.0 + wind_resistance * 0.5)  # Slower steps in strong wind
		
		if int(floor(OS.get_ticks_msec() / step_interval)) % 2 == 0:
			play_footstep()
	else:
		var direction = Vector2.ZERO
		var dir_string = last_direction
		
		if Input.is_action_pressed("ui_right"):
			direction.x += 1
			dir_string = "right"
		elif Input.is_action_pressed("ui_left"):
			direction.x -= 1
			dir_string = "left"
		elif Input.is_action_pressed("ui_up"):
			direction.y -= 1
			dir_string = "up"
		elif Input.is_action_pressed("ui_down"):
			direction.y += 1
			dir_string = "down"
			
		if direction != Vector2.ZERO:
			target_position = position + (direction * grid_size)
			is_moving = true
			update_animation(dir_string, true)

func _on_wind_changed(strength, direction):
	wind_influence = direction
	wind_resistance = strength
	
	# Update particle behavior based on wind
	particles.initial_velocity = 20 + (strength * 30)
	particles.lifetime = 0.4 + (strength * 0.3)
	particles.spread = 30.0 + (strength * 20.0)
