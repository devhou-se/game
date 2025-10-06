from PIL import Image, ImageDraw

# Create a 64x64 image
size = 64
img = Image.new('RGB', (size, size), color='gray')
draw = ImageDraw.Draw(img)

# Draw black border (4 pixels thick)
border_width = 4
draw.rectangle([0, 0, size-1, size-1], outline='black', width=border_width)

# Save the image
img.save('../assets/object-tile.png')
print("Object tile generated: ../assets/object-tile.png")
