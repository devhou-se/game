#!/usr/bin/env python3
"""
Extract tiles from the Japanese City tileset (GuttyKreum) for gamev2.
Keeps tiles at native 32x32 resolution to avoid scaling artifacts.
"""

from PIL import Image
import os
import sys

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

def extract_tile_by_id(tileset, tile_id, output_path, tile_size=32):
    """
    Extract a tile by its ID from the tileset.

    Args:
        tileset: PIL Image object of the tileset
        tile_id: The tile ID (0-based index in the tilemap)
        output_path: Path to save the extracted tile
        tile_size: Size of each tile in pixels (default 32x32)
    """
    # Japanese City tileset is 1920x768 pixels, tiles are 32x32
    # This gives us a 60x24 grid (60 tiles wide, 24 tiles high)
    tiles_per_row = 60

    # Calculate position
    row = tile_id // tiles_per_row
    col = tile_id % tiles_per_row
    x = col * tile_size
    y = row * tile_size

    # Validate we're not out of bounds
    if x >= tileset.width or y >= tileset.height:
        print(f"Warning: Tile {tile_id} is out of bounds (position {x},{y})")
        return False

    # Extract the tile at native resolution (NO SCALING)
    tile = tileset.crop((x, y, x + tile_size, y + tile_size))

    # Save the tile
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    tile.save(output_path)

    return True

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    game_dir = os.path.dirname(script_dir)

    tileset_path = os.path.join(game_dir, "Assets", "GuttyKreum",
                                "JapaneseCity_Complete_v7_1", "Tilemap", "Tilemap.png")
    output_dir = os.path.join(game_dir, "gamev2", "assets", "sprites")

    # Check if tileset exists
    if not os.path.exists(tileset_path):
        print(f"Error: Japanese City tileset not found at {tileset_path}")
        return 1

    # Load the tileset once
    print(f"Loading Japanese City tileset from {tileset_path}")
    tileset = Image.open(tileset_path)
    print(f"Tileset size: {tileset.width}x{tileset.height} pixels")
    print(f"Tile grid: {tileset.width//32}x{tileset.height//32} tiles (32x32 each)")

    print(f"\nExtracting {len(USED_TILE_IDS)} tiles at native 32x32 resolution...")
    print("-" * 60)

    # Extract each tile
    success_count = 0
    for i, tile_id in enumerate(USED_TILE_IDS):
        output_path = os.path.join(output_dir, f"tile_{tile_id}.png")

        try:
            if extract_tile_by_id(tileset, tile_id, output_path):
                success_count += 1
            if (i + 1) % 20 == 0:
                print(f"Extracted {i + 1}/{len(USED_TILE_IDS)} tiles...")
        except Exception as e:
            print(f"Error extracting tile {tile_id}: {e}")
            return 1

    print(f"\n✓ Successfully extracted {success_count}/{len(USED_TILE_IDS)} tiles to {output_dir}")
    print(f"Tiles are at native 32x32 resolution (no scaling artifacts)")
    print("-" * 60)
    print("Tile extraction complete!")
    print("\nNext steps:")
    print("1. Update gamev2/config.json to use gridSize: 32 instead of 64")
    print("2. Test the game to see the properly rendered tiles")

    return 0

if __name__ == "__main__":
    sys.exit(main())
