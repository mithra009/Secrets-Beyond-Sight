"""
Steganalysis Module
Implements Chi-Square statistical attack to detect hidden messages
"""

import numpy as np
from PIL import Image
from scipy.stats import chisquare


def chi_square_attack(image_path: str, channel: str = 'red') -> dict:
    """
    Perform Chi-Square statistical test on image LSBs to detect steganography.
    
    IMPORTANT LIMITATION:
    This test analyzes the ENTIRE image's LSB distribution. If the original cover
    image already has non-random LSBs (common in natural photos), this test will
    show "DETECTED" even without any hidden message.
    
    For DP-enhanced steganography, you should:
    1. Compare the ORIGINAL vs STEGO image (use compare_images function)
    2. Check if the p-value CHANGED significantly
    3. A proper test requires the original cover image for comparison
    
    Theory:
    - In a truly random image, LSBs should be 50% 0s and 50% 1s
    - Natural photos often have biased LSBs (e.g., 53% vs 47%)
    - When a message is embedded, it changes this distribution
    - Low p-value (< 0.05) = Non-random distribution detected
    - High p-value (>= 0.05) = Random-looking distribution
    
    Args:
        image_path (str): Path to the image to analyze
        channel (str): Which color channel to test ('red', 'green', 'blue', or 'all')
        
    Returns:
        dict: Analysis results including chi-square statistic, p-value, and verdict
    """
    # Load image and convert to RGB
    img = Image.open(image_path).convert("RGB")
    img_array = np.array(img)
    
    # Select channel to analyze
    if channel.lower() == 'red':
        channel_data = img_array[:, :, 0].flatten()
        channel_name = "Red"
    elif channel.lower() == 'green':
        channel_data = img_array[:, :, 1].flatten()
        channel_name = "Green"
    elif channel.lower() == 'blue':
        channel_data = img_array[:, :, 2].flatten()
        channel_name = "Blue"
    elif channel.lower() == 'all':
        # Analyze all channels combined
        channel_data = img_array.flatten()
        channel_name = "All (RGB)"
    else:
        raise ValueError("Channel must be 'red', 'green', 'blue', or 'all'")
    
    # Extract LSBs (least significant bits)
    lsbs = channel_data & 1  # Bitwise AND with 1 extracts the LSB
    
    # Count 0s and 1s
    count_0 = np.sum(lsbs == 0)
    count_1 = np.sum(lsbs == 1)
    
    observed_freq = np.array([count_0, count_1])
    
    # Expected frequencies for a perfectly random distribution (50/50)
    total = len(lsbs)
    expected_freq = np.array([total / 2, total / 2])
    
    # Perform Chi-Square test
    # chi2_stat measures the magnitude of difference
    # p_value tells us the probability of seeing this difference by chance
    chi2_stat, p_value = chisquare(f_obs=observed_freq, f_exp=expected_freq)
    
    # Calculate percentage deviation from perfect 50/50
    expected_percent = 50.0
    actual_percent_0 = (count_0 / total) * 100
    actual_percent_1 = (count_1 / total) * 100
    deviation = abs(actual_percent_0 - expected_percent)
    
    # Determine verdict with proper terminology
    # Standard threshold: p < 0.05 means "statistically significant difference"
    alpha = 0.05
    if p_value < alpha:
        verdict = "NON-RANDOM LSB DISTRIBUTION"
        confidence = "High"
        explanation = (
            f"LSB distribution deviates {deviation:.2f}% from perfect randomness (50/50). "
            f"Current distribution: {actual_percent_0:.2f}% zeros / {actual_percent_1:.2f}% ones. "
            "\n\nWARNING: This result is NORMAL for natural photographs. "
            "Real photos almost always have biased LSB distributions due to camera sensors, "
            "compression artifacts, and scene characteristics. "
            "\n\nNOTE: This test CANNOT determine if a hidden message exists. "
            "\nNote: To properly evaluate DP-steganography, use the 'Compare Images' feature "
            "to analyze how much the distribution changed from original to stego image."
        )
    else:
        verdict = "RANDOM-LOOKING LSB DISTRIBUTION"
        confidence = "Low" if p_value < 0.2 else "Very Low"
        explanation = (
            f"LSB distribution is close to random (50/50), with only {deviation:.2f}% deviation. "
            f"Current distribution: {actual_percent_0:.2f}% zeros / {actual_percent_1:.2f}% ones. "
            "\n\nIMPORTANT: This result is RARE for natural photographs. "
            "This suggests either: (1) synthetic/noise image, (2) previous randomization, "
            "or (3) extremely uniform scene. "
            "\n\nNOTE: This test STILL CANNOT determine if a message exists. "
            "\nNote: Use 'Compare Images' for proper steganographic analysis."
        )
    
    return {
        'channel': channel_name,
        'total_pixels': total,
        'lsb_0_count': int(count_0),
        'lsb_1_count': int(count_1),
        'lsb_0_percent': actual_percent_0,
        'lsb_1_percent': actual_percent_1,
        'deviation_from_50_50': deviation,
        'chi_square_statistic': chi2_stat,
        'p_value': p_value,
        'verdict': verdict,
        'detection_confidence': confidence,
        'explanation': explanation,
        'threshold_alpha': alpha
    }


def compare_images(original_path: str, stego_path: str) -> dict:
    """
    Compare LSB statistics between original and stego images.
    
    NOTE: This is the proper test for DP-ENHANCED steganography.
    
    Single-image tests are invalid because:
    - Natural photos always have biased LSBs (show "DETECTED")
    - We can't distinguish "natural bias" from "message bias"
    
    The correct approach:
    - Compare ORIGINAL vs STEGO to measure the CHANGE in distribution
    - Small change (< 1%) = DP is working effectively
    - Large change (> 2%) = Steganography may be detectable
    
    Args:
        original_path (str): Path to original cover image
        stego_path (str): Path to stego image with hidden message
        
    Returns:
        dict: Comparison results with proper DP effectiveness evaluation
    """
    # Run Chi-Square test on both images
    original_result = chi_square_attack(original_path, channel='all')
    stego_result = chi_square_attack(stego_path, channel='all')
    
    # Calculate changes
    p_value_change = stego_result['p_value'] - original_result['p_value']
    deviation_change = abs(stego_result['deviation_from_50_50'] - original_result['deviation_from_50_50'])
    
    # Determine effectiveness with proper thresholds
    if deviation_change < 0.5:
        effectiveness = "EXCELLENT"
        color_code = "green"
        dp_verdict = "STEGANOGRAPHY UNDETECTABLE"
        summary = (
            f"Deviation changed by only {deviation_change:.3f}% - virtually undetectable! "
            "The DP mechanism successfully masked the message embedding."
        )
    elif deviation_change < 1.0:
        effectiveness = "GOOD"
        color_code = "lightgreen"
        dp_verdict = "STEGANOGRAPHY MOSTLY UNDETECTABLE"
        summary = (
            f"Deviation changed by {deviation_change:.3f}% - good concealment. "
            "The embedding is well-hidden but not perfect."
        )
    elif deviation_change < 2.0:
        effectiveness = "FAIR"
        color_code = "yellow"
        dp_verdict = "STEGANOGRAPHY POSSIBLY DETECTABLE"
        summary = (
            f"Deviation changed by {deviation_change:.3f}% - moderate risk. "
            "The embedding caused noticeable statistical change."
        )
    else:
        effectiveness = "POOR"
        color_code = "red"
        dp_verdict = "STEGANOGRAPHY DETECTABLE"
        summary = (
            f"Deviation changed by {deviation_change:.3f}% - high risk of detection! "
            "Consider: longer message to use more capacity, or adjust epsilon value."
        )
    
    # Explain why both might show "NON-RANDOM"
    interpretation = (
        "\n━━━ INTERPRETATION GUIDE ━━━\n\n"
        f"Original Image: {original_result['verdict']}\n"
        f"  └─ Deviation: {original_result['deviation_from_50_50']:.2f}% from perfect randomness\n"
        f"  └─ This is NORMAL for natural photographs!\n\n"
        f"Stego Image: {stego_result['verdict']}\n"
        f"  └─ Deviation: {stego_result['deviation_from_50_50']:.2f}% from perfect randomness\n\n"
        f"Change in Deviation: {deviation_change:.3f}%\n"
        f"  └─ This is the KEY metric!\n"
        f"  └─ Small change = Good DP protection\n"
        f"  └─ Large change = Detectable steganography\n\n"
        f"VERDICT: {dp_verdict}\n"
        f"EFFECTIVENESS: {effectiveness}\n"
        f"REASON: {summary}"
    )
    
    return {
        'original': original_result,
        'stego': stego_result,
        'changes': {
            'p_value_change': p_value_change,
            'p_value_change_percent': (p_value_change / original_result['p_value']) * 100 if original_result['p_value'] > 0 else 0,
            'deviation_change': deviation_change,
            'original_deviation': original_result['deviation_from_50_50'],
            'stego_deviation': stego_result['deviation_from_50_50'],
            'detection_changed': original_result['verdict'] != stego_result['verdict'],
        },
        'effectiveness': {
            'rating': effectiveness,
            'color': color_code,
            'verdict': dp_verdict,
            'summary': summary,
            'interpretation': interpretation
        }
    }


def multi_channel_analysis(image_path: str) -> dict:
    """
    Perform Chi-Square analysis on all color channels separately.
    
    Sometimes steganography is only applied to one channel. This test
    checks each channel independently to catch such cases.
    
    Args:
        image_path (str): Path to the image to analyze
        
    Returns:
        dict: Results for each channel
    """
    results = {}
    
    for channel in ['red', 'green', 'blue']:
        results[channel] = chi_square_attack(image_path, channel=channel)
    
    # Overall verdict: DETECTED if any channel is detected
    any_detected = any(r['verdict'] == 'DETECTED' for r in results.values())
    
    results['overall_verdict'] = 'DETECTED' if any_detected else 'UNDETECTED'
    results['channels_detected'] = [
        ch for ch, r in results.items() 
        if ch != 'overall_verdict' and r['verdict'] == 'DETECTED'
    ]
    
    return results


def calculate_visual_difference(original_path: str, stego_path: str) -> dict:
    """
    Calculate visual similarity metrics between original and stego images.
    
    LSB steganography should produce imperceptible changes. This function
    quantifies how visually similar the images are.
    
    Args:
        original_path (str): Path to original image
        stego_path (str): Path to stego image
        
    Returns:
        dict: Visual difference metrics including MSE and PSNR
    """
    # Load images
    orig_img = np.array(Image.open(original_path).convert("RGB"))
    stego_img = np.array(Image.open(stego_path).convert("RGB"))
    
    # Ensure same dimensions
    if orig_img.shape != stego_img.shape:
        raise ValueError("Images must have the same dimensions")
    
    # Calculate Mean Squared Error (MSE)
    mse = np.mean((orig_img.astype(float) - stego_img.astype(float)) ** 2)
    
    # Calculate Peak Signal-to-Noise Ratio (PSNR)
    # Higher PSNR = better quality (less difference)
    # PSNR > 40 dB is considered excellent (imperceptible)
    if mse == 0:
        psnr = float('inf')
    else:
        max_pixel = 255.0
        psnr = 20 * np.log10(max_pixel / np.sqrt(mse))
    
    # Calculate percentage of pixels changed
    pixels_changed = np.sum(orig_img != stego_img)
    total_pixels = orig_img.size
    percent_changed = (pixels_changed / total_pixels) * 100
    
    # Interpret results
    if psnr == float('inf'):
        quality = "Identical (no changes)"
    elif psnr > 40:
        quality = "Excellent (imperceptible changes)"
    elif psnr > 30:
        quality = "Good (barely perceptible)"
    elif psnr > 20:
        quality = "Fair (noticeable if inspected)"
    else:
        quality = "Poor (visibly different)"
    
    return {
        'mse': mse,
        'psnr': psnr,
        'quality_rating': quality,
        'pixels_changed': int(pixels_changed),
        'total_pixels': int(total_pixels),
        'percent_pixels_changed': percent_changed
    }


def generate_random_lsb_image(width: int = 512, height: int = 512, save_path: str = None, seed: int = None) -> str:
    """
    Generate a synthetic test image with truly random LSBs (50/50 distribution).
    
    This creates an ideal baseline for testing steganalysis tools. Natural photos
    never have perfectly random LSBs, so this synthetic image helps validate
    that the Chi-Square test can detect the difference.
    
    Method:
    - Generate random pixel values (0-255) for RGB channels
    - This naturally produces ~50/50 LSB distribution due to randomness
    - Use seed for reproducibility (same seed = same image)
    
    Args:
        width (int): Image width in pixels
        height (int): Image height in pixels
        save_path (str): Where to save the image (optional)
        seed (int): Random seed for reproducibility (optional, default: 42)
        
    Returns:
        str: Path to the saved image (or None if not saved)
    """
    # Set seed for reproducibility
    if seed is None:
        seed = 42  # Default seed for consistent results
    
    np.random.seed(seed)
    
    # Generate random noise for each RGB channel
    random_array = np.random.randint(0, 256, (height, width, 3), dtype=np.uint8)
    
    # Create image
    img = Image.fromarray(random_array, 'RGB')
    
    # Save if path provided
    if save_path:
        if not save_path.lower().endswith('.png'):
            save_path = save_path.rsplit('.', 1)[0] + '.png'
        img.save(save_path, "PNG")
        return save_path
    
    return None


def calculate_epsilon_visibility(message_bits: int, image_capacity: int, epsilon_low: float, epsilon_high: float) -> dict:
    """
    Calculate when epsilon differences become statistically visible.
    
    The effect of epsilon depends on:
    - Message size relative to image capacity
    - The scale of Laplace noise (Δf/ε)
    - Statistical power to detect the difference
    
    Args:
        message_bits (int): Number of bits in the message
        image_capacity (int): Total bit capacity of image
        epsilon_low (float): Lower epsilon value (e.g., 0.1)
        epsilon_high (float): Higher epsilon value (e.g., 5.0)
        
    Returns:
        dict: Analysis of epsilon visibility
    """
    # Sensitivity for bit count (Δf = 8 in our implementation)
    sensitivity = 8
    
    # Calculate Laplace scales
    scale_low = sensitivity / max(0.01, epsilon_low)
    scale_high = sensitivity / max(0.01, epsilon_high)
    
    # Expected noise magnitude (mean absolute deviation of Laplace = scale)
    expected_noise_low = scale_low
    expected_noise_high = scale_high
    noise_difference = abs(expected_noise_low - expected_noise_high)
    
    # Calculate capacity usage
    capacity_percent = (message_bits / image_capacity) * 100
    
    # Determine if difference is visible
    # Rule of thumb: Need at least 5% capacity AND 10+ bits noise difference
    visible = capacity_percent >= 5 and noise_difference >= 10
    
    recommendation = ""
    if visible:
        recommendation = (
            f"Epsilon effects WILL be visible in statistical tests. "
            f"Noise difference of {noise_difference:.1f} bits with {capacity_percent:.1f}% capacity usage."
        )
    elif capacity_percent < 5:
        recommendation = (
            f"Epsilon effects NOT visible - capacity usage too low ({capacity_percent:.1f}%). "
            f"Need at least 5% capacity usage. Current message uses {message_bits} bits, "
            f"try reducing image size or increasing message length."
        )
    else:
        recommendation = (
            f"Epsilon effects MARGINAL - noise difference only {noise_difference:.1f} bits. "
            f"May not be detectable in Chi-Square test. Consider extreme epsilon values "
            f"(e.g., 0.05 vs 10.0) for demonstration."
        )
    
    return {
        'scale_low_epsilon': scale_low,
        'scale_high_epsilon': scale_high,
        'expected_noise_difference': noise_difference,
        'capacity_usage_percent': capacity_percent,
        'statistically_visible': visible,
        'recommendation': recommendation
    }
