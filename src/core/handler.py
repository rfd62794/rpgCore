"""
DGT Window Handler - ADR 108: Dedicated Raster Pipeline
Thread-safe, high-performance window management for real-time game rendering
"""

import tkinter as tk
from tkinter import Canvas
import queue
import threading
import time
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass
from enum import Enum
from loguru import logger


class CommandType(Enum):
    """Command types for the render pipeline"""
    DRAW_SPRITE = "draw_sprite"
    DRAW_RECT = "draw_rect"
    DRAW_TEXT = "draw_text"
    CLEAR = "clear"
    UPDATE_ENTITY = "update_entity"
    MOVE_CAMERA = "move_camera"
    SET_FPS = "set_fps"


@dataclass
class RenderCommand:
    """Single render command for the pipeline"""
    command_type: CommandType
    entity_id: Optional[str] = None
    position: Optional[tuple] = None
    sprite_id: Optional[str] = None
    color: Optional[str] = None
    size: Optional[tuple] = None
    text: Optional[str] = None
    layer: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None


class RasterCache:
    """High-performance raster cache for pre-rendered patterns"""
    
    def __init__(self):
        self.pattern_cache: Dict[str, tk.PhotoImage] = {}
        self.sprite_cache: Dict[str, tk.PhotoImage] = {}
        
        # Pre-generate common dithering patterns
        self._generate_dither_patterns()
    
    def _generate_dither_patterns(self) -> None:
        """Generate common dithering patterns for instant blitting"""
        patterns = {
            "checkerboard_2x2": self._create_checkerboard(2, "#000000", "#ffffff"),
            "checkerboard_4x4": self._create_checkerboard(4, "#000000", "#ffffff"),
            "vertical_lines": self._create_lines("vertical", "#333333", "#666666"),
            "horizontal_lines": self._create_lines("horizontal", "#333333", "#666666"),
            "diagonal_lines": self._create_lines("diagonal", "#333333", "#666666"),
        }
        
        for pattern_name, pattern in patterns.items():
            self.pattern_cache[pattern_name] = pattern
        
        logger.info(f"🎨 Generated {len(self.pattern_cache)} dither patterns")
    
    def _create_checkerboard(self, size: int, color1: str, color2: str) -> tk.PhotoImage:
        """Create checkerboard pattern"""
        pattern = tk.PhotoImage(width=size*2, height=size*2)
        
        for y in range(size*2):
            for x in range(size*2):
                if (x // size + y // size) % 2 == 0:
                    pattern.put(color1, (x, y))
                else:
                    pattern.put(color2, (x, y))
        
        return pattern
    
    def _create_lines(self, direction: str, color1: str, color2: str) -> tk.PhotoImage:
        """Create line pattern"""
        pattern = tk.PhotoImage(width=8, height=8)
        
        for y in range(8):
            for x in range(8):
                if direction == "vertical":
                    color = color1 if x % 2 == 0 else color2
                elif direction == "horizontal":
                    color = color1 if y % 2 == 0 else color2
                else:  # diagonal
                    color = color1 if (x + y) % 2 == 0 else color2
                
                pattern.put(color, (x, y))
        
        return pattern
    
    def get_pattern(self, pattern_name: str) -> Optional[tk.PhotoImage]:
        """Get cached pattern"""
        return self.pattern_cache.get(pattern_name)
    
    def cache_sprite(self, sprite_id: str, sprite: tk.PhotoImage) -> None:
        """Cache a sprite for instant retrieval"""
        self.sprite_cache[sprite_id] = sprite
    
    def get_sprite(self, sprite_id: str) -> Optional[tk.PhotoImage]:
        """Get cached sprite"""
        return self.sprite_cache.get(sprite_id)


class InputInterceptor:
    """Low-level input handler to prevent stuck keys during frame drops"""
    
    def __init__(self, window_handler):
        self.window_handler = window_handler
        self.pressed_keys = set()
        self.key_state_buffer = {}
        self.last_frame_time = time.time()
        
    def register_keys(self, root: tk.Tk) -> None:
        """Register key handlers with tkinter"""
        root.bind('<KeyPress>', self._on_key_press)
        root.bind('<KeyRelease>', self._on_key_release)
        root.bind('<FocusIn>', self._on_focus_in)
        root.bind('<FocusOut>', self._on_focus_out)
        
        logger.info("⌨️ Input interceptor registered")
    
    def _on_key_press(self, event) -> None:
        """Handle key press with state tracking"""
        key = event.keysym.lower()
        current_time = time.time()
        
        # Detect stuck key (same key held for too long without release)
        if key in self.pressed_keys and key in self.key_state_buffer:
            hold_duration = current_time - self.key_state_buffer[key]
            if hold_duration > 0.5:  # 500ms threshold
                logger.warning(f"⚠️ Stuck key detected: {key}")
                self._clear_stuck_key(key)
        
        self.pressed_keys.add(key)
        self.key_state_buffer[key] = current_time
        
        # Queue command for game logic
        command = RenderCommand(
            command_type=CommandType.UPDATE_ENTITY,
            entity_id="input",
            metadata={"action": "key_press", "key": key}
        )
        self.window_handler.queue_command(command)
    
    def _on_key_release(self, event) -> None:
        """Handle key release"""
        key = event.keysym.lower()
        self.pressed_keys.discard(key)
        if key in self.key_state_buffer:
            del self.key_state_buffer[key]
        
        # Queue command for game logic
        command = RenderCommand(
            command_type=CommandType.UPDATE_ENTITY,
            entity_id="input",
            metadata={"action": "key_release", "key": key}
        )
        self.window_handler.queue_command(command)
    
    def _on_focus_in(self, event) -> None:
        """Handle window focus gain"""
        logger.debug("🎯 Window gained focus")
        self._clear_all_stuck_keys()
    
    def _on_focus_out(self, event) -> None:
        """Handle window focus loss"""
        logger.debug("🎯 Window lost focus")
        self._clear_all_stuck_keys()
    
    def _clear_stuck_key(self, key: str) -> None:
        """Clear a specific stuck key"""
        self.pressed_keys.discard(key)
        if key in self.key_state_buffer:
            del self.key_state_buffer[key]
        
        # Send release event to game logic
        command = RenderCommand(
            command_type=CommandType.UPDATE_ENTITY,
            entity_id="input",
            metadata={"action": "key_release", "key": key}
        )
        self.window_handler.queue_command(command)
    
    def _clear_all_stuck_keys(self) -> None:
        """Clear all stuck keys (focus change)"""
        for key in list(self.pressed_keys):
            self._clear_stuck_key(key)
    
    def get_pressed_keys(self) -> set:
        """Get currently pressed keys"""
        return self.pressed_keys.copy()


class DGTWindowHandler:
    """
    Dedicated Tkinter Handler - ADR 108 Implementation
    Thread-safe raster pipeline with 60Hz pulse loop
    ADR 109: Static-Dynamic Decoupling with Background Baking
    """
    
    def __init__(self, root: tk.Tk, width: int = 800, height: int = 600):
        self.root = root
        self.width = width
        self.height = height
        
        # Core components
        self.canvas = Canvas(
            root,
            width=width,
            height=height,
            bg='#0a0a0a',
            highlightthickness=0
        )
        self.canvas.pack()
        
        # Command pipeline
        self.command_queue = queue.Queue()
        self.render_queue = queue.Queue()
        
        # Performance tracking
        self.fps_limit = 60
        self.frame_time_ms = 1000 // self.fps_limit
        self.actual_fps = 0
        self.frame_count = 0
        self.last_fps_time = time.time()
        self.pulse_times = []
        
        # Caching system
        self.raster_cache = RasterCache()
        
        # ADR 109: Background Baking System
        self.background_buffer: Optional[tk.PhotoImage] = None
        self.background_dirty = True
        self.static_tiles: Dict[tuple, str] = {}  # (x, y) -> sprite_id
        self.dynamic_entities: List[Dict] = []  # Dynamic entity data
        
        # Dirty rectangle system for dynamic updates
        self.dirty_rects: List[tuple] = []  # List of (x, y, width, height)
        self.full_redraw = True
        
        # Input handling
        self.input_interceptor = InputInterceptor(self)
        self.input_interceptor.register_keys(root)
        
        # Game state callback
        self.game_update_callback: Optional[Callable] = None
        
        # Threading
        self.game_thread: Optional[threading.Thread] = None
        self.running = False
        
        logger.info(f"🎮 DGT Window Handler initialized: {width}x{height} @ {self.fps_limit}Hz")
        logger.info("🎨 ADR 109: Background Baking System enabled")
    
    def queue_command(self, command: RenderCommand) -> None:
        """Queue a render command (thread-safe)"""
        try:
            self.command_queue.put_nowait(command)
        except queue.Full:
            logger.warning("⚠️ Command queue full, dropping command")
    
    def set_game_update_callback(self, callback: Callable) -> None:
        """Set the game logic update callback"""
        self.game_update_callback = callback
    
    def start_game_thread(self) -> None:
        """Start the game logic in separate thread"""
        if self.game_update_callback:
            self.game_thread = threading.Thread(
                target=self._game_loop_thread,
                daemon=True,
                name="GameLogic"
            )
            self.game_thread.start()
            logger.info("🎯 Game thread started")
    
    def _game_loop_thread(self) -> None:
        """Game logic running in separate thread"""
        while self.running:
            try:
                # Run game logic
                if self.game_update_callback:
                    self.game_update_callback()
                
                # Sleep to match target rate (30Hz for game logic)
                time.sleep(1/30)
                
            except Exception as e:
                logger.error(f"⚠️ Game thread error: {e}")
    
    def pulse(self) -> None:
        """Main pulse loop - 60Hz render cycle"""
        if not self.running:
            return
        
        pulse_start = time.time()
        
        try:
            # 1. Process all pending commands
            self._process_commands()
            
            # 2. Update PPU and render
            self._render_frame()
            
            # 3. Update performance metrics
            self._update_performance_metrics(pulse_start)
            
        except Exception as e:
            logger.error(f"⚠️ Pulse error: {e}")
        
        # Schedule next pulse
        finally:
            self.root.after(self.frame_time_ms, self.pulse)
    
    def _process_commands(self) -> None:
        """Process all pending render commands"""
        commands_processed = 0
        
        while not self.command_queue.empty() and commands_processed < 100:
            try:
                command = self.command_queue.get_nowait()
                self._execute_command(command)
                commands_processed += 1
                
            except queue.Empty:
                break
            except Exception as e:
                logger.error(f"⚠️ Command execution error: {e}")
        
        if commands_processed > 50:
            logger.debug(f"📊 Processed {commands_processed} commands this frame")
    
    def _execute_command(self, command: RenderCommand) -> None:
        """Execute a single render command"""
        if command.command_type == CommandType.DRAW_SPRITE:
            self._draw_sprite_command(command)
        elif command.command_type == CommandType.DRAW_RECT:
            self._draw_rect_command(command)
        elif command.command_type == CommandType.DRAW_TEXT:
            self._draw_text_command(command)
        elif command.command_type == CommandType.CLEAR:
            self._clear_command(command)
        elif command.command_type == CommandType.UPDATE_ENTITY:
            self._update_entity_command(command)
        elif command.command_type == CommandType.MOVE_CAMERA:
            self._move_camera_command(command)
        elif command.command_type == CommandType.SET_FPS:
            self._set_fps_command(command)
    
    def _draw_sprite_command(self, command: RenderCommand) -> None:
        """Draw sprite command"""
        if not command.position or not command.sprite_id:
            return
        
        sprite = self.raster_cache.get_sprite(command.sprite_id)
        if sprite:
            x, y = command.position
            self.canvas.create_image(x, y, image=sprite, anchor='nw', tags=f"entity_{command.entity_id}")
            
            # Mark dirty rectangle
            self._mark_dirty(x, y, sprite.width(), sprite.height())
    
    def _draw_rect_command(self, command: RenderCommand) -> None:
        """Draw rectangle command"""
        if not command.position or not command.size or not command.color:
            return
        
        x, y = command.position
        w, h = command.size
        
        self.canvas.create_rectangle(
            x, y, x + w, y + h,
            fill=command.color,
            outline="",
            tags=f"entity_{command.entity_id}"
        )
        
        self._mark_dirty(x, y, w, h)
    
    def _draw_text_command(self, command: RenderCommand) -> None:
        """Draw text command"""
        if not command.position or not command.text:
            return
        
        x, y = command.position
        self.canvas.create_text(
            x, y,
            text=command.text,
            fill="#00ff00",
            font=("Courier", 10),
            anchor='nw',
            tags=f"entity_{command.entity_id}"
        )
    
    def _clear_command(self, command: RenderCommand) -> None:
        """Clear canvas command"""
        self.canvas.delete("all")
        self.full_redraw = True
        self.dirty_rects.clear()
    
    def _update_entity_command(self, command: RenderCommand) -> None:
        """Update entity command (for input, etc.)"""
        # This would be handled by the game logic callback
        pass
    
    def _move_camera_command(self, command: RenderCommand) -> None:
        """Move camera command"""
        # Camera implementation would go here
        pass
    
    def _set_fps_command(self, command: RenderCommand) -> None:
        """Set FPS limit command"""
        if command.metadata and "fps" in command.metadata:
            self.fps_limit = command.metadata["fps"]
            self.frame_time_ms = 1000 // self.fps_limit
            logger.info(f"🎯 FPS limit set to {self.fps_limit}")
    
    def _mark_dirty(self, x: int, y: int, width: int, height: int) -> None:
        """Mark a rectangle as dirty for partial redraw"""
        self.dirty_rects.append((x, y, width, height))
    
    def _render_frame(self) -> None:
        """Render the current frame with ADR 109 background baking"""
        # Draw baked background if dirty or first time
        if self.background_dirty or self.background_buffer is None:
            self._draw_baked_background()
            self.background_dirty = False
        
        if self.full_redraw:
            # Full redraw - draw background then clear dynamic layer
            self.canvas.delete("all")
            if self.background_buffer:
                self.canvas.create_image(0, 0, image=self.background_buffer, anchor='nw', tags="background")
            self.full_redraw = False
        else:
            # Smart redraw - only update dirty rectangles
            for rect in self.dirty_rects:
                x, y, w, h = rect
                # Clear dirty area and redraw background portion
                self.canvas.create_rectangle(x, y, x + w, y + h, fill='#0a0a0a', outline="", tags="dirty")
                
                # Redraw background portion if available
                if self.background_buffer:
                    # Create temporary clipped view of background
                    self.canvas.create_image(x, y, image=self.background_buffer, anchor='nw', tags="background_patch")
        
        # Always draw dynamic entities (they change every frame)
        self._draw_dynamic_entities()
        
        self.dirty_rects.clear()
    
    def _draw_dynamic_entities(self) -> None:
        """Draw all dynamic entities"""
        # Clear previous dynamic entities
        self.canvas.delete("dynamic")
        
        # Draw current dynamic entities
        for entity in self.dynamic_entities:
            if entity.get('position') and entity.get('sprite_id'):
                sprite = self.raster_cache.get_sprite(entity['sprite_id'])
                if sprite:
                    x, y = entity['position']
                    self.canvas.create_image(
                        x, y, image=sprite, anchor='nw',
                        tags="dynamic"
                    )
                    self._mark_dirty(x, y, sprite.width(), sprite.height())
    
    def _update_performance_metrics(self, pulse_start: float) -> None:
        """Update FPS and performance metrics"""
        pulse_time = (time.time() - pulse_start) * 1000
        self.pulse_times.append(pulse_time)
        
        # Keep only last 60 pulse times
        if len(self.pulse_times) > 60:
            self.pulse_times.pop(0)
        
        # Calculate FPS
        self.frame_count += 1
        current_time = time.time()
        if current_time - self.last_fps_time >= 1.0:
            self.actual_fps = self.frame_count
            self.frame_count = 0
            self.last_fps_time = current_time
            
            # Log performance if needed
            if self.actual_fps < self.fps_limit * 0.9:
                avg_pulse = sum(self.pulse_times) / len(self.pulse_times)
                logger.warning(f"⚠️ FPS drop: {self.actual_fps}/{self.fps_limit} (avg pulse: {avg_pulse:.1f}ms)")
    
    def start(self) -> None:
        """Start the window handler"""
        self.running = True
        self.start_game_thread()
        self.pulse()  # Start the pulse loop
        logger.info("🚀 DGT Window Handler started")
    
    def stop(self) -> None:
        """Stop the window handler"""
        self.running = False
        logger.info("🛑 DGT Window Handler stopped")
    
    def set_static_tile(self, x: int, y: int, sprite_id: str) -> None:
        """Set a static tile for background baking"""
        self.static_tiles[(x, y)] = sprite_id
        self.background_dirty = True
        logger.debug(f"🏠 Static tile set at ({x}, {y}): {sprite_id}")
    
    def add_dynamic_entity(self, entity_data: Dict) -> None:
        """Add a dynamic entity (drawn every frame)"""
        self.dynamic_entities.append(entity_data)
    
    def clear_dynamic_entities(self) -> None:
        """Clear all dynamic entities"""
        self.dynamic_entities.clear()
    
    def bake_background(self) -> None:
        """ADR 109: Pre-render static tiles into single background buffer"""
        logger.info("🍞 Baking background buffer...")
        
        # Create background buffer
        self.background_buffer = tk.PhotoImage(width=self.width, height=self.height)
        
        # Fill with base color
        for y in range(self.height):
            for x in range(self.width):
                self.background_buffer.put('#0a0a0a', (x, y))
        
        # Draw static tiles
        tiles_drawn = 0
        for (tile_x, tile_y), sprite_id in self.static_tiles.items():
            sprite = self.raster_cache.get_sprite(sprite_id)
            if sprite:
                self._blit_sprite_to_buffer(self.background_buffer, sprite, tile_x, tile_y)
                tiles_drawn += 1
        
        logger.info(f"✅ Background baked: {tiles_drawn} tiles rendered")
        self.background_dirty = False
    
    def _blit_sprite_to_buffer(self, buffer: tk.PhotoImage, sprite: tk.PhotoImage, x: int, y: int) -> None:
        """Blit a sprite to the background buffer"""
        sprite_width = sprite.width()
        sprite_height = sprite.height()
        
        for sy in range(sprite_height):
            for sx in range(sprite_width):
                if x + sx < self.width and y + sy < self.height:
                    # Get pixel color from sprite
                    try:
                        color = sprite.get(sx, sy)
                        if color and color != '' and color != 'None' and color != '0':
                            buffer.put(color, (x + sx, y + sy))
                    except Exception:
                        # Skip invalid pixels
                        continue
    
        
    def invalidate_background(self) -> None:
        """Mark background as dirty (call when static tiles change)"""
        self.background_dirty = True
        logger.debug("🔄 Background invalidated")
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get current performance statistics"""
        avg_pulse = sum(self.pulse_times) / len(self.pulse_times) if self.pulse_times else 0
        
        return {
            "fps_limit": self.fps_limit,
            "actual_fps": self.actual_fps,
            "avg_pulse_time_ms": avg_pulse,
            "command_queue_size": self.command_queue.qsize(),
            "cached_patterns": len(self.raster_cache.pattern_cache),
            "cached_sprites": len(self.raster_cache.sprite_cache),
            "dirty_rects": len(self.dirty_rects),
            "static_tiles": len(self.static_tiles),
            "dynamic_entities": len(self.dynamic_entities),
            "background_baked": self.background_buffer is not None,
            "background_dirty": self.background_dirty
        }


# Factory function
def create_dgt_window_handler(root: tk.Tk, width: int = 800, height: int = 600) -> DGTWindowHandler:
    """Create DGT window handler"""
    return DGTWindowHandler(root, width, height)
