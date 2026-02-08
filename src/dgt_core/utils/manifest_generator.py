"""
Session Manifest Generator: Iron Frame Legacy Tracking

Creates comprehensive session manifests that survive outside the chat,
detailing the Voyager's path, Faction shifts, and deterministic seeds.

This ensures the "Iron Frame Legacy" is traceable and provides a complete
audit trail of each 1,000-year world simulation session.
"""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
import hashlib

from loguru import logger
from game_state import GameState
from world_ledger import Coordinate
from d20_core import D20Result
from logic.faction_system import FactionSystem


@dataclass
class SessionEvent:
    """A single event in the session timeline."""
    timestamp: float
    turn: int
    event_type: str  # "action", "movement", "dialogue", "combat", "faction_change"
    description: str
    position: Tuple[int, int]
    heading: float
    data: Dict[str, Any]  # Event-specific data
    deterministic_seed: Optional[int] = None


@dataclass
class VoyagerPath:
    """Complete path taken by the Voyager during the session."""
    coordinates: List[Tuple[int, int]]
    headings: List[float]
    timestamps: List[float]
    turns: List[int]
    
    def add_position(self, coord: Tuple[int, int], heading: float, timestamp: float, turn: int) -> None:
        """Add a new position to the path."""
        self.coordinates.append(coord)
        self.headings.append(heading)
        self.timestamps.append(timestamp)
        self.turns.append(turn)
    
    def get_total_distance(self) -> float:
        """Calculate total Manhattan distance traveled."""
        if len(self.coordinates) < 2:
            return 0.0
        
        total = 0.0
        for i in range(1, len(self.coordinates)):
            prev = self.coordinates[i-1]
            curr = self.coordinates[i]
            total += abs(curr[0] - prev[0]) + abs(curr[1] - prev[1])
        
        return total


@dataclass
class FactionShift:
    """A change in faction relationships during the session."""
    timestamp: float
    turn: int
    faction_a: str
    faction_b: str
    old_relation: str
    new_relation: str
    cause: str  # "player_action", "npc_interaction", "world_event"
    context: str


@dataclass
class WorldStateSnapshot:
    """Snapshot of world state at a specific turn."""
    turn: int
    timestamp: float
    player_hp: int
    player_gold: int
    player_position: Tuple[int, int]
    active_quests: List[str]
    discovered_locations: List[str]
    faction_states: Dict[str, Dict[str, Any]]
    world_time: int  # In-game time in turns since epoch


class SessionManifest:
    """
    Complete session manifest for Iron Frame legacy tracking.
    
    Captures every aspect of a session to ensure traceability
    and provide a comprehensive audit trail.
    """
    
    def __init__(self, session_id: str, start_time: float):
        """
        Initialize session manifest.
        
        Args:
            session_id: Unique session identifier
            start_time: Session start timestamp
        """
        self.session_id = session_id
        self.start_time = start_time
        self.end_time: Optional[float] = None
        
        # Session metadata
        self.version = "1.0"
        self.game_version = "DGT-IronFrame-1.0"
        
        # Session data
        self.events: List[SessionEvent] = []
        self.voyager_path = VoyagerPath([], [], [], [])
        self.faction_shifts: List[FactionShift] = []
        self.world_snapshots: List[WorldStateSnapshot] = []
        
        # Performance metrics
        self.boot_time_ms: Optional[float] = None
        self.total_actions: int = 0
        self.narrative_cache_hits: int = 0
        self.narrative_cache_misses: int = 0
        self.cache_invalidations: int = 0
        
        # Deterministic seeds used
        self.deterministic_seeds: List[int] = []
        
        logger.info(f"📋 Session Manifest initialized: {session_id}")
    
    def add_event(self, event: SessionEvent) -> None:
        """Add an event to the session timeline."""
        self.events.append(event)
        
        # Track deterministic seeds
        if event.deterministic_seed and event.deterministic_seed not in self.deterministic_seeds:
            self.deterministic_seeds.append(event.deterministic_seed)
        
        # Update action count
        if event.event_type == "action":
            self.total_actions += 1
    
    def update_position(self, position: Tuple[int, int], heading: float, turn: int) -> None:
        """Update Voyager position and heading."""
        timestamp = time.time()
        self.voyager_path.add_position(position, heading, timestamp, turn)
    
    def add_faction_shift(self, shift: FactionShift) -> None:
        """Add a faction relationship change."""
        self.faction_shifts.append(shift)
    
    def add_world_snapshot(self, snapshot: WorldStateSnapshot) -> None:
        """Add a world state snapshot."""
        self.world_snapshots.append(snapshot)
    
    def finalize(self, end_time: float) -> None:
        """Finalize the session manifest."""
        self.end_time = end_time
        logger.info(f"📋 Session Manifest finalized: {self.session_id}")
    
    def get_session_duration(self) -> float:
        """Get total session duration in seconds."""
        if self.end_time is None:
            return time.time() - self.start_time
        return self.end_time - self.start_time
    
    def get_cache_hit_rate(self) -> float:
        """Calculate narrative cache hit rate."""
        total_requests = self.narrative_cache_hits + self.narrative_cache_misses
        if total_requests == 0:
            return 0.0
        return self.narrative_cache_hits / total_requests
    
    def generate_checksum(self) -> str:
        """Generate checksum for integrity verification."""
        # Create a deterministic representation
        manifest_data = {
            "session_id": self.session_id,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "events": len(self.events),
            "seeds": sorted(self.deterministic_seeds)
        }
        
        manifest_json = json.dumps(manifest_data, sort_keys=True)
        return hashlib.sha256(manifest_json.encode()).hexdigest()[:16]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert manifest to dictionary for serialization."""
        return {
            "session_id": self.session_id,
            "version": self.version,
            "game_version": self.game_version,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_seconds": self.get_session_duration(),
            "checksum": self.generate_checksum(),
            
            # Voyager path
            "voyager_path": {
                "coordinates": self.voyager_path.coordinates,
                "headings": self.voyager_path.headings,
                "timestamps": self.voyager_path.timestamps,
                "turns": self.voyager_path.turns,
                "total_distance": self.voyager_path.get_total_distance()
            },
            
            # Events
            "events": [asdict(event) for event in self.events],
            
            # Faction shifts
            "faction_shifts": [asdict(shift) for shift in self.faction_shifts],
            
            # World snapshots
            "world_snapshots": [asdict(snapshot) for snapshot in self.world_snapshots],
            
            # Performance metrics
            "performance": {
                "boot_time_ms": self.boot_time_ms,
                "total_actions": self.total_actions,
                "narrative_cache_hits": self.narrative_cache_hits,
                "narrative_cache_misses": self.narrative_cache_misses,
                "cache_hit_rate": self.get_cache_hit_rate(),
                "cache_invalidations": self.cache_invalidations
            },
            
            # Deterministic seeds
            "deterministic_seeds": {
                "seeds_used": self.deterministic_seeds,
                "total_unique": len(self.deterministic_seeds),
                "seed_range": [min(self.deterministic_seeds), max(self.deterministic_seeds)] if self.deterministic_seeds else []
            }
        }


class ManifestGenerator:
    """
    Generates and manages session manifests.
    
    Provides automatic tracking of all session events and
    generates comprehensive legacy artifacts.
    """
    
    def __init__(self, output_dir: Path = Path("sessions")):
        """
        Initialize manifest generator.
        
        Args:
            output_dir: Directory for session manifests
        """
        self.output_dir = output_dir
        self.output_dir.mkdir(exist_ok=True)
        
        self._current_manifest: Optional[SessionManifest] = None
        self._last_faction_states: Dict[str, Dict[str, Any]] = {}
        
        logger.info("📋 Manifest Generator initialized")
    
    def start_session(self, session_id: Optional[str] = None) -> str:
        """
        Start a new session and create manifest.
        
        Args:
            session_id: Optional session ID (auto-generated if None)
            
        Returns:
            Session ID
        """
        if session_id is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            session_id = f"dgt_session_{timestamp}"
        
        self._current_manifest = SessionManifest(session_id, time.time())
        logger.info(f"🚀 Session started: {session_id}")
        
        return session_id
    
    def track_action(self, action_result: D20Result, game_state: GameState, player_input: str) -> None:
        """
        Track a player action in the current session.
        
        Args:
            action_result: Result of D20 resolution
            game_state: Current game state
            player_input: Original player input
        """
        if not self._current_manifest:
            return
        
        # Create event
        event = SessionEvent(
            timestamp=time.time(),
            turn=game_state.turn_count,
            event_type="action",
            description=f"Action: {player_input}",
            position=game_state.player.position,
            heading=getattr(game_state, 'player_heading', 0.0),
            data={
                "intent": getattr(action_result, 'intent_id', 'unknown'),
                "success": action_result.success,
                "roll": action_result.roll,
                "hp_delta": action_result.hp_delta,
                "reputation_deltas": action_result.reputation_deltas
            },
            deterministic_seed=getattr(action_result, 'deterministic_seed', None)
        )
        
        self._current_manifest.add_event(event)
        
        # Update position
        self._current_manifest.update_position(
            game_state.player.position,
            getattr(game_state, 'player_heading', 0.0),
            game_state.turn_count
        )
        
        # Check for faction shifts
        self._check_faction_shifts(game_state)
        
        # Add world snapshot every 10 turns
        if game_state.turn_count % 10 == 0:
            self._add_world_snapshot(game_state)
    
    def track_movement(self, old_position: Tuple[int, int], new_position: Tuple[int, int], 
                       heading: float, turn: int) -> None:
        """
        Track player movement.
        
        Args:
            old_position: Previous position
            new_position: New position
            heading: Player heading
            turn: Current turn
        """
        if not self._current_manifest:
            return
        
        if old_position != new_position:
            event = SessionEvent(
                timestamp=time.time(),
                turn=turn,
                event_type="movement",
                description=f"Moved from {old_position} to {new_position}",
                position=new_position,
                heading=heading,
                data={"old_position": old_position, "new_position": new_position}
            )
            
            self._current_manifest.add_event(event)
        
        self._current_manifest.update_position(new_position, heading, turn)
    
    def track_dialogue(self, npc_id: str, player_input: str, npc_response: str, 
                      position: Tuple[int, int], heading: float, turn: int) -> None:
        """
        Track a dialogue interaction.
        
        Args:
            npc_id: ID of NPC
            player_input: Player's input
            npc_response: NPC's response
            position: Position of interaction
            heading: Player heading
            turn: Current turn
        """
        if not self._current_manifest:
            return
        
        event = SessionEvent(
            timestamp=time.time(),
            turn=turn,
            event_type="dialogue",
            description=f"Dialogue with {npc_id}",
            position=position,
            heading=heading,
            data={
                "npc_id": npc_id,
                "player_input": player_input,
                "npc_response": npc_response[:100] + "..." if len(npc_response) > 100 else npc_response
            }
        )
        
        self._current_manifest.add_event(event)
    
    def update_performance_metrics(self, boot_time_ms: Optional[float] = None,
                                  cache_hits: Optional[int] = None,
                                  cache_misses: Optional[int] = None,
                                  cache_invalidations: Optional[int] = None) -> None:
        """
        Update performance metrics.
        
        Args:
            boot_time_ms: Boot time in milliseconds
            cache_hits: Narrative cache hits
            cache_misses: Narrative cache misses
            cache_invalidations: Cache invalidations
        """
        if not self._current_manifest:
            return
        
        if boot_time_ms is not None:
            self._current_manifest.boot_time_ms = boot_time_ms
        if cache_hits is not None:
            self._current_manifest.narrative_cache_hits = cache_hits
        if cache_misses is not None:
            self._current_manifest.narrative_cache_misses = cache_misses
        if cache_invalidations is not None:
            self._current_manifest.cache_invalidations = cache_invalidations
    
    def end_session(self) -> Optional[Path]:
        """
        End the current session and save manifest.
        
        Returns:
            Path to saved manifest file
        """
        if not self._current_manifest:
            logger.warning("No active session to end")
            return None
        
        # Finalize manifest
        self._current_manifest.finalize(time.time())
        
        # Save manifest
        manifest_path = self._save_manifest(self._current_manifest)
        
        # Generate summary
        self._generate_summary(self._current_manifest)
        
        logger.info(f"📋 Session ended: {self._current_manifest.session_id}")
        
        # Clear current manifest
        self._current_manifest = None
        self._last_faction_states.clear()
        
        return manifest_path
    
    def _check_faction_shifts(self, game_state: GameState) -> None:
        """Check for faction relationship changes."""
        if not hasattr(game_state, 'faction_system') or not game_state.faction_system:
            return
        
        current_states = {}
        faction_system = game_state.faction_system
        
        # Get current faction states
        for faction_id, faction in faction_system.factions.items():
            current_states[faction_id] = {
                "power": faction.current_power,
                "territories": len(faction.territories),
                "relations": {rel_id: rel.relation_type for rel_id, rel in faction.relations.items()}
            }
        
        # Check for changes
        for faction_id, current_state in current_states.items():
            if faction_id in self._last_faction_states:
                last_state = self._last_faction_states[faction_id]
                
                # Check relations changes
                for other_faction, current_relation in current_state["relations"].items():
                    last_relation = last_state["relations"].get(other_faction)
                    if last_relation and last_relation != current_relation:
                        shift = FactionShift(
                            timestamp=time.time(),
                            turn=game_state.turn_count,
                            faction_a=faction_id,
                            faction_b=other_faction,
                            old_relation=last_relation,
                            new_relation=current_relation,
                            cause="player_action",
                            context=f"Relation changed from {last_relation} to {current_relation}"
                        )
                        self._current_manifest.add_faction_shift(shift)
        
        self._last_faction_states = current_states
    
    def _add_world_snapshot(self, game_state: GameState) -> None:
        """Add a world state snapshot."""
        snapshot = WorldStateSnapshot(
            turn=game_state.turn_count,
            timestamp=time.time(),
            player_hp=game_state.player.hp,
            player_gold=game_state.player.gold,
            player_position=game_state.player.position,
            active_quests=getattr(game_state, 'active_quests', []),
            discovered_locations=getattr(game_state, 'discovered_locations', []),
            faction_states=self._last_faction_states.copy(),
            world_time=getattr(game_state, 'world_time', game_state.turn_count)
        )
        
        self._current_manifest.add_world_snapshot(snapshot)
    
    def _save_manifest(self, manifest: SessionManifest) -> Path:
        """Save manifest to file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{manifest.session_id}_manifest.json"
        manifest_path = self.output_dir / filename
        
        with open(manifest_path, 'w') as f:
            json.dump(manifest.to_dict(), f, indent=2)
        
        logger.info(f"📋 Manifest saved: {manifest_path}")
        return manifest_path
    
    def _generate_summary(self, manifest: SessionManifest) -> None:
        """Generate human-readable summary."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        summary_filename = f"{manifest.session_id}_summary.md"
        summary_path = self.output_dir / summary_filename
        
        with open(summary_path, 'w') as f:
            f.write(f"# DGT Session Summary\n\n")
            f.write(f"**Session ID:** {manifest.session_id}\n")
            f.write(f"**Date:** {datetime.fromtimestamp(manifest.start_time).strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"**Duration:** {manifest.get_session_duration():.1f} seconds\n")
            f.write(f"**Total Turns:** {manifest.world_snapshots[-1].turn if manifest.world_snapshots else 0}\n\n")
            
            f.write("## Voyager Journey\n\n")
            f.write(f"- **Total Distance:** {manifest.voyager_path.get_total_distance():.1f} tiles\n")
            f.write(f"- **Positions Visited:** {len(set(manifest.voyager_path.coordinates))}\n")
            f.write(f"- **Final Position:** {manifest.voyager_path.coordinates[-1] if manifest.voyager_path.coordinates else 'Unknown'}\n\n")
            
            f.write("## Performance Metrics\n\n")
            f.write(f"- **Boot Time:** {manifest.boot_time_ms:.1f}ms\n")
            f.write(f"- **Total Actions:** {manifest.total_actions}\n")
            f.write(f"- **Cache Hit Rate:** {manifest.get_cache_hit_rate():.1%}\n")
            f.write(f"- **Cache Invalidations:** {manifest.cache_invalidations}\n\n")
            
            f.write("## World Events\n\n")
            f.write(f"- **Total Events:** {len(manifest.events)}\n")
            f.write(f"- **Faction Shifts:** {len(manifest.faction_shifts)}\n")
            f.write(f"- **World Snapshots:** {len(manifest.world_snapshots)}\n\n")
            
            f.write("## Deterministic Seeds\n\n")
            f.write(f"- **Unique Seeds Used:** {len(manifest.deterministic_seeds)}\n")
            if manifest.deterministic_seeds:
                f.write(f"- **Seed Range:** {min(manifest.deterministic_seeds)} - {max(manifest.deterministic_seeds)}\n")
            f.write(f"- **Checksum:** `{manifest.generate_checksum()}`\n\n")
            
            f.write("## Session Integrity\n\n")
            f.write("This manifest provides a complete audit trail of the session, ensuring:")
            f.write("\n- ✅ **Deterministic Replay**: All actions can be reproduced exactly")
            f.write("\n- ✅ **World Consistency**: Faction shifts and world changes are tracked")
            f.write("\n- ✅ **Performance Trace**: System behavior is fully documented")
            f.write("\n- ✅ **Legacy Preservation**: The 1,000-year world simulation is preserved")
        
        logger.info(f"📋 Summary saved: {summary_path}")


# Global instance for easy access
_manifest_generator: Optional[ManifestGenerator] = None


def get_manifest_generator() -> ManifestGenerator:
    """Get the global manifest generator instance."""
    global _manifest_generator
    if _manifest_generator is None:
        _manifest_generator = ManifestGenerator()
    return _manifest_generator


def start_session(session_id: Optional[str] = None) -> str:
    """Start a new session and return session ID."""
    return get_manifest_generator().start_session(session_id)


def end_session() -> Optional[Path]:
    """End the current session and save manifest."""
    return get_manifest_generator().end_session()


def track_action(action_result: D20Result, game_state: GameState, player_input: str) -> None:
    """Track a player action in the current session."""
    get_manifest_generator().track_action(action_result, game_state, player_input)


def track_movement(old_position: Tuple[int, int], new_position: Tuple[int, int], 
                   heading: float, turn: int) -> None:
    """Track player movement."""
    get_manifest_generator().track_movement(old_position, new_position, heading, turn)


def track_dialogue(npc_id: str, player_input: str, npc_response: str, 
                  position: Tuple[int, int], heading: float, turn: int) -> None:
    """Track a dialogue interaction."""
    get_manifest_generator().track_dialogue(npc_id, player_input, npc_response, position, heading, turn)
