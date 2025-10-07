#!/usr/bin/env python3
"""
Convert our custom tilemap format to Tiled JSON format
"""

import json
import sys

def convert_to_tiled_format(input_file, output_file):
    """Convert custom format to Tiled JSON format"""

    with open(input_file, 'r') as f:
        data = json.load(f)

    width = data['width']
    height = data['height']
    tilewidth = data['tilewidth']
    tileheight = data['tileheight']

    # Convert layers from dict to array
    layers_array = []
    layer_names_priority = ['floor', 'overfloor', 'overworld-noncollidables', 'overworld-collidables', 'dimensions']

    # Get all layer names, prioritize certain ones
    all_layer_names = set(data['layers'].keys())
    sorted_layer_names = []

    # Add priority layers first
    for name in layer_names_priority:
        if name in all_layer_names:
            sorted_layer_names.append(name)
            all_layer_names.remove(name)

    # Add remaining layers
    sorted_layer_names.extend(sorted(all_layer_names))

    for layer_name in sorted_layer_names:
        layer_data = data['layers'][layer_name]

        # Determine if this is a collision layer
        visible = True
        if 'collidable' in layer_name or layer_name == 'overworld-collidables':
            visible = False

        # Convert tile IDs to gids (add 1 for firstgid, but keep -1 as-is for empty tiles)
        raw_data = layer_data.get('data', [])
        converted_data = []
        for tile_id in raw_data:
            if tile_id == -1 or tile_id == 0:
                converted_data.append(0)  # Empty tile
            else:
                converted_data.append(tile_id + 1)  # Add firstgid offset

        layer_obj = {
            "name": layer_name,
            "type": "tilelayer",
            "data": converted_data,
            "width": width,
            "height": height,
            "x": 0,
            "y": 0,
            "visible": visible,
            "opacity": 1
        }

        layers_array.append(layer_obj)

    # Create tileset reference
    tilesets = [
        {
            "name": "overworld_tiles",
            "firstgid": 1,
            "tilewidth": tilewidth,
            "tileheight": tileheight,
            "tilecount": 175,
            "columns": 16,
            "image": "overworld_tileset.png",
            "imagewidth": 1024,
            "imageheight": 704
        }
    ]

    # Create Tiled format output
    tiled_data = {
        "width": width,
        "height": height,
        "tilewidth": tilewidth,
        "tileheight": tileheight,
        "layers": layers_array,
        "tilesets": tilesets,
        "type": "map",
        "version": "1.0",
        "tiledversion": "1.0.0",
        "orientation": "orthogonal",
        "renderorder": "right-down",
        "infinite": False
    }

    # Write output
    with open(output_file, 'w') as f:
        json.dump(tiled_data, f, indent=2)

    print(f"Converted {input_file} to Tiled format: {output_file}")
    print(f"  Layers: {len(layers_array)}")
    print(f"  Size: {width}x{height}")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 convert_to_tiled_format.py <input.json> <output.json>")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]

    convert_to_tiled_format(input_file, output_file)
