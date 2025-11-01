import numpy as np
from PIL import Image

# Create a 512x512 image with 3 color channels (RGB)
# Fill it with purely random pixel values (0-255)
width, height = 512, 512
random_data = np.random.randint(0, 256, (height, width, 3), dtype=np.uint8)

# Convert the numpy array to a PIL Image
img = Image.fromarray(random_data, 'RGB')

# Save the image as a lossless PNG
img.save('synthetic_random.png')

print(f"Successfully created 'synthetic_random.png' ({width}x{height}).")
print("Use this file for Experiment 1 (Table 4) to get a high p-value.")
