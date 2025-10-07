#!/usr/bin/env python3
"""
Godot Tilemap Parser
Extracts tilemap data from Godot .tscn files and converts to Phaser-compatible JSON format
"""

import re
import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional


class GodotTilemapParser:
    def __init__(self, tscn_file_path: str):
        self.tscn_path = Path(tscn_file_path)
        if not self.tscn_path.exists():
            raise FileNotFoundError(f"Scene file not found: {tscn_file_path}")

        self.content = self.tscn_path.read_text()
        self.tilemaps = {}
        self.grid_size = 64  # Default grid size for v2

    def parse(self) -> Dict:
        """Parse the Godot scene file and extract all TileMap nodes"""
        # Find all TileMap nodes
        tilemap_pattern = r'\[node name="([^"]+)" type="TileMap"[^\]]*\](.*?)(?=\[node|$)'
        matches = re.finditer(tilemap_pattern, self.content, re.DOTALL)

        for match in matches:
            layer_name = match.group(1)
            layer_content = match.group(2)

            # Extract tile_data from the layer
            tile_data = self._extract_tile_data(layer_content)

            if tile_data:
                self.tilemaps[layer_name] = {
                    'name': layer_name,
                    'tiles': tile_data
                }

        return self.tilemaps

    def _extract_tile_data(self, layer_content: str) -> Optional[List[Tuple[int, int, int]]]:
        """Extract tile data from a TileMap node content"""
        # Find tile_data line
        tile_data_match = re.search(r'tile_data = PoolIntArray\((.*?)\)', layer_content, re.DOTALL)

        if not tile_data_match:
            return None

        # Parse the PoolIntArray data
        data_str = tile_data_match.group(1)
        # Remove any whitespace and split by comma
        values = [int(v.strip()) for v in data_str.split(',') if v.strip()]

        # Godot stores tile data as triplets: [cell_id, tile_id, autotile_coord]
        # cell_id is encoded position, tile_id is the tile index
        tiles = []

        for i in range(0, len(values), 3):
            if i + 2 >= len(values):
                break

            cell_id = values[i]
            tile_id = values[i + 1]
            autotile_coord = values[i + 2]

            # Decode Godot's cell position encoding
            # Godot uses a custom encoding for negative coordinates
            x, y = self._decode_cell_position(cell_id)

            tiles.append((x, y, tile_id))

        return tiles

    def _decode_cell_position(self, cell_id: int) -> Tuple[int, int]:
        """
        Decode Godot's cell position encoding
        Godot uses a 2D coordinate system encoded in a single integer
        """
        # Godot's TileMap uses 16-bit coordinates
        # The cell_id is: y * 65536 + x
        # But with special handling for negative numbers

        # For large negative numbers, we need to handle wraparound
        if cell_id < -2147483648:  # Check if out of 32-bit signed int range
            cell_id = cell_id & 0xFFFFFFFF

        # Extract x and y
        x = cell_id & 0xFFFF
        y = (cell_id >> 16) & 0xFFFF

        # Handle negative coordinates (values > 32767 are negative)
        if x > 32767:
            x = x - 65536
        if y > 32767:
            y = y - 65536

        return (x, y)

    def to_phaser_tilemap(self, width: int = 15, height: int = 10) -> Dict:
        """
        Convert Godot tilemap data to Phaser-compatible tilemap JSON
        """
        if not self.tilemaps:
            self.parse()

        # Determine bounds from tile data
        all_x = []
        all_y = []

        for layer_data in self.tilemaps.values():
            for x, y, _ in layer_data['tiles']:
                all_x.append(x)
                all_y.append(y)

        if not all_x:
            print("Warning: No tiles found in tilemap data")
            min_x = min_y = 0
            max_x = width - 1
            max_y = height - 1
        else:
            min_x = min(all_x)
            max_x = max(all_x)
            min_y = min(all_y)
            max_y = max(all_y)

        # Calculate map dimensions
        map_width = max_x - min_x + 1
        map_height = max_y - min_y + 1

        print(f"Map bounds: X({min_x} to {max_x}), Y({min_y} to {max_y})")
        print(f"Map size: {map_width} x {map_height}")

        # Create layers array
        layers_data = {}

        for layer_name, layer_data in self.tilemaps.items():
            # Initialize empty layer grid
            layer_grid = [[-1 for _ in range(map_width)] for _ in range(map_height)]

            # Fill in tiles
            for x, y, tile_id in layer_data['tiles']:
                # Translate to 0-based coordinates
                grid_x = x - min_x
                grid_y = y - min_y

                if 0 <= grid_x < map_width and 0 <= grid_y < map_height:
                    layer_grid[grid_y][grid_x] = tile_id

            # Flatten for Phaser (row-major order)
            flattened = []
            for row in layer_grid:
                flattened.extend(row)

            layers_data[layer_name] = {
                'name': layer_name,
                'data': flattened,
                'width': map_width,
                'height': map_height
            }

        # Create Phaser tilemap JSON structure
        phaser_data = {
            'width': map_width,
            'height': map_height,
            'tilewidth': self.grid_size,
            'tileheight': self.grid_size,
            'layers': layers_data,
            'tilesetName': 'overworld_tiles',
            'tilesetImage': 'overworld_tiles',
            'bounds': {
                'minX': min_x,
                'maxX': max_x,
                'minY': min_y,
                'maxY': max_y
            }
        }

        return phaser_data

    def save_as_json(self, output_path: str, width: int = 15, height: int = 10):
        """Save the parsed tilemap as Phaser-compatible JSON"""
        phaser_data = self.to_phaser_tilemap(width, height)

        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with output_file.open('w') as f:
            json.dump(phaser_data, f, indent=2)

        print(f"Saved tilemap JSON to: {output_path}")
        print(f"  - Layers: {len(phaser_data['layers'])}")
        print(f"  - Size: {phaser_data['width']} x {phaser_data['height']}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 godot_tilemap_parser.py <input.tscn> [output.json]")
        print("Example: python3 godot_tilemap_parser.py ../../Scenes/tokyo/tokyo_outside.tscn tokyo_tilemap.json")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None

    # Parse the scene file
    parser = GodotTilemapParser(input_file)
    tilemaps = parser.parse()

    print(f"\nParsed {len(tilemaps)} tilemap layers from {input_file}:")
    for name, data in tilemaps.items():
        print(f"  - {name}: {len(data['tiles'])} tiles")

    # Save to JSON if output file specified
    if output_file:
        parser.save_as_json(output_file)
    else:
        # Print sample data
        phaser_data = parser.to_phaser_tilemap()
        print("\nPhaser tilemap structure:")
        print(json.dumps({k: v for k, v in phaser_data.items() if k != 'layers'}, indent=2))


if __name__ == "__main__":
    main()
