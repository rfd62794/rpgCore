"""
DGT Infinite Tournament Loop
Always-On tournament system with auto-bake and evolution tracking

Implements the Sovereign Loop for continuous genetic evolution
Auto-starts tournaments, updates evolution logs, and tracks legendary lineages
"""

import time
import threading
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from pathlib import Path
import json

from loguru import logger
from .tournament import get_tournament_service, TournamentStatus
from .roster import roster_manager
from .narrative import narrative_bridge
try:
    from ..registry.evolution_log import EvolutionLog
except ImportError:
    # Fallback if registry module not available
    EvolutionLog = None


@dataclass
class TournamentConfig:
    """Configuration for infinite tournament loop"""
    auto_start: bool = True
    tournament_interval: float = 30.0  # Seconds between tournaments
    min_participants: int = 16
    max_participants: int = 32
    auto_bake_evolution: bool = True
    generate_narratives: bool = True
    save_championship_genomes: bool = True


class InfiniteTournamentLoop:
    """Always-On tournament system for continuous evolution"""
    
    def __init__(self, config: Optional[TournamentConfig] = None):
        self.config = config or TournamentConfig()
        self.tournament_service = get_tournament_service()
        self.evolution_log = EvolutionLog() if EvolutionLog else None
        
        # State tracking
        self.running = False
        self.current_tournament_id: Optional[str] = None
        self.tournament_count = 0
        self.last_tournament_time = 0.0
        self.championship_history: List[Dict[str, Any]] = []
        
        # Threading
        self.loop_thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()
        
        logger.info("♾️ Infinite Tournament Loop initialized")
    
    def start(self) -> bool:
        """Start the infinite tournament loop"""
        if self.running:
            logger.warning("♾️ Tournament loop already running")
            return False
        
        self.running = True
        self.stop_event.clear()
        
        # Start background loop
        self.loop_thread = threading.Thread(target=self._tournament_loop, daemon=True)
        self.loop_thread.start()
        
        logger.info("♾️ Infinite Tournament Loop started")
        return True
    
    def stop(self):
        """Stop the infinite tournament loop"""
        if not self.running:
            return
        
        self.running = False
        self.stop_event.set()
        
        if self.loop_thread:
            self.loop_thread.join(timeout=5.0)
        
        logger.info("♾️ Infinite Tournament Loop stopped")
    
    def _tournament_loop(self):
        """Background tournament loop"""
        logger.info("♾️ Starting tournament loop thread")
        
        while self.running and not self.stop_event.is_set():
            try:
                # Check if we need to start a new tournament
                if self._should_start_tournament():
                    self._start_new_tournament()
                
                # Process current tournament
                if self.current_tournament_id:
                    self._process_current_tournament()
                
                # Small sleep to prevent CPU overload
                time.sleep(1.0)
                
            except Exception as e:
                logger.error(f"♾️ Tournament loop error: {e}")
                time.sleep(5.0)  # Wait longer on error
        
        logger.info("♾️ Tournament loop thread ended")
    
    def _should_start_tournament(self) -> bool:
        """Check if a new tournament should be started"""
        # No current tournament
        if not self.current_tournament_id:
            return True
        
        # Check if current tournament is finished
        status = self.tournament_service.get_tournament_status(self.current_tournament_id)
        if status and status['status'] == TournamentStatus.FINISHED:
            return True
        
        # Check if enough time has passed since last tournament
        if time.time() - self.last_tournament_time >= self.config.tournament_interval:
            return True
        
        return False
    
    def _start_new_tournament(self):
        """Start a new tournament"""
        try:
            # Clean up previous tournament if needed
            if self.current_tournament_id:
                self.tournament_service.cleanup_tournament(self.current_tournament_id)
            
            # Create new tournament
            participant_count = min(
                self.config.max_participants,
                max(self.config.min_participants, len(roster_manager.active_roster))
            )
            
            tournament_name = f"Evolution Championship #{self.tournament_count + 1}"
            tournament_id = self.tournament_service.create_tournament(tournament_name, participant_count)
            
            if tournament_id:
                # Start tournament
                if self.tournament_service.start_tournament(tournament_id):
                    self.current_tournament_id = tournament_id
                    self.tournament_count += 1
                    self.last_tournament_time = time.time()
                    
                    logger.info(f"♾️ Started tournament #{self.tournament_count}: {tournament_name}")
                else:
                    logger.error(f"♾️ Failed to start tournament: {tournament_id}")
            else:
                logger.warning("♾️ Failed to create tournament - insufficient participants")
                
        except Exception as e:
            logger.error(f"♾️ Failed to start new tournament: {e}")
    
    def _process_current_tournament(self):
        """Process the current tournament"""
        if not self.current_tournament_id:
            return
        
        try:
            # Run next heat if available
            heat_result = self.tournament_service.run_next_heat(self.current_tournament_id)
            
            if heat_result:
                self._process_heat_result(heat_result)
            
            # Check if tournament is finished
            status = self.tournament_service.get_tournament_status(self.current_tournament_id)
            if status and status['status'] == TournamentStatus.FINISHED:
                self._finalize_tournament(status)
                
        except Exception as e:
            logger.error(f"♾️ Error processing tournament: {e}")
    
    def _process_heat_result(self, heat_result: Dict[str, Any]):
        """Process individual heat results"""
        results = heat_result.get('results', [])
        
        for result in results:
            turtle_id = result['turtle_id']
            position = result['position']
            
            # Get turtle record
            turtle = roster_manager.active_roster.get(turtle_id)
            if not turtle:
                continue
            
            # Generate narrative for significant achievements
            if self.config.generate_narratives:
                tournament_name = heat_result.get('tournament_name', 'Unknown Tournament')
                narrative = narrative_bridge.process_tournament_result(turtle, tournament_name, position)
                
                if narrative and narrative.is_legendary:
                    logger.info(f"♾️ LEGENDARY ASCENSION: {turtle.name} - {narrative.title}")
    
    def _finalize_tournament(self, status: Dict[str, Any]):
        """Finalize tournament and save championship data"""
        try:
            tournament_id = status['tournament_id']
            tournament_name = status['name']
            
            # Get tournament winner
            winner = None
            if self.current_tournament_id:
                # Try to get winner from tournament service
                # This would need to be implemented in the tournament service
                pass
            
            # Create championship record
            championship = {
                'tournament_id': tournament_id,
                'tournament_name': tournament_name,
                'tournament_number': self.tournament_count,
                'completed_at': time.time(),
                'duration': status.get('duration', 0.0),
                'total_matches': status.get('total_matches', 0),
                'total_participants': status.get('participants', 0),
                'winner_id': winner.get('turtle_id') if winner else None,
                'winner_name': winner.get('name') if winner else 'Unknown',
                'championship_genome': winner.get('genome_data') if winner else None
            }
            
            # Save championship history
            self.championship_history.append(championship)
            self._save_championship_history()
            
            # Auto-bake evolution log
            if self.config.auto_bake_evolution and winner:
                self._bake_champion_genome(winner, championship)
            
            logger.info(f"♾️ Tournament finalized: {tournament_name}")
            
        except Exception as e:
            logger.error(f"♾️ Error finalizing tournament: {e}")
    
    def _bake_champion_genome(self, winner: Dict[str, Any], championship: Dict[str, Any]):
        """Save championship genome to evolution log"""
        try:
            # Create evolution entry for champion
            champion_data = {
                'turtle_id': winner['turtle_id'],
                'generation': winner.get('generation', 0),
                'genome_data': winner.get('genome_data', {}),
                'parent_signatures': winner.get('parent_signatures', []),
                'fitness_score': winner.get('fitness_score', 0.0),
                'shell_pattern': winner.get('shell_pattern', ''),
                'primary_color': winner.get('primary_color', ''),
                'secondary_color': winner.get('secondary_color', ''),
                'speed': winner.get('speed', 0.0),
                'stamina': winner.get('stamina', 0.0),
                'intelligence': winner.get('intelligence', 0.0),
                'championship_data': {
                    'tournament_number': championship['tournament_number'],
                    'tournament_name': championship['tournament_name'],
                    'completed_at': championship['completed_at'],
                    'duration': championship['duration']
                }
            }
            
            # Log to evolution registry
            if self.evolution_log:
                success = self.evolution_log.log_turtle_birth(champion_data)
                
                if success:
                    logger.info(f"♾️ Champion genome baked: {winner['name']} (Tournament #{championship['tournament_number']})")
                else:
                    logger.warning(f"♾️ Failed to bake champion genome: {winner['name']}")
            else:
                logger.info(f"♾️ Evolution logging not available - champion data saved locally")
                
        except Exception as e:
            logger.error(f"♾️ Error baking champion genome: {e}")
    
    def _save_championship_history(self):
        """Save championship history to file"""
        try:
            history_path = Path(__file__).parent.parent.parent.parent / "data" / "championship_history.json"
            history_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(history_path, 'w') as f:
                json.dump(self.championship_history, f, indent=2)
            
            logger.debug(f"♾️ Saved championship history: {len(self.championship_history)} tournaments")
            
        except Exception as e:
            logger.error(f"♾️ Failed to save championship history: {e}")
    
    def get_loop_status(self) -> Dict[str, Any]:
        """Get current loop status"""
        status = {
            'running': self.running,
            'tournament_count': self.tournament_count,
            'current_tournament_id': self.current_tournament_id,
            'last_tournament_time': self.last_tournament_time,
            'total_championships': len(self.championship_history)
        }
        
        # Add current tournament status if available
        if self.current_tournament_id:
            tournament_status = self.tournament_service.get_tournament_status(self.current_tournament_id)
            if tournament_status:
                status['current_tournament'] = tournament_status
        
        return status
    
    def get_evolution_metrics(self) -> Dict[str, Any]:
        """Get evolution metrics and statistics"""
        try:
            # Get roster stats
            roster_stats = roster_manager.get_roster_stats()
            
            # Get narrative summary
            narrative_summary = narrative_bridge.get_narrative_summary()
            
            # Get evolution log summary
            evolution_summary = self.evolution_log.get_summary()
            
            # Calculate evolution metrics
            metrics = {
                'roster_stats': roster_stats,
                'narrative_summary': narrative_summary,
                'evolution_summary': evolution_summary,
                'championship_count': len(self.championship_history),
                'legendary_count': narrative_summary.get('legendary_turtles', 0),
                'loop_config': {
                    'auto_start': self.config.auto_start,
                    'tournament_interval': self.config.tournament_interval,
                    'auto_bake_evolution': self.config.auto_bake_evolution,
                    'generate_narratives': self.config.generate_narratives
                }
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"♾️ Error getting evolution metrics: {e}")
            return {'error': str(e)}
    
    def force_tournament_start(self) -> Optional[str]:
        """Force start a new tournament immediately"""
        if self.running:
            self.last_tournament_time = 0  # Reset timer to trigger immediate start
            return "Tournament start forced"
        return "Loop not running"


# Global infinite tournament instance
infinite_tournament = InfiniteTournamentLoop()
