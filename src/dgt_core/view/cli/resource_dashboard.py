"""
Resource Dashboard - Rich CLI Component for Resource Management
ADR 172: Resource Status Display with Visual Feedback
"""

import time
from typing import Dict, Any, List, Optional

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, BarColumn, TextColumn
from rich.text import Text
from rich.align import Align
from rich.layout import Layout

from loguru import logger

from ...tactics.stakes_manager import StakesManager, ResourceStatus, DeathCause


class ResourceDashboard:
    """Rich CLI dashboard for resource management and permadeath tracking"""
    
    def __init__(self, stakes_manager: StakesManager):
        self.stakes_manager = stakes_manager
        self.console = Console()
        
        logger.debug("⚰️ ResourceDashboard initialized")
    
    def create_resource_table(self, ship_data: Dict[str, Any]) -> Table:
        """Create resource status table"""
        table = Table(title="⚰️ Fleet Resources", border_style="red", show_header=True)
        
        # Define columns
        table.add_column("Ship ID", style="bold white", width=12)
        table.add_column("Fuel", justify="center", width=8)
        table.add_column("Thermal", justify="center", width=8)
        table.add_column("Hull", justify="center", width=8)
        table.add_column("Status", justify="center", width=12)
        table.add_column("Warning", justify="center", width=10)
        
        # Add ship data
        for ship_id, metrics in ship_data.items():
            # Fuel indicator
            fuel_pct = metrics["fuel"]
            if fuel_pct < 20:
                fuel_style = "bold red"
                fuel_text = f"[{fuel_style}]{fuel_pct:.0f}%[/{fuel_style}]"
            elif fuel_pct < 50:
                fuel_style = "yellow"
                fuel_text = f"[{fuel_style}]{fuel_pct:.0f}%[/{fuel_style}]"
            else:
                fuel_style = "green"
                fuel_text = f"[{fuel_style}]{fuel_pct:.0f}%[/{fuel_style}]"
            
            # Thermal indicator
            thermal_pct = metrics["thermal"]
            if thermal_pct > 80:
                thermal_style = "bold red"
                thermal_text = f"[{thermal_style}]{thermal_pct:.0f}%[/{thermal_style}]"
            elif thermal_pct > 60:
                thermal_style = "yellow"
                thermal_text = f"[{thermal_style}]{thermal_pct:.0f}%[/{thermal_style}]"
            else:
                thermal_style = "green"
                thermal_text = f"[{thermal_style}]{thermal_pct:.0f}%[/{thermal_style}]"
            
            # Hull indicator
            hull_pct = metrics["hull"]
            if hull_pct < 20:
                hull_style = "bold red"
                hull_text = f"[{hull_style}]{hull_pct:.0f}%[/{hull_style}]"
            elif hull_pct < 50:
                hull_style = "yellow"
                hull_text = f"[{hull_style}]{hull_pct:.0f}%[/{hull_style}]"
            else:
                hull_style = "green"
                hull_text = f"[{hull_style}]{hull_pct:.0f}%[/{hull_style}]"
            
            # Status
            status = metrics["status"]
            if status == "depleted":
                status_style = "bold red blink"
                status_text = f"[{status_style}]DEPLETED[/{status_style}]"
            elif status == "critical":
                status_style = "bold red"
                status_text = f"[{status_style}]CRITICAL[/{status_style}]"
            elif status == "low":
                status_style = "yellow"
                status_text = f"[{status_style}]LOW[/{status_style}]"
            else:
                status_style = "green"
                status_text = f"[{status_style}]OPERATIONAL[/{status_style}]"
            
            # Warning indicator
            if not metrics["operational"]:
                warning_text = "[bold red blink]⚠️[/bold red blink]"
            elif status in ["critical", "low"]:
                warning_text = "[yellow]⚠️[/yellow]"
            else:
                warning_text = "[green]✓[/green]"
            
            table.add_row(
                ship_id,
                fuel_text,
                thermal_text,
                hull_text,
                status_text,
                warning_text
            )
        
        return table
    
    def create_graveyard_panel(self, graveyard_data: List[Dict[str, Any]]) -> Panel:
        """Create graveyard summary panel"""
        if not graveyard_data:
            content = Text("No ships in graveyard", style="green")
        else:
            # Create recent deaths table
            table = Table(title="Recent Casualties", border_style="dim red", show_header=True)
            table.add_column("Ship ID", style="bold white", width=12)
            table.add_column("Cause", style="yellow", width=15)
            table.add_column("Gen", justify="center", width=4)
            table.add_column("Victories", justify="center", width=9)
            table.add_column("Epitaph", style="dim", width=30)
            
            for entry in graveyard_data[:5]:  # Show top 5
                cause_style = "red" if entry["death_cause"] == "combat_destruction" else "yellow"
                table.add_row(
                    entry["ship_id"],
                    f"[{cause_style}]{entry['death_cause']}[/{cause_style}]",
                    str(entry["final_generation"]),
                    str(entry["total_victories"]),
                    entry["epitaph"][:27] + "..." if len(entry["epitaph"]) > 30 else entry["epitaph"]
                )
            
            content = table
        
        return Panel(
            content,
            title="⚰️ Graveyard",
            border_style="red",
            padding=(1, 1)
        )
    
    def create_chassis_panel(self, chassis_data: Dict[str, Any]) -> Panel:
        """Create chassis slots panel"""
        total_slots = chassis_data["chassis_slots"]
        used_slots = total_slots - chassis_data["available_slots"]
        graveyard_count = chassis_data["graveyard_count"]
        
        # Create slot visualization
        slot_text = Text()
        for i in range(total_slots):
            if i < used_slots:
                slot_text.append("█", style="green")  # Active ship
            else:
                slot_text.append("░", style="dim")    # Empty slot
        
        slot_text.append(f" {used_slots}/{total_slots} Active")
        
        # Create stats
        stats_text = Text()
        stats_text.append(f"Available Slots: {chassis_data['available_slots']}\n", style="green")
        stats_text.append(f"Graveyard Count: {graveyard_count}\n", style="red")
        stats_text.append(f"Total Lost: {graveyard_count}", style="yellow")
        
        content = Align.center(slot_text) + "\n\n" + stats_text
        
        return Panel(
            content,
            title="🏗️ Chassis Status",
            border_style="cyan",
            padding=(1, 1)
        )
    
    def create_resource_bars(self, ship_id: str) -> Panel:
        """Create individual ship resource bars"""
        metrics = self.stakes_manager.get_resource_status(ship_id)
        if not metrics:
            return Panel(Text("Ship not found", style="red"), title="Resource Status")
        
        # Create progress bars
        progress = Progress(
            TextColumn("[bold]{task.fields[resource]}"),
            BarColumn(bar_width=20),
            TextColumn("{task.percentage:>3.0f}%"),
        )
        
        # Fuel bar
        fuel_color = "red" if metrics.fuel_level < 20 else "yellow" if metrics.fuel_level < 50 else "green"
        fuel_task = progress.add_task("Fuel", total=100, resource="Fuel", completed=metrics.fuel_level)
        progress.update(fuel_task, description=f"[{fuel_color}]Fuel[/{fuel_color}]")
        
        # Thermal bar
        thermal_color = "red" if metrics.thermal_load > 80 else "yellow" if metrics.thermal_load > 60 else "green"
        thermal_task = progress.add_task("Thermal", total=100, resource="Thermal", completed=metrics.thermal_load)
        progress.update(thermal_task, description=f"[{thermal_color}]Thermal[/{thermal_color}]")
        
        # Hull bar
        hull_color = "red" if metrics.hull_integrity < 20 else "yellow" if metrics.hull_integrity < 50 else "green"
        hull_task = progress.add_task("Hull", total=100, resource="Hull", completed=metrics.hull_integrity)
        progress.update(hull_task, description=f"[{hull_color}]Hull[/{hull_color}]")
        
        # Status text
        status = metrics.get_status().value.upper()
        status_color = "red blink" if status == "DEPLETED" else "red" if status == "CRITICAL" else "yellow" if status == "LOW" else "green"
        
        status_text = Text(f"Status: ", style="white")
        status_text.append(f"[{status_color}]{status}[/{status_color}]", style="bold")
        
        content = progress + "\n\n" + Align.center(status_text)
        
        return Panel(
            content,
            title=f"⚰️ {ship_id} Resources",
            border_style="red",
            padding=(1, 1)
        )
    
    def create_refit_panel(self, ship_id: str) -> Panel:
        """Create refit costs panel"""
        costs = self.stakes_manager.get_refit_costs(ship_id)
        if not costs:
            return Panel(Text("Ship not found", style="red"), title="Refit Costs")
        
        # Create costs table
        table = Table(title="Refit Costs", border_style="yellow", show_header=False)
        table.add_column("Service", style="white")
        table.add_column("Cost", justify="right", style="yellow")
        
        total_cost = 0
        for service, cost in costs.items():
            if cost > 0:
                service_name = service.replace("_", " ").title()
                table.add_row(service_name, f"{cost:.0f} credits")
                total_cost += cost
        
        if total_cost > 0:
            table.add_row("─" * 20, "─" * 10)
            table.add_row("[bold]Total[/bold]", f"[bold yellow]{total_cost:.0f} credits[/bold yellow]")
        else:
            table.add_row("[green]All systems optimal[/green]", "")
        
        return Panel(
            table,
            title=f"🔧 {ship_id} Refit",
            border_style="yellow",
            padding=(1, 1)
        )
    
    def generate_full_dashboard(self, ship_id: Optional[str] = None) -> Layout:
        """Generate complete resource dashboard"""
        # Get data
        all_status = self.stakes_manager.get_all_status()
        graveyard = self.stakes_manager.get_graveyard()
        
        # Create layout
        layout = Layout()
        
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="main"),
            Layout(name="footer", size=3)
        )
        
        layout["main"].split_row(
            Layout(name="resources", ratio=2),
            Layout(name="sidebar", ratio=1)
        )
        
        layout["sidebar"].split_column(
            Layout(name="chassis"),
            Layout(name="graveyard")
        )
        
        # Populate sections
        layout["header"].update(self._create_header_panel())
        layout["resources"].update(self.create_resource_table(all_status["active_ships"]))
        layout["chassis"].update(self.create_chassis_panel(all_status))
        layout["graveyard"].update(self.create_graveyard_panel(graveyard))
        
        # Add individual ship details if specified
        if ship_id:
            layout["footer"].update(self.create_resource_bars(ship_id))
        else:
            layout["footer"].update(self._create_footer_panel())
        
        return layout
    
    def _create_header_panel(self) -> Panel:
        """Create header panel"""
        title = Text("⚰️ DGT RESOURCE COMMAND", style="bold red")
        subtitle = Text(f"Hardware Burn & Permadeath System - {time.strftime('%Y-%m-%d %H:%M:%S')}", style="dim")
        
        header_content = Align.center(title) + "\n" + Align.center(subtitle)
        
        return Panel(
            header_content,
            border_style="red",
            padding=(1, 2)
        )
    
    def _create_footer_panel(self) -> Panel:
        """Create footer panel"""
        warning_text = Text("⚠️ WARNING: Resource depletion leads to permadeath. Monitor fuel and thermal levels carefully.", style="yellow")
        return Panel(
            Align.center(warning_text),
            border_style="yellow",
            padding=(1, 1)
        )
    
    def print_emergency_alert(self, ship_id: str, alert_type: str):
        """Print emergency alert to console"""
        if alert_type == "fuel_critical":
            alert = Text(f"🚨 FUEL CRITICAL: {ship_id} - {self.stakes_manager.get_resource_status(ship_id).fuel_level:.1f}% remaining", style="bold red blink")
        elif alert_type == "thermal_critical":
            alert = Text(f"🚨 THERMAL OVERLOAD: {ship_id} - {self.stakes_manager.get_resource_status(ship_id).thermal_load:.1f}% load", style="bold red blink")
        elif alert_type == "hull_critical":
            alert = Text(f"🚨 HULL BREACH: {ship_id} - {self.stakes_manager.get_resource_status(ship_id).hull_integrity:.1f}% integrity", style="bold red blink")
        elif alert_type == "perma_death":
            alert = Text(f"⚰️ PERMADEATH: {ship_id} has been lost to the void", style="bold red")
        else:
            return
        
        self.console.print(Panel(alert, border_style="red", padding=(1, 1)))
