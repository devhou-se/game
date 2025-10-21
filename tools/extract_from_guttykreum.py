#!/usr/bin/env python3
"""
Extract tiles from GuttyKreum mega-tileset by parsing the .tres file
and extracting each tile from its correct source tileset.
"""

from PIL import Image
import os
import sys
import re

# All tile IDs used in the tokyo_outside scene
USED_TILE_IDS = [
    0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 17, 18, 19, 20,
    21, 22, 23, 24, 25, 26, 30, 31, 32, 33, 34, 35, 36, 37, 38, 44, 45, 46,
    47, 48, 50, 52, 53, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 79,
    80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 91, 92, 93, 94, 95, 96, 97, 98,
    99, 100, 101, 102, 103, 104, 105, 106, 107, 108, 110, 111, 112, 113, 114,
    115, 116, 117, 118, 120, 121, 123, 124, 125, 126, 127, 128, 129, 130, 131,
    132, 133, 135, 136, 137, 138, 141, 142, 143, 145, 146, 147, 148, 149, 150,
    151, 152, 153, 157, 158, 159, 160, 163, 164, 165, 166, 167, 168, 169, 170,
    171, 172, 173, 174, 175, 176
]

def parse_guttykreum_tres(tres_path, game_dir):
    """
    Parse GuttyKreum.tres to get tile mappings.
    Returns dict of {tile_id: (texture_path, region)}
    """
    with open(tres_path, 'r') as f:
        content = f.read()

    # First, parse ExtResource mappings
    ext_resources = {}
    for match in re.finditer(r'\[ext_resource path="res://([^"]+)" type="Texture" id=(\d+)\]', content):
        path = match.group(1)
        resource_id = int(match.group(2))
        # Convert Godot path to file system path
        fs_path = os.path.join(game_dir, path.replace('/', os.sep))
        ext_resources[resource_id] = fs_path

    print(f"Found {len(ext_resources)} texture resources")

    # Parse tile definitions
    tiles = {}
    current_tile_id = None
    current_texture_id = None
    current_region = None

    for line in content.split('\n'):
        line = line.strip()

        # Match tile ID line like "8/name = "block""
        tile_match = re.match(r'(\d+)/name = "(.*)"', line)
        if tile_match:
            current_tile_id = int(tile_match.group(1))
            continue

        # Match texture reference like "8/texture = ExtResource( 3 )"
        texture_match = re.match(r'\d+/texture = ExtResource\( (\d+) \)', line)
        if texture_match and current_tile_id is not None:
            current_texture_id = int(texture_match.group(1))
            continue

        # Match region like "8/region = Rect2( 128, 224, 32, 32 )"
        region_match = re.match(r'\d+/region = Rect2\( ([\d.]+), ([\d.]+), ([\d.]+), ([\d.]+) \)', line)
        if region_match and current_tile_id is not None:
            x = int(float(region_match.group(1)))
            y = int(float(region_match.group(2)))
            w = int(float(region_match.group(3)))
            h = int(float(region_match.group(4)))
            current_region = (x, y, w, h)

            # We have all the info for this tile
            if current_texture_id in ext_resources:
                tiles[current_tile_id] = (ext_resources[current_texture_id], current_region)

            # Reset for next tile
            current_tile_id = None
            current_texture_id = None
            current_region = None

    return tiles

def extract_tile(source_image_path, region, output_path, target_size=64):
    """
    Extract a tile from a source image at the given region and scale to target size.
    Handles autotiles by extracting just the top-left cell.
    Uses NEAREST for pixel art to maintain sharp edges (2x scale is clean for pixel art).
    """
    if not os.path.exists(source_image_path):
        print(f"Warning: Source image not found: {source_image_path}")
        return False

    try:
        source = Image.open(source_image_path)
        x, y, w, h = region

        # Handle autotiles (regions larger than 32x32)
        # Extract just the top-left 32x32 cell for consistency
        if w > 32 or h > 32:
            # This is an autotile - extract just the first 32x32 cell
            tile = source.crop((x, y, x + 32, y + 32))
        else:
            # Regular tile - extract the full region
            tile = source.crop((x, y, x + w, y + h))

        # Scale to 64x64 for gamev2
        # Use NEAREST for exact 2x integer scaling (32x32 -> 64x64)
        # This maintains pixel art sharpness since it's exactly 2x
        if tile.width != target_size or tile.height != target_size:
            tile = tile.resize((target_size, target_size), Image.NEAREST)

        # Save at target resolution
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        tile.save(output_path)
        return True
    except Exception as e:
        print(f"Error extracting tile: {e}")
        return False

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    game_dir = os.path.dirname(script_dir)

    tres_path = os.path.join(game_dir, "Assets", "Tilemap", "GuttyKreum.tres")
    output_dir = os.path.join(game_dir, "gamev2", "assets", "sprites")

    if not os.path.exists(tres_path):
        print(f"Error: GuttyKreum.tres not found at {tres_path}")
        return 1

    print(f"Parsing GuttyKreum tileset from {tres_path}")
    print("-" * 60)

    tile_mappings = parse_guttykreum_tres(tres_path, game_dir)
    print(f"Parsed {len(tile_mappings)} tile definitions")

    print(f"\nExtracting {len(USED_TILE_IDS)} tiles...")
    print("-" * 60)

    success_count = 0
    for i, tile_id in enumerate(USED_TILE_IDS):
        if tile_id not in tile_mappings:
            print(f"Warning: Tile {tile_id} not found in GuttyKreum.tres")
            continue

        source_path, region = tile_mappings[tile_id]
        output_path = os.path.join(output_dir, f"tile_{tile_id}.png")

        if extract_tile(source_path, region, output_path):
            success_count += 1

        if (i + 1) % 20 == 0:
            print(f"Extracted {i + 1}/{len(USED_TILE_IDS)} tiles...")

    print(f"\n✓ Successfully extracted {success_count}/{len(USED_TILE_IDS)} tiles")
    print(f"Tiles saved to {output_dir}")
    print("-" * 60)
    print("Extraction complete!")
    print("\nThe tiles are now correctly extracted from their source tilesets")
    print("Refresh your browser to see the properly rendered Tokyo scene!")

    return 0

if __name__ == "__main__":
    sys.exit(main())
