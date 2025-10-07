#!/usr/bin/env python3
"""
Extract a section of a tilemap and create a simplified v2 room configuration
"""

import json
import sys
from pathlib import Path
from collections import Counter


def extract_section(tilemap_json, center_x=None, center_y=None, width=30, height=20):
    """Extract a section of the tilemap centered at the given coordinates"""

    with open(tilemap_json, 'r') as f:
        data = json.load(f)

    map_width = data['width']
    map_height = data['height']

    # Default to center of map if not specified
    if center_x is None:
        center_x = map_width // 2
    if center_y is None:
        center_y = map_height // 2

    # Calculate extraction bounds
    start_x = max(0, center_x - width // 2)
    start_y = max(0, center_y - height // 2)
    end_x = min(map_width, start_x + width)
    end_y = min(map_height, start_y + height)

    # Adjust if we hit boundaries
    if end_x - start_x < width:
        start_x = max(0, end_x - width)
    if end_y - start_y < height:
        start_y = max(0, end_y - height)

    actual_width = end_x - start_x
    actual_height = end_y - start_y

    print(f"Extracting region: x={start_x} to {end_x}, y={start_y} to {end_y}")
    print(f"Actual size: {actual_width} x {actual_height}")

    # Extract tiles for each layer
    extracted_layers = {}
    all_tiles = []

    for layer_name, layer_data in data['layers'].items():
        layer_tiles = layer_data['data']
        extracted = []

        for y in range(start_y, end_y):
            row_start = y * map_width + start_x
            row_end = y * map_width + end_x
            row = layer_tiles[row_start:row_end]
            extracted.extend(row)
            all_tiles.extend([t for t in row if t != -1])

        extracted_layers[layer_name] = {
            'name': layer_name,
            'data': extracted,
            'width': actual_width,
            'height': actual_height
        }

    # Get tile usage stats
    tile_counts = Counter(all_tiles)
    print(f"\nTile usage in extracted region:")
    print(f"  Unique tiles: {len(tile_counts)}")
    print(f"  Most common tiles: {tile_counts.most_common(10)}")

    # Create new tilemap data
    result = {
        'width': actual_width,
        'height': actual_height,
        'tilewidth': data['tilewidth'],
        'tileheight': data['tileheight'],
        'layers': extracted_layers,
        'tilesetName': data['tilesetName'],
        'tilesetImage': data['tilesetImage'],
        'original_bounds': {
            'start_x': start_x,
            'start_y': start_y,
            'end_x': end_x,
            'end_y': end_y
        }
    }

    return result, tile_counts


def create_v2_room_config(tilemap_data, room_name, tile_mapping):
    """
    Create a v2-compatible room configuration from tilemap data
    Uses the floor layer as the base and creates a floor dict
    """

    floor_layer = tilemap_data['layers'].get('floor')
    collision_layer = tilemap_data['layers'].get('overworld-collidables')

    if not floor_layer:
        print("Warning: No floor layer found in tilemap")
        return None

    width = floor_layer['width']
    height = floor_layer['height']
    grid_size = tilemap_data['tilewidth']

    # Create floor tile mapping for v2
    floor_tiles = {}
    collision_objects = []

    for y in range(height):
        for x in range(width):
            idx = y * width + x
            tile_id = floor_layer['data'][idx]

            if tile_id != -1:
                # Map tile ID to sprite name
                sprite_name = tile_mapping.get(tile_id, f"tile_{tile_id}")
                floor_tiles[f"{x},{y}"] = sprite_name

    # Create collision objects from collision layer
    if collision_layer:
        for y in range(height):
            for x in range(width):
                idx = y * width + x
                tile_id = collision_layer['data'][idx]

                if tile_id != -1:
                    collision_objects.append({
                        "gridX": x,
                        "gridY": y
                    })

    room_config = {
        "name": room_name,
        "width": width,
        "height": height,
        "worldWidth": width * grid_size,
        "worldHeight": height * grid_size,
        "floor": floor_tiles,
        "objects": collision_objects,
        "npcs": [],
        "transporters": []
    }

    return room_config


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 extract_tilemap_section.py <tilemap.json> [output.json] [width] [height]")
        print("Example: python3 extract_tilemap_section.py tokyo_tilemap.json tokyo_section.json 30 20")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else "section.json"
    width = int(sys.argv[3]) if len(sys.argv) > 3 else 30
    height = int(sys.argv[4]) if len(sys.argv) > 4 else 20

    # Extract section
    section_data, tile_counts = extract_section(input_file, width=width, height=height)

    # Save extracted section
    with open(output_file, 'w') as f:
        json.dump(section_data, f, indent=2)

    print(f"\nSaved extracted section to: {output_file}")

    # Generate a basic tile mapping (tile ID -> sprite name)
    tile_mapping = {}
    for tile_id in tile_counts.keys():
        # For now, use placeholder names
        tile_mapping[tile_id] = f"tile_{tile_id}"

    # Create v2 room config
    room_name = Path(input_file).stem.replace('_tilemap', '')
    room_config = create_v2_room_config(section_data, room_name, tile_mapping)

    if room_config:
        room_config_file = output_file.replace('.json', '_room.json')
        with open(room_config_file, 'w') as f:
            json.dump(room_config, f, indent=2)

        print(f"Saved v2 room config to: {room_config_file}")
        print(f"  Floor tiles: {len(room_config['floor'])}")
        print(f"  Collision objects: {len(room_config['objects'])}")


if __name__ == "__main__":
    main()
