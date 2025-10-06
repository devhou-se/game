from PIL import Image

# Grid specifications
CELL_SIZE = 64
GRID_CELLS_X = 15
GRID_CELLS_Y = 10
TOTAL_WIDTH = CELL_SIZE * GRID_CELLS_X
TOTAL_HEIGHT = CELL_SIZE * GRID_CELLS_Y

# Create image
img = Image.new('RGB', (TOTAL_WIDTH, TOTAL_HEIGHT))
pixels = img.load()

# Colors
white = (255, 255, 255)
light_gray = (220, 220, 220)

# Draw each cell with checkerboard pattern
for cell_y in range(GRID_CELLS_Y):
    for cell_x in range(GRID_CELLS_X):
        # Calculate cell's top-left pixel position
        start_x = cell_x * CELL_SIZE
        start_y = cell_y * CELL_SIZE

        # Determine cell color (checkerboard pattern)
        if (cell_x + cell_y) % 2 == 0:
            cell_color = white
        else:
            cell_color = light_gray

        # Fill the entire cell with the color
        for y in range(CELL_SIZE):
            for x in range(CELL_SIZE):
                pixel_x = start_x + x
                pixel_y = start_y + y
                pixels[pixel_x, pixel_y] = cell_color

# Save the image
img.save('../assets/background-grid.png')
print(f"Generated ../assets/background-grid.png ({TOTAL_WIDTH}x{TOTAL_HEIGHT}, {GRID_CELLS_X}x{GRID_CELLS_Y} cells, {CELL_SIZE}px per cell)")
print(f"Alternating white and grey cells (checkerboard pattern)")
