"""
Utility functions for DP-Enhanced Steganography
Handles password-based seeding, bit conversions, and pixel shuffling
"""

import hashlib
import numpy as np


def password_to_seed(password: str) -> int:
    """
    Convert a password string to a 64-bit integer seed using SHA-256 hashing.
    
    This ensures that the same password always produces the same seed,
    enabling sender and receiver to independently generate the same
    shuffled pixel sequence without sharing the actual shuffle map.
    
    Args:
        password (str): The secret password shared between sender and receiver
        
    Returns:
        int: A 64-bit integer seed for random number generation
    """
    # Hash the password using SHA-256 (produces 256-bit hash)
    hash_bytes = hashlib.sha256(password.encode('utf-8')).digest()
    
    # Take the first 8 bytes (64 bits) and convert to integer
    seed = int.from_bytes(hash_bytes[:8], byteorder='big')
    
    return seed


def string_to_bits(text: str) -> list:
    """
    Convert a text string to a list of bits (0s and 1s).
    
    Uses 8-bit ASCII encoding. Each character becomes 8 bits.
    Example: 'A' (ASCII 65) -> [0, 1, 0, 0, 0, 0, 0, 1]
    
    Args:
        text (str): The message to convert
        
    Returns:
        list: A list of integers (0 or 1) representing the binary encoding
    """
    bits = []
    for char in text:
        # Get ASCII value of character
        ascii_val = ord(char)
        
        # Convert to 8-bit binary (e.g., 65 -> '01000001')
        binary_str = format(ascii_val, '08b')
        
        # Add each bit as an integer
        bits.extend([int(bit) for bit in binary_str])
    
    return bits


def bits_to_string(bits: list) -> str:
    """
    Convert a list of bits back to a text string.
    
    Groups bits into 8-bit chunks and converts each to an ASCII character.
    
    Args:
        bits (list): A list of integers (0 or 1) representing binary data
        
    Returns:
        str: The decoded text message
    """
    text = ""
    
    # Process bits in chunks of 8
    for i in range(0, len(bits), 8):
        # Get the next 8 bits
        byte = bits[i:i+8]
        
        # Convert binary list to string ('01000001')
        binary_str = ''.join(str(bit) for bit in byte)
        
        # Convert binary string to integer, then to character
        ascii_val = int(binary_str, 2)
        text += chr(ascii_val)
    
    return text


def get_pixel_indices(image_shape: tuple, num_channels: int, seed: int) -> np.ndarray:
    """
    Generate a shuffled list of pixel channel indices based on a seed.
    
    This is the core of the "shared secret" mechanism. Given the same seed,
    this function will ALWAYS produce the same shuffled sequence.
    
    Key Implementation Details:
    - We shuffle channel indices (0 to height*width*3), not (row, col) pairs
    - Channel index can be converted: row = idx // (width*3), 
      col = (idx % (width*3)) // 3, channel = idx % 3
    - The sender uses num_channels = total_channels_to_modify (message + noise)
    - The receiver uses num_channels = message_length_bits (just the message)
    - Since both use the same seed, the receiver's list is exactly the first N
      elements of the sender's list
    
    Args:
        image_shape (tuple): (height, width, channels) of the image
        num_channels (int): How many pixel channels to return
        seed (int): Random seed for reproducible shuffling
        
    Returns:
        np.ndarray: Array of shuffled channel indices
    """
    height, width, channels = image_shape
    
    # Total number of color channels in the image (usually height * width * 3)
    total_channels = height * width * channels
    
    # Ensure we don't request more channels than exist
    if num_channels > total_channels:
        raise ValueError(
            f"Requested {num_channels} channels but image only has {total_channels}"
        )
    
    # Create a reproducible random generator with the seed
    rng = np.random.default_rng(seed)
    
    # Create array of all channel indices: [0, 1, 2, ..., total_channels-1]
    all_indices = np.arange(total_channels)
    
    # Shuffle the entire array (this is the secret path through the image)
    rng.shuffle(all_indices)
    
    # Return only the first num_channels (sender gets more, receiver gets fewer)
    return all_indices[:num_channels]


def index_to_pixel(index: int, width: int, channels: int) -> tuple:
    """
    Convert a flat channel index to (row, col, channel) coordinates.
    
    Helper function for debugging and understanding the pixel shuffling.
    
    Args:
        index (int): Flat channel index
        width (int): Image width
        channels (int): Number of channels (usually 3 for RGB)
        
    Returns:
        tuple: (row, col, channel) coordinates
    """
    row = index // (width * channels)
    col = (index % (width * channels)) // channels
    channel = index % channels
    
    return (row, col, channel)


def pixel_to_index(row: int, col: int, channel: int, width: int, channels: int) -> int:
    """
    Convert (row, col, channel) coordinates to a flat channel index.
    
    Inverse of index_to_pixel().
    
    Args:
        row (int): Pixel row
        col (int): Pixel column
        channel (int): Color channel (0=R, 1=G, 2=B)
        width (int): Image width
        channels (int): Number of channels (usually 3 for RGB)
        
    Returns:
        int: Flat channel index
    """
    return row * (width * channels) + col * channels + channel
