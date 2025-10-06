from PIL import Image, ImageDraw

# Create a 64x64 image with transparent background
img = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
draw = ImageDraw.Draw(img)

# Red color (RGB)
red = (204, 0, 0, 255)

# Draw 2px thick border
border_width = 2
for i in range(border_width):
    draw.rectangle(
        [i, i, 63-i, 63-i],
        outline=red,
        width=1
    )

# Save the image
img.save('../assets/npc-tile.png')
print("Generated ../assets/npc-tile.png (64x64 with 2px red border)")
