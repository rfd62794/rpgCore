"""
Rust-Powered Sprite Scanner - Python 3.12 Compatible
High-performance semantic scanning without PyO3 build complexity
"""

import ctypes
from typing import Tuple, Optional
from pathlib import Path
from loguru import logger
import subprocess
import sys

# Load the compiled Rust library
try:
    # Try to load the compiled Rust module
    if sys.platform.startswith('win'):
        lib_path = Path(__file__).parent / "maturin" / "dgt_harvest_rust.dll"
    else:
        lib_path = Path(__file__).parent / "libdgt_harvest_rust.so"
    
    if lib_path.exists():
        rust_lib = ctypes.CDLL(str(lib_path))
        logger.success(f"🦀 Loaded Rust harvest core from {lib_path}")
    else:
        logger.warning("⚠️ Rust harvest core not found, falling back to Python implementation")
        rust_lib = None
except Exception as e:
    logger.error(f"⚠️ Failed to load Rust library: {e}")
    rust_lib = None


class RustSpriteScanner:
    """
    High-performance sprite scanner using Rust when available,
    falling back to Python implementation
    """
    
    def __init__(self, chest_threshold: float = 0.3, green_threshold: float = 0.2, 
                 gray_threshold: float = 0.3, diversity_threshold: float = 0.05):
        self.chest_threshold = chest_threshold
        self.green_threshold = green_threshold
        self.gray_threshold = gray_threshold
        self.diversity_threshold = diversity_threshold
        self.use_rust = rust_lib is not None
        
        if self.use_rust:
            logger.info("🚀 Using Rust-powered sprite scanner")
        else:
            logger.info("🐍 Using Python fallback scanner")
    
    def analyze_sprite(self, pixels: bytes, width: int, height: int) -> dict:
        """
        Analyze sprite for semantic properties
        Returns analysis results as a dictionary
        """
        if self.use_rust and rust_lib:
            return self._analyze_with_rust(pixels, width, height)
        else:
            return self._analyze_with_python(pixels, width, height)
    
    def _analyze_with_rust(self, pixels: bytes, width: int, height: int) -> dict:
        """Use Rust implementation for maximum performance"""
        try:
            # Define Rust function signature
            scan_function = rust_lib.scan_sprite_for_chest
            scan_function.argtypes = [ctypes.c_char_p, ctypes.c_uint, ctypes.c_uint]
            scan_function.restype = ctypes.c_double
            
            # Convert pixels to bytes
            pixels_ptr = ctypes.create_string_buffer(pixels)
            
            # Call Rust function
            chest_prob = scan_function(pixels_ptr, width, height)
            
            # Additional analysis with Python fallback for now
            analysis = self._analyze_with_python(pixels, width, height)
            analysis['chest_probability'] = chest_prob
            analysis['is_chest'] = chest_prob > self.chest_threshold
            
            return analysis
            
        except Exception as e:
            logger.error(f"⚠️ Rust analysis failed: {e}, falling back to Python")
            return self._analyze_with_python(pixels, width, height)
    
    def _analyze_with_python(self, pixels: bytes, width: int, height: int) -> dict:
        """Python fallback implementation"""
        brown_gold_pixels = 0
        green_pixels = 0
        gray_pixels = 0
        total_pixels = 0
        min_x, min_y = width, height
        max_x, max_y = 0, 0
        
        colors = set()
        
        # Process pixels in chunks of 4 (RGBA)
        for i in range(0, len(pixels), 4):
            if i + 3 >= len(pixels):
                break
                
            x = (i // 4) % width
            y = (i // 4) // width
            
            r = pixels[i]
            g = pixels[i + 1]
            b = pixels[i + 2]
            a = pixels[i + 3]
            
            if a > 0:  # Non-transparent pixel
                total_pixels += 1
                
                # Track content bounds
                min_x = min(min_x, x)
                min_y = min(min_y, y)
                max_x = max(max_x, x)
                max_y = max(max_y, y)
                
                # Track color diversity
                colors.add((r, g, b))
                
                # Chest detection (extended brown/gold ranges)
                if (80 <= r <= 180 and 40 <= g <= 140 and b <= 80) or \
                   (160 <= r <= 255 and 100 <= g <= 200 and b <= 100) or \
                   (200 <= r <= 255 and 180 <= g <= 220 and b <= 100):
                    brown_gold_pixels += 1
                
                # Plant detection
                if g > r and g > b:
                    green_pixels += 1
                
                # Rock detection
                if abs(r - g) < 40 and abs(g - b) < 40:
                    gray_pixels += 1
        
        total_pixels_f = total_pixels if total_pixels > 0 else 1
        chest_probability = brown_gold_pixels / total_pixels_f
        green_ratio = green_pixels / total_pixels_f
        gray_ratio = gray_pixels / total_pixels_f
        color_diversity = len(colors) / total_pixels_f
        
        # Character detection
        aspect_ratio = width / height if height > 0 else 1.0
        is_character = (total_pixels > 20 and 
                          0.5 <= aspect_ratio <= 2.0 and 
                          len(colors) > 3)
        
        # Decoration detection
        is_decoration = (color_diversity > 0.05 or 
                         green_ratio > 0.2 or 
                         gray_ratio > 0.3)
        
        # Material detection
        is_material = color_diversity < 0.1
        
        return {
            'chest_probability': chest_probability,
            'is_chest': chest_probability > self.chest_threshold,
            'content_bounds': (min_x, min_y, max_x, max_y),
            'color_diversity': color_diversity,
            'green_ratio': green_ratio,
            'gray_ratio': gray_ratio,
            'brown_gold_ratio': chest_probability,
            'is_character': is_character,
            'is_decoration': is_decoration,
            'is_material': is_material,
        }
    
    def auto_clean_edges(self, pixels: bytes, width: int, height: int, threshold: int = 2) -> bytes:
        """Auto-clean sprite edges"""
        if self.use_rust and rust_lib:
            try:
                # Define Rust function signature
                clean_function = rust_lib.clean_sprite_edges
                clean_function.argtypes = [ctypes.c_char_p, ctypes.c_uint, ctypes.c_uint, ctypes.c_uint]
                clean_function.restype = ctypes.POINTER(ctypes.c_char)
                
                # Convert pixels to bytes
                pixels_ptr = ctypes.create_string_buffer(pixels)
                
                # Call Rust function
                result_ptr = clean_function(pixels_ptr, width, height, threshold)
                
                # Convert result back to Python bytes
                result_size = width * height * 4
                result = ctypes.string_at(result_ptr, result_size)
                
                return result
                
            except Exception as e:
                logger.error(f"⚠️ Rust edge cleaning failed: {e}, falling back to Python")
        
        # Python fallback
        return self._clean_edges_with_python(pixels, width, height, threshold)
    
    def _clean_edges_with_python(self, pixels: bytes, width: int, height: int, threshold: int) -> bytes:
        """Python fallback edge cleaning"""
        # Convert to list for modification
        pixel_list = list(pixels)
        
        # Find content bounds
        min_x, min_y = width, height
        max_x, max_y = 0, 0
        
        for i in range(0, len(pixels), 4):
            if i + 3 >= len(pixels):
                break
                
            x = (i // 4) % width
            y = (i // 4) // width
            
            if pixels[i + 3] > 0:  # Non-transparent
                min_x = min(min_x, x)
                min_y = min(min_y, y)
                max_x = max(max_x, x)
                max_y = max(max_y, y)
        
        # Apply threshold padding
        min_x = max(0, min_x - threshold)
        min_y = max(0, min_y - threshold)
        max_x = min(width - 1, max_x + threshold)
        max_y = min(height - 1, max_y + threshold)
        
        # Clear pixels outside content bounds
        for y in range(height):
            for x in range(width):
                if x < min_x or x > max_x or y < min_y or y > max_y:
                    idx = (y * width + x) * 4
                    if idx + 3 < len(pixel_list):
                        pixel_list[idx] = 0     # R
                        pixel_list[idx + 1] = 0 # G
                        pixel_list[idx + 2] = 0 # B
                        pixel_list[idx + 3] = 0 # A
        
        return bytes(pixel_list)


# Convenience functions for direct use
def scan_sprite_for_chest(pixels: bytes, width: int, height: int) -> float:
    """Quick chest detection function"""
    scanner = RustSpriteScanner()
    analysis = scanner.analyze_sprite(pixels, width, height)
    return analysis['chest_probability']


def clean_sprite_edges(pixels: bytes, width: int, height: int, threshold: int = 2) -> bytes:
    """Quick edge cleaning function"""
    scanner = RustSpriteScanner()
    return scanner.auto_clean_edges(pixels, width, height, threshold)


if __name__ == "__main__":
    # Test the scanner
    print("🔧 Testing Rust-Powered Sprite Scanner")
    
    # Create test data (16x16 RGBA)
    test_pixels = bytes([100, 50, 30, 255] * 256)  # Brown pixels
    
    scanner = RustSpriteScanner()
    analysis = scanner.analyze_sprite(test_pixels, 16, 16)
    
    print(f"📊 Analysis Results:")
    print(f"  Chest Probability: {analysis['chest_probability']:.3f}")
    print(f"  Is Chest: {analysis['is_chest']}")
    print(f"  Content Bounds: {analysis['content_bounds']}")
    print(f"  Color Diversity: {analysis['color_diversity']:.3f}")
    print(f"  Green Ratio: {analysis['green_ratio']:.3f}")
    print(f"  Gray Ratio: {analysis['gray_ratio']:.3f}")
    print(f"  Is Character: {analysis['is_character']}")
    print(f"  Is Decoration: {analysis['is_decoration']}")
    print(f"  Is Material: {analysis['is_material']}")
    
    print("✅ Rust-Powered Scanner working!")
