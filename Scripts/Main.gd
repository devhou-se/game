extends Node2D
# Main game scene controller. Ported from Main.cs.

func _ready():
	var controller = get_node("GameController")
	Global.controller = controller
