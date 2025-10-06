from PIL import Image, ImageDraw

# Create 16x16 image with transparent background
img = Image.new('RGBA', (16, 16), (0, 0, 0, 0))
draw = ImageDraw.Draw(img)

# Draw yellow border around the tile
yellow = (255, 255, 0, 255)

# Draw rectangle border (edges)
draw.rectangle([(0, 0), (15, 15)], outline=yellow, width=1)

# Save the image
img.save('single-tile.png')
print("Generated 16x16 single tile with yellow border and transparent background")
