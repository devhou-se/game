#!/usr/bin/env python3
"""
Update gamev2 config.json with the parsed Tokyo room data.
"""

import json
import os
import sys

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    game_dir = os.path.dirname(script_dir)

    # Paths
    config_path = os.path.join(game_dir, "gamev2", "config.json")
    parsed_tokyo_path = os.path.join(script_dir, "tokyo_parsed.json")

    # Load existing config
    with open(config_path, 'r') as f:
        config = json.load(f)

    # Load parsed Tokyo room
    with open(parsed_tokyo_path, 'r') as f:
        new_tokyo = json.load(f)

    print("Updating gamev2 config with new Tokyo room data...")
    print("-" * 60)

    # Store existing NPCs, objects, and transporters from Tokyo room
    existing_tokyo = config["rooms"].get("Tokyo", {})
    new_tokyo["npcs"] = existing_tokyo.get("npcs", [])
    new_tokyo["objects"] = existing_tokyo.get("objects", [])
    new_tokyo["transporters"] = existing_tokyo.get("transporters", [])

    # Calculate new world dimensions based on the tilemap
    # Find max coordinates in the floor
    max_x = 0
    max_y = 0
    for coord in new_tokyo["floor"].keys():
        x, y = map(int, coord.split(','))
        max_x = max(max_x, x)
        max_y = max(max_y, y)

    # World dimensions (add 1 because coordinates are 0-indexed)
    world_width_cells = max_x + 1
    world_height_cells = max_y + 1

    grid_size = config["game"]["gridSize"]
    world_width_pixels = world_width_cells * grid_size
    world_height_pixels = world_height_cells * grid_size

    print(f"Tokyo tilemap size: {world_width_cells}x{world_height_cells} cells")
    print(f"World dimensions: {world_width_pixels}x{world_height_pixels} pixels")
    print(f"Tile count: {len(new_tokyo['floor'])}")

    # Update the config
    config["rooms"]["Tokyo"] = new_tokyo
    config["game"]["worldWidth"] = world_width_pixels
    config["game"]["worldHeight"] = world_height_pixels

    # Write updated config
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)

    print(f"\n✓ Updated config.json")
    print(f"  - Replaced Tokyo room floor tiles")
    print(f"  - Preserved {len(new_tokyo['npcs'])} NPCs")
    print(f"  - Preserved {len(new_tokyo['objects'])} objects")
    print(f"  - Updated world size to {world_width_pixels}x{world_height_pixels}")

    print("-" * 60)
    print("Configuration update complete!")

    return 0

if __name__ == "__main__":
    sys.exit(main())
