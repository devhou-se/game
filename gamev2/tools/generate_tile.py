from PIL import Image, ImageDraw

# Create a 64x64 image with transparent background
img = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
draw = ImageDraw.Draw(img)

# Dark yellow color (RGB)
dark_yellow = (204, 204, 0, 255)

# Draw 2px thick border
border_width = 2
for i in range(border_width):
    draw.rectangle(
        [i, i, 63-i, 63-i],
        outline=dark_yellow,
        width=1
    )

# Save the image
img.save('../assets/single-tile.png')
print("Generated ../assets/single-tile.png (64x64 with 2px dark yellow border)")
