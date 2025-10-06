from PIL import Image, ImageDraw

# Create a 64x64 image with transparent background
img = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
draw = ImageDraw.Draw(img)

# Green color (RGB)
green = (0, 255, 0, 255)

# Draw 2px thick border
border_width = 2
for i in range(border_width):
    draw.rectangle(
        [i, i, 63-i, 63-i],
        outline=green,
        width=1
    )

# Save the image
img.save('../assets/transporter.png')
print("Generated ../assets/transporter.png (64x64 with 2px green border)")
