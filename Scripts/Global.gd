extends Node
# Autoload singleton: shared game state (ported from Global.cs).
# Accessed as Global.<member> from any script.

var player_name: String = "Flake"
var controller = null  # set by GameController._ready()

# Conversation cooldown to prevent rapid-fire NPC interactions.
var conversation_cooldown: float = 0.0

func _process(delta):
	if conversation_cooldown > 0:
		conversation_cooldown -= delta
