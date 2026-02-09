"""
Glass Cockpit - ADR 193 Right Wing Component

Phase 2: Component Consolidation with Sovereign Viewport Protocol

Modular dashboard for resource management and ship health monitoring.
Renders in the right wing of the sovereign viewport, providing strategic
information and system status displays.

This component has been migrated from src/body/ to support the ADR 193
viewport architecture with responsive scaling and wing integration.
"""

import tkinter as tk
from tkinter import ttk
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
import sys
from pathlib import Path
import time

# Add parent directories for imports
sys.path.append(str(Path(__file__).parent.parent.parent.parent))
sys.path.append(str(Path(__file__).parent.parent.parent))

from loguru import logger
from ..protocols import RenderProtocol, Result
from ...kernel.models import Rectangle
from ...exceptions.core import RenderException, create_render_exception


@dataclass
class MeterConfig:
    """Configuration for a cockpit meter"""
    name: str
    min_value: float = 0.0
    max_value: float = 100.0
    units: str = ""
    color: str = "blue"
    width: int = 200
    height: int = 20


@dataclass
class LabelConfig:
    """Configuration for a cockpit label"""
    name: str
    text: str = ""
    font: str = "Arial"
    font_size: int = 10
    color: str = "black"
    width: int = 150
    height: int = 25


class GlassCockpit(RenderProtocol):
    """Modular dashboard for right wing rendering"""
    
    def __init__(self):
        self.current_wing: Optional[Rectangle] = None
        
        # UI components
        self.root_window: Optional[tk.Tk] = None
        self.main_frame: Optional[ttk.Frame] = None
        self.meters: Dict[str, ttk.Progressbar] = {}
        self.labels: Dict[str, ttk.Label] = {}
        
        # Dashboard state
        self.system_status: Dict[str, float] = {}
        self.alerts: List[str] = []
        
        # Configuration
        self.meter_configs: Dict[str, MeterConfig] = {}
        self.label_configs: Dict[str, LabelConfig] = {}
        
        # Initialize default dashboard
        self._initialize_default_dashboard()
        
        logger.info("🪟 GlassCockpit initialized for right wing rendering")
    
    def initialize(self) -> Result[bool]:
        """Initialize the glass cockpit"""
        try:
            # Create main window if not exists
            if not self.root_window:
                self.root_window = tk.Tk()
                self.root_window.title("Glass Cockpit")
                self.root_window.withdraw()  # Hide main window
            
            # Create main frame
            self.main_frame = ttk.Frame(self.root_window)
            
            # Create dashboard components
            self._create_meters()
            self._create_labels()
            self._create_alert_panel()
            
            logger.success("🪟 GlassCockpit initialized successfully")
            return Result.success_result(True)
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize GlassCockpit: {e}")
            return Result.failure_result(f"Initialization error: {str(e)}")
    
    def shutdown(self) -> Result[None]:
        """Clean shutdown of glass cockpit"""
        try:
            if self.main_frame:
                self.main_frame.destroy()
                self.main_frame = None
            
            if self.root_window:
                self.root_window.destroy()
                self.root_window = None
            
            logger.info("🪟 GlassCockpit shutdown complete")
            return Result.success_result(None)
            
        except Exception as e:
            logger.error(f"❌ Failed to shutdown GlassCockpit: {e}")
            return Result.failure_result(f"Shutdown error: {str(e)}")
    
    def get_state(self) -> Dict[str, Any]:
        """Get current cockpit state"""
        return {
            "system_status": self.system_status.copy(),
            "alerts": self.alerts.copy(),
            "meter_count": len(self.meters),
            "label_count": len(self.labels),
            "wing_region": self.current_wing.__dict__ if self.current_wing else None
        }
    
    def render_to_wing(self, wing_region: Rectangle, scale: float = 1.0) -> Result[bytes]:
        """Render cockpit to wing region with scaling"""
        try:
            self.current_wing = wing_region
            
            # Calculate scaled dimensions
            scaled_width = int(wing_region.width / scale)
            scaled_height = int(wing_region.height / scale)
            
            # Update frame dimensions if needed
            if self.main_frame:
                self.main_frame.config(width=scaled_width, height=scaled_height)
            
            # Update dashboard data
            self._update_dashboard()
            
            # Render cockpit content
            self._render_cockpit_content()
            
            # Get frame as image data
            image_data = self._get_frame_image_data()
            
            return Result.success_result(image_data)
            
        except Exception as e:
            logger.error(f"❌ Failed to render to wing: {e}")
            return Result.failure_result(f"Wing rendering error: {str(e)}")
    
    def update_system_status(self, system_name: str, value: float) -> Result[None]:
        """Update system status value"""
        try:
            self.system_status[system_name] = value
            
            # Update corresponding meter if exists
            if system_name in self.meters:
                meter_config = self.meter_configs.get(system_name)
                if meter_config:
                    # Normalize value to 0-100 range
                    normalized = ((value - meter_config.min_value) / 
                                (meter_config.max_value - meter_config.min_value)) * 100
                    normalized = max(0, min(100, normalized))
                    self.meters[system_name]['value'] = normalized
            
            # Check for alerts
            self._check_alerts(system_name, value)
            
            return Result.success_result(None)
            
        except Exception as e:
            logger.error(f"❌ Failed to update system status: {e}")
            return Result.failure_result(f"Status update error: {str(e)}")
    
    def add_label(self, config: LabelConfig) -> Result[None]:
        """Add a label to the cockpit"""
        try:
            self.label_configs[config.name] = config
            
            if self.main_frame:
                # Create label widget
                label = ttk.Label(
                    self.main_frame,
                    text=config.text,
                    font=(config.font, config.font_size),
                    foreground=config.color
                )
                
                self.labels[config.name] = label
            
            return Result.success_result(None)
            
        except Exception as e:
            logger.error(f"❌ Failed to add label: {e}")
            return Result.failure_result(f"Label addition error: {str(e)}")
    
    def add_meter(self, config: MeterConfig) -> Result[None]:
        """Add a meter to the cockpit"""
        try:
            self.meter_configs[config.name] = config
            
            if self.main_frame:
                # Create progress bar
                meter = ttk.Progressbar(
                    self.main_frame,
                    length=config.width,
                    maximum=100,
                    mode='determinate',
                    orient='horizontal'
                )
                
                self.meters[config.name] = meter
            
            return Result.success_result(None)
            
        except Exception as e:
            logger.error(f"❌ Failed to add meter: {e}")
            return Result.failure_result(f"Meter addition error: {str(e)}")
    
    def add_alert(self, alert_message: str) -> Result[None]:
        """Add an alert to the cockpit"""
        try:
            self.alerts.append(alert_message)
            
            # Keep only recent alerts
            if len(self.alerts) > 10:
                self.alerts = self.alerts[-10:]
            
            return Result.success_result(None)
            
        except Exception as e:
            logger.error(f"❌ Failed to add alert: {e}")
            return Result.failure_result(f"Alert addition error: {str(e)}")
    
    def _initialize_default_dashboard(self) -> None:
        """Initialize default dashboard configuration"""
        # Default meters
        default_meters = {
            "hull_integrity": MeterConfig("Hull Integrity", 0, 100, "%", "green", 200, 20),
            "energy_level": MeterConfig("Energy Level", 0, 100, "%", "blue", 200, 20),
            "shield_strength": MeterConfig("Shield Strength", 0, 100, "%", "cyan", 200, 20),
            "oxygen_level": MeterConfig("Oxygen Level", 0, 100, "%", "yellow", 200, 20),
            "fuel_level": MeterConfig("Fuel Level", 0, 1000, "L", "orange", 200, 20),
            "temperature": MeterConfig("Temperature", -50, 50, "°C", "red", 200, 20)
        }
        
        for name, config in default_meters.items():
            self.meter_configs[name] = config
            self.system_status[name] = 100.0  # Default to full
        
        # Default labels
        default_labels = {
            "ship_name": LabelConfig("Ship Name", "SOVEREIGN SCOUT", "Arial", 12, "white", 150, 25),
            "status": LabelConfig("Status", "OPERATIONAL", "Arial", 10, "green", 150, 25),
            "location": LabelConfig("Location", "SECTOR 7-ALPHA", "Arial", 10, "blue", 150, 25),
            "time": LabelConfig("Time", "00:00:00", "Arial", 10, "white", 150, 25)
        }
        
        for name, config in default_labels.items():
            self.label_configs[name] = config
    
    def _create_meters(self) -> None:
        """Create meter widgets"""
        if not self.main_frame:
            return
        
        meter_frame = ttk.LabelFrame(self.main_frame, text="Systems Status")
        meter_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        for i, (name, config) in enumerate(self.meter_configs.items()):
            # Create label
            label = ttk.Label(meter_frame, text=f"{config.name}:")
            label.grid(row=i, column=0, sticky='w', padx=5, pady=2)
            
            # Create meter
            meter = ttk.Progressbar(
                meter_frame,
                length=config.width,
                maximum=100,
                mode='determinate',
                orient='horizontal'
            )
            meter.grid(row=i, column=1, padx=5, pady=2)
            
            # Create value label
            value_label = ttk.Label(meter_frame, text=f"{config.max_value}{config.units}")
            value_label.grid(row=i, column=2, padx=5, pady=2)
            
            self.meters[name] = meter
    
    def _create_labels(self) -> None:
        """Create label widgets"""
        if not self.main_frame:
            return
        
        label_frame = ttk.LabelFrame(self.main_frame, text="Information")
        label_frame.pack(fill='x', padx=5, pady=5)
        
        for i, (name, config) in enumerate(self.label_configs.items()):
            label = ttk.Label(
                label_frame,
                text=config.text,
                font=(config.font, config.font_size),
                foreground=config.color
            )
            label.pack(anchor='w', padx=5, pady=2)
            
            self.labels[name] = label
    
    def _create_alert_panel(self) -> None:
        """Create alert panel"""
        if not self.main_frame:
            return
        
        alert_frame = ttk.LabelFrame(self.main_frame, text="Alerts")
        alert_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Create text widget for alerts
        alert_text = tk.Text(alert_frame, height=5, width=30, wrap='word')
        alert_text.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Store reference
        self.alert_text = alert_text
    
    def _update_dashboard(self) -> None:
        """Update dashboard with current data"""
        # Update meters
        for name, meter in self.meters.items():
            if name in self.system_status:
                meter_config = self.meter_configs.get(name)
                if meter_config:
                    # Normalize value to 0-100 range
                    normalized = ((self.system_status[name] - meter_config.min_value) / 
                                (meter_config.max_value - meter_config.min_value)) * 100
                    normalized = max(0, min(100, normalized))
                    meter['value'] = normalized
        
        # Update alert panel
        if hasattr(self, 'alert_text'):
            self.alert_text.delete(1.0, tk.END)
            for alert in self.alerts:
                self.alert_text.insert(tk.END, f"• {alert}\n")
    
    def _render_cockpit_content(self) -> None:
        """Render cockpit content"""
        if self.main_frame:
            self.main_frame.update()
    
    def _check_alerts(self, system_name: str, value: float) -> None:
        """Check for alerts based on system status"""
        meter_config = self.meter_configs.get(system_name)
        if not meter_config:
            return
        
        # Check for critical levels
        critical_threshold = meter_config.max_value * 0.2  # 20%
        warning_threshold = meter_config.max_value * 0.5  # 50%
        
        if value <= critical_threshold:
            self.add_alert(f"CRITICAL: {system_name} at {value}{meter_config.units}")
        elif value <= warning_threshold:
            self.add_alert(f"WARNING: {system_name} at {value}{meter_config.units}")
    
    def _get_frame_image_data(self) -> bytes:
        """Get frame as image data"""
        # In a real implementation, this would convert the frame to image data
        # For now, return placeholder data
        return b"cockpit_frame_data_placeholder"


# Factory function for easy creation
def create_glass_cockpit() -> GlassCockpit:
    """Create a GlassCockpit instance"""
    return GlassCockpit()
