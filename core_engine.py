"""
Core Steganography Engine with Differential Privacy
Implements LSB embedding and extraction with noisy pixel selection
"""

import numpy as np
from PIL import Image
from utils import password_to_seed, string_to_bits, bits_to_string, get_pixel_indices


def embed(cover_image_path: str, message: str, password: str, epsilon: float, 
          save_path: str) -> dict:
    """
    Embed a secret message into an image using DP-enhanced LSB steganography.
    
    Algorithm:
    1. Convert message to bits (true_count bits)
    2. Add Laplace noise to get noisy_count (DP mechanism)
    3. Generate shuffled pixel list using password-derived seed
    4. Embed message bits in first true_count pixels
    5. Embed random decoy bits in remaining (noisy_count - true_count) pixels
    6. Save as PNG to preserve LSB data
    
    Args:
        cover_image_path (str): Path to the cover image
        message (str): Secret message to hide
        password (str): Password for generating pixel shuffle
        epsilon (float): Privacy parameter (0.1-5.0)
                        Low epsilon = high privacy = more noise
                        High epsilon = low privacy = less noise
        save_path (str): Path to save stego image (must be .png)
        
    Returns:
        dict: Statistics about the embedding process including:
              - message_length_bits: True number of message bits
              - noisy_count: Number with added noise
              - total_pixels_modified: Actual pixels modified
              - epsilon: Privacy parameter used
              - capacity_used_percent: Percentage of image capacity used
    """
    # Load and standardize image to RGB (removes alpha channel)
    img = Image.open(cover_image_path).convert("RGB")
    img_array = np.array(img)
    height, width, channels = img_array.shape
    
    # Convert message to binary
    message_bits = string_to_bits(message)
    true_count = len(message_bits)
    
    # Check if message fits in image
    total_capacity = height * width * channels
    if true_count > total_capacity:
        raise ValueError(
            f"Message too large! Need {true_count} bits but image only has "
            f"{total_capacity} pixels. Maximum message length: "
            f"{total_capacity // 8} characters."
        )
    
    # Ensure epsilon is not zero (prevents division by zero)
    epsilon = max(0.01, epsilon)
    
    # === DIFFERENTIAL PRIVACY: Add Laplace Noise ===
    # Sensitivity: Adding 1 character adds 8 bits, so Δf = 8
    sensitivity = 8
    
    # Laplace scale: b = Δf / ε
    laplace_scale = sensitivity / epsilon
    
    # Generate Laplace noise
    noise = np.random.laplace(loc=0, scale=laplace_scale)
    
    # Noisy count (may be negative, but we handle that below)
    noisy_count = true_count + int(noise)
    
    # Practical trade-off: Always embed at least the full message
    # Pure DP would allow noisy_count < true_count, truncating the message
    # For a messaging app, we prioritize message integrity
    total_channels_to_modify = max(true_count, noisy_count)
    
    # Sanity check: Don't exceed image capacity
    total_channels_to_modify = min(total_channels_to_modify, total_capacity)
    
    # Generate seed from password
    seed = password_to_seed(password)
    
    # Get shuffled list of pixel channel indices
    pixel_indices = get_pixel_indices(
        image_shape=img_array.shape,
        num_channels=total_channels_to_modify,
        seed=seed
    )
    
    # Create a copy of the image array for modification
    stego_array = img_array.copy()
    
    # === EMBEDDING: Message + Decoys ===
    for bit_index, channel_index in enumerate(pixel_indices):
        # Convert flat index to (row, col, channel)
        row = channel_index // (width * channels)
        col = (channel_index % (width * channels)) // channels
        channel = channel_index % channels
        
        # Get current pixel value
        pixel_value = stego_array[row, col, channel]
        
        if bit_index < true_count:
            # Embed actual message bit
            bit_to_embed = message_bits[bit_index]
        else:
            # Embed random decoy bit (noise to mask statistical signature)
            bit_to_embed = np.random.randint(0, 2)
        
        # LSB substitution: Clear LSB and set to our bit
        # Example: pixel_value = 156 (10011100)
        #          & 0xFE = 254 (11111110) -> 10011100 & 11111110 = 10011100
        #          | bit (0 or 1) -> sets the LSB
        new_pixel_value = (pixel_value & 0xFE) | bit_to_embed
        
        # Update the pixel
        stego_array[row, col, channel] = new_pixel_value
    
    # Convert back to image and save
    stego_image = Image.fromarray(stego_array.astype('uint8'), 'RGB')
    
    # CRITICAL: Must save as PNG! JPEG will destroy LSB data
    if not save_path.lower().endswith('.png'):
        save_path = save_path.rsplit('.', 1)[0] + '.png'
    
    stego_image.save(save_path, "PNG")
    
    # Return statistics
    return {
        'message_length_bits': true_count,
        'message_length_chars': len(message),
        'noisy_count': noisy_count,
        'noise_added': noisy_count - true_count,
        'total_pixels_modified': total_channels_to_modify,
        'decoy_pixels': total_channels_to_modify - true_count,
        'epsilon': epsilon,
        'laplace_scale': laplace_scale,
        'total_capacity': total_capacity,
        'capacity_used_percent': (total_channels_to_modify / total_capacity) * 100,
        'image_dimensions': f"{width}x{height}",
        'save_path': save_path
    }


def extract(stego_image_path: str, password: str, message_length_bits: int) -> str:
    """
    Extract a hidden message from a stego image.
    
    Note: This function does NOT need epsilon! The privacy parameter is only
    for embedding. Extraction only needs:
    1. The password (to regenerate the same shuffled pixel list)
    2. The message length in bits (to know when to stop reading)
    
    Algorithm:
    1. Generate seed from password
    2. Generate shuffled pixel list (same as embedding)
    3. Read LSB from first message_length_bits pixels
    4. Convert bits back to text
    
    Args:
        stego_image_path (str): Path to the stego image
        password (str): Password used during embedding
        message_length_bits (int): Number of message bits to extract
                                   (provided by sender, e.g., 800 for 100 chars)
        
    Returns:
        str: The extracted secret message
    """
    # Load image and standardize to RGB
    img = Image.open(stego_image_path).convert("RGB")
    img_array = np.array(img)
    height, width, channels = img_array.shape
    
    # Validate message length
    total_capacity = height * width * channels
    if message_length_bits > total_capacity:
        raise ValueError(
            f"Invalid message length! Requested {message_length_bits} bits "
            f"but image only has {total_capacity} pixels."
        )
    
    # Generate seed from password
    seed = password_to_seed(password)
    
    # Get the SAME shuffled list of pixel indices (first N elements)
    # This will match the first N pixels used by the embedder
    pixel_indices = get_pixel_indices(
        image_shape=img_array.shape,
        num_channels=message_length_bits,
        seed=seed
    )
    
    # Extract bits
    extracted_bits = []
    
    for channel_index in pixel_indices:
        # Convert flat index to (row, col, channel)
        row = channel_index // (width * channels)
        col = (channel_index % (width * channels)) // channels
        channel = channel_index % channels
        
        # Get pixel value
        pixel_value = img_array[row, col, channel]
        
        # Extract LSB (bit 0)
        lsb = pixel_value & 1
        
        extracted_bits.append(lsb)
    
    # Convert bits back to string
    message = bits_to_string(extracted_bits)
    
    return message


def get_image_capacity(image_path: str) -> dict:
    """
    Calculate the maximum message capacity of an image.
    
    Args:
        image_path (str): Path to the image
        
    Returns:
        dict: Capacity information including max characters and bits
    """
    img = Image.open(image_path).convert("RGB")
    width, height = img.size
    
    total_pixels = width * height * 3  # RGB channels
    max_chars = total_pixels // 8  # 8 bits per character
    
    return {
        'dimensions': f"{width}x{height}",
        'total_pixels': total_pixels,
        'max_bits': total_pixels,
        'max_characters': max_chars,
        'max_characters_with_overhead': int(max_chars * 0.8)  # Conservative estimate
    }


def embed_standard_lsb(cover_image_path: str, message: str, save_path: str) -> dict:
    """
    Embed a message using STANDARD sequential LSB steganography (NO DP, NO shuffling).
    This serves as the baseline for comparison with DP-enhanced steganography.
    
    Key differences from DP-enhanced version:
    - NO password-based pixel shuffling (sequential embedding)
    - NO Laplace noise (no privacy protection)
    - NO decoy bits (only embeds actual message)
    - Easily detectable by statistical analysis
    
    Args:
        cover_image_path (str): Path to the cover image
        message (str): Secret message to hide
        save_path (str): Path to save stego image (must be .png)
        
    Returns:
        dict: Statistics about the embedding process
    """
    # Load and standardize image to RGB
    img = Image.open(cover_image_path).convert("RGB")
    img_array = np.array(img)
    height, width, channels = img_array.shape
    
    # Convert message to binary
    message_bits = string_to_bits(message)
    message_length = len(message_bits)
    
    # Check if message fits
    total_capacity = height * width * channels
    if message_length > total_capacity:
        raise ValueError(
            f"Message too large! Need {message_length} bits but image only has "
            f"{total_capacity} pixels."
        )
    
    # Create a copy for modification
    stego_array = img_array.copy()
    
    # === SEQUENTIAL LSB EMBEDDING (No shuffling!) ===
    bit_index = 0
    for row in range(height):
        for col in range(width):
            for channel in range(channels):
                if bit_index >= message_length:
                    break
                
                # Get current pixel value
                pixel_value = stego_array[row, col, channel]
                
                # Embed message bit using LSB substitution
                bit_to_embed = message_bits[bit_index]
                new_pixel_value = (pixel_value & 0xFE) | bit_to_embed
                
                # Update pixel
                stego_array[row, col, channel] = new_pixel_value
                bit_index += 1
            
            if bit_index >= message_length:
                break
        if bit_index >= message_length:
            break
    
    # Convert back to image and save as PNG
    stego_image = Image.fromarray(stego_array.astype('uint8'), 'RGB')
    
    if not save_path.lower().endswith('.png'):
        save_path = save_path.rsplit('.', 1)[0] + '.png'
    
    stego_image.save(save_path, "PNG")
    
    # Return statistics
    return {
        'message_length_bits': message_length,
        'message_length_chars': len(message),
        'total_pixels_modified': message_length,
        'total_capacity': total_capacity,
        'capacity_used_percent': (message_length / total_capacity) * 100,
        'image_dimensions': f"{width}x{height}",
        'save_path': save_path,
        'method': 'Standard Sequential LSB (No DP)'
    }
