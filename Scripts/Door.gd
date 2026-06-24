extends Area2D
# Scene-transition door. Ported from Door.cs.

@export var destination: String

func _ready():
	body_entered.connect(_on_body_entered)

func _on_body_entered(body):
	if body is Player:
		# Defer: this fires during a physics flush, and goto() frees/adds nodes
		# (changing physics state), which errors if done mid-flush.
		Global.controller.call_deferred("goto", destination)
