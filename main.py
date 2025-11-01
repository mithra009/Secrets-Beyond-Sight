"""
DP-Enhanced Steganography
Main entry point for the application
"""

import sys
import os

# Add the project directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gui import main

if __name__ == "__main__":
    print("=" * 70)
    print("  DP-ENHANCED STEGANOGRAPHY")
    print("  Differential Privacy Meets LSB Steganography")
    print("=" * 70)
    print()
    print("Starting GUI application...")
    print()
    
    try:
        main()
    except Exception as e:
        print(f"Error starting application: {e}")
        input("Press Enter to exit...")
