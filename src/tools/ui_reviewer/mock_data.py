import random
from src.shared.teams.roster import Roster, RosterSlime
from src.shared.genetics.inheritance import generate_random

def generate_mock_roster() -> Roster:
    """Generates a deterministic roster for UI review."""
    roster = Roster()
    
    # Generate slimes of different cultures/levels
    cultures = ["ember", "coastal", "verdant", "void"]
    for i, culture in enumerate(cultures):
        # Level 1
        s1 = RosterSlime(
            slime_id=f"mock_{culture}_lv1",
            name=f"{culture.capitalize()} Lv1",
            genome=generate_random(), # In a real system we'd force the culture byte
            level=1
        )
        roster.slimes.append(s1)
        
        # Level 10
        s10 = RosterSlime(
            slime_id=f"mock_{culture}_lv10",
            name=f"{culture.capitalize()} Lv10",
            genome=generate_random(),
            level=10
        )
        roster.slimes.append(s10)
        
    return roster
