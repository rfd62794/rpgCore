"""
DGT Tournament Service - ADR 127 Implementation
Manages tournament brackets, heats, and multi-lens broadcasting

Ported from TurboShells race_manager.py with distributed architecture support
Handles 16-turtle brackets with real-time odds calculation
"""

import time
import random
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json

from loguru import logger
from .roster import RosterManager, TurtleRecord, TurtleStats
from .racing import RacingService, RaceTrack
from .genetics import TurboGenome, genetic_registry


class TournamentStatus(str, Enum):
    """Tournament status states"""
    PREPARING = "preparing"
    IN_PROGRESS = "in_progress"
    HEAT_BREAK = "heat_break"
    FINISHED = "finished"
    CANCELLED = "cancelled"


@dataclass
class TournamentMatch:
    """Single tournament match/heat"""
    match_id: str
    round_number: int
    heat_number: int
    participants: List[str]  # Turtle IDs
    results: List[Dict[str, Any]] = field(default_factory=list)
    start_time: float = 0.0
    end_time: float = 0.0
    duration: float = 0.0
    finished: bool = False
    
    def __post_init__(self):
        if not self.match_id:
            self.match_id = f"r{self.round_number}_h{self.heat_number}_{int(time.time())}"


@dataclass
class TournamentBracket:
    """Tournament bracket structure"""
    name: str
    participants: List[str]  # Turtle IDs
    tournament_id: str = ""
    matches: List[TournamentMatch] = field(default_factory=list)
    current_round: int = 1
    total_rounds: int = 4
    participants_per_heat: int = 4
    status: TournamentStatus = TournamentStatus.PREPARING
    created_at: float = field(default_factory=time.time)
    started_at: float = 0.0
    finished_at: float = 0.0
    
    def __post_init__(self):
        if not self.tournament_id:
            self.tournament_id = f"tournament_{int(self.created_at)}"


class WinProbabilityCalculator:
    """Calculates real-time win probabilities based on turtle stats"""
    
    @staticmethod
    def calculate_match_odds(participants: List[TurtleRecord]) -> Dict[str, float]:
        """Calculate win probabilities for a match"""
        if not participants:
            return {}
        
        # Calculate power scores for all participants
        power_scores = {}
        total_score = 0.0
        
        for turtle in participants:
            # Base power score from stats
            stat_score = turtle.stats.calculate_power_score()
            
            # Genetic fitness bonus
            genetic_score = turtle.genome.calculate_fitness()
            
            # Experience bonus (wins and races)
            experience_bonus = 1.0 + (turtle.wins * 0.1) + (turtle.total_races * 0.01)
            
            # Recent performance bonus (last 5 races)
            recent_bonus = 1.0
            if turtle.race_history:
                recent_races = turtle.race_history[-5:]
                avg_position = sum(r['position'] for r in recent_races) / len(recent_races)
                recent_bonus = 2.0 - (avg_position / len(recent_races))  # Better positions = higher bonus
            
            # Combine all factors
            combined_score = stat_score * genetic_score * experience_bonus * recent_bonus
            power_scores[turtle.turtle_id] = combined_score
            total_score += combined_score
        
        # Convert to probabilities
        probabilities = {}
        for turtle_id, score in power_scores.items():
            probabilities[turtle_id] = score / total_score if total_score > 0 else 0.25
        
        return probabilities
    
    @staticmethod
    def calculate_tournament_odds(participants: List[TurtleRecord]) -> Dict[str, float]:
        """Calculate overall tournament win odds"""
        if not participants:
            return {}
        
        # Use tournament performance as primary factor
        odds = {}
        total_odds = 0.0
        
        for turtle in participants:
            # Base odds from win rate
            win_rate = turtle.wins / max(1, turtle.total_races)
            
            # Power score bonus
            power_bonus = turtle.stats.calculate_power_score() / 10.0
            
            # Generation bonus (higher generation = more refined genetics)
            generation_bonus = 1.0 + (turtle.generation * 0.05)
            
            # Earnings bonus (success indicator)
            earnings_bonus = 1.0 + (turtle.earnings / 1000.0)
            
            combined_odds = win_rate * power_bonus * generation_bonus * earnings_bonus
            odds[turtle.turtle_id] = combined_odds
            total_odds += combined_odds
        
        # Normalize to probabilities
        for turtle_id in odds:
            odds[turtle_id] = odds[turtle_id] / total_odds if total_odds > 0 else 0.0
        
        return odds


class TournamentService:
    """Tournament management service"""
    
    def __init__(self, roster_manager: RosterManager):
        self.roster_manager = roster_manager
        self.active_tournaments: Dict[str, TournamentBracket] = {}
        self.racing_service = RacingService()
        
        logger.info("🏆 Tournament Service initialized")
    
    def create_tournament(self, name: str, participant_count: int = 16) -> Optional[str]:
        """Create a new tournament"""
        # Get tournament candidates
        candidates = self.roster_manager.get_tournament_candidates(participant_count)
        
        if len(candidates) < participant_count:
            logger.warning(f"🏆 Not enough candidates: {len(candidates)} < {participant_count}")
            return None
        
        # Create tournament bracket
        tournament = TournamentBracket(
            name=name,
            participants=[t.turtle_id for t in candidates]
        )
        
        # Generate matches
        self._generate_tournament_matches(tournament)
        
        # Store tournament
        self.active_tournaments[tournament.tournament_id] = tournament
        
        logger.info(f"🏆 Created tournament: {name} with {len(candidates)} participants")
        return tournament.tournament_id
    
    def _generate_tournament_matches(self, tournament: TournamentBracket):
        """Generate tournament bracket matches"""
        participants = tournament.participants.copy()
        random.shuffle(participants)  # Random seeding
        
        # Round 1: 4 heats of 4 participants each
        round_matches = []
        for i in range(0, len(participants), tournament.participants_per_heat):
            heat_participants = participants[i:i + tournament.participants_per_heat]
            
            match = TournamentMatch(
                round_number=1,
                heat_number=len(round_matches) + 1,
                participants=heat_participants
            )
            round_matches.append(match)
        
        tournament.matches = round_matches
        tournament.total_rounds = self._calculate_total_rounds(len(participants))
        
        logger.debug(f"🏆 Generated {len(round_matches)} matches for round 1")
    
    def _calculate_total_rounds(self, participant_count: int) -> int:
        """Calculate total rounds needed for tournament"""
        rounds = 0
        remaining = participant_count
        
        while remaining > 1:
            remaining = (remaining + tournament.participants_per_heat - 1) // tournament.participants_per_heat
            rounds += 1
        
        return max(1, rounds)
    
    def start_tournament(self, tournament_id: str) -> bool:
        """Start tournament execution"""
        if tournament_id not in self.active_tournaments:
            logger.error(f"🏆 Tournament not found: {tournament_id}")
            return False
        
        tournament = self.active_tournaments[tournament_id]
        tournament.status = TournamentStatus.IN_PROGRESS
        tournament.started_at = time.time()
        
        logger.info(f"🏆 Starting tournament: {tournament.name}")
        return True
    
    def run_next_heat(self, tournament_id: str) -> Optional[Dict[str, Any]]:
        """Run the next heat in tournament"""
        if tournament_id not in self.active_tournaments:
            return None
        
        tournament = self.active_tournaments[tournament_id]
        
        # Find next unfinished match
        next_match = None
        for match in tournament.matches:
            if not match.finished and match.round_number == tournament.current_round:
                next_match = match
                break
        
        if not next_match:
            # Check if round is complete
            round_matches = [m for m in tournament.matches if m.round_number == tournament.current_round]
            if all(m.finished for m in round_matches):
                # Advance to next round
                if tournament.current_round < tournament.total_rounds:
                    tournament.current_round += 1
                    tournament.status = TournamentStatus.HEAT_BREAK
                    logger.info(f"🏆 Advancing to round {tournament.current_round}")
                    return self._generate_next_round_matches(tournament)
                else:
                    # Tournament finished
                    tournament.status = TournamentStatus.FINISHED
                    tournament.finished_at = time.time()
                    logger.info(f"🏆 Tournament finished: {tournament.name}")
                    return self._finalize_tournament(tournament)
            else:
                return None
        
        # Run the heat
        return self._run_heat(tournament, next_match)
    
    def _run_heat(self, tournament: TournamentBracket, match: TournamentMatch) -> Dict[str, Any]:
        """Execute a single heat"""
        logger.info(f"🏆 Running heat {match.heat_number} of round {match.round_number}")
        
        # Get participant records
        participants = []
        for turtle_id in match.participants:
            turtle = self.roster_manager.active_roster.get(turtle_id)
            if turtle:
                participants.append(turtle)
        
        if len(participants) < 2:
            logger.warning(f"🏆 Not enough participants for heat: {len(participants)}")
            return None
        
        # Calculate pre-race odds
        pre_race_odds = WinProbabilityCalculator.calculate_match_odds(participants)
        
        # Setup racing service
        self.racing_service.cleanup_race()
        
        # Register participants with racing service
        for turtle in participants:
            # Convert TurtleRecord to TurboGenome for racing
            self.racing_service.register_racer(turtle.turtle_id, turtle.genome)
        
        # Start the race
        if not self.racing_service.start_race():
            logger.error(f"🏆 Failed to start heat {match.heat_number}")
            return None
        
        # Simulate race (run for fixed time or until completion)
        race_duration = 10.0  # 10 second races
        start_time = time.time()
        
        while time.time() - start_time < race_duration:
            race_state = self.racing_service.update_race(0.1)  # 10 TPS
            
            # Check if race finished early
            if race_state.get('race_active', False) == False:
                break
            
            time.sleep(0.1)
        
        # Get results
        leaderboard = self.racing_service.get_leaderboard()
        
        # Process results
        results = []
        for i, entry in enumerate(leaderboard):
            turtle_id = entry['turtle_id']
            position = i + 1
            
            # Update roster with results
            earnings = 100.0 / position  # Simple earnings structure
            self.roster_manager.update_race_result(turtle_id, position, earnings)
            
            results.append({
                'turtle_id': turtle_id,
                'position': position,
                'earnings': earnings,
                'finish_time': entry.get('finish_time', 0.0),
                'avg_speed': entry.get('avg_speed', 0.0)
            })
        
        # Update match
        match.results = results
        match.start_time = start_time
        match.end_time = time.time()
        match.duration = match.end_time - match.start_time
        match.finished = True
        
        # Save race log
        self.racing_service.save_race_log(f"tournament_{tournament.tournament_id}_heat_{match.heat_number}.yaml")
        
        logger.info(f"🏆 Heat {match.heat_number} completed: {len(results)} results")
        
        return {
            'tournament_id': tournament.tournament_id,
            'match_id': match.match_id,
            'round': match.round_number,
            'heat': match.heat_number,
            'pre_race_odds': pre_race_odds,
            'results': results,
            'duration': match.duration
        }
    
    def _generate_next_round_matches(self, tournament: TournamentBracket) -> Dict[str, Any]:
        """Generate matches for next tournament round"""
        # Get winners from previous round
        previous_round = tournament.current_round - 1
        previous_matches = [m for m in tournament.matches if m.round_number == previous_round]
        
        # Collect winners (top 2 from each heat advance)
        advancing_turtles = []
        for match in previous_matches:
            if match.results:
                # Sort by position and take top 2
                sorted_results = sorted(match.results, key=lambda r: r['position'])
                advancing_turtles.extend([r['turtle_id'] for r in sorted_results[:2]])
        
        # Generate new matches
        round_matches = []
        for i in range(0, len(advancing_turtles), tournament.participants_per_heat):
            heat_participants = advancing_turtles[i:i + tournament.participants_per_heat]
            
            match = TournamentMatch(
                round_number=tournament.current_round,
                heat_number=len(round_matches) + 1,
                participants=heat_participants
            )
            round_matches.append(match)
        
        tournament.matches.extend(round_matches)
        
        # Calculate new tournament odds
        advancing_records = []
        for turtle_id in advancing_turtles:
            turtle = self.roster_manager.active_roster.get(turtle_id)
            if turtle:
                advancing_records.append(turtle)
        
        tournament_odds = WinProbabilityCalculator.calculate_tournament_odds(advancing_records)
        
        logger.info(f"🏆 Generated {len(round_matches)} matches for round {tournament.current_round}")
        
        return {
            'tournament_id': tournament.tournament_id,
            'round': tournament.current_round,
            'advancing_turtles': advancing_turtles,
            'new_matches': len(round_matches),
            'tournament_odds': tournament_odds
        }
    
    def _finalize_tournament(self, tournament: TournamentBracket) -> Dict[str, Any]:
        """Finalize tournament and determine winner"""
        # Get final round results
        final_matches = [m for m in tournament.matches if m.round_number == tournament.total_rounds]
        
        if not final_matches:
            logger.error(f"🏆 No final matches found for tournament {tournament.tournament_id}")
            return None
        
        # Get winner (best position in final heat)
        winner = None
        best_position = float('inf')
        
        for match in final_matches:
            if match.results:
                match_winner = min(match.results, key=lambda r: r['position'])
                if match_winner['position'] < best_position:
                    best_position = match_winner['position']
                    winner = match_winner
        
        if winner:
            # Award tournament prize
            prize_earnings = 1000.0
            self.roster_manager.update_race_result(winner['turtle_id'], 1, prize_earnings)
            
            logger.info(f"🏆 Tournament winner: {winner['turtle_id']} - Prize: ${prize_earnings}")
        
        return {
            'tournament_id': tournament.tournament_id,
            'name': tournament.name,
            'winner': winner,
            'total_duration': tournament.finished_at - tournament.started_at,
            'total_matches': len(tournament.matches),
            'total_participants': len(tournament.participants)
        }
    
    def get_tournament_status(self, tournament_id: str) -> Optional[Dict[str, Any]]:
        """Get current tournament status"""
        if tournament_id not in self.active_tournaments:
            return None
        
        tournament = self.active_tournaments[tournament_id]
        
        # Calculate current odds
        participants = []
        for turtle_id in tournament.participants:
            turtle = self.roster_manager.active_roster.get(turtle_id)
            if turtle:
                participants.append(turtle)
        
        tournament_odds = WinProbabilityCalculator.calculate_tournament_odds(participants)
        
        return {
            'tournament_id': tournament.tournament_id,
            'name': tournament.name,
            'status': tournament.status.value,
            'current_round': tournament.current_round,
            'total_rounds': tournament.total_rounds,
            'total_matches': len(tournament.matches),
            'completed_matches': sum(1 for m in tournament.matches if m.finished),
            'participants': len(tournament.participants),
            'tournament_odds': tournament_odds,
            'created_at': tournament.created_at,
            'started_at': tournament.started_at,
            'duration': time.time() - tournament.started_at if tournament.started_at > 0 else 0
        }
    
    def get_live_heat_odds(self, tournament_id: str) -> Optional[Dict[str, Any]]:
        """Get live odds for current heat"""
        if tournament_id not in self.active_tournaments:
            return None
        
        tournament = self.active_tournaments[tournament_id]
        
        # Find current or next heat
        current_heat = None
        for match in tournament.matches:
            if not match.finished and match.round_number == tournament.current_round:
                current_heat = match
                break
        
        if not current_heat:
            return None
        
        # Get participants
        participants = []
        for turtle_id in current_heat.participants:
            turtle = self.roster_manager.active_roster.get(turtle_id)
            if turtle:
                participants.append(turtle)
        
        # Calculate odds
        heat_odds = WinProbabilityCalculator.calculate_match_odds(participants)
        
        return {
            'tournament_id': tournament_id,
            'match_id': current_heat.match_id,
            'round': current_heat.round_number,
            'heat': current_heat.heat_number,
            'participants': current_heat.participants,
            'live_odds': heat_odds,
            'status': 'starting_soon'
        }
    
    def cleanup_tournament(self, tournament_id: str):
        """Clean up finished tournament"""
        if tournament_id in self.active_tournaments:
            del self.active_tournaments[tournament_id]
            logger.info(f"🏆 Cleaned up tournament: {tournament_id}")


# Global tournament service instance
# Note: This will be initialized when the module is imported
tournament_service = None

def get_tournament_service():
    """Get or create tournament service instance"""
    global tournament_service
    if tournament_service is None:
        from .roster import roster_manager
        tournament_service = TournamentService(roster_manager)
    return tournament_service
