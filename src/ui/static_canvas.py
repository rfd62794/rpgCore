"""
Static Canvas Protocol

Phase 11: Static Canvas Implementation
Fixed-grid rendering system that prevents data loss and flicker.

ADR 028: Static Canvas Rendering Protocol
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum
import time

from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.align import Align
from rich.live import Live
from rich.text import Text

from loguru import logger

# Import components
from .components.dashboard_ui import DashboardUI, ZoneType
from .components.vitals import VitalStatus
from .components.inventory import InventoryItem
from .components.goals import GoalState
from .components.viewport import ViewportState

from game_state import GameState
from world_ledger import WorldLedger
from logic.faction_system import FactionSystem


class RenderMode(Enum):
    """Rendering modes for the static canvas."""
    LIVE = "live"          # Real-time updates with Live display
    STATIC = "static"        # Manual refresh calls
    AUTO = "auto"           # Automatic refresh at intervals


@dataclass
class CanvasState:
    """Current state of the static canvas."""
    game_state: GameState
    viewport_state: ViewportState
    vital_status: VitalStatus
    inventory_items: List[InventoryItem]
    goal_state: GoalState
    conversation_messages: List[Dict[str, Any]]
    system_status: Dict[str, Any]
    last_render_time: float
    frame_count: int
    is_dirty: bool
    
    def mark_dirty(self):
        """Mark the canvas as needing redraw."""
        self.is_dirty = True
        self.last_render_time = time.time()


class StaticCanvas:
    """
    Static Canvas Protocol for fixed-grid rendering.
    
    Prevents data loss and flicker by treating the terminal as a static canvas
    rather than a scrolling log.
    """
    
    def __init__(self, console: Console, world_ledger: WorldLedger, faction_system: Optional[FactionSystem] = None):
        """Initialize the static canvas."""
        self.console = console
        self.world_ledger = world_ledger
        self.faction_system = faction_system
        
        # Initialize dashboard UI
        self.dashboard = DashboardUI(console, world_ledger, faction_system)
        
        # Canvas state
        self.state = CanvasState(
            game_state=None,
            viewport_state=self.dashboard.viewport.state,
            vital_status=VitalStatus(
                hp=100,
                max_hp=100,
                fatigue=0,
                max_fatigue=100,
                attributes={"strength": 12, "dexterity": 14, "constitution": 13, "intelligence": 11, "wisdom": 10, "charisma": 12},
                status_effects=[]
            ),
            inventory_items=[],
            goal_state=GoalState(
                active_goals=[],
                completed_goals=[],
                current_objective=None,
                legacy_resonance=[],
                total_completed=0,
                total_failed=0,
                last_update=0.0
            ),
            conversation_messages=[],
            system_status={},
            last_render_time=0.0,
            frame_count=0,
            is_dirty=True
        )
        
        # Rendering configuration
        self.render_mode = RenderMode.LIVE
        self.target_fps = 10.0  # Target refresh rate
        self.min_terminal_width = 80  # Reduced for testing
        self.min_terminal_height = 24  # Reduced for testing
        
        # Live display
        self.live = None
        self.is_active = False
        
        # Layout configuration
        self.layout_config = {
            "header_height": 3,
            "footer_height": 5,
            "viewport_ratio": 2,
            "sidebar_ratio": 1,
            "vitals_ratio": 1,
            "inventory_ratio": 1,
            "goals_ratio": 2,
            "dialogue_ratio": 1
        }
        
        logger.info("Static Canvas initialized with fixed-grid protocol")
    
    def start_live_display(self) -> bool:
        """
        Start the live display mode.
        
        Returns:
            True if live display started successfully
        """
        if self.is_active:
            return False
        
        # Check terminal size
        if not self._check_terminal_size():
            return False
        
        try:
            self.live = Live(
                self._render_frame(),
                console=self.console,
                refresh_per_second=self.target_fps,
                transient=False  # Don't clear screen on exit
            )
            self.live.start()
            self.is_active = True
            self.render_mode = RenderMode.LIVE
            
            logger.info(f"Static Canvas live display started at {self.target_fps} FPS")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start live display: {e}")
            return False
    
    def stop_live_display(self) -> None:
        """Stop the live display mode."""
        if not self.is_active:
            return
        
        if self.live:
            self.live.stop()
            self.live = None
        
        self.is_active = False
        self.render_mode = RenderMode.STATIC
        
        logger.info("Static Canvas live display stopped")
    
    def update_game_state(self, game_state: GameState) -> None:
        """
        Update the game state and mark canvas as dirty.
        
        Args:
            game_state: New game state
        """
        self.state.game_state = game_state
        self.state.viewport_state.player_position = (game_state.position.x, game_state.position.y)
        self.state.viewport_state.player_angle = game_state.player_angle
        
        # Update vital status
        self.state.vital_status = VitalStatus(
            hp=game_state.player.hp,
            max_hp=game_state.player.max_hp,
            fatigue=0,  # TODO: Add fatigue tracking
            max_fatigue=100,
            attributes=game_state.player.attributes,
            status_effects=[]
        )
        
        # Update system status
        self.state.system_status = {
            "turn": game_state.world_time,
            "position": (game_state.position.x, game_state.position.y),
            "active": self.is_active
        }
        
        # Update dashboard state as well
        self.dashboard.update_game_state(game_state)
        
        # Mark as dirty for redraw
        self.state.mark_dirty()
    
    def refresh(self) -> bool:
        """
        Force a refresh of the canvas.
        
        Returns:
            True if refresh was successful
        """
        if not self.is_active:
            # In static mode, just render once
            try:
                panel = self._render_frame()
                self.console.clear()
                self.console.print(panel)
                return True
            except Exception as e:
                logger.error(f"Failed to refresh canvas: {e}")
                return False
        else:
            # In live mode, the canvas refreshes automatically
            self.state.mark_dirty()
            return True
    
    def _render_frame(self) -> Panel:
        """
        Render the complete canvas frame.
        
        Returns:
            Rich Panel containing the complete canvas
        """
        try:
            # Create layout
            layout = self._create_layout()
            
            # Add content to each section
            self._populate_layout(layout)
            
            # Create main panel
            main_panel = Panel(
                layout,
                title="[bold blue]DIRECTOR'S CONSOLE[/bold blue]",
                border_style="blue",
                padding=(0, 0)
            )
            
            # Update state
            self.state.frame_count += 1
            self.state.is_dirty = False
            
            return main_panel
            
        except Exception as e:
            logger.error(f"Error rendering canvas frame: {e}")
            return Panel(
                f"[red]Canvas Render Error[/red]\n{str(e)}",
                title="[red]CANVAS ERROR[/red]",
                border_style="red"
            )
    
    def _create_layout(self) -> Layout:
        """Create the fixed-grid layout."""
        layout = Layout()
        
        # Get terminal size
        terminal_size = self.console.size
        if not terminal_size:
            terminal_width, terminal_height = self.min_terminal_width, self.min_terminal_height
        else:
            terminal_width, terminal_height = terminal_size
        
        # Split into main sections
        layout.split_column(
            Layout(name="header", size=self.layout_config["header_height"]),
            Layout(name="main"),
            Layout(name="footer", size=self.layout_config["footer_height"])
        )
        
        # Split main into viewport and sidebar
        layout["main"].split_row(
            Layout(name="viewport", ratio=self.layout_config["viewport_ratio"]),
            Layout(name="sidebar", ratio=self.layout_config["sidebar_ratio"])
        )
        
        # Split sidebar into vitals and inventory
        layout["sidebar"].split_column(
            Layout(name="vitals", ratio=self.layout_config["vitals_ratio"]),
            Layout(name="inventory", ratio=self.layout_config["inventory_ratio"])
        )
        
        # Split footer into goals and conversation
        layout["footer"].split_row(
            Layout(name="goals", ratio=self.layout_config["goals_ratio"]),
            Layout(name="conversation", ratio=self.layout_config["dialogue_ratio"])
        )
        
        return layout
    
    def _populate_layout(self, layout: Layout) -> None:
        """Populate the layout with component content."""
        # Add header
        layout["header"].update(Panel(
            "[bold blue]DIRECTOR'S CONSOLE[/bold blue] - Static Canvas Protocol",
            border_style="blue"
        ))
        
        # Add viewport
        try:
            viewport_panel = self.dashboard._render_component(self.dashboard.viewport, ZoneType.VIEWPORT)
            layout["viewport"].update(viewport_panel)
        except Exception as e:
            logger.error(f"Error rendering viewport: {e}")
            layout["viewport"].update(Panel(
                f"[red]Viewport Error[/red]\n{str(e)}",
                title="[red]VIEWPORT ERROR[/red]",
                border_style="red"
            ))
        
        # Add vitals
        try:
            pulse = self.dashboard.vitals.update_pulse()
            vitals_panel = self.dashboard.vitals.render_vitals(self.state.vital_status, pulse)
            layout["vitals"].update(vitals_panel)
        except Exception as e:
            logger.error(f"Error rendering vitals: {e}")
            layout["vitals"].update(Panel(
                f"[red]Vitals Error[/red]\n{str(e)}",
                title="[red]VITALS ERROR[/red]",
                border_style="red"
            ))
        
        # Add inventory
        try:
            inventory_panel = self.dashboard.inventory.render_inventory()
            layout["inventory"].update(inventory_panel)
        except Exception as e:
            logger.error(f"Error rendering inventory: {e}")
            layout["inventory"].update(Panel(
                f"[red]Inventory Error[/red]\n{str(e)}",
                title="[red]INVENTORY ERROR[/red]",
                border_style="red"
            ))
        
        # Add goals
        try:
            goals_panel = self.dashboard.goals.render_goals(self.state.goal_state)
            layout["goals"].update(goals_panel)
        except Exception as e:
            logger.error(f"Error rendering goals: {e}")
            layout["goals"].update(Panel(
                f"[red]Goals Error[/red]\n{str(e)}",
                title="[red]GOALS ERROR[/red]",
                border_style="red"
            ))
        
        # Add conversation
        layout["conversation"].update(Panel(
            "[dim]Conversation Feed[/dim]\n[dim]Ready for dialogue...[/dim]",
            title="[dim]DIALOGUE[/dim]",
            border_style="dim"
        ))
    
    def _check_terminal_size(self) -> bool:
        """
        Check if terminal meets minimum size requirements.
        
        Returns:
            True if terminal size is adequate
        """
        terminal_size = self.console.size
        if not terminal_size:
            logger.warning("Could not determine terminal size")
            return False
        
        width, height = terminal_size
        
        if width < self.min_terminal_width or height < self.min_terminal_height:
            logger.warning(f"Terminal too small: {width}x{height} (minimum: {self.min_terminal_width}x{self.min_terminal_height})")
            
            # Show warning panel
            warning_panel = Panel(
                f"[yellow]Terminal size too small![/yellow]\n\n"
                f"Current: {width}x{height}\n"
                f"Required: {self.min_terminal_width}x{self.min_terminal_height}\n\n"
                f"Please resize your terminal and try again.",
                title="[red]SIZE WARNING[/red]",
                border_style="red"
            )
            
            self.console.print(warning_panel)
            return False
        
        return True
    
    def get_canvas_info(self) -> Dict[str, Any]:
        """Get information about the canvas state."""
        return {
            "render_mode": self.render_mode.value,
            "is_active": self.is_active,
            "target_fps": self.target_fps,
            "frame_count": self.state.frame_count,
            "is_dirty": self.state.is_dirty,
            "last_render_time": self.state.last_render_time,
            "terminal_size": self.console.size,
            "layout_config": self.layout_config
        }
    
    def set_render_mode(self, mode: RenderMode) -> None:
        """Set the rendering mode."""
        self.render_mode = mode
        
        if mode == RenderMode.LIVE and not self.is_active:
            self.start_live_display()
        elif mode == RenderMode.STATIC and self.is_active:
            self.stop_live_display()
    
    def cleanup(self) -> None:
        """Clean up resources."""
        if self.is_active:
            self.stop_live_display()


# Export for use by other modules
__all__ = ["StaticCanvas", "CanvasState", "RenderMode"]
