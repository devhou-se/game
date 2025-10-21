#!/usr/bin/env python3
"""
Extract tiles from Godot tileset and convert them to gamev2 sprites.
"""

from PIL import Image
import os
import sys

def extract_tile(tileset_path, region, output_path, target_size=64):
    """
    Extract a tile from a tileset image and resize it.

    Args:
        tileset_path: Path to the tileset PNG file
        region: Tuple of (x, y, width, height) defining the tile region
        output_path: Path to save the extracted tile
        target_size: Target size for the output tile (default 64x64)
    """
    try:
        # Load the tileset
        tileset = Image.open(tileset_path)

        # Extract the region
        x, y, width, height = region
        tile = tileset.crop((x, y, x + width, y + height))

        # If the region contains multiple tiles, we need to handle it
        # For now, we'll just use the first tile in the region
        if width > 32 or height > 32:
            # Assume we want the top-left tile
            tile = tile.crop((0, 0, min(32, width), min(32, height)))

        # Resize to target size
        tile_resized = tile.resize((target_size, target_size), Image.NEAREST)

        # Save the tile
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        tile_resized.save(output_path)
        print(f"Extracted tile to {output_path}")

        return True
    except Exception as e:
        print(f"Error extracting tile: {e}")
        return False

def main():
    # Define paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    game_dir = os.path.dirname(script_dir)

    tileset_path = os.path.join(game_dir, "Assets", "Modern_Exteriors_RPG_Maker_MV", "Tileset_1_MV.png")
    output_dir = os.path.join(game_dir, "gamev2", "sprites")

    # Check if tileset exists
    if not os.path.exists(tileset_path):
        print(f"Error: Tileset not found at {tileset_path}")
        return 1

    # Define tile regions from overworld_tiles.tres
    # Tile 8: Rect2(240, 672, 144, 96) - stone/brick
    # Tile 9: Rect2(624, 0, 144, 48) - grass
    tiles = [
        {
            "id": 8,
            "name": "tile_8_stone",
            "region": (240, 672, 144, 96),
            "description": "Stone/brick ground tile"
        },
        {
            "id": 9,
            "name": "tile_9_grass",
            "region": (624, 0, 144, 48),
            "description": "Grass ground tile"
        }
    ]

    # Extract each tile
    print(f"Extracting tiles from {tileset_path}")
    print("-" * 60)

    for tile in tiles:
        output_path = os.path.join(output_dir, f"{tile['name']}.png")
        print(f"Extracting Tile {tile['id']}: {tile['description']}")
        print(f"  Region: {tile['region']}")

        success = extract_tile(tileset_path, tile['region'], output_path)

        if success:
            print(f"  ✓ Saved to {output_path}")
        else:
            print(f"  ✗ Failed to extract tile {tile['id']}")
            return 1

        print()

    print("-" * 60)
    print("Tile extraction complete!")
    return 0

if __name__ == "__main__":
    sys.exit(main())
