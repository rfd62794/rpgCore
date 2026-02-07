"""
Asset Display Tool - WYSIWYG Sprite Gallery
ADR 086: The Fault-Tolerant Asset Pipeline

This tool treats the PPU as a Standalone Gallery for visual asset validation.
If a sprite is missing or the YAML is malformed, the tool provides immediate visual feedback.
"""

import os
import sys
import tkinter as tk
from typing import Dict, List, Tuple, Optional
from loguru import logger
from pathlib import Path

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from graphics.ppu_tk_native import NativeTkinterPPU
from core.system_config import create_default_config
from assets.parser import AssetParser
from assets.fabricator_tkinter import AssetFabricator
from assets.registry import AssetRegistry

class AssetDisplayTool:
    """WYSIWYG Asset Display Tool for visual asset validation"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🛠️ Asset Display Tool - WYSIWYG Sprite Gallery")
        self.root.geometry("800x600")
        
        # Deconstructed Asset Components (ADR 086)
        self.config = create_default_config(seed="ASSET_DISPLAY")
        self.parser = None
        self.fabricator = None
        self.registry = None
        self.ppu = None
        
        # UI Components
        self.canvas = None
        self.info_frame = None
        self.info_text = None
        self.hover_sprite_id = None
        
        # Build UI first
        self._build_ui()
        
        # Initialize deconstructed systems
        self._initialize_deconstructed_systems()
        
        # Display assets
        self._display_all_assets()
        
        # Start the tool
        self.root.mainloop()
    
    def _initialize_deconstructed_systems(self) -> None:
        """Initialize deconstructed asset systems"""
        try:
            # Initialize Parser
            assets_path = Path(__file__).parent / "assets"
            self.parser = AssetParser(assets_path)
            logger.info("📄 Parser initialized")
            
            # Initialize Fabricator
            self.fabricator = AssetFabricator()
            logger.info("🎨 Fabricator initialized")
            
            # Initialize Registry
            self.registry = AssetRegistry()
            logger.info("📚 Registry initialized")
            
            # Load assets using deconstructed pipeline
            parsed_data = self.parser.load_all_assets()
            
            # Generate sprites
            sprites = self.fabricator.generate_all_sprites(parsed_data)
            
            # Load into registry
            self.registry.load_from_parsed_data(parsed_data, sprites)
            
            # Initialize PPU now that canvas exists
            if self.canvas:
                try:
                    self.ppu = NativeTkinterPPU(self.canvas, self.registry)
                    logger.info("🎨 PPU initialized for asset display")
                except Exception as e:
                    print(f"⚠️ PPU initialization failed: {e}")
            
        except Exception as e:
            print(f"💥 System initialization failed: {e}")
    
    def _build_ui(self) -> None:
        """Build the UI components"""
        # Main frame
        main_frame = tk.Frame(self.root, bg="black")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Title
        title_label = tk.Label(
            main_frame,
            text="🛠️ Asset Display Tool - WYSIWYG Sprite Gallery (Deconstructed)",
            bg="black",
            fg="cyan",
            font=("Arial", 16, "bold")
        )
        title_label.pack(pady=(0, 10))
        
        # Canvas for sprite display
        canvas_frame = tk.Frame(main_frame, bg="black", relief=tk.SUNKEN, bd=2)
        canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        self.canvas = tk.Canvas(
            canvas_frame,
            width=640,
            height=400,
            bg="#1a3a1a",
            highlightthickness=0
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Info panel
        info_frame = tk.Frame(main_frame, bg="black", height=150)
        info_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.info_text = tk.Text(
            info_frame,
            height=8,
            bg="black",
            fg="green",
            font=("Courier", 9),
            wrap=tk.WORD
        )
        self.info_text.pack(fill=tk.BOTH, expand=True)
        
        # Status label
        self.status_label = tk.Label(
            main_frame,
            text="🛠️ Deconstructed Asset Display Tool Ready - Hover over sprites for details",
            bg="black",
            fg="yellow",
            font=("Arial", 10)
        )
        self.status_label.pack(pady=(5, 0))
        
        # Bind hover events
        self.canvas.bind("<Motion>", self.on_hover)
        self.canvas.bind("<Leave>", self.on_leave)
    
    def _display_all_assets(self) -> None:
        """Display all registered assets in a grid"""
        if not self.registry:
            self.info_text.insert(tk.END, "❌ No assets loaded - check YAML syntax\n")
            return
        
        # Get all sprite IDs
        sprite_ids = list(self.registry.get_all_sprites().keys())
        
        if not sprite_ids:
            self.info_text.insert(tk.END, "❌ No sprites found in registry\n")
            return
        
        # Calculate grid dimensions
        grid_size = 8  # 8x8 grid
        cell_size = 80  # 80x80 pixels per cell
        padding = 10
        
        # Display sprites in grid
        row, col = 0, 0
        for sprite_id in sprite_ids:
            if row >= grid_size:
                break
                
            x = padding + col * (cell_size + padding)
            y = padding + row * (cell_size + padding)
            
            try:
                sprite = self.registry.get_sprite(sprite_id)
                if sprite:
                    self.canvas.create_image(
                        x + cell_size // 2,
                        y + cell_size // 2,
                        image=sprite,
                        anchor="center",
                        tags=(sprite_id, "asset")
                    )
                    
                    # Add label
                    self.canvas.create_text(
                        x + cell_size // 2,
                        y + cell_size + 20,
                        text=sprite_id[:10],  # Truncate long names
                        fill="white",
                        font=("Arial", 8),
                        tags=(sprite_id, "label")
                    )
                    
                    # Next position
                    col += 1
                    if col >= grid_size:
                        col = 0
                        row += 1
                
            except Exception as e:
                # Show pink X for missing sprite
                self.canvas.create_rectangle(
                    x, y,
                    x + cell_size, y + cell_size,
                    fill="pink",
                    outline="red",
                    width=2
                )
                self.canvas.create_text(
                    x + cell_size // 2,
                    y + cell_size // 2,
                    text="X",
                    fill="red",
                    font=("Arial", 20, "bold"),
                    tags=(sprite_id, "error")
                )
                self.canvas.create_text(
                    x + cell_size // 2,
                    y + cell_size + 20,
                    text=f"❌ {sprite_id}",
                    fill="red",
                    font=("Arial", 8),
                    tags=(sprite_id, "error")
                )
        
        # Display registry stats
        stats = self.registry.get_registry_stats()
        self.status_label.config(text=f"🛠️ Deconstructed Registry: {stats['objects']} objects, {stats['materials']} materials, {stats['animations']} animations, {stats['sprites']} sprites")
        self.info_text.insert(tk.END, f"✅ Deconstructed Asset Pipeline Working!\n")
        self.info_text.insert(tk.END, f"📄 Parser: {len(self.parser.get_loaded_files())} files loaded\n")
        self.info_text.insert(tk.END, f"🎨 Fabricator: {len(self.fabricator.get_failed_sprites())} failed sprites (Pink X)\n")
        self.info_text.insert(tk.END, f"📚 Registry: {stats['total'] if hasattr(stats, 'total') else sum(stats.values())} total assets\n")
        
        if self.parser.get_failed_files():
            self.info_text.insert(tk.END, f"⚠️ Failed files: {self.parser.get_failed_files()}\n")
    
    def on_hover(self, event) -> None:
        """Handle mouse hover over sprites"""
        # Find what's under the cursor
        x, y = event.x, event.y
        
        # Find closest sprite
        closest_item = self.canvas.find_closest(x, y)
        if closest_item:
            tags = self.canvas.gettags(closest_item)
            if tags:
                sprite_id = tags[0]
                if sprite_id != self.hover_sprite_id:
                    # Clear previous hover
                    if self.hover_sprite_id:
                        self.canvas.itemconfig(self.hover_sprite_id, outline="")
                    
                    # Set new hover
                    self.hover_sprite_id = sprite_id
                    self.canvas.itemconfig(closest_item, outline="yellow", width=3)
                    
                    # Display sprite info
                    self.display_sprite_info(sprite_id)
    
    def on_leave(self, event) -> None:
        """Handle mouse leave"""
        if self.hover_sprite_id:
            self.canvas.itemconfig(self.hover_sprite_id, outline="")
            self.hover_sprite_id = None
            self.info_text.delete(1.0, tk.END)
            self.status_label.config(text="🛠️ Deconstructed Asset Display Tool Ready - Hover over sprites for details")
    
    def display_sprite_info(self, sprite_id: str) -> None:
        """Display detailed information about a sprite"""
        try:
            # Clear previous info
            self.info_text.delete(1.0, tk.END)
            
            # Get sprite
            sprite = self.registry.get_sprite(sprite_id)
            if not sprite:
                self.info_text.insert(tk.END, f"❌ Sprite '{sprite_id}' not found in registry\n")
                return
            
            # Get asset definition if available
            asset_def = self.registry.get_object(sprite_id)
            
            # Display information
            info = f"🎨 Sprite: {sprite_id}\n"
            
            if asset_def:
                info += f"📋 Material: {asset_def.material}\n"
                info += f"🏷️ Integrity: {asset_def.integrity}\n"
                info += f"🏷️ Collision: {asset_def.collision}\n"
                info += f"🏷️ Friction: {asset_def.friction}\n"
                
                if asset_def.tags:
                    info += f"🏷️ Tags: {', '.join(asset_def.tags)}\n"
                
                if asset_def.d20_checks:
                    info += f"🎲 D20 Checks:\n"
                    for check_name, check_data in asset_def.d20_checks.items():
                        info += f"  • {check_name}: DC {check_data.get('difficulty', 'N/A')}\n"
                
                if asset_def.triggers:
                    info += f"⚡ Triggers:\n"
                    for trigger_name, trigger_data in asset_def.triggers.items():
                        info += f"  • {trigger_name}: {trigger_data}\n"
                
                if asset_def.metadata:
                    info += f"📊 Metadata:\n"
                    for key, value in asset_def.metadata.items():
                        info += f"  • {key}: {value}\n"
            
            info += f"🖼️ Size: {sprite.width}x{sprite.height} pixels\n"
            info += f"🎨 Type: {type(sprite).__name__}\n"
            info += "-" * 40 + "\n"
            
            self.info_text.insert(tk.END, info)
            
        except Exception as e:
            self.info_text.insert(tk.END, f"❌ Error displaying info for '{sprite_id}': {e}\n")

if __name__ == "__main__":
    tool = AssetDisplayTool()
