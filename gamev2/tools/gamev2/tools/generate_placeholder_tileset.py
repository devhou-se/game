#!/usr/bin/env python3
"""
Generate a placeholder tileset image for testing
Creates numbered tiles for each tile ID
"""

from PIL import Image, ImageDraw, ImageFont
import sys


def generate_tileset(tile_ids, tile_size=64, tiles_per_row=16, output_file="tileset.png"):
    """
    Generate a tileset image with numbered tiles

    Args:
        tile_ids: List of tile IDs to include
        tile_size: Size of each tile in pixels
        tiles_per_row: Number of tiles per row
        output_file: Output filename
    """

    # Calculate dimensions
    num_tiles = max(tile_ids) + 1  # Need to include all IDs up to max
    rows = (num_tiles + tiles_per_row - 1) // tiles_per_row
    width = tiles_per_row * tile_size
    height = rows * tile_size

    # Create image
    img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Try to load a font, fall back to default if not available
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 20)
    except:
        font = ImageFont.load_default()

    # Define color palettes for different tile types
    colors = {
        'floor': (100, 150, 100, 255),      # Green-gray for floor
        'wall': (80, 80, 80, 255),           # Gray for walls
        'decoration': (150, 120, 80, 255),   # Brown for decoration
        'special': (120, 120, 200, 255)      # Blue for special
    }

    # Generate each tile
    for tile_id in range(num_tiles):
        row = tile_id // tiles_per_row
        col = tile_id % tiles_per_row
        x = col * tile_size
        y = row * tile_size

        # Choose color based on tile ID
        if tile_id in tile_ids:
            # Vary colors for visual distinction
            if tile_id < 50:
                color = colors['floor']
            elif tile_id < 100:
                color = colors['decoration']
            elif tile_id < 150:
                color = colors['wall']
            else:
                color = colors['special']
        else:
            # Empty/unused tiles are transparent
            continue

        # Draw tile background
        draw.rectangle([x, y, x + tile_size, y + tile_size], fill=color, outline=(200, 200, 200, 255))

        # Draw tile number
        text = str(tile_id)
        # Get text bounding box
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        text_x = x + (tile_size - text_width) // 2
        text_y = y + (tile_size - text_height) // 2

        # Draw text with shadow for visibility
        draw.text((text_x + 1, text_y + 1), text, fill=(0, 0, 0, 255), font=font)
        draw.text((text_x, text_y), text, fill=(255, 255, 255, 255), font=font)

    # Save image
    img.save(output_file)
    print(f"Generated tileset: {output_file}")
    print(f"  Size: {width}x{height} ({tiles_per_row} tiles per row, {rows} rows)")
    print(f"  Tile size: {tile_size}x{tile_size}")
    print(f"  Total tiles: {num_tiles}")
    print(f"  Used tiles: {len(tile_ids)}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 generate_placeholder_tileset.py <tile_ids> [output.png]")
        print("Example: python3 generate_placeholder_tileset.py \"0,1,2,8,9,100,157\" tileset.png")
        sys.exit(1)

    tile_ids_str = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else "tileset.png"

    # Parse tile IDs
    tile_ids = [int(x.strip()) for x in tile_ids_str.split(',')]

    print(f"Generating tileset with {len(tile_ids)} tiles...")
    generate_tileset(tile_ids, output_file=output_file)


if __name__ == "__main__":
    main()
