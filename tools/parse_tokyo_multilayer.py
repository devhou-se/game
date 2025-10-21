#!/usr/bin/env python3
"""
Parse tokyo_outside.tscn with multi-layer support.
Generates a config.json-ready Tokyo room with proper layer structure.
"""

import sys
import os
import json

# Import from parse_godot_scene
sys.path.insert(0, os.path.dirname(__file__))
from parse_godot_scene import parse_tscn_file, convert_to_gamev2_format

# Layer configuration with z-ordering and collision
LAYER_CONFIG = {
    "dimensions": {"skip": True},  # Skip dimensions layer (not visual)
    "zone-allocation": {"skip": True},  # Skip zone allocation (not visual)
    "floor": {
        "z": 0,
        "collision": False,
        "name": "Floor"
    },
    "overfloor": {
        "z": 1,
        "collision": False,
        "name": "Over Floor"
    },
    "overworld-collidables": {
        "z": 5,
        "collision": True,
        "name": "Collidables"
    },
    "julia-tmp": {
        "z": 3,
        "collision": False,
        "name": "Decorations"
    },
    "overworld-noncollidables": {
        "z": 4,
        "collision": False,
        "name": "Non-Collidables"
    },
    "other-tmp": {
        "z": 6,
        "collision": False,
        "name": "Other"
    }
}

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    game_dir = os.path.dirname(script_dir)

    tscn_path = os.path.join(game_dir, "Scenes", "tokyo", "tokyo_outside.tscn")
    output_path = os.path.join(script_dir, "tokyo_multilayer.json")

    if not os.path.exists(tscn_path):
        print(f"Error: Scene file not found at {tscn_path}")
        return 1

    print(f"Parsing Tokyo scene with multi-layer support...")
    print(f"Source: {tscn_path}")
    print("-" * 60)

    # Parse all layers
    layers_dict = parse_tscn_file(tscn_path, multi_layer=True)

    print(f"\nFound {len(layers_dict)} TileMap layers")
    print("\nProcessing layers:")

    # Convert each layer
    gamev2_layers = []
    for layer_name, tiles in layers_dict.items():
        layer_cfg = LAYER_CONFIG.get(layer_name, {"skip": False, "z": 99, "collision": False, "name": layer_name})

        if layer_cfg.get("skip"):
            print(f"  Skipping {layer_name} (non-visual)")
            continue

        print(f"  Processing {layer_name} -> z={layer_cfg['z']}, collision={layer_cfg['collision']}")

        # Convert tiles for this layer
        floor_data = convert_to_gamev2_format(
            tiles,
            max_width=40,
            max_height=30,
            crop_start_x=9,
            crop_start_y=9
        )

        if floor_data:
            gamev2_layers.append({
                "name": layer_cfg["name"],
                "z": layer_cfg["z"],
                "collision": layer_cfg["collision"],
                "tiles": floor_data
            })
            print(f"    → {len(floor_data)} tiles")
        else:
            print(f"    → No tiles in cropped region")

    # Sort layers by z-index
    gamev2_layers.sort(key=lambda l: l["z"])

    # Create room configuration
    room_config = {
        "name": "Tokyo",
        "layers": gamev2_layers,
        "boundary": [],
        "npcs": [],
        "objects": [],
        "transporters": []
    }

    # Save output
    with open(output_path, 'w') as f:
        json.dump(room_config, f, indent=2)

    print(f"\n✓ Generated {len(gamev2_layers)} layers for gamev2")
    print(f"✓ Saved to {output_path}")
    print("\nLayer summary:")
    for layer in gamev2_layers:
        print(f"  z={layer['z']}: {layer['name']} ({len(layer['tiles'])} tiles, collision={layer['collision']})")

    print("-" * 60)
    print("Multi-layer parsing complete!")
    print("\nNext steps:")
    print("1. Update config.json to use the new layer structure")
    print("2. Modify GameScene.js to render layers")
    print("3. Implement per-layer collision detection")

    return 0

if __name__ == "__main__":
    sys.exit(main())
