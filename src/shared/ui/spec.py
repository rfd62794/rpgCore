from dataclasses import dataclass
from typing import Tuple, Optional

@dataclass
class UISpec:
    # Screen
    screen_width: int
    screen_height: int
    scale_factor: float  # 1.0 at 1280x720
    
    # Typography
    font_size_sm: int    # 10
    font_size_md: int    # 14
    font_size_lg: int    # 18
    font_size_xl: int    # 24
    font_size_hd: int    # 32
    
    # Spacing
    padding_sm: int    # 8
    padding_md: int    # 16
    padding_lg: int    # 24
    margin_sm: int     # 8
    margin_md: int     # 16
    
    # Colors
    color_bg: tuple          # (15, 15, 25)
    color_surface: tuple     # (25, 25, 40)
    color_surface_alt: tuple # (35, 35, 55)
    color_border: tuple      # (70, 70, 100)
    color_text: tuple        # (220, 220, 240)
    color_text_dim: tuple    # (140, 140, 160)
    color_accent: tuple      # (100, 180, 255)
    color_accent_alt: tuple   # (150, 200, 255)
    color_danger: tuple      # (200, 60, 60)
    color_success: tuple     # (60, 200, 100)
    color_warning: tuple     # (200, 160, 40)
    
    # Cultural colors
    color_ember: tuple   # (220, 80, 40)
    color_crystal: tuple # (80, 160, 220)
    color_moss: tuple    # (80, 180, 80)
    color_coastal: tuple # (60, 180, 200)
    color_void: tuple    # (140, 60, 200)
    color_mixed: tuple   # (160, 160, 160)
    
    # Component sizes
    button_height_sm: int   # 32
    button_height_md: int   # 44
    button_height_lg: int   # 56
    card_width: int       # 220
    card_height: int      # 140
    panel_width: int      # 300
    bar_height: int       # 36

# --- Standard 720p Reference ---
SPEC_720 = UISpec(
    screen_width=1280,
    screen_height=720,
    scale_factor=1.0,
    
    font_size_sm=10,
    font_size_md=14,
    font_size_lg=18,
    font_size_xl=24,
    font_size_hd=32,
    
    padding_sm=8,
    padding_md=16,
    padding_lg=24,
    margin_sm=8,
    margin_md=16,
    
    color_bg=(15, 15, 25),
    color_surface=(25, 25, 40),
    color_surface_alt=(35, 35, 55),
    color_border=(70, 70, 100),
    color_text=(220, 220, 240),
    color_text_dim=(140, 140, 160),
    color_accent=(100, 180, 255),
    color_accent_alt=(150, 200, 255),
    color_danger=(200, 60, 60),
    color_success=(60, 200, 100),
    color_warning=(200, 160, 40),
    
    color_ember=(220, 80, 40),
    color_crystal=(80, 160, 220),
    color_moss=(80, 180, 80),
    color_coastal=(60, 180, 200),
    color_void=(140, 60, 200),
    color_mixed=(160, 160, 160),
    
    button_height_sm=32,
    button_height_md=44,
    button_height_lg=56,
    card_width=220,
    card_height=140,
    panel_width=300,
    bar_height=36
)

# --- Standard 1080p Scaled ---
SPEC_1080 = UISpec(
    screen_width=1920,
    screen_height=1080,
    scale_factor=1.5,
    
    font_size_sm=int(10 * 1.5),
    font_size_md=int(14 * 1.5),
    font_size_lg=int(18 * 1.5),
    font_size_xl=int(24 * 1.5),
    font_size_hd=int(32 * 1.5),
    
    padding_sm=int(8 * 1.5),
    padding_md=int(16 * 1.5),
    padding_lg=int(24 * 1.5),
    margin_sm=int(8 * 1.5),
    margin_md=int(16 * 1.5),
    
    color_bg=SPEC_720.color_bg,
    color_surface=SPEC_720.color_surface,
    color_surface_alt=SPEC_720.color_surface_alt,
    color_border=SPEC_720.color_border,
    color_text=SPEC_720.color_text,
    color_text_dim=SPEC_720.color_text_dim,
    color_accent=SPEC_720.color_accent,
    color_accent_alt=SPEC_720.color_accent_alt,
    color_danger=SPEC_720.color_danger,
    color_success=SPEC_720.color_success,
    color_warning=SPEC_720.color_warning,
    
    color_ember=SPEC_720.color_ember,
    color_crystal=SPEC_720.color_crystal,
    color_moss=SPEC_720.color_moss,
    color_coastal=SPEC_720.color_coastal,
    color_void=SPEC_720.color_void,
    color_mixed=SPEC_720.color_mixed,
    
    button_height_sm=int(32 * 1.5),
    button_height_md=int(44 * 1.5),
    button_height_lg=int(56 * 1.5),
    card_width=int(220 * 1.5),
    card_height=int(140 * 1.5),
    panel_width=int(300 * 1.5),
    bar_height=int(36 * 1.5)
)
