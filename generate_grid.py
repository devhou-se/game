from PIL import Image, ImageDraw

# Tile specifications
tile_size = 64
grid_count = 16
total_size = tile_size * grid_count

# Create image with white background
img = Image.new('RGB', (total_size, total_size), 'white')
draw = ImageDraw.Draw(img)

# Draw black borders for each tile
for x in range(grid_count + 1):
    # Vertical lines
    draw.line([(x * tile_size, 0), (x * tile_size, total_size)], fill='black', width=1)

for y in range(grid_count + 1):
    # Horizontal lines
    draw.line([(0, y * tile_size), (total_size, y * tile_size)], fill='black', width=1)

# Save the image
img.save('background-grid.png')
print(f"Generated {total_size}x{total_size} grid image with {grid_count}x{grid_count} tiles")
