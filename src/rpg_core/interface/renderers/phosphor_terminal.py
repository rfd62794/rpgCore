"""
Phosphor Terminal - ADR 193 Left Wing Component

Phase 2: Component Consolidation with Sovereign Viewport Protocol

CRT-style terminal with phosphor glow, scanlines, and energy-based effects.
Renders in the left wing of the sovereign viewport, providing narrative
"Story Drips" and system logs.

This component has been migrated from src/ui/ to support the ADR 193
viewport architecture with responsive scaling and wing integration.
"""

import tkinter as tk
import time
import random
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from pathlib import Path
import sys

# Add parent directories for imports
sys.path.append(str(Path(__file__).parent.parent.parent.parent))
sys.path.append(str(Path(__file__).parent.parent.parent))

from loguru import logger
from ..protocols import RenderProtocol, Result
from ...kernel.models import Rectangle
from ...exceptions.core import RenderException, create_render_exception


@dataclass
class PhosphorConfig:
    """Configuration for phosphor terminal effects"""
    # Display settings
    width: int = 80
    height: int = 24
    char_width: int = 8
    char_height: int = 16
    
    # CRT effects
    phosphor_color: str = "#00FF00"  # Classic terminal green
    phosphor_glow: str = "#00FF00"  # Glow color
    scanline_intensity: float = 0.3  # Scanline darkness
    flicker_rate: float = 0.05      # Random flicker probability
    
    # Animation settings
    typewriter_speed: float = 0.05  # Seconds per character
    phosphor_decay: float = 0.95     # Afterimage decay rate
    
    # Energy-based effects
    brownout_threshold: float = 25.0  # Energy level for brownout
    glitch_threshold: float = 10.0   # Energy level for glitches


class PhosphorTerminal(RenderProtocol):
    """CRT-style terminal with phosphor effects for left wing rendering"""
    
    def __init__(self, config: Optional[PhosphorConfig] = None):
        self.config = config or PhosphorConfig()
        self.energy_level: float = 100.0
        self.current_wing: Optional[Rectangle] = None
        
        # Terminal state
        self.buffer: List[List[str]] = []
        self.cursor_x: int = 0
        self.cursor_y: int = 0
        self.typewriter_queue: List[str] = []
        self.typewriter_active: bool = False
        
        # Phosphor effects
        self.phosphor_decay: List[List[float]] = []
        self.last_flicker: float = 0.0
        
        # Canvas for rendering
        self.canvas: Optional[tk.Canvas] = None
        self.root_window: Optional[tk.Tk] = None
        
        # Initialize buffer
        self._initialize_buffer()
        
        logger.info("📟 PhosphorTerminal initialized for left wing rendering")
    
    def initialize(self) -> Result[bool]:
        """Initialize the phosphor terminal"""
        try:
            # Create canvas if not exists
            if not self.canvas:
                self.canvas = tk.Canvas(
                    self.root_window if self.root_window else tk.Tk(),
                    width=self.config.width * self.config.char_width,
                    height=self.config.height * self.config.char_height,
                    bg='black',
                    highlightthickness=0
                )
            
            # Initialize phosphor decay buffer
            self.phosphor_decay = [
                [0.0 for _ in range(self.config.width * self.config.char_width)]
                for _ in range(self.config.height * self.config.char_height)
            ]
            
            logger.success("📟 PhosphorTerminal initialized successfully")
            return Result.success_result(True)
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize PhosphorTerminal: {e}")
            return Result.failure_result(f"Initialization error: {str(e)}")
    
    def shutdown(self) -> Result[None]:
        """Clean shutdown of phosphor terminal"""
        try:
            if self.canvas:
                self.canvas.destroy()
                self.canvas = None
            
            if self.root_window:
                self.root_window.destroy()
                self.root_window = None
            
            logger.info("📟 PhosphorTerminal shutdown complete")
            return Result.success_result(None)
            
        except Exception as e:
            logger.error(f"❌ Failed to shutdown PhosphorTerminal: {e}")
            return Result.failure_result(f"Shutdown error: {str(e)}")
    
    def get_state(self) -> Dict[str, Any]:
        """Get current terminal state"""
        return {
            "energy_level": self.energy_level,
            "buffer": self.buffer.copy(),
            "cursor_position": (self.cursor_x, self.cursor_y),
            "typewriter_active": self.typewriter_active,
            "typewriter_queue_length": len(self.typewriter_queue),
            "wing_region": self.current_wing.__dict__ if self.current_wing else None
        }
    
    def render_to_wing(self, wing_region: Rectangle, scale: float = 1.0) -> Result[bytes]:
        """Render terminal to wing region with scaling"""
        try:
            self.current_wing = wing_region
            
            # Calculate scaled dimensions
            scaled_width = int(wing_region.width / scale)
            scaled_height = int(wing_region.height / scale)
            
            # Update canvas dimensions if needed
            if self.canvas:
                self.canvas.config(width=scaled_width, height=scaled_height)
            
            # Render terminal content
            self._render_terminal_content()
            
            # Apply CRT effects
            self._apply_crt_effects()
            
            # Get canvas as image data
            image_data = self._get_canvas_image_data()
            
            return Result.success_result(image_data)
            
        except Exception as e:
            logger.error(f"❌ Failed to render to wing: {e}")
            return Result.failure_result(f"Wing rendering error: {str(e)}")
    
    def set_energy_level(self, energy: float) -> Result[None]:
        """Set energy level for brownout and glitch effects"""
        self.energy_level = max(0.0, min(100.0, energy))
        
        # Apply energy-based effects
        if self.energy_level < self.config.brownout_threshold:
            self._apply_brownout_effect()
        elif self.energy_level < self.config.glitch_threshold:
            self._apply_glitch_effect()
        
        return Result.success_result(None)
    
    def write_text(self, text: str, typewriter: bool = False) -> Result[None]:
        """Write text to terminal"""
        try:
            if typewriter:
                # Add to typewriter queue
                for char in text:
                    self.typewriter_queue.append(char)
                if not self.typewriter_active:
                    self._start_typewriter()
            else:
                # Write directly to buffer
                self._write_to_buffer(text)
            
            return Result.success_result(None)
            
        except Exception as e:
            logger.error(f"❌ Failed to write text: {e}")
            return Result.failure_result(f"Write error: {str(e)}")
    
    def write_story_drip(self, story: str, typewriter: bool = False) -> Result[None]:
        """Write story with drip effect"""
        return self.write_text(story, typewriter)
    
    def clear_screen(self) -> Result[None]:
        """Clear the terminal screen"""
        try:
            self._initialize_buffer()
            self.cursor_x = 0
            self.cursor_y = 0
            return Result.success_result(None)
            
        except Exception as e:
            logger.error(f"❌ Failed to clear screen: {e}")
            return Result.failure_result(f"Clear error: {str(e)}")
    
    def _initialize_buffer(self) -> None:
        """Initialize terminal buffer"""
        self.buffer = [[" " for _ in range(self.config.width)] for _ in range(self.config.height)]
    
    def _write_to_buffer(self, text: str) -> None:
        """Write text directly to buffer"""
        for char in text:
            if char == '\n':
                self.cursor_x = 0
                self.cursor_y = min(self.cursor_y + 1, self.config.height - 1)
            elif char == '\r':
                self.cursor_x = 0
            else:
                if self.cursor_x < self.config.width and self.cursor_y < self.config.height:
                    self.buffer[self.cursor_y][self.cursor_x] = char
                    self.cursor_x += 1
                    
                    # Auto-wrap
                    if self.cursor_x >= self.config.width:
                        self.cursor_x = 0
                        self.cursor_y = min(self.cursor_y + 1, self.config.height - 1)
    
    def _start_typewriter(self) -> None:
        """Start typewriter animation"""
        self.typewriter_active = True
        # In a real implementation, this would start a timer
        # For now, we'll process the queue immediately
        self._process_typewriter_queue()
    
    def _process_typewriter_queue(self) -> None:
        """Process typewriter queue"""
        while self.typewriter_queue:
            char = self.typewriter_queue.pop(0)
            self._write_to_buffer(char)
            time.sleep(self.config.typewriter_speed)
        
        self.typewriter_active = False
    
    def _render_terminal_content(self) -> None:
        """Render terminal content to canvas"""
        if not self.canvas:
            return
        
        self.canvas.delete("all")
        
        # Render each character
        for y, line in enumerate(self.buffer):
            for x, char in enumerate(line):
                if char.strip():  # Skip spaces
                    self._render_character(x, y, char)
    
    def _render_character(self, x: int, y: int, char: str) -> None:
        """Render a single character with phosphor effect"""
        if not self.canvas:
            return
        
        # Calculate position
        px = x * self.config.char_width
        py = y * self.config.char_height
        
        # Apply phosphor glow
        glow_color = self._get_phosphor_color()
        
        # Draw character
        self.canvas.create_text(
            px + self.config.char_width // 2,
            py + self.config.char_height // 2,
            text=char,
            fill=glow_color,
            font=("Courier", self.config.char_height - 2),
            anchor="center"
        )
    
    def _get_phosphor_color(self) -> str:
        """Get phosphor color based on energy level"""
        if self.energy_level < self.config.brownout_threshold:
            return "#444400"  # Dim brown
        elif self.energy_level < self.config.glitch_threshold:
            return "#FF0000" if random.random() < 0.1 else self.config.phosphor_color
        else:
            return self.config.phosphor_color
    
    def _apply_crt_effects(self) -> None:
        """Apply CRT effects to canvas"""
        if not self.canvas:
            return
        
        # Apply scanlines
        for y in range(0, self.config.height * self.config.char_height, 2):
            self.canvas.create_line(
                0, y, self.config.width * self.config.char_width, y,
                fill="#000000", width=self.config.scanline_intensity * 10,
                tags="scanline"
            )
        
        # Apply random flicker
        if random.random() < self.config.flicker_rate:
            self._apply_flicker_effect()
    
    def _apply_flicker_effect(self) -> None:
        """Apply random flicker effect"""
        if not self.canvas:
            return
        
        # Randomly dim some characters
        for _ in range(random.randint(1, 5)):
            x = random.randint(0, self.config.width - 1)
            y = random.randint(0, self.config.height - 1)
            
            px = x * self.config.char_width
            py = y * self.config.char_height
            
            self.canvas.create_rectangle(
                px, py, px + self.config.char_width, py + self.config.char_height,
                fill="black", outline="", tags="flicker"
            )
    
    def _apply_brownout_effect(self) -> None:
        """Apply brownout effect for low energy"""
        if not self.canvas:
            return
        
        # Create brownout overlay
        self.canvas.create_rectangle(
            0, 0, self.config.width * self.config.char_width, self.config.height * self.config.char_height,
            fill="#330000", stipple="gray50", tags="brownout"
        )
    
    def _apply_glitch_effect(self) -> None:
        """Apply glitch effect for very low energy"""
        if not self.canvas:
            return
        
        # Random character corruption
        for _ in range(random.randint(1, 3)):
            x = random.randint(0, self.config.width - 1)
            y = random.randint(0, self.config.height - 1)
            
            if y < len(self.buffer) and x < len(self.buffer[y]):
                # Replace character with random symbol
                glitch_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
                self.buffer[y][x] = random.choice(glitch_chars)
    
    def _get_canvas_image_data(self) -> bytes:
        """Get canvas as image data"""
        # In a real implementation, this would convert the canvas to image data
        # For now, return placeholder data
        return b"canvas_image_data_placeholder"


# Factory function for easy creation
def create_phosphor_terminal(config: Optional[PhosphorConfig] = None) -> PhosphorTerminal:
    """Create a PhosphorTerminal instance"""
    return PhosphorTerminal(config)
