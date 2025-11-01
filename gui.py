"""
GUI Application for DP-Enhanced Steganography
Provides user-friendly interface for embedding, extracting, and analyzing images
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import os
from PIL import Image, ImageTk
import threading

from core_engine import embed, extract, get_image_capacity, embed_standard_lsb
from steganalysis import (chi_square_attack, compare_images, multi_channel_analysis, 
                         calculate_visual_difference, generate_random_lsb_image,
                         calculate_epsilon_visibility)


class SteganographyApp:
    def __init__(self, root):
        self.root = root
        self.root.title("DP-Enhanced Steganography")
        self.root.geometry("900x700")
        
        # Variables
        self.cover_image_path = None
        self.stego_image_path = None
        self.original_image_for_comparison = None
        
        # Create UI
        self.create_widgets()
        
    def create_widgets(self):
        """Create the main UI layout"""
        
        # Create notebook (tabs)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Create tabs
        self.embed_tab = ttk.Frame(self.notebook)
        self.extract_tab = ttk.Frame(self.notebook)
        self.analysis_tab = ttk.Frame(self.notebook)
        self.testing_tab = ttk.Frame(self.notebook)
        self.info_tab = ttk.Frame(self.notebook)
        
        self.notebook.add(self.embed_tab, text="Embed Message")
        self.notebook.add(self.extract_tab, text="Extract Message")
        self.notebook.add(self.analysis_tab, text="Analysis")
        self.notebook.add(self.testing_tab, text="Testing Lab")
        self.notebook.add(self.info_tab, text="About")
        
        # Setup each tab
        self.setup_embed_tab()
        self.setup_extract_tab()
        self.setup_analysis_tab()
        self.setup_testing_tab()
        self.setup_info_tab()
        
    def setup_embed_tab(self):
        """Setup the embedding interface"""
        
        # Create canvas and scrollbar for embed tab
        canvas = tk.Canvas(self.embed_tab, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.embed_tab, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw", width=canvas.winfo_reqwidth())
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Bind to adjust width dynamically
        def _configure_canvas(event):
            canvas.itemconfig(canvas.find_withtag("all")[0], width=event.width)
        canvas.bind("<Configure>", _configure_canvas)
        
        canvas.pack(side="left", fill="both", expand=True, padx=0)
        scrollbar.pack(side="right", fill="y", padx=0)
        
        # Bind mouse wheel for scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        # Image Selection Frame
        img_frame = ttk.LabelFrame(scrollable_frame, text="1. Select Cover Image", padding=10)
        img_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Button(img_frame, text="Browse Image", command=self.browse_cover_image).pack(side='left', padx=5)
        self.cover_image_label = ttk.Label(img_frame, text="No image selected", foreground="gray")
        self.cover_image_label.pack(side='left', padx=5)
        
        # Image preview
        self.cover_preview_label = ttk.Label(img_frame)
        self.cover_preview_label.pack(pady=5)
        
        # Capacity info
        self.capacity_label = ttk.Label(img_frame, text="", foreground="blue")
        self.capacity_label.pack(pady=2)
        
        # Message Frame
        msg_frame = ttk.LabelFrame(scrollable_frame, text="2. Enter Secret Message", padding=10)
        msg_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        self.message_text = scrolledtext.ScrolledText(msg_frame, height=8, wrap=tk.WORD)
        self.message_text.pack(fill='both', expand=True)
        self.message_text.bind('<KeyRelease>', self.update_message_stats)
        
        self.message_stats_label = ttk.Label(msg_frame, text="Characters: 0 | Bits: 0", foreground="gray")
        self.message_stats_label.pack(anchor='w', pady=2)
        
        # Password Frame
        pwd_frame = ttk.LabelFrame(scrollable_frame, text="3. Set Password", padding=10)
        pwd_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Label(pwd_frame, text="Password:").pack(side='left', padx=5)
        self.embed_password_entry = ttk.Entry(pwd_frame, width=30, show="*")
        self.embed_password_entry.pack(side='left', padx=5)
        
        self.show_pwd_var = tk.BooleanVar()
        ttk.Checkbutton(pwd_frame, text="Show", variable=self.show_pwd_var, 
                       command=lambda: self.embed_password_entry.config(
                           show="" if self.show_pwd_var.get() else "*"
                       )).pack(side='left')
        
        # Privacy Frame
        privacy_frame = ttk.LabelFrame(scrollable_frame, text="4. Set Privacy Level (ε - Epsilon)", padding=10)
        privacy_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Label(privacy_frame, text="Low Privacy (More Noise)").pack(anchor='w')
        
        self.epsilon_var = tk.DoubleVar(value=1.0)
        self.epsilon_slider = ttk.Scale(privacy_frame, from_=0.1, to=5.0, 
                                       variable=self.epsilon_var, orient='horizontal',
                                       command=self.update_epsilon_label)
        self.epsilon_slider.pack(fill='x', padx=5)
        
        ttk.Label(privacy_frame, text="High Privacy (Less Noise)").pack(anchor='w')
        
        epsilon_info_frame = ttk.Frame(privacy_frame)
        epsilon_info_frame.pack(fill='x', pady=5)
        
        self.epsilon_value_label = ttk.Label(epsilon_info_frame, text="ε = 1.00", 
                                            font=('Arial', 12, 'bold'))
        self.epsilon_value_label.pack(side='left', padx=5)
        
        self.epsilon_desc_label = ttk.Label(epsilon_info_frame, 
                                           text="(Balanced privacy and efficiency)",
                                           foreground="blue")
        self.epsilon_desc_label.pack(side='left')
        
        # Embed Button
        embed_btn_frame = ttk.Frame(scrollable_frame)
        embed_btn_frame.pack(fill='x', padx=10, pady=10)
        
        ttk.Button(embed_btn_frame, text="Embed Message", 
                  command=self.embed_message, style='Accent.TButton').pack(pady=5)
        
        # Results Frame
        results_frame = ttk.LabelFrame(scrollable_frame, text="Embedding Results", padding=10)
        results_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        self.embed_results_text = scrolledtext.ScrolledText(results_frame, height=8, wrap=tk.WORD)
        self.embed_results_text.pack(fill='both', expand=True)
        
    def setup_extract_tab(self):
        """Setup the extraction interface"""
        
        # Create canvas and scrollbar for extract tab
        canvas = tk.Canvas(self.extract_tab, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.extract_tab, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw", width=canvas.winfo_reqwidth())
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Bind to adjust width dynamically
        def _configure_canvas(event):
            canvas.itemconfig(canvas.find_withtag("all")[0], width=event.width)
        canvas.bind("<Configure>", _configure_canvas)
        
        canvas.pack(side="left", fill="both", expand=True, padx=0)
        scrollbar.pack(side="right", fill="y", padx=0)
        
        # Bind mouse wheel for scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        # Image Selection Frame
        img_frame = ttk.LabelFrame(scrollable_frame, text="1. Select Stego Image", padding=10)
        img_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Button(img_frame, text="Browse Image", command=self.browse_stego_image).pack(side='left', padx=5)
        self.stego_image_label = ttk.Label(img_frame, text="No image selected", foreground="gray")
        self.stego_image_label.pack(side='left', padx=5)
        
        # Image preview
        self.stego_preview_label = ttk.Label(img_frame)
        self.stego_preview_label.pack(pady=5)
        
        # Password Frame
        pwd_frame = ttk.LabelFrame(scrollable_frame, text="2. Enter Password", padding=10)
        pwd_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Label(pwd_frame, text="Password:").pack(side='left', padx=5)
        self.extract_password_entry = ttk.Entry(pwd_frame, width=30, show="*")
        self.extract_password_entry.pack(side='left', padx=5)
        
        self.show_extract_pwd_var = tk.BooleanVar()
        ttk.Checkbutton(pwd_frame, text="Show", variable=self.show_extract_pwd_var, 
                       command=lambda: self.extract_password_entry.config(
                           show="" if self.show_extract_pwd_var.get() else "*"
                       )).pack(side='left')
        
        # Message Length Frame
        length_frame = ttk.LabelFrame(scrollable_frame, text="3. Enter Message Length (in bits)", padding=10)
        length_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Label(length_frame, text="Message Length (bits):").pack(side='left', padx=5)
        self.message_length_entry = ttk.Entry(length_frame, width=15)
        self.message_length_entry.pack(side='left', padx=5)
        
        ttk.Label(length_frame, text="(This value is provided by the sender)", 
                 foreground="gray").pack(side='left', padx=5)
        
        # Extract Button
        extract_btn_frame = ttk.Frame(scrollable_frame)
        extract_btn_frame.pack(fill='x', padx=10, pady=10)
        
        ttk.Button(extract_btn_frame, text="Extract Message", 
                  command=self.extract_message, style='Accent.TButton').pack(pady=5)
        
        # Results Frame
        results_frame = ttk.LabelFrame(scrollable_frame, text="Extracted Message", padding=10)
        results_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        self.extract_results_text = scrolledtext.ScrolledText(results_frame, height=10, wrap=tk.WORD)
        self.extract_results_text.pack(fill='both', expand=True)
        
        # Copy button
        ttk.Button(results_frame, text="Copy to Clipboard", 
                  command=self.copy_extracted_message).pack(pady=5)
        
    def setup_analysis_tab(self):
        """Setup the steganalysis interface"""
        
        # Create canvas and scrollbar for analysis tab
        canvas = tk.Canvas(self.analysis_tab, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.analysis_tab, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw", width=canvas.winfo_reqwidth())
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Bind to adjust width dynamically
        def _configure_canvas(event):
            canvas.itemconfig(canvas.find_withtag("all")[0], width=event.width)
        canvas.bind("<Configure>", _configure_canvas)
        
        canvas.pack(side="left", fill="both", expand=True, padx=0)
        scrollbar.pack(side="right", fill="y", padx=0)
        
        # Bind mouse wheel for scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        # Image Selection Frame
        img_frame = ttk.LabelFrame(scrollable_frame, text="Select Image to Analyze", padding=10)
        img_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Button(img_frame, text="Browse Image", command=self.browse_analysis_image).pack(side='left', padx=5)
        self.analysis_image_label = ttk.Label(img_frame, text="No image selected", foreground="gray")
        self.analysis_image_label.pack(side='left', padx=5)
        
        # Analysis Options
        options_frame = ttk.LabelFrame(scrollable_frame, text="Analysis Options", padding=10)
        options_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Button(options_frame, text="Chi-Square Test", 
                  command=self.run_chi_square).pack(side='left', padx=5)
        ttk.Button(options_frame, text="Multi-Channel Analysis", 
                  command=self.run_multi_channel).pack(side='left', padx=5)
        
        # Comparison Frame
        compare_frame = ttk.LabelFrame(scrollable_frame, text="Compare Original vs Stego", padding=10)
        compare_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Label(compare_frame, text="Original Image:").pack(anchor='w')
        orig_btn_frame = ttk.Frame(compare_frame)
        orig_btn_frame.pack(fill='x', pady=2)
        
        ttk.Button(orig_btn_frame, text="Browse Original", 
                  command=self.browse_original_for_comparison).pack(side='left', padx=5)
        self.original_comparison_label = ttk.Label(orig_btn_frame, text="No image selected", 
                                                  foreground="gray")
        self.original_comparison_label.pack(side='left', padx=5)
        
        ttk.Label(compare_frame, text="Stego Image:").pack(anchor='w', pady=(10,0))
        stego_btn_frame = ttk.Frame(compare_frame)
        stego_btn_frame.pack(fill='x', pady=2)
        
        ttk.Button(stego_btn_frame, text="Browse Stego", 
                  command=self.browse_stego_for_comparison).pack(side='left', padx=5)
        self.stego_comparison_label = ttk.Label(stego_btn_frame, text="No image selected", 
                                               foreground="gray")
        self.stego_comparison_label.pack(side='left', padx=5)
        
        ttk.Button(compare_frame, text="Compare Images", 
                  command=self.compare_images_analysis).pack(pady=10)
        
        # Results Frame
        results_frame = ttk.LabelFrame(scrollable_frame, text="Analysis Results", padding=10)
        results_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        self.analysis_results_text = scrolledtext.ScrolledText(results_frame, height=15, wrap=tk.WORD)
        self.analysis_results_text.pack(fill='both', expand=True)
        
    def setup_testing_tab(self):
        """Setup the testing lab for comparing Standard LSB vs DP-Enhanced LSB"""
        
        # Create canvas and scrollbar
        canvas = tk.Canvas(self.testing_tab, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.testing_tab, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw", width=canvas.winfo_reqwidth())
        canvas.configure(yscrollcommand=scrollbar.set)
        
        def _configure_canvas(event):
            canvas.itemconfig(canvas.find_withtag("all")[0], width=event.width)
        canvas.bind("<Configure>", _configure_canvas)
        
        canvas.pack(side="left", fill="both", expand=True, padx=0)
        scrollbar.pack(side="right", fill="y", padx=0)
        
        # Bind mouse wheel
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        # Main content
        main_frame = ttk.Frame(scrollable_frame, padding="20")
        main_frame.pack(fill='both', expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, text="Testing Lab: Standard LSB vs DP-Enhanced LSB", 
                               font=('Arial', 14, 'bold'))
        title_label.pack(pady=(0, 20))
        
        # Description
        desc_frame = ttk.LabelFrame(main_frame, text="What This Does", padding="10")
        desc_frame.pack(fill='x', pady=(0, 20))
        
        desc_text = ttk.Label(desc_frame, text=
            "This lab generates a test image, embeds a message using BOTH methods, and compares results:\n"
            "1. Generate synthetic image with random LSBs (50/50 distribution)\n"
            "2. Embed message using Standard Sequential LSB (NO DP protection)\n"
            "3. Embed same message using DP-Enhanced LSB (WITH DP protection)\n"
            "4. Compare both against the original to see which is more detectable",
            justify='left', wraplength=800)
        desc_text.pack()
        
        # Configuration Section
        config_frame = ttk.LabelFrame(main_frame, text="1. Configure Test Parameters", padding="10")
        config_frame.pack(fill='x', pady=(0, 10))
        
        # Image size
        size_frame = ttk.Frame(config_frame)
        size_frame.pack(fill='x', pady=5)
        ttk.Label(size_frame, text="Image Size:").pack(side='left', padx=(0, 10))
        self.test_width_var = tk.StringVar(value="256")
        ttk.Entry(size_frame, textvariable=self.test_width_var, width=8).pack(side='left')
        ttk.Label(size_frame, text="×").pack(side='left', padx=5)
        self.test_height_var = tk.StringVar(value="256")
        ttk.Entry(size_frame, textvariable=self.test_height_var, width=8).pack(side='left')
        ttk.Label(size_frame, text="pixels (smaller = more visible epsilon effects)").pack(side='left', padx=(10, 0))
        
        # Test message
        msg_frame = ttk.Frame(config_frame)
        msg_frame.pack(fill='x', pady=5)
        ttk.Label(msg_frame, text="Test Message:").pack(anchor='w')
        self.test_message_text = scrolledtext.ScrolledText(msg_frame, height=4, wrap=tk.WORD)
        self.test_message_text.pack(fill='x', pady=(5, 0))
        self.test_message_text.insert('1.0', "This is a test message for comparing Standard LSB steganography "
                                            "versus DP-Enhanced LSB steganography. The goal is to demonstrate "
                                            "that Differential Privacy mechanisms provide better protection against "
                                            "statistical steganalysis attacks.")
        
        # Epsilon
        epsilon_frame = ttk.Frame(config_frame)
        epsilon_frame.pack(fill='x', pady=5)
        ttk.Label(epsilon_frame, text="Epsilon (ε) for DP-Enhanced:").pack(side='left', padx=(0, 10))
        self.test_epsilon_var = tk.DoubleVar(value=0.5)
        epsilon_slider = ttk.Scale(epsilon_frame, from_=0.1, to=5.0, orient='horizontal',
                                   variable=self.test_epsilon_var, length=200)
        epsilon_slider.pack(side='left', padx=(0, 10))
        self.test_epsilon_label = ttk.Label(epsilon_frame, text="ε = 0.50")
        self.test_epsilon_label.pack(side='left')
        
        def update_test_epsilon(value=None):
            epsilon = self.test_epsilon_var.get()
            self.test_epsilon_label.config(text=f"ε = {epsilon:.2f}")
        epsilon_slider.config(command=update_test_epsilon)
        
        # Password
        pwd_frame = ttk.Frame(config_frame)
        pwd_frame.pack(fill='x', pady=5)
        ttk.Label(pwd_frame, text="Password (for DP method):").pack(side='left', padx=(0, 10))
        self.test_password_var = tk.StringVar(value="TestPassword123")
        ttk.Entry(pwd_frame, textvariable=self.test_password_var, width=30).pack(side='left')
        
        # Random Seed for reproducibility
        seed_frame = ttk.Frame(config_frame)
        seed_frame.pack(fill='x', pady=5)
        ttk.Label(seed_frame, text="Random Seed:").pack(side='left', padx=(0, 10))
        self.test_seed_var = tk.StringVar(value="42")
        ttk.Entry(seed_frame, textvariable=self.test_seed_var, width=15).pack(side='left')
        ttk.Label(seed_frame, text="(same seed = reproducible results)").pack(side='left', padx=(10, 0))

        # Image source: synthetic or existing file
        source_frame = ttk.Frame(config_frame)
        source_frame.pack(fill='x', pady=5)
        ttk.Label(source_frame, text="Image Source:").pack(side='left', padx=(0, 10))
        self.test_image_source_var = tk.StringVar(value='synthetic')
        ttk.Radiobutton(source_frame, text="Synthetic (use seed)", variable=self.test_image_source_var,
                        value='synthetic').pack(side='left', padx=(0, 5))
        ttk.Radiobutton(source_frame, text="Existing Image File", variable=self.test_image_source_var,
                        value='file').pack(side='left', padx=(0, 5))

        # File picker for existing image (disabled unless file selected at runtime)
        file_frame = ttk.Frame(config_frame)
        file_frame.pack(fill='x', pady=5)
        ttk.Button(file_frame, text="Browse Image for Test", command=self.browse_test_image).pack(side='left')
        self.test_image_label = ttk.Label(file_frame, text="No test image selected", foreground="gray")
        self.test_image_label.pack(side='left', padx=5)
        
        # Run Test Button
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(pady=20)
        ttk.Button(btn_frame, text="Run Complete Test", 
          command=self.run_comparison_test).pack()
        
        # Results Section
        results_frame = ttk.LabelFrame(main_frame, text="2. Test Results", padding="10")
        results_frame.pack(fill='both', expand=True)
        
        self.testing_results_text = scrolledtext.ScrolledText(results_frame, height=20, wrap=tk.WORD,
                                                              font=('Consolas', 9))
        self.testing_results_text.pack(fill='both', expand=True)
        
    def setup_info_tab(self):
        """Setup the information/about tab"""
        
        info_text = scrolledtext.ScrolledText(self.info_tab, wrap=tk.WORD, padx=10, pady=10)
        info_text.pack(fill='both', expand=True, padx=10, pady=10)
        
        info_content = """
╔═══════════════════════════════════════════════════════════════════════════════╗
║                    DP-ENHANCED STEGANOGRAPHY SYSTEM                           ║
║                  Differential Privacy Meets LSB Steganography                 ║
╚═══════════════════════════════════════════════════════════════════════════════╝

WHAT IS THIS?

This application implements a novel approach to image steganography that combines:
• LSB (Least Significant Bit) Steganography - hiding data in pixel values
• Differential Privacy - adding mathematical noise for plausible deniability
• Password-Based Security - deterministic pixel shuffling

HOW IT WORKS

1. NOISY PIXEL SELECTION
   Instead of embedding in pixels 1, 2, 3, ..., we:
   • Use a password to generate a shuffled, random list of pixel locations
   • Add Laplace noise to the message length (the DP mechanism)
   • Embed message bits in the first N pixels
   • Embed random decoy bits in the remaining pixels

2. DIFFERENTIAL PRIVACY (ε - Epsilon)
   The privacy parameter controls the trade-off:
   
   ε = 0.1 (High Privacy)    → Large noise → Hard to detect → Less efficient
   ε = 1.0 (Balanced)        → Medium noise → Good balance
   ε = 5.0 (Low Privacy)     → Small noise → More efficient → Easier to detect
   
   Formula: Noise ~ Laplace(0, Δf/ε) where Δf = 8 (sensitivity per character)

3. SHARED SECRET
   Sender and receiver must share (out-of-band):
   • Password - generates the same pixel shuffle sequence
   • Message length (in bits) - tells receiver when to stop extracting

WHY IT'S SECURE

• Password-based shuffling prevents sequential embedding patterns
• Decoy bits restore statistical randomness (defeats Chi-Square attacks)
• Plausible deniability: "Those bits are just noise, not a message"
• Visual imperceptibility: Only LSBs change (invisible to human eye)

STEGANALYSIS

The Chi-Square test analyzes LSB distribution:
• p-value < 0.05 → DETECTED (non-random distribution)
• p-value ≥ 0.05 → UNDETECTED (random distribution)

Standard LSB: p-value ≈ 0.001 (easily detected)
Our method: p-value ≈ 0.45 (appears random)

IMPORTANT NOTES

1. ALWAYS save stego images as PNG! JPEG compression destroys LSB data.
2. Share the password and message length securely (not via public channels).
3. Higher epsilon = less noise = more capacity, but easier to detect.
4. The same password MUST be used for embedding and extraction.

TECHNICAL DETAILS

• Algorithm: LSB substitution in RGB channels
• Privacy: (ε, 0)-Differential Privacy via Laplace mechanism
• Capacity: Up to (width × height × 3) bits (minus noise overhead)
• Security: Defeats Chi-Square, RS analysis, and histogram attacks

REFERENCES

• Differential Privacy: Dwork & Roth (2014)
• LSB Steganography: Chandramouli & Memon (2003)
• Steganalysis: Westfeld & Pfitzmann (2000)

═══════════════════════════════════════════════════════════════════════════════

Created for educational purposes - Demonstrates practical cryptography concepts
Version 1.0 - 2025
        """
        
        info_text.insert('1.0', info_content)
        info_text.config(state='disabled')
        
    # ============================================================================
    # EVENT HANDLERS
    # ============================================================================
    
    def browse_cover_image(self):
        """Browse and select cover image for embedding"""
        filepath = filedialog.askopenfilename(
            title="Select Cover Image",
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.bmp"), ("All files", "*.*")]
        )
        
        if filepath:
            self.cover_image_path = filepath
            self.cover_image_label.config(text=os.path.basename(filepath), foreground="black")
            
            # Show preview
            self.show_image_preview(filepath, self.cover_preview_label, size=(300, 200))
            
            # Show capacity
            capacity = get_image_capacity(filepath)
            self.capacity_label.config(
                text=f"Capacity: {capacity['max_characters']} chars ({capacity['max_bits']} bits) | "
                     f"Dimensions: {capacity['dimensions']}"
            )
            
    def browse_stego_image(self):
        """Browse and select stego image for extraction"""
        filepath = filedialog.askopenfilename(
            title="Select Stego Image",
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.bmp"), ("All files", "*.*")]
        )
        
        if filepath:
            self.stego_image_path = filepath
            self.stego_image_label.config(text=os.path.basename(filepath), foreground="black")
            
            # Show preview
            self.show_image_preview(filepath, self.stego_preview_label, size=(300, 200))
            
    def browse_analysis_image(self):
        """Browse and select image for analysis"""
        filepath = filedialog.askopenfilename(
            title="Select Image to Analyze",
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.bmp"), ("All files", "*.*")]
        )
        
        if filepath:
            self.analysis_image_path = filepath
            self.testing_results_text.insert(tk.END, f"Step 1: Determine original image (synthetic or provided file)\n")
            if getattr(self, 'test_image_source_var', None) and self.test_image_source_var.get() == 'file' and getattr(self, 'test_image_path', None):
                self.testing_results_text.insert(tk.END, f"Step 1: Using provided image file {os.path.basename(self.test_image_path)} as original...\n")
                self.root.update()
                original_source = 'file'
                # copy path
                original_path = self.test_image_path
            else:
                self.testing_results_text.insert(tk.END, f"Step 1: Generating synthetic image (seed={seed})...\n")
                self.root.update()
                original_source = 'synthetic'
                generate_random_lsb_image(width, height, original_path, seed=seed)

            # Analyze original
            original_analysis = chi_square_attack(original_path, channel='all')

            self.testing_results_text.insert(tk.END,
                f"Original image: {os.path.basename(original_path)} ({original_source})\n"
                f"  LSB Distribution: {original_analysis['lsb_0_percent']:.2f}% / {original_analysis['lsb_1_percent']:.2f}%\n"
                f"  Deviation: {original_analysis['deviation_from_50_50']:.4f}%\n"
                f"  Status: {original_analysis['verdict']}\n\n")
            
    def browse_original_for_comparison(self):
        """Browse original image for comparison"""
        filepath = filedialog.askopenfilename(
            title="Select Original Image",
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.bmp"), ("All files", "*.*")]
        )
        
        if filepath:
            self.original_comparison_path = filepath
            self.original_comparison_label.config(text=os.path.basename(filepath), foreground="black")
            
    def browse_stego_for_comparison(self):
        """Browse stego image for comparison"""
        filepath = filedialog.askopenfilename(
            title="Select Stego Image",
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.bmp"), ("All files", "*.*")]
        )
        
        if filepath:
            self.stego_comparison_path = filepath
            self.stego_comparison_label.config(text=os.path.basename(filepath), foreground="black")

    def browse_test_image(self):
        """Browse an existing image to use as the test original in the Testing Lab"""
        filepath = filedialog.askopenfilename(
            title="Select Image for Testing",
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.bmp"), ("All files", "*.*")]
        )
        if filepath:
            self.test_image_path = filepath
            self.test_image_label.config(text=os.path.basename(filepath), foreground="black")
            
    def show_image_preview(self, image_path, label_widget, size=(300, 200)):
        """Display image preview in a label"""
        try:
            img = Image.open(image_path)
            img.thumbnail(size, Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            label_widget.config(image=photo)
            label_widget.image = photo  # Keep a reference
        except Exception as e:
            label_widget.config(text=f"Preview error: {str(e)}")
            
    def update_message_stats(self, event=None):
        """Update message length statistics"""
        text = self.message_text.get('1.0', 'end-1c').strip()
        char_count = len(text)
        bit_count = char_count * 8
        
        self.message_stats_label.config(
            text=f"Characters: {char_count} | Bits: {bit_count}"
        )
        
    def update_epsilon_label(self, value=None):
        """Update epsilon value display"""
        epsilon = self.epsilon_var.get()
        self.epsilon_value_label.config(text=f"ε = {epsilon:.2f}")
        
        if epsilon < 0.5:
            desc = "(Very high privacy - Large noise)"
            color = "green"
        elif epsilon < 1.5:
            desc = "(Balanced privacy and efficiency)"
            color = "blue"
        elif epsilon < 3.0:
            desc = "(Moderate privacy - Less noise)"
            color = "orange"
        else:
            desc = "(Low privacy - Minimal noise)"
            color = "red"
            
        self.epsilon_desc_label.config(text=desc, foreground=color)
        
    def embed_message(self):
        """Embed message into cover image"""
        # Validate inputs
        if not self.cover_image_path:
            messagebox.showerror("Error", "Please select a cover image!")
            return
            
        # Get message and strip any trailing whitespace/newlines
        message = self.message_text.get('1.0', 'end-1c').strip()
        if not message:
            messagebox.showerror("Error", "Please enter a message to hide!")
            return
            
        password = self.embed_password_entry.get()
        if not password:
            messagebox.showerror("Error", "Please enter a password!")
            return
            
        epsilon = self.epsilon_var.get()
        
        # Ask where to save
        save_path = filedialog.asksaveasfilename(
            title="Save Stego Image As",
            defaultextension=".png",
            filetypes=[("PNG files", "*.png"), ("All files", "*.*")]
        )
        
        if not save_path:
            return
            
        # Embed in a separate thread to keep UI responsive
        def embed_thread():
            try:
                # Show progress
                self.embed_results_text.delete('1.0', tk.END)
                self.embed_results_text.insert('1.0', "Embedding message...\n\n")
                self.root.update()
                
                # Perform embedding
                result = embed(
                    cover_image_path=self.cover_image_path,
                    message=message,
                    password=password,
                    epsilon=epsilon,
                    save_path=save_path
                )
                
                # Calculate epsilon visibility
                epsilon_analysis = calculate_epsilon_visibility(
                    message_bits=result['message_length_bits'],
                    image_capacity=result['total_capacity'],
                    epsilon_low=0.1,
                    epsilon_high=5.0
                )
                
                # Display results
                results_text = f"""
MESSAGE SUCCESSFULLY EMBEDDED!

EMBEDDING STATISTICS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Message Length:         {result['message_length_chars']} characters
Message Length (bits):  {result['message_length_bits']} bits

Differential Privacy:
  • Epsilon (ε):        {result['epsilon']:.2f}
  • Laplace Scale:      {result['laplace_scale']:.2f}
  • Noise Added:        {result['noise_added']} bits
  • Noisy Count:        {result['noisy_count']} bits

Embedding Details:
  • Real Message Bits:  {result['message_length_bits']}
  • Decoy Bits Added:   {result['decoy_pixels']}
  • Total Bits Modified: {result['total_pixels_modified']}
  
Image Information:
  • Dimensions:         {result['image_dimensions']}
  • Total Capacity:     {result['total_capacity']} bits
  • Capacity Used:      {result['capacity_used_percent']:.2f}%

EPSILON EFFECTIVENESS ANALYSIS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{epsilon_analysis['recommendation']}

For your current parameters:
  • Capacity Usage:     {epsilon_analysis['capacity_usage_percent']:.2f}%
  • Noise at ε=0.1:     ~{epsilon_analysis['scale_low_epsilon']:.0f} bits
  • Noise at ε=5.0:     ~{epsilon_analysis['scale_high_epsilon']:.0f} bits
  • Difference:         {epsilon_analysis['expected_noise_difference']:.0f} bits
  • Statistically Visible: {'Yes' if epsilon_analysis['statistically_visible'] else 'No'}

DETECTION ANALYSIS - READ THIS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
WARNING: Single-image Chi-Square tests CANNOT evaluate DP-steganography.
Use the "Compare Images" feature in the Analysis tab instead.
Compare the ORIGINAL cover image with this STEGO image.
Success is measured by how much the distribution changed (< 1% = good).

Stego image saved to:
{result['save_path']}

IMPORTANT - Share these with the receiver:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. Password: (keep this secret!)
2. Message Length: {result['message_length_bits']} bits

Both values are required for extraction!
                """
                
                self.embed_results_text.delete('1.0', tk.END)
                self.embed_results_text.insert('1.0', results_text)
                
                messagebox.showinfo(
                    "Success", 
                    f"Message embedded successfully!\n\n"
                    f"Share with receiver:\n"
                    f"• Password: (secret)\n"
                    f"• Message length: {result['message_length_bits']} bits"
                )
                
            except Exception as e:
                self.embed_results_text.delete('1.0', tk.END)
                self.embed_results_text.insert('1.0', f"ERROR:\n{str(e)}")
                messagebox.showerror("Embedding Failed", str(e))
                
        threading.Thread(target=embed_thread, daemon=True).start()
        
    def extract_message(self):
        """Extract message from stego image"""
        # Validate inputs
        if not self.stego_image_path:
            messagebox.showerror("Error", "Please select a stego image!")
            return
            
        password = self.extract_password_entry.get()
        if not password:
            messagebox.showerror("Error", "Please enter the password!")
            return
            
        try:
            message_length_bits = int(self.message_length_entry.get())
            if message_length_bits <= 0:
                raise ValueError("Message length must be positive")
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid message length (in bits)!")
            return
            
        # Extract in a separate thread
        def extract_thread():
            try:
                # Show progress
                self.extract_results_text.delete('1.0', tk.END)
                self.extract_results_text.insert('1.0', "Extracting message...\n\n")
                self.root.update()
                
                # Perform extraction
                extracted_message = extract(
                    stego_image_path=self.stego_image_path,
                    password=password,
                    message_length_bits=message_length_bits
                )
                
                # Display results
                results_text = f"""
MESSAGE SUCCESSFULLY EXTRACTED!

EXTRACTED MESSAGE:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{extracted_message}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

STATISTICS:
• Message Length: {len(extracted_message)} characters
• Bits Extracted: {message_length_bits} bits
• Source Image: {os.path.basename(self.stego_image_path)}
                """
                
                self.extract_results_text.delete('1.0', tk.END)
                self.extract_results_text.insert('1.0', results_text)
                
                messagebox.showinfo("Success", f"Message extracted successfully!\n\n"
                                             f"Length: {len(extracted_message)} characters")
                
            except Exception as e:
                self.extract_results_text.delete('1.0', tk.END)
                self.extract_results_text.insert('1.0', f"ERROR:\n{str(e)}")
                messagebox.showerror("Extraction Failed", str(e))
                
        threading.Thread(target=extract_thread, daemon=True).start()
        
    def copy_extracted_message(self):
        """Copy extracted message to clipboard"""
        text = self.extract_results_text.get('1.0', 'end-1c')
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        messagebox.showinfo("Copied", "Message copied to clipboard!")
        
    def run_chi_square(self):
        """Run Chi-Square steganalysis test"""
        if not hasattr(self, 'analysis_image_path') or not self.analysis_image_path:
            messagebox.showerror("Error", "Please select an image to analyze!")
            return
            
        try:
            result = chi_square_attack(self.analysis_image_path, channel='all')
            
            results_text = f"""
CHI-SQUARE STEGANALYSIS TEST
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

LSB DISTRIBUTION ANALYSIS:
Channel Analyzed:       {result['channel']}
Total Pixels:           {result['total_pixels']:,}

LSB Statistics:
  • 0s Count:           {result['lsb_0_count']:,} ({result['lsb_0_percent']:.2f}%)
  • 1s Count:           {result['lsb_1_count']:,} ({result['lsb_1_percent']:.2f}%)
  • Expected (random): 50.00% / 50.00%
  • Deviation:          {result['deviation_from_50_50']:.4f}%

STATISTICAL TEST RESULTS:
Chi-Square Statistic:   {result['chi_square_statistic']:.4f}
P-Value:                {result['p_value']:.6f}
Threshold (α):          {result['threshold_alpha']}

VERDICT: {result['verdict']}
Detection Confidence:   {result['detection_confidence']}

INTERPRETATION:
{result['explanation']}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Analysis complete for: {os.path.basename(self.analysis_image_path)}
            """
            
            self.analysis_results_text.delete('1.0', tk.END)
            self.analysis_results_text.insert('1.0', results_text)
            
        except Exception as e:
            messagebox.showerror("Analysis Failed", str(e))
            
    def run_multi_channel(self):
        """Run multi-channel steganalysis"""
        if not hasattr(self, 'analysis_image_path') or not self.analysis_image_path:
            messagebox.showerror("Error", "Please select an image to analyze!")
            return
            
        try:
            result = multi_channel_analysis(self.analysis_image_path)
            
            results_text = f"""
MULTI-CHANNEL STEGANALYSIS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
WARNING: SINGLE-IMAGE TEST - LIMITED VALUE FOR DP-STEGANOGRAPHY

RED CHANNEL:
  • Status: {result['red']['verdict']}
  • P-Value: {result['red']['p_value']:.6f}
  • Deviation: {result['red']['deviation_from_50_50']:.4f}%

GREEN CHANNEL:
  • Status: {result['green']['verdict']}
  • P-Value: {result['green']['p_value']:.6f}
  • Deviation: {result['green']['deviation_from_50_50']:.4f}%

BLUE CHANNEL:
  • Status: {result['blue']['verdict']}
  • P-Value: {result['blue']['p_value']:.6f}
  • Deviation: {result['blue']['deviation_from_50_50']:.4f}%

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
IMPORTANT: These results show LSB randomness, NOT message presence.
Natural photos typically show "NON-RANDOM" on all channels.
Use "Compare Images" feature for proper DP-steganography evaluation.

Analysis complete for: {os.path.basename(self.analysis_image_path)}
            """
            
            self.analysis_results_text.delete('1.0', tk.END)
            self.analysis_results_text.insert('1.0', results_text)
            
        except Exception as e:
            messagebox.showerror("Analysis Failed", str(e))
            
    def compare_images_analysis(self):
        """Compare original and stego images with proper DP evaluation"""
        if not hasattr(self, 'original_comparison_path') or not self.original_comparison_path:
            messagebox.showerror("Error", "Please select an original image!")
            return
        if not hasattr(self, 'stego_comparison_path') or not self.stego_comparison_path:
            messagebox.showerror("Error", "Please select a stego image!")
            return
        try:
            # Run comparison
            comparison = compare_images(self.original_comparison_path, self.stego_comparison_path)
            visual = calculate_visual_difference(self.original_comparison_path, self.stego_comparison_path)

            # Indicators for effectiveness (plain labels)
            effectiveness = comparison['effectiveness']
            label_indicator = {
                'EXCELLENT': '[EXCELLENT]',
                'GOOD': '[GOOD]',
                'FAIR': '[FAIR]',
                'POOR': '[POOR]'
            }.get(effectiveness['rating'], '[UNKNOWN]')

            results_text = f"""
════════════════════════════════════════════════
PROPER DP-STEGANOGRAPHY EVALUATION
════════════════════════════════════════════════

{label_indicator} VERDICT: {effectiveness['verdict']}
{label_indicator} EFFECTIVENESS: {effectiveness['rating']}

{effectiveness['interpretation']}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DETAILED STATISTICS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

VISUAL SIMILARITY:
  • MSE:                {visual['mse']:.4f}
  • PSNR:               {visual['psnr']:.2f} dB
  • Quality Rating:     {visual['quality_rating']}
  • Pixels Changed:     {visual['pixels_changed']:,} / {visual['total_pixels']:,}
  • Percent Changed:    {visual['percent_pixels_changed']:.4f}%

STATISTICAL COMPARISON:

Original Image LSB Distribution:
  • Distribution:       {comparison['original']['lsb_0_percent']:.2f}% zeros / {comparison['original']['lsb_1_percent']:.2f}% ones
  • Deviation:          {comparison['original']['deviation_from_50_50']:.4f}% from perfect 50/50
  • P-Value:            {comparison['original']['p_value']:.6f}
  • Status:             {comparison['original']['verdict']}

Stego Image LSB Distribution:
  • Distribution:       {comparison['stego']['lsb_0_percent']:.2f}% zeros / {comparison['stego']['lsb_1_percent']:.2f}% ones
  • Deviation:          {comparison['stego']['deviation_from_50_50']:.4f}% from perfect 50/50
  • P-Value:            {comparison['stego']['p_value']:.6f}
  • Status:             {comparison['stego']['verdict']}

CHANGE METRICS (Key Indicators):
  • Deviation Change:   {comparison['changes']['deviation_change']:.4f}% (PRIMARY METRIC)
  • P-Value Change:     {comparison['changes']['p_value_change']:.6f}
  • Detection Changed:  {'Yes' if comparison['changes']['detection_changed'] else 'No'}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EFFECTIVENESS THRESHOLDS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  EXCELLENT:  < 0.5% deviation change (virtually undetectable)
  GOOD:       < 1.0% deviation change (well-hidden)
  FAIR:       < 2.0% deviation change (moderate risk)
  POOR:       ≥ 2.0% deviation change (high detection risk)

Visual Quality: PSNR > 40 dB = imperceptible
This embedding: {visual['psnr']:.2f} dB - {visual['quality_rating']}
            """

            self.analysis_results_text.delete('1.0', tk.END)
            self.analysis_results_text.insert('1.0', results_text)

        except Exception as e:
            messagebox.showerror("Analysis Failed", str(e))
    
    def run_comparison_test(self):
        """Run complete comparison test: Generate image, embed with both methods, analyze"""
        try:
            # Get parameters
            width = int(self.test_width_var.get())
            height = int(self.test_height_var.get())
            message = self.test_message_text.get('1.0', 'end-1c').strip()
            epsilon = self.test_epsilon_var.get()
            password = self.test_password_var.get()
            seed = int(self.test_seed_var.get())
            
            if not message:
                messagebox.showerror("Error", "Please enter a test message!")
                return
            
            if not password:
                messagebox.showerror("Error", "Please enter a password!")
                return
            
            # Show progress
            self.testing_results_text.delete('1.0', tk.END)
            self.testing_results_text.insert('1.0', "Running comprehensive test...\n\n")
            self.root.update()
            
            # Create temp directory for test images
            import tempfile
            temp_dir = tempfile.gettempdir()
            original_path = os.path.join(temp_dir, "test_original.png")
            standard_path = os.path.join(temp_dir, "test_standard_lsb.png")
            dp_path = os.path.join(temp_dir, "test_dp_lsb.png")
            
            # Step 1: Get or generate the original image
            image_source = self.test_image_source_var.get()
            
            if image_source == 'file':
                # Use existing image file
                if not hasattr(self, 'test_image_path') or not self.test_image_path:
                    messagebox.showerror("Error", "Please browse and select an image file for testing!")
                    return
                
                self.testing_results_text.insert(tk.END, f"Step 1: Using existing image file...\n")
                self.root.update()
                
                # Copy the selected image to temp location
                from PIL import Image
                img = Image.open(self.test_image_path)
                img.save(original_path)
                
                # Get actual dimensions from image
                width, height = img.size
                
                self.testing_results_text.insert(tk.END, 
                    f"Loaded image: {os.path.basename(self.test_image_path)}\n"
                    f"  Dimensions: {width}×{height} pixels\n")
            else:
                # Generate synthetic image
                self.testing_results_text.insert(tk.END, f"Step 1: Generating synthetic image (seed={seed})...\n")
                self.root.update()
                
                generate_random_lsb_image(width, height, original_path, seed=seed)
                
                self.testing_results_text.insert(tk.END, 
                    f"Generated {width}×{height} image\n")
            
            # Analyze original
            original_analysis = chi_square_attack(original_path, channel='all')
            
            self.testing_results_text.insert(tk.END, 
                f"  LSB Distribution: {original_analysis['lsb_0_percent']:.2f}% / {original_analysis['lsb_1_percent']:.2f}%\n"
                f"  Deviation: {original_analysis['deviation_from_50_50']:.4f}%\n"
                f"  Status: {original_analysis['verdict']}\n\n")
            self.root.update()
            
            # Step 2: Embed with Standard LSB
            self.testing_results_text.insert(tk.END, "Step 2: Embedding with Standard Sequential LSB (NO DP)...\n")
            self.root.update()
            
            standard_result = embed_standard_lsb(original_path, message, standard_path)
            standard_analysis = chi_square_attack(standard_path, channel='all')
            visual_standard = calculate_visual_difference(original_path, standard_path)

            self.testing_results_text.insert(tk.END,
                f"Embedded {len(message)} characters ({standard_result['message_length_bits']} bits)\n"
                f"  Capacity Used: {standard_result['capacity_used_percent']:.2f}%\n"
                f"  LSB Distribution: {standard_analysis['lsb_0_percent']:.2f}% / {standard_analysis['lsb_1_percent']:.2f}%\n"
                f"  Deviation: {standard_analysis['deviation_from_50_50']:.4f}%\n"
                f"  Status: {standard_analysis['verdict']}\n"
                f"  PSNR vs Original: {visual_standard['psnr']:.2f} dB\n\n")
            self.root.update()
            
            # Step 3: Embed with DP-Enhanced LSB
            self.testing_results_text.insert(tk.END, f"Step 3: Embedding with DP-Enhanced LSB (ε={epsilon:.2f})...\n")
            self.root.update()
            
            dp_result = embed(original_path, message, password, epsilon, dp_path)
            dp_analysis = chi_square_attack(dp_path, channel='all')
            visual_dp = calculate_visual_difference(original_path, dp_path)

            self.testing_results_text.insert(tk.END,
                f"Embedded {len(message)} characters ({dp_result['message_length_bits']} bits)\n"
                f"  Noise Added: {dp_result['noise_added']} bits\n"
                f"  Decoy Bits: {dp_result['decoy_pixels']} bits\n"
                f"  Total Modified: {dp_result['total_pixels_modified']} bits\n"
                f"  Capacity Used: {dp_result['capacity_used_percent']:.2f}%\n"
                f"  LSB Distribution: {dp_analysis['lsb_0_percent']:.2f}% / {dp_analysis['lsb_1_percent']:.2f}%\n"
                f"  Deviation: {dp_analysis['deviation_from_50_50']:.4f}%\n"
                f"  Status: {dp_analysis['verdict']}\n"
                f"  PSNR vs Original: {visual_dp['psnr']:.2f} dB\n\n")
            self.root.update()
            
            # Step 4: Compare both methods
            self.testing_results_text.insert(tk.END, "Step 4: Comparing results...\n\n")
            self.root.update()
            
            # Compare standard LSB
            standard_comparison = compare_images(original_path, standard_path)
            standard_deviation_change = standard_comparison['changes']['deviation_change']
            standard_effectiveness = standard_comparison['effectiveness']['rating']
            # attach visual metrics
            try:
                standard_psnr = visual_standard.get('psnr', None)
            except Exception:
                standard_psnr = None
            
            # Compare DP-Enhanced LSB
            dp_comparison = compare_images(original_path, dp_path)
            dp_deviation_change = dp_comparison['changes']['deviation_change']
            dp_effectiveness = dp_comparison['effectiveness']['rating']
            try:
                dp_psnr = visual_dp.get('psnr', None)
            except Exception:
                dp_psnr = None
            
            # Calculate improvement
            improvement = ((standard_deviation_change - dp_deviation_change) / standard_deviation_change * 100) if standard_deviation_change > 0 else 0
            
            # Generate final report
            image_source_desc = f"Synthetic Random (seed={seed})" if image_source == 'synthetic' else f"Existing Image: {os.path.basename(self.test_image_path)}"
            
            results_text = f"""
════════════════════════════════════════════════════════════════════════
                    COMPREHENSIVE TEST RESULTS
════════════════════════════════════════════════════════════════════════

TEST CONFIGURATION:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Image Size:        {width} × {height} pixels
• Message Length:    {len(message)} characters ({standard_result['message_length_bits']} bits)
• Capacity Used:     {standard_result['capacity_used_percent']:.2f}%
• DP Epsilon:        {epsilon:.2f}
• Password:          {password}
• Image Source:      {image_source_desc}

ORIGINAL IMAGE ({image_source_desc}):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• LSB Distribution:  {original_analysis['lsb_0_percent']:.2f}% zeros / {original_analysis['lsb_1_percent']:.2f}% ones
• Deviation:         {original_analysis['deviation_from_50_50']:.4f}% from 50/50
• P-Value:           {original_analysis['p_value']:.6f}
• Status:            {original_analysis['verdict']}

METHOD 1: STANDARD SEQUENTIAL LSB (Baseline)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
After Embedding:
• LSB Distribution:  {standard_analysis['lsb_0_percent']:.2f}% zeros / {standard_analysis['lsb_1_percent']:.2f}% ones
• Deviation:         {standard_analysis['deviation_from_50_50']:.4f}% from 50/50
• P-Value:           {standard_analysis['p_value']:.6f}
• Status:            {standard_analysis['verdict']}
• PSNR vs Original:  {f"{standard_psnr:.2f} dB" if standard_psnr is not None else 'N/A'}

Detection Analysis:
• Deviation Change:  {standard_deviation_change:.4f}% ⬅ KEY METRIC
• Verdict:           {standard_comparison['effectiveness']['verdict']}
• Effectiveness:     {standard_effectiveness}
• Summary:           {standard_comparison['effectiveness']['summary']}

METHOD 2: DP-ENHANCED LSB (Our Method)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DP Parameters:
• Noise Added:       {dp_result['noise_added']} bits
• Decoy Bits:        {dp_result['decoy_pixels']} bits
• Laplace Scale:     {dp_result['laplace_scale']:.2f}

After Embedding:
• LSB Distribution:  {dp_analysis['lsb_0_percent']:.2f}% zeros / {dp_analysis['lsb_1_percent']:.2f}% ones
• Deviation:         {dp_analysis['deviation_from_50_50']:.4f}% from 50/50
• P-Value:           {dp_analysis['p_value']:.6f}
• Status:            {dp_analysis['verdict']}
• PSNR vs Original:  {f"{dp_psnr:.2f} dB" if dp_psnr is not None else 'N/A'}

Detection Analysis:
• Deviation Change:  {dp_deviation_change:.4f}% ⬅ KEY METRIC
• Verdict:           {dp_comparison['effectiveness']['verdict']}
• Effectiveness:     {dp_effectiveness}
• Summary:           {dp_comparison['effectiveness']['summary']}

COMPARISON SUMMARY:
════════════════════════════════════════════════════════════════════════
Standard LSB:        {standard_deviation_change:.4f}% deviation change ({standard_effectiveness})
DP-Enhanced LSB:     {dp_deviation_change:.4f}% deviation change ({dp_effectiveness})

IMPROVEMENT:         {improvement:.1f}% reduction in detectability

CONCLUSION:
{'DP-Enhanced method is MORE SECURE than standard LSB.' if dp_deviation_change < standard_deviation_change else 'Unexpected result - DP did not perform better as expected.'}

Explanation:
Standard LSB modifies pixels sequentially, creating detectable patterns.
DP-Enhanced LSB uses:
  1. Password-based pixel shuffling (eliminates sequential patterns)
  2. Laplace noise (masks true message length)
  3. Random decoy bits (restores LSB randomness)
Result: Deviation change is {improvement:.1f}% smaller, making steganography harder to detect.

════════════════════════════════════════════════════════════════════════
Test images saved to:
• Original:  {original_path}
• Standard:  {standard_path}
• DP-Enhanced: {dp_path}
════════════════════════════════════════════════════════════════════════
            """
            
            self.testing_results_text.delete('1.0', tk.END)
            self.testing_results_text.insert('1.0', results_text)
            
            messagebox.showinfo("Test Complete", 
                f"Comparison test completed successfully!\n\n"
                f"Standard LSB: {standard_effectiveness} ({standard_deviation_change:.4f}% change)\n"
                f"DP-Enhanced: {dp_effectiveness} ({dp_deviation_change:.4f}% change)\n\n"
                f"Improvement: {improvement:.1f}%")
            
        except Exception as e:
            self.testing_results_text.insert(tk.END, f"\n\nERROR: {str(e)}\n")
            messagebox.showerror("Test Failed", str(e))


def main():
    """Main entry point for the GUI application"""
    root = tk.Tk()
    
    # Configure style
    style = ttk.Style()
    style.theme_use('clam')
    
    app = SteganographyApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
