#!/usr/bin/env python3
"""
Parse Godot .tscn files and convert them to gamev2 JSON format.
"""

import re
import json
import os
import sys

# Tile ID to sprite name mapping
# All 140 tiles used in tokyo_outside.tscn
TILE_MAP = {
    0: "tile_0", 1: "tile_1", 2: "tile_2", 3: "tile_3", 4: "tile_4",
    5: "tile_5", 6: "tile_6", 7: "tile_7", 8: "tile_8", 9: "tile_9",
    10: "tile_10", 11: "tile_11", 12: "tile_12", 13: "tile_13", 14: "tile_14",
    15: "tile_15", 17: "tile_17", 18: "tile_18", 19: "tile_19", 20: "tile_20",
    21: "tile_21", 22: "tile_22", 23: "tile_23", 24: "tile_24", 25: "tile_25",
    26: "tile_26", 30: "tile_30", 31: "tile_31", 32: "tile_32", 33: "tile_33",
    34: "tile_34", 35: "tile_35", 36: "tile_36", 37: "tile_37", 38: "tile_38",
    44: "tile_44", 45: "tile_45", 46: "tile_46", 47: "tile_47", 48: "tile_48",
    50: "tile_50", 52: "tile_52", 53: "tile_53", 59: "tile_59", 60: "tile_60",
    61: "tile_61", 62: "tile_62", 63: "tile_63", 64: "tile_64", 65: "tile_65",
    66: "tile_66", 67: "tile_67", 68: "tile_68", 69: "tile_69", 70: "tile_70",
    79: "tile_79", 80: "tile_80", 81: "tile_81", 82: "tile_82", 83: "tile_83",
    84: "tile_84", 85: "tile_85", 86: "tile_86", 87: "tile_87", 88: "tile_88",
    89: "tile_89", 91: "tile_91", 92: "tile_92", 93: "tile_93", 94: "tile_94",
    95: "tile_95", 96: "tile_96", 97: "tile_97", 98: "tile_98", 99: "tile_99",
    100: "tile_100", 101: "tile_101", 102: "tile_102", 103: "tile_103", 104: "tile_104",
    105: "tile_105", 106: "tile_106", 107: "tile_107", 108: "tile_108", 110: "tile_110",
    111: "tile_111", 112: "tile_112", 113: "tile_113", 114: "tile_114", 115: "tile_115",
    116: "tile_116", 117: "tile_117", 118: "tile_118", 120: "tile_120", 121: "tile_121",
    123: "tile_123", 124: "tile_124", 125: "tile_125", 126: "tile_126", 127: "tile_127",
    128: "tile_128", 129: "tile_129", 130: "tile_130", 131: "tile_131", 132: "tile_132",
    133: "tile_133", 135: "tile_135", 136: "tile_136", 137: "tile_137", 138: "tile_138",
    141: "tile_141", 142: "tile_142", 143: "tile_143", 145: "tile_145", 146: "tile_146",
    147: "tile_147", 148: "tile_148", 149: "tile_149", 150: "tile_150", 151: "tile_151",
    152: "tile_152", 153: "tile_153", 157: "tile_157", 158: "tile_158", 159: "tile_159",
    160: "tile_160", 163: "tile_163", 164: "tile_164", 165: "tile_165", 166: "tile_166",
    167: "tile_167", 168: "tile_168", 169: "tile_169", 170: "tile_170", 171: "tile_171",
    172: "tile_172", 173: "tile_173", 174: "tile_174", 175: "tile_175", 176: "tile_176"
}

def decode_godot_coordinate(godot_pos, cell_size=32):
    """
    Convert Godot's tile coordinate to x,y position.
    Godot uses: y * 65536 + x for encoding positions (signed 16-bit values).
    """
    # In Godot 3.x, tile coordinates are encoded as:
    # position = y * 65536 + x
    # Both x and y are signed 16-bit values (-32768 to 32767)

    # Extract y (high 16 bits) and x (low 16 bits)
    # Using proper two's complement for signed integers
    y = godot_pos >> 16  # Arithmetic right shift preserves sign
    x = godot_pos & 0xFFFF  # Get lower 16 bits

    # Convert x to signed 16-bit
    if x >= 32768:
        x -= 65536

    return x, y

def parse_pool_int_array(array_str):
    """
    Parse a PoolIntArray string from Godot and extract tile data.

    Returns a dict of {(x, y): tile_id}
    """
    # Remove "PoolIntArray( " prefix and " )" suffix
    array_str = array_str.strip()
    if array_str.startswith("PoolIntArray("):
        array_str = array_str[13:]  # Remove "PoolIntArray("
    if array_str.endswith(")"):
        array_str = array_str[:-1]  # Remove ")"

    # Split by comma and convert to integers
    try:
        values = [int(x.strip()) for x in array_str.split(',') if x.strip()]
    except ValueError as e:
        print(f"Error parsing array values: {e}")
        return {}

    # Parse triplets: (position, tile_id, flags)
    tiles = {}
    for i in range(0, len(values), 3):
        if i + 2 < len(values):
            position = values[i]
            tile_id = values[i + 1]
            flags = values[i + 2]

            x, y = decode_godot_coordinate(position)
            tiles[(x, y)] = tile_id

    return tiles

def parse_tscn_file(tscn_path, multi_layer=False):
    """
    Parse a Godot .tscn file and extract tilemap data.

    Args:
        tscn_path: Path to the .tscn file
        multi_layer: If True, return dict of {layer_name: tiles}. If False, merge all layers.

    Returns:
        If multi_layer=True: dict of {layer_name: {(x,y): tile_id}}
        If multi_layer=False: dict of {(x,y): tile_id} (all layers merged)
    """
    with open(tscn_path, 'r') as f:
        content = f.read()

    # Find TileMap nodes
    tilemap_pattern = r'\[node name="([^"]+)" type="TileMap"[^\]]*\](.*?)(?=\[node|\Z)'
    tilemaps = re.findall(tilemap_pattern, content, re.DOTALL)

    if multi_layer:
        layers = {}
        for tilemap_name, tilemap_content in tilemaps:
            print(f"Found TileMap layer: {tilemap_name}")

            # Extract tile_data
            tile_data_match = re.search(r'tile_data = PoolIntArray\((.*?)\)', tilemap_content, re.DOTALL)

            if tile_data_match:
                array_str = "PoolIntArray(" + tile_data_match.group(1) + ")"
                tiles = parse_pool_int_array(array_str)

                print(f"  Parsed {len(tiles)} tiles from {tilemap_name}")
                layers[tilemap_name] = tiles
        return layers
    else:
        all_tiles = {}
        for tilemap_name, tilemap_content in tilemaps:
            print(f"Found TileMap: {tilemap_name}")

            # Extract tile_data
            tile_data_match = re.search(r'tile_data = PoolIntArray\((.*?)\)', tilemap_content, re.DOTALL)

            if tile_data_match:
                array_str = "PoolIntArray(" + tile_data_match.group(1) + ")"
                tiles = parse_pool_int_array(array_str)

                print(f"  Parsed {len(tiles)} tiles from {tilemap_name}")
                all_tiles.update(tiles)
        return all_tiles

def convert_to_gamev2_format(tiles, grid_size=64, filter_tiles=None, max_width=None, max_height=None, crop_start_x=None, crop_start_y=None):
    """
    Convert Godot tiles to gamev2 floor format.

    Args:
        tiles: Dict of {(x, y): tile_id}
        grid_size: gamev2 grid size (default 64)
        filter_tiles: List of tile IDs to include (None = all)
        max_width: Maximum width in tiles (None = unlimited)
        max_height: Maximum height in tiles (None = unlimited)

    Returns:
        Dict suitable for gamev2's floor configuration
    """
    floor = {}

    # Filter tiles if requested
    if filter_tiles is not None:
        tiles = {pos: tid for pos, tid in tiles.items() if tid in filter_tiles}
        print(f"Filtered to {len(tiles)} tiles with IDs: {filter_tiles}")

    # Find the bounds of the tilemap
    if not tiles:
        return floor

    min_x = min(x for x, y in tiles.keys())
    min_y = min(y for x, y in tiles.keys())
    max_x = max(x for x, y in tiles.keys())
    max_y = max(y for x, y in tiles.keys())

    print(f"\nTilemap bounds:")
    print(f"  X: {min_x} to {max_x} (width: {max_x - min_x + 1})")
    print(f"  Y: {min_y} to {max_y} (height: {max_y - min_y + 1})")

    # Calculate bounds for cropping
    if max_width or max_height:
        # Use specified crop coordinates if provided, otherwise use center
        if crop_start_x is not None and crop_start_y is not None:
            crop_min_x = crop_start_x
            crop_min_y = crop_start_y
        else:
            center_x = (min_x + max_x) // 2
            center_y = (min_y + max_y) // 2
            crop_min_x = center_x - (max_width // 2) if max_width else min_x
            crop_min_y = center_y - (max_height // 2) if max_height else min_y

        crop_max_x = crop_min_x + max_width - 1 if max_width else max_x
        crop_max_y = crop_min_y + max_height - 1 if max_height else max_y

        print(f"\nCropping to region:")
        print(f"  X: {crop_min_x} to {crop_max_x} (width: {crop_max_x - crop_min_x + 1})")
        print(f"  Y: {crop_min_y} to {crop_max_y} (height: {crop_max_y - crop_min_y + 1})")

        # Filter to cropped region
        tiles = {pos: tid for pos, tid in tiles.items()
                if crop_min_x <= pos[0] <= crop_max_x and crop_min_y <= pos[1] <= crop_max_y}

        if tiles:
            # Recalculate min based on actual tiles in cropped region
            min_x = min(x for x, y in tiles.keys())
            min_y = min(y for x, y in tiles.keys())
        else:
            min_x, min_y = crop_min_x, crop_min_y

    # Convert each tile
    for (x, y), tile_id in tiles.items():
        # Normalize coordinates (make min_x, min_y = 0, 0)
        norm_x = x - min_x
        norm_y = y - min_y

        # Get sprite name for this tile
        sprite_name = TILE_MAP.get(tile_id, f"tile_{tile_id}_unknown")

        # Add to floor
        floor[f"{norm_x},{norm_y}"] = sprite_name

    return floor

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 parse_godot_scene.py <path_to_tscn_file> [output_json]")
        return 1

    tscn_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else None

    if not os.path.exists(tscn_path):
        print(f"Error: File not found: {tscn_path}")
        return 1

    print(f"Parsing Godot scene: {tscn_path}")
    print("-" * 60)

    # Parse the .tscn file
    tiles = parse_tscn_file(tscn_path)

    if not tiles:
        print("Error: No tiles found in the scene file")
        return 1

    # Convert to gamev2 format
    print("\nConverting to gamev2 format...")
    # Convert all tiles, crop to a 40x30 region for optimal city view
    floor = convert_to_gamev2_format(
        tiles,
        filter_tiles=None,  # Include all tiles
        max_width=40,
        max_height=30,
        crop_start_x=9,  # Urban region with buildings and variety
        crop_start_y=9
    )

    print(f"✓ Converted {len(floor)} tiles")

    # Create room configuration
    room_config = {
        "name": "Tokyo",
        "floor": floor,
        "boundary": [],
        "npcs": [],
        "objects": [],
        "transporters": []
    }

    # Output result
    if output_path:
        with open(output_path, 'w') as f:
            json.dump(room_config, f, indent=2)
        print(f"\n✓ Saved room configuration to {output_path}")
    else:
        # Print first 10 tiles as sample
        print("\nSample floor tiles:")
        for i, (coord, sprite) in enumerate(list(floor.items())[:10]):
            print(f"  {coord}: {sprite}")
        if len(floor) > 10:
            print(f"  ... and {len(floor) - 10} more tiles")

    print("-" * 60)
    print("Conversion complete!")

    return 0

if __name__ == "__main__":
    sys.exit(main())
