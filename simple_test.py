import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from ui.pixel_renderer import PixelRenderer, Pixel

# Simple test - just set one pixel and check it
renderer = PixelRenderer(10, 10)
pixel = Pixel(r=1, g=1, b=1, intensity=1.0)

print("Testing single pixel setting:")
renderer.set_pixel(5, 5, pixel)
print(f"Immediately after set_pixel(5,5): empty={renderer.pixels[5][5].is_empty()}")

# Test setting pixel (6,2) specifically
print("\nTesting pixel (6,2):")
renderer.set_pixel(6, 2, pixel)
print(f"Immediately after set_pixel(6,2): empty={renderer.pixels[2][6].is_empty()}")

# Test the rectangle drawing without debug prints
print("\nTesting rectangle without debug:")
renderer.clear()
# Remove debug prints from draw_rectangle by temporarily commenting them out
