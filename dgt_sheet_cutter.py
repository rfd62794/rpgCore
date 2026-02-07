"""
DGT Sovereign Sheet-Cutter - Factory-to-Engine Bridge
Professional sprite sheet slicing and metadata generation tool
"""

import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk, ImageDraw, ImageFilter
import os
import yaml
from pathlib import Path
from loguru import logger
from typing import Optional, Tuple, List, Dict, Set


class DGTSheetCutter:
    """
    DGT Sovereign Sheet-Cutter - High-performance sprite sheet slicing tool
    Designed for visual alignment, slicing, and baking Tiny Farm assets into SovereignRegistry
    """
    
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("DGT Sovereign Sheet-Cutter")
        self.root.geometry("1000x700")
        self.root.configure(bg="#2e2e2e")
        
        # State
        self.raw_image: Optional[Image.Image] = None
        self.display_image: Optional[Image.Image] = None
        self.photo: Optional[ImageTk.PhotoImage] = None
        self.grid_size = 16
        self.offset_x = 0
        self.offset_y = 0
        self.zoom = 1.0
        self.selected_coords: Optional[Tuple[int, int]] = None
        self.batch_mode = False
        self.cut_sprites: List[Dict] = []
        
        self._setup_ui()
        self._setup_bindings()
        
        logger.info("🔪 DGT Sheet-Cutter Online.")
    
    def _setup_ui(self) -> None:
        """Setup the user interface"""
        # Main Layout
        self.paned = tk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        self.paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Left Panel: Controls
        self.ctrl_frame = tk.Frame(self.paned, width=250, bg="#2e2e2e")
        self.paned.add(self.ctrl_frame, minsize=200)

        self._setup_control_panel()
        
        # Right Panel: Canvas
        self.canvas_frame = tk.Frame(self.paned, bg="#1a1a1a")
        self.paned.add(self.canvas_frame)
        
        self._setup_canvas()
        
    def _setup_control_panel(self) -> None:
        """Setup the control panel"""
        # Title
        title_label = tk.Label(self.ctrl_frame, text="🔪 DGT Sheet-Cutter", 
                              font=("Arial", 14, "bold"), bg="#2e2e2e", fg="#00ff00")
        title_label.pack(pady=10)
        
        # File Operations
        tk.Label(self.ctrl_frame, text="📁 File Operations", bg="#2e2e2e", fg="white", 
                font=("Arial", 10, "bold")).pack(pady=(20, 5))
        
        tk.Button(self.ctrl_frame, text="Load Sheet", command=self.load_image,
                 bg="#4CAF50", fg="white", font=("Arial", 9, "bold")).pack(pady=5, fill=tk.X, padx=10)
        
        # Grid Controls
        tk.Label(self.ctrl_frame, text="📐 Grid Settings", bg="#2e2e2e", fg="white",
                font=("Arial", 10, "bold")).pack(pady=(20, 5))
        
        # Grid Size
        tk.Label(self.ctrl_frame, text="Grid Size (px):", bg="#2e2e2e", fg="white").pack()
        self.grid_entry = tk.Entry(self.ctrl_frame, bg="#3e3e3e", fg="white", insertbackground="white")
        self.grid_entry.insert(0, "16")
        self.grid_entry.pack(pady=2, fill=tk.X, padx=10)
        
        # Offset X
        tk.Label(self.ctrl_frame, text="Offset X:", bg="#2e2e2e", fg="white").pack()
        self.off_x_entry = tk.Entry(self.ctrl_frame, bg="#3e3e3e", fg="white", insertbackground="white")
        self.off_x_entry.insert(0, "0")
        self.off_x_entry.pack(pady=2, fill=tk.X, padx=10)
        
        # Offset Y
        tk.Label(self.ctrl_frame, text="Offset Y:", bg="#2e2e2e", fg="white").pack()
        self.off_y_entry = tk.Entry(self.ctrl_frame, bg="#3e3e3e", fg="white", insertbackground="white")
        self.off_y_entry.insert(0, "0")
        self.off_y_entry.pack(pady=2, fill=tk.X, padx=10)
        
        tk.Button(self.ctrl_frame, text="Refresh Grid", command=self.draw_grid,
                 bg="#2196F3", fg="white").pack(pady=10, fill=tk.X, padx=10)
        
        # Metadata
        tk.Label(self.ctrl_frame, text="🏷️ Metadata", bg="#2e2e2e", fg="white",
                font=("Arial", 10, "bold")).pack(pady=(20, 5))
        
        tk.Label(self.ctrl_frame, text="Asset ID Prefix:", bg="#2e2e2e", fg="white").pack()
        self.prefix_entry = tk.Entry(self.ctrl_frame, bg="#3e3e3e", fg="white", insertbackground="white")
        self.prefix_entry.insert(0, "tiny_farm_")
        self.prefix_entry.pack(pady=2, fill=tk.X, padx=10)
        
        # Object Type
        tk.Label(self.ctrl_frame, text="Object Type:", bg="#2e2e2e", fg="white").pack()
        self.type_var = tk.StringVar(value="material")
        type_menu = tk.OptionMenu(self.ctrl_frame, self.type_var, "material", "entity", "decoration", "effect")
        type_menu.config(bg="#3e3e3e", fg="white", activebackground="#4e4e4e")
        type_menu.pack(pady=2, fill=tk.X, padx=10)
        
        # Material ID
        tk.Label(self.ctrl_frame, text="Material ID:", bg="#2e2e2e", fg="white").pack()
        self.material_entry = tk.Entry(self.ctrl_frame, bg="#3e3e3e", fg="white", insertbackground="white")
        self.material_entry.insert(0, "organic")
        self.material_entry.pack(pady=2, fill=tk.X, padx=10)
        
        # Collision
        self.collision_var = tk.BooleanVar(value=False)
        tk.Checkbutton(self.ctrl_frame, text="Has Collision", variable=self.collision_var,
                      bg="#2e2e2e", fg="white", selectcolor="#2e2e2e").pack(pady=5)
        
        # Smart Detection Options
        tk.Label(self.ctrl_frame, text="🧠 Smart Detection", bg="#2e2e2e", fg="white",
                font=("Arial", 10, "bold")).pack(pady=(20, 5))
        
        # Auto-detect object type
        self.auto_detect_var = tk.BooleanVar(value=True)
        tk.Checkbutton(self.ctrl_frame, text="Auto-detect Object Type", variable=self.auto_detect_var,
                      bg="#2e2e2e", fg="white", selectcolor="#2e2e2e").pack(pady=2)
        
        # Auto-clean edges
        self.auto_clean_var = tk.BooleanVar(value=True)
        tk.Checkbutton(self.ctrl_frame, text="Auto-clean Edges", variable=self.auto_clean_var,
                      bg="#2e2e2e", fg="white", selectcolor="#2e2e2e").pack(pady=2)
        
        # Detect chests specifically
        self.detect_chests_var = tk.BooleanVar(value=True)
        tk.Checkbutton(self.ctrl_frame, text="Detect Chests", variable=self.detect_chests_var,
                      bg="#2e2e2e", fg="white", selectcolor="#2e2e2e").pack(pady=2)
        
        # Edge cleaning threshold
        tk.Label(self.ctrl_frame, text="Edge Threshold:", bg="#2e2e2e", fg="white").pack()
        self.threshold_var = tk.IntVar(value=10)
        threshold_spin = tk.Spinbox(self.ctrl_frame, from_=1, to=50, textvariable=self.threshold_var, width=10)
        threshold_spin.pack(pady=2)
        
        # Action Buttons
        tk.Label(self.ctrl_frame, text="⚡ Actions", bg="#2e2e2e", fg="white",
                font=("Arial", 10, "bold")).pack(pady=(20, 5))
        
        tk.Button(self.ctrl_frame, text="CUT SELECTED", command=self.cut_sprite,
                 bg="#FF9800", fg="white", font=("Arial", 10, "bold")).pack(pady=5, fill=tk.X, padx=10)
        
        tk.Button(self.ctrl_frame, text="BATCH CUT ALL", command=self.batch_cut_all,
                 bg="#9C27B0", fg="white", font=("Arial", 10, "bold")).pack(pady=5, fill=tk.X, padx=10)
        
        tk.Button(self.ctrl_frame, text="Clear Selection", command=self.clear_selection,
                 bg="#607D8B", fg="white").pack(pady=5, fill=tk.X, padx=10)
        
        # Status
        tk.Label(self.ctrl_frame, text="📊 Status", bg="#2e2e2e", fg="white",
                font=("Arial", 10, "bold")).pack(pady=(20, 5))
        
        self.status_label = tk.Label(self.ctrl_frame, text="No sheet loaded", bg="#2e2e2e", fg="#00ff00",
                                    font=("Arial", 8))
        self.status_label.pack(pady=5)
        
        self.cut_count_label = tk.Label(self.ctrl_frame, text="Sprites cut: 0", bg="#2e2e2e", fg="white",
                                      font=("Arial", 8))
        self.cut_count_label.pack(pady=2)
        
        # Instructions
        tk.Label(self.ctrl_frame, text="📖 Instructions", bg="#2e2e2e", fg="white",
                font=("Arial", 10, "bold")).pack(pady=(20, 5))
        
        instructions = [
            "1. Load sprite sheet",
            "2. Adjust grid/offset",
            "3. Click tile to select",
            "4. Press Ctrl+S to cut",
            "5. Use Batch for all tiles"
        ]
        
        for instruction in instructions:
            tk.Label(self.ctrl_frame, text=instruction, bg="#2e2e2e", fg="#cccccc",
                    font=("Arial", 7)).pack(anchor=tk.W, padx=10)
    
    def _setup_canvas(self) -> None:
        """Setup the canvas"""
        # Canvas with scrollbars
        canvas_container = tk.Frame(self.canvas_frame, bg="#1a1a1a")
        canvas_container.pack(fill=tk.BOTH, expand=True)
        
        self.canvas = tk.Canvas(canvas_container, bg="#1a1a1a", cursor="cross", highlightthickness=0)
        
        # Scrollbars
        v_scrollbar = tk.Scrollbar(canvas_container, orient=tk.VERTICAL, command=self.canvas.yview)
        h_scrollbar = tk.Scrollbar(canvas_container, orient=tk.HORIZONTAL, command=self.canvas.xview)
        
        self.canvas.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Grid layout
        self.canvas.grid(row=0, column=0, sticky='nsew')
        v_scrollbar.grid(row=0, column=1, sticky='ns')
        h_scrollbar.grid(row=1, column=0, sticky='ew')
        
        canvas_container.grid_rowconfigure(0, weight=1)
        canvas_container.grid_columnconfigure(0, weight=1)
    
    def _setup_bindings(self) -> None:
        """Setup keyboard and mouse bindings"""
        # Canvas mouse events
        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<MouseWheel>", self.on_mousewheel)
        
        # Keyboard shortcuts
        self.root.bind("<Control-s>", lambda e: self.cut_sprite())
        self.root.bind("<Control-b>", lambda e: self.batch_cut_all())
        self.root.bind("<Escape>", lambda e: self.clear_selection())
        
        # Enter key for grid refresh
        self.grid_entry.bind("<Return>", lambda e: self.draw_grid())
        self.off_x_entry.bind("<Return>", lambda e: self.draw_grid())
        self.off_y_entry.bind("<Return>", lambda e: self.draw_grid())
    
    def load_image(self) -> None:
        """Load a sprite sheet image"""
        path = filedialog.askopenfilename(
            title="Select Sprite Sheet",
            filetypes=[
                ("PNG files", "*.png"),
                ("Image files", "*.png *.jpg *.jpeg *.gif *.bmp"),
                ("All files", "*.*")
            ]
        )
        
        if not path:
            return
        
        try:
            self.raw_image = Image.open(path)
            self.draw_grid()
            
            # Update status
            filename = os.path.basename(path)
            self.status_label.config(text=f"Loaded: {filename}")
            
            logger.info(f"📄 Loaded sprite sheet: {filename} ({self.raw_image.size[0]}x{self.raw_image.size[1]})")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load image:\n{e}")
            logger.error(f"⚠️ Error loading image: {e}")
    
    def draw_grid(self) -> None:
        """Draw the sprite sheet with grid overlay"""
        if not self.raw_image:
            return
        
        # Update values
        try:
            self.grid_size = int(self.grid_entry.get())
            self.offset_x = int(self.off_x_entry.get())
            self.offset_y = int(self.off_y_entry.get())
        except ValueError:
            messagebox.showerror("Error", "Invalid grid settings")
            return
        
        # Create display image
        self.display_image = self.raw_image.copy()
        self.photo = ImageTk.PhotoImage(self.display_image)
        
        # Clear canvas
        self.canvas.delete("all")
        
        # Draw image
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo, tags="image")
        
        # Draw grid lines
        w, h = self.raw_image.size
        
        # Vertical lines
        for x in range(self.offset_x, w, self.grid_size):
            self.canvas.create_line(x, 0, x, h, fill="#ffffff", dash=(2, 2), tags="grid")
        
        # Horizontal lines
        for y in range(self.offset_y, h, self.grid_size):
            self.canvas.create_line(0, y, w, y, fill="#ffffff", dash=(2, 2), tags="grid")
        
        # Update scroll region
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        
        # Clear selection
        self.clear_selection()
    
    def on_click(self, event) -> None:
        """Handle canvas click - snap to grid and select tile"""
        if not self.raw_image:
            return
        
        # Get canvas coordinates
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)
        
        # Snap to grid
        x = ((int(canvas_x) - self.offset_x) // self.grid_size) * self.grid_size + self.offset_x
        y = ((int(canvas_y) - self.offset_y) // self.grid_size) * self.grid_size + self.offset_y
        
        # Ensure coordinates are within bounds
        w, h = self.raw_image.size
        x = max(self.offset_x, min(x, w - self.grid_size))
        y = max(self.offset_y, min(y, h - self.grid_size))
        
        # Draw selection
        self.canvas.delete("selector")
        self.canvas.create_rectangle(
            x, y, x + self.grid_size, y + self.grid_size,
            outline="#ff00ff", width=2, tags="selector"
        )
        
        self.selected_coords = (x, y)
        
        # Update status
        grid_x = (x - self.offset_x) // self.grid_size
        grid_y = (y - self.offset_y) // self.grid_size
        self.status_label.config(text=f"Selected: ({grid_x}, {grid_y})")
    
    def on_mousewheel(self, event) -> None:
        """Handle mouse wheel for scrolling"""
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
    
    def clear_selection(self) -> None:
        """Clear the current selection"""
        self.canvas.delete("selector")
        self.selected_coords = None
        self.status_label.config(text="No selection")
    
    def cut_sprite(self) -> None:
        """Cut the selected sprite and save with metadata"""
        if not self.selected_coords:
            messagebox.showwarning("Warning", "Click a tile first!")
            return
        
        if not self.raw_image:
            messagebox.showwarning("Warning", "Load a sprite sheet first!")
            return
        
        x, y = self.selected_coords
        
        # Validate coordinates
        w, h = self.raw_image.size
        if x + self.grid_size > w or y + self.grid_size > h:
            messagebox.showerror("Error", "Selection out of bounds!")
            return
        
        # Crop sprite
        box = (x, y, x + self.grid_size, y + self.grid_size)
        sprite = self.raw_image.crop(box)
        
        # Check if sprite is not empty (has non-transparent pixels)
        if self._is_empty_sprite(sprite):
            messagebox.showwarning("Warning", "Selected tile appears to be empty!")
            return
        
        # Apply smart detection and cleaning
        processed_sprite = sprite
        
        # Auto-clean edges if enabled
        if self.auto_clean_var.get():
            processed_sprite = self._auto_clean_edges(processed_sprite)
            logger.debug(f"✨ Auto-cleaned edges for sprite")
        
        # Auto-detect object type if enabled
        detected_type = self.type_var.get()
        if self.auto_detect_var.get():
            detected_type = self._detect_object_type(processed_sprite)
            # Update UI to show detected type
            self.type_var.set(detected_type)
            logger.debug(f"🧠 Detected object type: {detected_type}")
        
        # Auto-set collision for chests
        if self.detect_chests_var.get() and detected_type == "entity":
            # Check if this is actually a chest and set collision
            if self._is_chest(processed_sprite, {}, self.grid_size, self.grid_size):
                self.collision_var.set(True)
                logger.debug(f"📦 Auto-set collision for detected chest")
        
        # Generate asset ID
        prefix = self.prefix_entry.get().strip()
        grid_x = (x - self.offset_x) // self.grid_size
        grid_y = (y - self.offset_y) // self.grid_size
        asset_id = f"{prefix}{grid_x}_{grid_y}"
        
        # Add detection info to asset ID if detected
        if self.auto_detect_var.get() and detected_type != self.type_var.get():
            asset_id = f"{prefix}{detected_type}_{grid_x}_{grid_y}"
        
        # Save sprite and metadata
        self._save_sprite_with_metadata(processed_sprite, asset_id, (x, y), detected_type)
        
        # Add to cut sprites list
        self.cut_sprites.append({
            'id': asset_id,
            'coords': (x, y),
            'grid_pos': (grid_x, grid_y),
            'size': (self.grid_size, self.grid_size),
            'detected_type': detected_type,
            'auto_cleaned': self.auto_clean_var.get()
        })
        
        # Update UI
        self.cut_count_label.config(text=f"Sprites cut: {len(self.cut_sprites)}")
        self.root.title(f"DGT Sheet-Cutter - Saved: {asset_id} ({detected_type})")
        
        # Move to next tile (optional)
        self._select_next_tile(grid_x, grid_y)
        
        logger.success(f"🔪 Baked {asset_id} ({detected_type}) to disk.")
    
    def batch_cut_all(self) -> None:
        """Cut all non-empty tiles in the sprite sheet"""
        if not self.raw_image:
            messagebox.showwarning("Warning", "Load a sprite sheet first!")
            return
        
        # Confirm operation
        result = messagebox.askyesno(
            "Batch Cut", 
            f"This will cut all non-empty tiles in the sheet.\n"
            f"Grid: {self.grid_size}px, Offset: ({self.offset_x}, {self.offset_y})\n\n"
            f"Continue?"
        )
        
        if not result:
            return
        
        # Calculate grid dimensions
        w, h = self.raw_image.size
        cols = (w - self.offset_x) // self.grid_size
        rows = (h - self.offset_y) // self.grid_size
        
        cut_count = 0
        skipped_count = 0
        
        for row in range(rows):
            for col in range(cols):
                x = self.offset_x + col * self.grid_size
                y = self.offset_y + row * self.grid_size
                
                # Check bounds
                if x + self.grid_size > w or y + self.grid_size > h:
                    skipped_count += 1
                    continue
                
                # Crop sprite
                box = (x, y, x + self.grid_size, y + self.grid_size)
                sprite = self.raw_image.crop(box)
                
                # Skip empty sprites
                if self._is_empty_sprite(sprite):
                    skipped_count += 1
                    continue
                
                # Generate asset ID
                prefix = self.prefix_entry.get().strip()
                asset_id = f"{prefix}{col}_{row}"
                
                # Save sprite and metadata
                self._save_sprite_with_metadata(sprite, asset_id, (x, y))
                
                # Add to cut sprites list
                self.cut_sprites.append({
                    'id': asset_id,
                    'coords': (x, y),
                    'grid_pos': (col, row),
                    'size': (self.grid_size, self.grid_size)
                })
                
                cut_count += 1
        
        # Update UI
        self.cut_count_label.config(text=f"Sprites cut: {len(self.cut_sprites)}")
        self.root.title(f"DGT Sheet-Cutter - Batch cut: {cut_count} sprites")
        
        messagebox.showinfo(
            "Batch Cut Complete",
            f"Cut {cut_count} sprites successfully.\n"
            f"Skipped {skipped_count} empty tiles."
        )
        
        logger.success(f"🍪 Batch cut complete: {cut_count} sprites baked.")
    
    def _is_empty_sprite(self, sprite: Image.Image) -> bool:
        """Check if sprite is empty (all transparent)"""
        if sprite.mode != 'RGBA':
            sprite = sprite.convert('RGBA')
        
        # Check if all pixels are transparent using get_flattened_data
        try:
            # Use new method for Pillow 14+
            flattened = sprite.get_flattened_data()
            return all(pixel[3] == 0 for pixel in flattened)
        except AttributeError:
            # Fallback for older Pillow versions
            for pixel in sprite.getdata():
                if pixel[3] > 0:  # Alpha channel > 0
                    return False
            return True
    
    def _detect_object_type(self, sprite: Image.Image) -> str:
        """Intelligently detect object type from sprite characteristics"""
        if sprite.mode != 'RGBA':
            sprite = sprite.convert('RGBA')
        
        # Analyze sprite characteristics
        width, height = sprite.size
        pixels = list(sprite.get_flattened_data())
        
        # Count non-transparent pixels
        non_transparent = [p for p in pixels if p[3] > 0]
        
        if not non_transparent:
            return "material"  # Empty sprite
        
        # Analyze color distribution
        colors = {}
        for p in non_transparent:
            color = (p[0], p[1], p[2])  # RGB only
            colors[color] = colors.get(color, 0) + 1
        
        # Detect chests (rectangular, brown/gold colors, high density)
        if self.detect_chests_var.get():
            if self._is_chest(sprite, colors, width, height):
                return "entity"  # Chests are entities (interactive)
        
        # Detect decorations (irregular shapes, varied colors)
        if self._is_decoration(sprite, colors, width, height):
            return "decoration"
        
        # Detect materials (simple shapes, uniform colors)
        if self._is_material(sprite, colors, width, height):
            return "material"
        
        # Default to entity for complex objects
        return "entity"
    
    def _is_chest(self, sprite: Image.Image, colors: Dict, width: int, height: int) -> bool:
        """Detect if sprite is a chest based on visual characteristics"""
        # Chests are typically rectangular with brown/gold colors
        aspect_ratio = width / height
        
        # Check for reasonable chest proportions
        if not (0.5 <= aspect_ratio <= 2.0):
            return False
        
        # Look for brown/gold color dominance
        brown_gold_pixels = 0
        total_pixels = len(colors)
        
        for color, count in colors.items():
            r, g, b = color
            # Brown range
            if (100 <= r <= 150 and 50 <= g <= 100 and 0 <= b <= 50) or \
               (180 <= r <= 220 and 150 <= g <= 180 and 0 <= b <= 50):  # Gold range
                brown_gold_pixels += count
        
        # If brown/gold pixels dominate (>40%), likely a chest
        return (brown_gold_pixels / total_pixels) > 0.4
    
    def _is_decoration(self, sprite: Image.Image, colors: Dict, width: int, height: int) -> bool:
        """Detect if sprite is a decoration (plants, rocks, etc.)"""
        # Decorations often have natural, varied colors
        unique_colors = len(colors)
        total_pixels = sum(colors.values())
        
        # High color variety suggests decoration
        color_diversity = unique_colors / max(total_pixels, 1)
        
        # Plants are typically green-heavy
        green_pixels = sum(count for (r, g, b), count in colors.items() if g > r and g > b)
        
        # Rocks are typically gray-heavy
        gray_pixels = sum(count for (r, g, b), count in colors.items() 
                        if abs(r - g) < 30 and abs(g - b) < 30)
        
        return (color_diversity > 0.1) or (green_pixels / total_pixels > 0.3) or (gray_pixels / total_pixels > 0.4)
    
    def _is_material(self, sprite: Image.Image, colors: Dict, width: int, height: int) -> bool:
        """Detect if sprite is a material (tiles, bricks, etc.)"""
        # Materials typically have uniform colors and simple patterns
        unique_colors = len(colors)
        total_pixels = sum(colors.values())
        
        # Low color diversity suggests material
        color_diversity = unique_colors / max(total_pixels, 1)
        
        return color_diversity < 0.05
    
    def _auto_clean_edges(self, sprite: Image.Image) -> Image.Image:
        """Automatically clean up transparent edges around sprite"""
        if sprite.mode != 'RGBA':
            sprite = sprite.convert('RGBA')
        
        # Find bounding box of non-transparent pixels
        bbox = self._get_content_bounds(sprite)
        
        if not bbox:
            return sprite  # Empty sprite
        
        # Crop to content bounds with padding
        threshold = self.threshold_var.get()
        x1, y1, x2, y2 = bbox
        
        # Add small padding to preserve edge pixels
        x1 = max(0, x1 - threshold)
        y1 = max(0, y1 - threshold)
        x2 = min(sprite.width, x2 + threshold)
        y2 = min(sprite.height, y2 + threshold)
        
        # Crop sprite
        cleaned = sprite.crop((x1, y1, x2, y2))
        
        # Resize back to original grid size if needed
        if cleaned.size != (self.grid_size, self.grid_size):
            cleaned = cleaned.resize((self.grid_size, self.grid_size), Image.Resampling.LANCZOS)
        
        return cleaned
    
    def _get_content_bounds(self, sprite: Image.Image) -> Optional[Tuple[int, int, int, int]]:
        """Get the bounding box of non-transparent content"""
        width, height = sprite.size
        pixels = sprite.load()
        
        # Find bounds
        min_x, min_y = width, height
        max_x, max_y = 0, 0
        
        has_content = False
        
        for y in range(height):
            for x in range(width):
                if pixels[x, y][3] > 0:  # Alpha > 0
                    has_content = True
                    min_x = min(min_x, x)
                    min_y = min(min_y, y)
                    max_x = max(max_x, x)
                    max_y = max(max_y, y)
        
        if not has_content:
            return None
        
        return (min_x, min_y, max_x + 1, max_y + 1)
    
    def _save_sprite_with_metadata(self, sprite: Image.Image, asset_id: str, coords: Tuple[int, int], detected_type: str = "material") -> None:
        """Save sprite image and YAML metadata"""
        # Create output directory
        output_dir = Path("assets/harvested")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save PNG
        sprite_path = output_dir / f"{asset_id}.png"
        sprite.save(sprite_path)
        
        # Create YAML metadata (Sovereign DNA)
        metadata = {
            "object_id": asset_id,
            "object_type": detected_type,
            "material_id": self.material_entry.get().strip(),
            "sprite_path": f"assets/harvested/{asset_id}.png",
            "collision": self.collision_var.get(),
            "auto_detected": self.auto_detect_var.get(),
            "auto_cleaned": self.auto_clean_var.get(),
            "grid_coords": {
                "x": coords[0],
                "y": coords[1],
                "grid_size": self.grid_size,
                "offset_x": self.offset_x,
                "offset_y": self.offset_y
            },
            "dimensions": {
                "width": self.grid_size,
                "height": self.grid_size
            },
            "detection_info": {
                "detected_type": detected_type,
                "is_chest": detected_type == "entity" and self._is_chest(sprite, {}, self.grid_size, self.grid_size),
                "edge_threshold": self.threshold_var.get() if self.auto_clean_var.get() else None
            }
        }
        
        # Save YAML
        yaml_path = output_dir / f"{asset_id}.yaml"
        with open(yaml_path, 'w') as f:
            yaml.dump(metadata, f, default_flow_style=False, sort_keys=False)
        
        logger.info(f"💾 Saved {asset_id} ({detected_type}): PNG + YAML metadata")
    
    def _select_next_tile(self, current_x: int, current_y: int) -> None:
        """Select the next tile in the grid"""
        # Calculate next position (left to right, top to bottom)
        w, h = self.raw_image.size
        cols = (w - self.offset_x) // self.grid_size
        
        next_x = current_x + 1
        next_y = current_y
        
        if next_x >= cols:
            next_x = 0
            next_y += 1
        
        # Calculate pixel coordinates
        pixel_x = self.offset_x + next_x * self.grid_size
        pixel_y = self.offset_y + next_y * self.grid_size
        
        # Check bounds
        if pixel_x + self.grid_size <= w and pixel_y + self.grid_size <= h:
            # Select next tile
            self.canvas.delete("selector")
            self.canvas.create_rectangle(
                pixel_x, pixel_y, pixel_x + self.grid_size, pixel_y + self.grid_size,
                outline="#ff00ff", width=2, tags="selector"
            )
            
            self.selected_coords = (pixel_x, pixel_y)
            self.status_label.config(text=f"Selected: ({next_x}, {next_y})")


def main():
    """Main entry point"""
    root = tk.Tk()
    app = DGTSheetCutter(root)
    root.mainloop()


if __name__ == "__main__":
    main()
