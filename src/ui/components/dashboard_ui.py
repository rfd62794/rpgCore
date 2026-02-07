"""
Dashboard UI Component Registry

Phase 10: Component-Based UI Architecture
Fixed-Grid Component Registry for the Director's Console layout.

ADR 027: Component-Based UI Synchronization
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum

from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.align import Align
from rich.live import Live

from loguru import logger

# Import components
from .vitals import VitalsComponent, VitalStatus, HealthStatus, FatigueStatus
from .inventory import InventoryComponent, InventoryItem, ItemRarity, ItemType
from .viewport import ViewportComponent, ViewportState
from .goals import GoalsComponent, GoalState, ObjectiveType

from game_state import GameState
from world_ledger import WorldLedger
from logic.faction_system import FactionSystem


class ZoneType(Enum):
    """Dashboard zones for fixed-grid layout."""
    VIEWPORT = "viewport"      # Main world view (center)
    VITALS = "vitals"          # Character stats (top-right)
    INVENTORY = "inventory"      # Items and equipment (bottom-right)
    GOALS = "goals"              # Objectives and quests (bottom-left)
    CONVERSATION = "conversation"  # Dialogue feed (left)
    STATUS = "status"            # System status (top-left)


@dataclass
class DashboardState:
    """Global dashboard state for component synchronization."""
    viewport_state: ViewportState
    vital_status: VitalStatus
    inventory_items: List[InventoryItem]
    goal_state: GoalState
    conversation_messages: List[Dict[str, Any]]
    system_status: Dict[str, Any]
    last_update: float
    pulse_active: bool
    
    def needs_update(self, current_time: float) -> bool:
        """Check if dashboard needs update based on component states."""
        # Update every 100ms minimum
        return current_time - self.last_update > 0.1


class DashboardUI:
    """
    Fixed-Grid Component Registry for the Director's Console.
    
    Manages the 4-zone layout with synchronized component updates.
    """
    
    def __init__(self, console: Console, world_ledger: WorldLedger, faction_system: Optional[FactionSystem] = None):
        """Initialize the dashboard UI."""
        self.console = console
        self.world_ledger = world_ledger
        self.faction_system = faction_system
        
        # Initialize components
        self.viewport = ViewportComponent(console, world_ledger, faction_system)
        self.vitals = VitalsComponent(console)
        self.inventory = InventoryComponent(console)
        self.goals = GoalsComponent(console)
        
        # Dashboard state
        self.state = DashboardState(
            viewport_state=self.viewport.state,
            vital_status=VitalStatus(
                hp=100,
                max_hp=100,
                fatigue=0,
                max_fatigue=100,
                attributes={"strength": 12, "dexterity": 14, "constitution": 13, "intelligence": 11, "width": 10, "charisma": 12},
                status_effects=[]
            ),
            inventory_items=[],
            goal_state=GoalState(
                active_goals=[],
                completed_goals=[],
                current_objective=None,
                legacy_resonance=[]
            ),
            conversation_messages=[],
            system_status={},
            last_update=0.0,
            pulse_active=False
        )
        
        # Layout configuration
        self.zones = {
            ZoneType.VIEWPORT: {"position": (0, 0), "size": (80, 24), "priority": 1},
            ZoneType.VITALS: {"position": (80, 0), "size": (40, 12), "priority": 2},
            ZoneType.INVENTORY: {"position": (80, 12), "size": (40, 12), "priority": 3},
            ZoneType.GOALS: {"position": (0, 24), "size": (60, 12), "priority": 4},
            ZoneType.CONVERSATION: {"position": (60, 24), "size": (20, 12), "priority": 5},
            ZoneType.STATUS: {"position": (0, 36), "size": (80, 4), "priority": 6}
        }
        
        # Live display
        self.live = None
        self.is_active = False
        
        logger.info("Dashboard UI initialized with 4-zone fixed-grid layout")
    
    def start_dashboard(self) -> None:
        """Start the live dashboard display."""
        if self.is_active:
            return
        
        self.is_active = True
        self.live = Live(self._render_dashboard, console=self.console, refresh_per_second=10)
        
        logger.info("Dashboard UI started with live display")
    
    def stop_dashboard(self) -> None:
        """Stop the live dashboard display."""
        if not self.is_active:
            return
        
        if self.live:
            self.live.stop()
            self.live = None
        
        self.is_active = False
        logger.info("Dashboard UI stopped")
    
    def update_game_state(self, game_state: GameState) -> None:
        """Update dashboard with new game state."""
        import time
        
        current_time = time.time()
        
        # Update vital status
        self.state.vital_status = VitalStatus(
            hp=game_state.player.hp,
            max_hp=game_state.player.max_hp,
            fatigue=0,  # TODO: Add fatigue tracking
            max_fatigue=100,
            attributes=game_state.player.attributes,
            status_effects=[]  # TODO: Add status effects
        )
        
        # Update viewport state
        self.state.viewport_state.player_position = (game_state.position.x, game_state.position.y)
        self.state.viewport_state.player_angle = game_state.player_angle
        
        # Update inventory
        # TODO: Sync with game_state.inventory
        
        # Update goals
        # TODO: Sync with game_state.goal_stack
        
        # Update conversation
        # TODO: Sync with conversation engine
        
        # Update system status
        self.state.system_status = {
            "turn": game_state.world_time,
            "position": (game_state.position.x, game_state.position.y),
            "active": self.is_active
        }
        
        # Check for pulse effect
        if self.vitals.update_vitals(self.state.vital_status):
            self.state.pulse_active = True
        
        self.state.last_update = current_time
    
    def _render_dashboard(self) -> Panel:
        """Render the complete dashboard layout."""
        # Create layout
        layout = Layout()
        
        # Add zones in order of priority
        for zone_type, config in sorted(self.zones.items(), key=lambda x: x[1]["priority"]):
            component = self._get_component_for_zone(zone_type)
            if component:
                panel = self._render_component(component, zone_type)
                layout[config["position"][0]:config["position"][1]] = panel
        
        # Create main panel
        main_panel = Panel(
            layout,
            title="[bold blue]DIRECTOR'S CONSOLE[/bold blue]",
            border_style="blue",
            padding=(0, 0)
        )
        
        return main_panel
    
    def _get_component_for_zone(self, zone_type: ZoneType):
        """Get the component for a specific zone."""
        component_map = {
            ZoneType.VIEWPORT: self.viewport,
            ZoneType.VITALS: self.vitals,
            ZoneType.INVENTORY: self.inventory,
            ZoneType.GOALS: self.goals
        }
        return component_map.get(zone_type)
    
    def _render_component(self, component, zone_type: ZoneType) -> Panel:
        """Render a specific component for its zone."""
        try:
            if zone_type == ZoneType.VIEWPORT:
                return component.render_frame(self._get_mock_game_state())
            elif zone_type == ZoneType.VITALS:
                pulse = self.vitals.update_pulse()
                return component.render_vitals(self.state.vital_status, pulse)
            elif zone_type == ZoneType.INVENTORY:
                return component.render_inventory()
            elif zone_type == ZoneType.GOALS:
                return component.render_goals(self.state.goal_state)
            else:
                return Panel("Component not implemented", title=f"[red]{zone_type.value}[/red]")
        except Exception as e:
            logger.error(f"Error rendering component {zone_type}: {e}")
            return Panel(f"[red]Error in {zone_type.value}[/red]\n{str(e)}", title=f"[red]{zone_type.value} ERROR[/red]")
    
    def _get_mock_game_state(self) -> GameState:
        """Get a mock game state for testing."""
        from game_state import PlayerStats
        
        player = PlayerStats(
            name="Test Player",
            attributes=self.state.vital_status.attributes,
            hp=self.state.vital_status.hp,
            max_hp=self.state.vital_status.max_hp,
            gold=100
        )
        
        from game_state import GameState
        game_state = GameState(player=player)
        game_state.position = self.state.viewport_state.player_position
        game_state.player_angle = self.state.viewport_state.player_angle
        game_state.world_time = self.state.system_status.get("turn", 0)
        
        return game_state
    
    def get_dashboard_summary(self) -> Dict[str, Any]:
        """Get summary of dashboard state."""
        return {
            "zones": list(self.zones.keys()),
            "viewport": self.viewport.get_viewport_summary(),
            "vitals": self.vitals.get_vitals_summary(self.state.vital_status),
            "inventory": self.inventory.get_inventory_summary(),
            "goals": self.goals.get_goals_summary(self.state.goal_state),
            "is_active": self.is_active,
            "pulse_active": self.state.pulse_active,
            "last_update": self.state.last_update
        }
    
    def resize_dashboard(self, terminal_width: int, terminal_height: int) -> bool:
        """
        Resize dashboard to fit terminal dimensions.
        
        Args:
            terminal_width: Terminal width
            terminal_height: Terminal height
            
        Returns:
            True if resize was successful
        """
        # Calculate new zone sizes
        viewport_width = min(80, terminal_width - 40)
        viewport_height = min(24, terminal_height - 12)
        
        # Update viewport component
        success = self.viewport.resize_viewport(viewport_width, viewport_height)
        
        if success:
            # Update zone configurations
            self.zones[ZoneType.VIEWPORT]["size"] = (viewport_width, viewport_height)
            self.zones[ZoneType.VITALS]["position"] = (viewport_width, 0)
            self.zones[ZoneType.INVENTORY]["position"] = (viewport_width, viewport_height // 2)
            self.zones[ZoneType.GOALS]["position"] = (0, viewport_height)
            self.zones[ZoneType.CONVERSATION]["position"] = (viewport_width, viewport_height)
            self.zones[ZoneType.STATUS]["position"] = (0, viewport_height + 12)
            
            logger.info(f"Dashboard resized to {terminal_width}x{terminal_height}")
        
        return success
    
    def handle_resize(self) -> None:
        """Handle terminal resize event."""
        # Get terminal dimensions
        terminal_size = self.console.size
        if terminal_size:
            terminal_width, terminal_height = terminal_size
            self.resize_dashboard(terminal_width, terminal_height)


# Export for use by other modules
__all__ = ["DashboardUI", "DashboardState", "ZoneType"]
