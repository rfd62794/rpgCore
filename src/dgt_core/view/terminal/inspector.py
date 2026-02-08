"""
Terminal Inspector - Raw State Dumps for Debug Mode
ADR 162: Terminal Utilities - Skeptical Auditor Mode
"""

import json
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict

from loguru import logger


@dataclass
class InspectorReport:
    """Comprehensive system inspection report"""
    timestamp: float
    system_state: Dict[str, Any]
    fleet_state: List[Dict[str, Any]]
    tactical_state: Dict[str, Any]
    evolution_state: Dict[str, Any]
    performance_metrics: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return asdict(self)
    
    def to_json(self, indent: int = 2) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict(), indent=indent, default=str)


class TerminalInspector:
    """Raw terminal state inspector for debugging and auditing"""
    
    def __init__(self):
        self.inspection_history: List[InspectorReport] = []
        self.max_history = 100
        
        logger.debug("🔍 TerminalInspector initialized")
    
    def inspect_system(self, 
                      system_state: Dict[str, Any],
                      fleet_state: List[Dict[str, Any]],
                      tactical_state: Dict[str, Any],
                      evolution_state: Dict[str, Any],
                      performance_metrics: Dict[str, Any]) -> InspectorReport:
        """Perform comprehensive system inspection"""
        
        report = InspectorReport(
            timestamp=time.time(),
            system_state=system_state,
            fleet_state=fleet_state,
            tactical_state=tactical_state,
            evolution_state=evolution_state,
            performance_metrics=performance_metrics
        )
        
        # Add to history
        self.inspection_history.append(report)
        if len(self.inspection_history) > self.max_history:
            self.inspection_history.pop(0)
        
        logger.debug(f"🔍 System inspection completed: {len(fleet_state)} ships")
        return report
    
    def dump_fleet_state(self, fleet_state: List[Dict[str, Any]], format_type: str = "table") -> str:
        """Dump fleet state in specified format"""
        if format_type == "table":
            return self._format_fleet_table(fleet_state)
        elif format_type == "json":
            return json.dumps(fleet_state, indent=2, default=str)
        elif format_type == "compact":
            return self._format_fleet_compact(fleet_state)
        else:
            return self._format_fleet_table(fleet_state)
    
    def _format_fleet_table(self, fleet_state: List[Dict[str, Any]]) -> str:
        """Format fleet state as ASCII table"""
        if not fleet_state:
            return "No ships in fleet"
        
        # Header
        header = f"{'Ship ID':<12} {'Pos':<12} {'Health':<8} {'Thrust':<8} {'Engine':<10} {'Role':<10}"
        separator = "-" * len(header)
        
        lines = [header, separator]
        
        # Ship data
        for ship in fleet_state:
            ship_id = ship.get('ship_id', 'UNKNOWN')[:12]
            pos = ship.get('position', (0, 0))
            pos_str = f"({pos[0]:.0f},{pos[1]:.0f})"[:12]
            health = f"{ship.get('health_percentage', 0):.0%}"[:8]
            thrust = "ON" if ship.get('thrust_active', False) else "OFF"
            engine = ship.get('engine_type', 'UNKNOWN')[:10]
            role = ship.get('role', 'UNKNOWN')[:10]
            
            line = f"{ship_id:<12} {pos_str:<12} {health:<8} {thrust:<8} {engine:<10} {role:<10}"
            lines.append(line)
        
        return "\n".join(lines)
    
    def _format_fleet_compact(self, fleet_state: List[Dict[str, Any]]) -> str:
        """Format fleet state in compact one-line-per-ship format"""
        lines = []
        
        for ship in fleet_state:
            ship_id = ship.get('ship_id', 'UNKNOWN')
            pos = ship.get('position', (0, 0))
            health = ship.get('health_percentage', 0)
            thrust = "T" if ship.get('thrust_active', False) else "F"
            
            line = f"{ship_id}:({pos[0]:.0f},{pos[1]:.0f}) H:{health:.0%} {thrust}"
            lines.append(line)
        
        return "\n".join(lines)
    
    def dump_tactical_state(self, tactical_state: Dict[str, Any]) -> str:
        """Dump tactical state"""
        lines = ["=== TACTICAL STATE ==="]
        
        tactical_items = [
            ("Total Ships", tactical_state.get('total_ships', 0)),
            ("Active Engagements", tactical_state.get('active_engagements', 0)),
            ("Fleet DPS", f"{tactical_state.get('fleet_dps', 0):.1f}"),
            ("Avg Accuracy", f"{tactical_state.get('avg_accuracy', 0):.1%}"),
            ("Command Confidence", f"{tactical_state.get('command_confidence', 0):.1%}"),
            ("Target Locks", tactical_state.get('target_locks', 0)),
        ]
        
        for key, value in tactical_items:
            lines.append(f"{key:<20}: {value}")
        
        return "\n".join(lines)
    
    def dump_evolution_state(self, evolution_state: Dict[str, Any]) -> str:
        """Dump evolution state"""
        lines = ["=== EVOLUTION STATE ==="]
        
        evolution_items = [
            ("Generation", evolution_state.get('generation', 0)),
            ("Population Size", evolution_state.get('population_size', 0)),
            ("Avg Fitness", f"{evolution_state.get('avg_fitness', 0):.3f}"),
            ("Best Fitness", f"{evolution_state.get('best_fitness', 0):.3f}"),
            ("Mutation Rate", f"{evolution_state.get('mutation_rate', 0):.3f}"),
            ("Elite Count", evolution_state.get('elite_count', 0)),
        ]
        
        for key, value in evolution_items:
            lines.append(f"{key:<20}: {value}")
        
        return "\n".join(lines)
    
    def dump_performance_metrics(self, performance_metrics: Dict[str, Any]) -> str:
        """Dump performance metrics"""
        lines = ["=== PERFORMANCE METRICS ==="]
        
        perf_items = [
            ("FPS", f"{performance_metrics.get('fps', 0):.1f}"),
            ("Frame Time", f"{performance_metrics.get('frame_time_ms', 0):.1f}ms"),
            ("Physics Time", f"{performance_metrics.get('physics_time_ms', 0):.1f}ms"),
            ("Render Time", f"{performance_metrics.get('render_time_ms', 0):.1f}ms"),
            ("Memory Usage", f"{performance_metrics.get('memory_mb', 0):.1f}MB"),
            ("CPU Usage", f"{performance_metrics.get('cpu_percent', 0):.1f}%"),
        ]
        
        for key, value in perf_items:
            lines.append(f"{key:<20}: {value}")
        
        return "\n".join(lines)
    
    def generate_full_report(self, report: InspectorReport) -> str:
        """Generate comprehensive inspection report"""
        sections = []
        
        sections.append(f"=== SYSTEM INSPECTION REPORT ===")
        sections.append(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(report.timestamp))}")
        sections.append("")
        
        sections.append(self.dump_fleet_state(report.fleet_state))
        sections.append("")
        
        sections.append(self.dump_tactical_state(report.tactical_state))
        sections.append("")
        
        sections.append(self.dump_evolution_state(report.evolution_state))
        sections.append("")
        
        sections.append(self.dump_performance_metrics(report.performance_metrics))
        
        return "\n".join(sections)
    
    def save_report_to_file(self, report: InspectorReport, filename: str) -> bool:
        """Save inspection report to file"""
        try:
            with open(filename, 'w') as f:
                f.write(self.generate_full_report(report))
            
            logger.info(f"🔍 Inspection report saved: {filename}")
            return True
            
        except Exception as e:
            logger.error(f"🔍 Failed to save report: {e}")
            return False
    
    def get_latest_report(self) -> Optional[InspectorReport]:
        """Get the most recent inspection report"""
        return self.inspection_history[-1] if self.inspection_history else None
    
    def clear_history(self):
        """Clear inspection history"""
        self.inspection_history.clear()
        logger.debug("🔍 Inspection history cleared")


# Factory function for easy initialization
def create_terminal_inspector() -> TerminalInspector:
    """Create a TerminalInspector instance"""
    return TerminalInspector()


# Global instance
terminal_inspector = create_terminal_inspector()
