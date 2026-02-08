"""
DGT Battle Integration - ADR 138 Implementation
Prestige System and Elite Pilot Battle Performance Tracking

Integrates elite pilot registry with battle system for comprehensive
performance tracking and prestige point accumulation.
"""

import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass

from loguru import logger

from .pilot_registry import PilotRegistry, get_pilot_registry
from .fleet_service import CommanderService, FleetMember


@dataclass
class BattleResult:
    """Individual battle result for a pilot"""
    pilot_id: str
    elite_pilot_id: Optional[str]
    won: bool
    kills: int
    damage_dealt: float
    damage_taken: float
    battle_time: float
    opponents_defeated: List[str]
    survival_time: float
    accuracy: float


class BattleIntegrator:
    """Integrates battle system with elite pilot registry and prestige tracking"""
    
    def __init__(self, commander_service: CommanderService):
        self.commander_service = commander_service
        self.pilot_registry = get_pilot_registry()
        
        # Battle tracking
        self.active_battles: Dict[str, Dict[str, Any]] = {}
        self.battle_history: List[Dict[str, Any]] = []
        
        logger.info("⚔️ BattleIntegrator initialized")
    
    def start_battle(self, battle_id: str, participants: List[FleetMember]) -> bool:
        """Start tracking a new battle"""
        if battle_id in self.active_battles:
            logger.warning(f"⚔️ Battle {battle_id} already active")
            return False
        
        # Initialize battle tracking
        battle_data = {
            'battle_id': battle_id,
            'start_time': time.time(),
            'participants': {},
            'initial_state': {}
        }
        
        # Record initial state
        for member in participants:
            battle_data['participants'][member.pilot_id] = {
                'fleet_member': member,
                'initial_health': 200.0,  # Should get from actual ship
                'shots_fired': 0,
                'shots_hit': 0,
                'damage_dealt': 0.0,
                'damage_taken': 0.0,
                'kills': 0
            }
            
            # Record initial elite pilot state
            if member.elite_pilot_id and self.pilot_registry:
                elite_pilot = self.pilot_registry.elite_pilots.get(member.elite_pilot_id)
                if elite_pilot:
                    battle_data['initial_state'][member.pilot_id] = {
                        'prestige_points': elite_pilot.stats.prestige_points,
                        'confirmed_kills': elite_pilot.stats.confirmed_kills,
                        'battles_won': elite_pilot.stats.battles_won,
                        'battles_lost': elite_pilot.stats.battles_lost
                    }
        
        self.active_battles[battle_id] = battle_data
        logger.info(f"⚔️ Battle {battle_id} started with {len(participants)} participants")
        return True
    
    def record_battle_event(self, battle_id: str, event_type: str, pilot_id: str, **kwargs):
        """Record a battle event (shot, hit, kill, etc.)"""
        if battle_id not in self.active_battles:
            logger.warning(f"⚔️ Battle {battle_id} not found")
            return
        
        battle_data = self.active_battles[battle_id]
        participant_data = battle_data['participants'].get(pilot_id)
        
        if not participant_data:
            logger.warning(f"⚔️ Pilot {pilot_id} not in battle {battle_id}")
            return
        
        # Record event
        if event_type == 'shot_fired':
            participant_data['shots_fired'] += 1
        elif event_type == 'shot_hit':
            participant_data['shots_hit'] += 1
        elif event_type == 'damage_dealt':
            participant_data['damage_dealt'] += kwargs.get('damage', 0.0)
        elif event_type == 'damage_taken':
            participant_data['damage_taken'] += kwargs.get('damage', 0.0)
        elif event_type == 'kill':
            participant_data['kills'] += 1
            logger.debug(f"⚔️ Pilot {pilot_id} scored a kill")
        
        logger.debug(f"⚔️ Battle event recorded: {event_type} by {pilot_id}")
    
    def end_battle(self, battle_id: str, results: Dict[str, bool]) -> Optional[Dict[str, Any]]:
        """End battle and calculate prestige updates"""
        if battle_id not in self.active_battles:
            logger.warning(f"⚔️ Battle {battle_id} not found")
            return None
        
        battle_data = self.active_battles[battle_id]
        end_time = time.time()
        battle_duration = end_time - battle_data['start_time']
        
        # Calculate battle results
        battle_results = []
        prestige_updates = {}
        
        for pilot_id, won in results.items():
            participant_data = battle_data['participants'].get(pilot_id)
            if not participant_data:
                continue
            
            fleet_member = participant_data['fleet_member']
            
            # Calculate accuracy
            shots_fired = participant_data['shots_fired']
            shots_hit = participant_data['shots_hit']
            accuracy = shots_hit / max(1, shots_fired)
            
            # Create battle result
            battle_result = BattleResult(
                pilot_id=pilot_id,
                elite_pilot_id=fleet_member.elite_pilot_id,
                won=won,
                kills=participant_data['kills'],
                damage_dealt=participant_data['damage_dealt'],
                damage_taken=participant_data['damage_taken'],
                battle_time=battle_duration,
                opponents_defeated=[],  # Would be populated from actual battle data
                survival_time=battle_duration if won else 0.0,
                accuracy=accuracy
            )
            
            battle_results.append(battle_result)
            
            # Update fleet member stats
            fleet_member.update_stats(won)
            
            # Calculate prestige updates for elite pilots
            if fleet_member.elite_pilot_id and self.pilot_registry:
                prestige_update = self._calculate_prestige_update(battle_result)
                prestige_updates[fleet_member.elite_pilot_id] = prestige_update
        
        # Apply prestige updates
        self._apply_prestige_updates(prestige_updates)
        
        # Update commander service
        battle_results_dict = {
            result.pilot_id: {
                'won': result.won,
                'kills': result.kills,
                'damage_dealt': result.damage_dealt,
                'damage_taken': result.damage_taken,
                'battle_time': result.battle_time
            }
            for result in battle_results
        }
        
        self.commander_service.update_fleet_battle_records(battle_results_dict)
        
        # Create battle summary
        battle_summary = {
            'battle_id': battle_id,
            'duration': battle_duration,
            'participants': len(battle_results),
            'results': battle_results_dict,
            'prestige_updates': prestige_updates,
            'timestamp': end_time
        }
        
        # Store battle history
        self.battle_history.append(battle_summary)
        
        # Remove from active battles
        del self.active_battles[battle_id]
        
        logger.info(f"⚔️ Battle {battle_id} completed: {len(battle_results)} participants")
        return battle_summary
    
    def _calculate_prestige_update(self, battle_result: BattleResult) -> Dict[str, Any]:
        """Calculate prestige update for elite pilot"""
        base_prestige = 0
        
        # Win bonus
        if battle_result.won:
            base_prestige += 25
        else:
            base_prestige += 5
        
        # Kill bonus
        base_prestige += battle_result.kills * 10
        
        # Performance bonuses
        if battle_result.accuracy > 0.8:
            base_prestige += 15  # Accuracy bonus
        elif battle_result.accuracy > 0.6:
            base_prestige += 10
        
        # Damage efficiency bonus
        if battle_result.damage_dealt > battle_result.damage_taken * 2:
            base_prestige += 10  # Damage efficiency
        
        # Survival bonus
        if battle_result.won and battle_result.survival_time > 30:
            base_prestige += 5
        
        return {
            'prestige_gain': base_prestige,
            'kills_added': battle_result.kills,
            'battle_won': battle_result.won,
            'accuracy': battle_result.accuracy,
            'damage_ratio': battle_result.damage_dealt / max(1, battle_result.damage_taken)
        }
    
    def _apply_prestige_updates(self, prestige_updates: Dict[str, Dict[str, Any]]):
        """Apply prestige updates to elite pilots"""
        if not self.pilot_registry:
            return
        
        for elite_pilot_id, update in prestige_updates.items():
            elite_pilot = self.pilot_registry.elite_pilots.get(elite_pilot_id)
            if not elite_pilot:
                continue
            
            # Update pilot stats
            elite_pilot.stats.prestige_points += update['prestige_gain']
            elite_pilot.stats.confirmed_kills += update['kills_added']
            
            if update['battle_won']:
                elite_pilot.stats.battles_won += 1
            else:
                elite_pilot.stats.battles_lost += 1
            
            # Update dynamic pricing
            price_adjustment = update['prestige_gain'] // 10
            elite_pilot.current_cost = min(10000, elite_pilot.current_cost + price_adjustment)
            
            logger.debug(f"⚔️ Prestige updated for {elite_pilot.call_sign}: +{update['prestige_gain']} points")
    
    def get_pilot_battle_history(self, elite_pilot_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get battle history for a specific elite pilot"""
        pilot_history = []
        
        for battle in reversed(self.battle_history[-limit:]):
            if elite_pilot_id in battle.get('prestige_updates', {}):
                pilot_history.append({
                    'battle_id': battle['battle_id'],
                    'timestamp': battle['timestamp'],
                    'duration': battle['duration'],
                    'prestige_update': battle['prestige_updates'][elite_pilot_id]
                })
        
        return pilot_history
    
    def get_top_aces(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top aces by prestige points"""
        if not self.pilot_registry:
            return []
        
        aces = []
        for pilot in self.pilot_registry.elite_pilots.values():
            aces.append({
                'pilot_id': pilot.pilot_id,
                'call_sign': pilot.call_sign,
                'generation': pilot.generation,
                'prestige_points': pilot.stats.prestige_points,
                'confirmed_kills': pilot.stats.confirmed_kills,
                'win_rate': pilot.stats.get_win_rate(),
                'combat_rating': pilot.stats.combat_rating(),
                'specialization': pilot.specialization.value,
                'current_cost': pilot.current_cost
            })
        
        # Sort by prestige points
        aces.sort(key=lambda x: x['prestige_points'], reverse=True)
        
        return aces[:limit]
    
    def generate_battle_report(self, battle_id: str) -> Optional[Dict[str, Any]]:
        """Generate comprehensive battle report"""
        # Find battle in history
        battle = next((b for b in self.battle_history if b['battle_id'] == battle_id), None)
        if not battle:
            return None
        
        # Generate report
        report = {
            'battle_summary': {
                'battle_id': battle['battle_id'],
                'timestamp': battle['timestamp'],
                'duration': battle['duration'],
                'participants': battle['participants']
            },
            'performance_analysis': {},
            'prestige_impact': battle['prestige_updates'],
            'recommendations': []
        }
        
        # Analyze performance
        for pilot_id, result in battle['results'].items():
            report['performance_analysis'][pilot_id] = {
                'won': result['won'],
                'kills': result['kills'],
                'damage_efficiency': result['damage_dealt'] / max(1, result['damage_taken']),
                'battle_time': result['battle_time']
            }
        
        return report


# Global battle integrator
battle_integrator = None

def initialize_battle_integrator(commander_service: CommanderService) -> BattleIntegrator:
    """Initialize global battle integrator"""
    global battle_integrator
    battle_integrator = BattleIntegrator(commander_service)
    logger.info("⚔️ Global BattleIntegrator initialized")
    return battle_integrator

def get_battle_integrator() -> Optional[BattleIntegrator]:
    """Get global battle integrator"""
    return battle_integrator
