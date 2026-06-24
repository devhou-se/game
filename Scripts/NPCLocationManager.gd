class_name NPCLocationManager
# Named NPC spawn locations. Ported from NPCLocationManager.cs (the C# singleton
# was detached from the tree so placement silently no-op'd; this version operates
# on the passed-in level node so it works).

const LOCATION_MAPPINGS := {
	"World": {
		"vending machine": Vector2(-200, -150),
		"center": Vector2(0, 0),
		"north entrance": Vector2(0, -100),
		"south entrance": Vector2(0, 100),
		"east plaza": Vector2(100, 0),
		"west plaza": Vector2(-100, 0),
		"top left corner": Vector2(-200, -150),
		"top right corner": Vector2(200, -150),
		"bottom left corner": Vector2(-200, 150),
		"bottom right corner": Vector2(200, 150),
	},
	"Tokyo": {
		"7-11": Vector2(200, 50),
		"station": Vector2(-150, -80),
		"ramen shop": Vector2(80, -40),
	},
}

static func get_location(world: String, area: String):
	if LOCATION_MAPPINGS.has(world) and LOCATION_MAPPINGS[world].has(area):
		return LOCATION_MAPPINGS[world][area]
	push_error("Location not found: %s - %s" % [world, area])
	return null

static func place_npc(scene_root: Node, npc_name: String, world: String, area: String):
	var coords = get_location(world, area)
	if coords == null:
		return
	place_npc_at_coords(scene_root, npc_name, coords)

static func place_npc_at_coords(scene_root: Node, npc_name: String, coords: Vector2):
	if scene_root == null:
		push_error("No current scene found")
		return
	var characters = scene_root.get_node_or_null("Characters")
	if characters == null:
		characters = scene_root.get_node_or_null("YSort/Characters")
	if characters == null:
		push_error("Characters node not found in current scene")
		return
	for child in characters.get_children():
		if child is NPC and child.npc_name == npc_name:
			child.position = coords
			return
	var npc_scene: PackedScene = load("res://Scenes/NPC.tscn")
	var new_npc = npc_scene.instantiate()
	new_npc.name = npc_name
	new_npc.npc_name = npc_name
	new_npc.position = coords
	characters.add_child(new_npc)
