"""
Slime Clan Faction Definitions
"""

from src.shared.world.faction import Faction, FactionType, FactionRelation

def get_slime_factions() -> list[Faction]:
    # The Ember Clan (RED)
    ember_clan = Faction(
        id="CLAN_RED",
        name="The Ember Clan",
        type=FactionType.MILITARY,
        color=(255, 80, 80),
        home_base=(9, 0),  # Top right corner typically
        current_power=0.7,
        territories=[],
        relations={"CLAN_BLUE": FactionRelation.HOSTILE},
        expansion_rate=0.6,
        aggression_level=0.8
    )
    
    # The Tide Clan (BLUE)
    tide_clan = Faction(
        id="CLAN_BLUE",
        name="The Tide Clan",
        type=FactionType.ISOLATIONIST,
        color=(50, 160, 255),
        home_base=(0, 9),  # Bottom left corner typically
        current_power=0.5,
        territories=[],
        relations={"CLAN_RED": FactionRelation.HOSTILE},
        expansion_rate=0.4,
        aggression_level=0.3
    )
    
    return [ember_clan, tide_clan]
