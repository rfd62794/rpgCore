"""
World Factory: Location & Scenario Generation

Handles procedural location generation and scenario loading.
Templates for Urban, Dungeon, and Wilderness environments.
Manages Social Graph persistence between room transitions.
"""

from typing import Dict, List, Optional

from loguru import logger
from pydantic import BaseModel

from game_state import Room, NPC, GameState


class LocationTemplate(BaseModel):
    """Template for generating locations."""
    name: str
    description: str
    environment_tags: List[str]
    initial_npcs: List[str]
    props: List[str]
    connections: Dict[str, str]  # direction -> location_id


class WorldFactory:
    """
    Factory for creating and managing game world locations.
    
    Responsible for:
    - Location templates (Urban, Dungeon, Wilderness)
    - Scenario loading (Heist, Diplomacy arcs)
    - Social Graph persistence
    """
    
    def __init__(self):
        """Initialize world factory with location templates."""
        self.templates = self._load_templates()
        self.scenarios = self._load_scenarios()
        logger.info("World Factory initialized with location templates")
    
    def _load_templates(self) -> Dict[str, LocationTemplate]:
        """Load location templates for different environment types."""
        return {
            # Urban Templates
            "tavern": LocationTemplate(
                name="The Rusty Flagon",
                description="A dimly lit tavern filled with the smell of ale and roasted meat. Rowdy patrons fill the wooden tables.",
                environment_tags=["Sticky Floors", "Rowdy Crowd", "Dimly Lit"],
                initial_npcs=["Bartender", "Guard"],
                props=["wooden table", "beer mug", "chair"],
                connections={"north": "town_square", "east": "alley"}
            ),
            
            "town_square": LocationTemplate(
                name="Town Square",
                description="A bustling town square with a fountain in the center. Merchants hawk their wares from colorful stalls.",
                environment_tags=["Crowded", "Noisy", "Open Space"],
                initial_npcs=["Merchant", "Town Crier"],
                props=["fountain", "market stall", "notice board"],
                connections={"south": "tavern", "west": "temple", "east": "market"}
            ),
            
            "alley": LocationTemplate(
                name="Dark Alley",
                description="A narrow, shadowy alley between buildings. The air smells of refuse and damp stone.",
                environment_tags=["Dimly Lit", "Confined", "Hidden"],
                initial_npcs=["Thug"],
                props=["dumpster", "broken crate", "graffiti"],
                connections={"west": "tavern", "north": "rooftop"}
            ),
            
            "temple": LocationTemplate(
                name="Temple of Wisdom",
                description="A serene temple with high vaulted ceilings. Sunlight streams through stained glass windows.",
                environment_tags=["Quiet", "Sacred", "Well-lit"],
                initial_npcs=["Priest", "Acolyte"],
                props=["altar", "candles", "holy book"],
                connections={"east": "town_square", "north": "crypt"}
            ),
            
            # Dungeon Templates
            "dungeon_entrance": LocationTemplate(
                name="Dungeon Entrance",
                description="A heavy stone doorway leads into darkness below. Ancient runes are carved into the archway.",
                environment_tags=["Dark", "Damp", "Ancient"],
                initial_npcs=["Doorwarden"],
                props=["iron door", "torch sconce", "runic inscription"],
                connections={"up": "surface", "down": "dungeon_hall"}
            ),
            
            "dungeon_hall": LocationTemplate(
                name="Dungeon Hall",
                description="A long stone hallway with dripping water echoing in the distance. Cobwebs hang from the ceiling.",
                environment_tags=["Dark", "Echoing", "Confined"],
                initial_npcs=["Skeleton Guard"],
                props=["stone pillar", "rusty chains", "bones"],
                connections={"up": "dungeon_entrance", "east": "treasure_room", "west": "cell_block"}
            ),
            
            # Wilderness Templates
            "forest_path": LocationTemplate(
                name="Forest Path",
                description="A winding path through dense forest. Sunlight filters through the canopy above.",
                environment_tags=["Natural", "Cover", "Uneven Ground"],
                initial_npcs=["Forest Ranger"],
                props=["ancient tree", "mossy rock", "bird nest"],
                connections={"north": "clearing", "south": "cave_entrance"}
            ),
            
            "clearing": LocationTemplate(
                name="Forest Clearing",
                description="An open clearing in the forest surrounded by tall trees. A small stream bubbles nearby.",
                environment_tags=["Open", "Natural", "Peaceful"],
                initial_npcs=["Hermit"],
                props=["campfire", "cooking pot", "bedroll"],
                connections={"south": "forest_path", "east": "ruins"}
            )
        }
    
    def _load_scenarios(self) -> Dict[str, Dict]:
        """Load pre-configured scenario blueprints."""
        return {
            "heist": {
                "act_name": "The Silent Heist",
                "sequence": [
                    {
                        "id": "tavern",
                        "name": "The Rusty Flagon",
                        "description": "A dimly lit tavern where you meet your contact.",
                        "tags": ["Sticky Floors", "Rowdy Crowd"],
                        "npcs": [
                            {"name": "Bartender", "description": "A burly man who knows things"},
                            {"name": "Shadow Contact", "description": "A mysterious figure in the corner"}
                        ],
                        "objectives": [
                            {"id": "meet_contact", "description": "Meet with the shadow contact", "required_intent": "charm", "target_tags": ["contact"]}
                        ]
                    },
                    {
                        "id": "alley",
                        "name": "Planning Alley",
                        "description": "A dark alley perfect for planning the heist.",
                        "tags": ["Dimly Lit", "Hidden"],
                        "npcs": [
                            {"name": "Shadow Contact", "description": "Your contact with the plan"}
                        ],
                        "objectives": [
                            {"id": "get_plan", "description": "Learn the heist details", "required_intent": "investigate", "target_tags": ["plan"]}
                        ]
                    },
                    {
                        "id": "target_house",
                        "name": "Target Estate",
                        "description": "The wealthy merchant's estate you're targeting.",
                        "tags": ["Well-guarded", "Locked"],
                        "npcs": [
                            {"name": "Guard", "description": "A vigilant guard protecting the estate"}
                        ],
                        "objectives": [
                            {"id": "infiltrate", "description": "Gain entry to the estate", "required_intent": "stealth"},
                            {"id": "secure_loot", "description": "Find and secure the treasure", "required_intent": "investigate", "target_tags": ["treasure"]}
                        ]
                    }
                ]
            },
            
            "peace": {
                "act_name": "The Diplomatic Mission",
                "sequence": [
                    {
                        "id": "temple",
                        "name": "Temple of Wisdom",
                        "description": "A sacred temple where negotiations begin.",
                        "tags": ["Quiet", "Sacred"],
                        "npcs": [
                            {"name": "High Priest", "description": "Leader of the temple council"},
                            {"name": "Temple Guard", "description": "A solemn guardian of the sacred space"}
                        ],
                        "objectives": [
                            {"id": "audience", "description": "Request audience with the High Priest", "required_intent": "charm", "target_tags": ["priest"]}
                        ]
                    },
                    {
                        "id": "town_square",
                        "name": "Town Square",
                        "description": "The public square where tensions run high.",
                        "tags": ["Crowded", "Tense"],
                        "npcs": [
                            {"name": "Angry Mob", "description": "Citizens demanding justice"},
                            {"name": "Town Crier", "description": "Spreading news through the square"}
                        ],
                        "objectives": [
                            {"id": "calm_crowd", "description": "Address the crowd's concerns", "required_intent": "charm", "target_tags": ["mob"]}
                        ]
                    }
                ]
            }
        }
    
    def get_location(self, location_id: str) -> Optional[Room]:
        """
        Get a Room object from location template.
        
        Args:
            location_id: Template identifier
            
        Returns:
            Room object or None if not found
        """
        template = self.templates.get(location_id)
        if not template:
            logger.warning(f"Location template not found: {location_id}")
            return None
        
        # Create NPCs
        npcs = []
        for npc_name in template.initial_npcs:
            npcs.append(NPC(name=npc_name))
        
        # Create Room
        room = Room(
            name=template.name,
            description=template.description,
            npcs=npcs,
            items=template.props,
            exits=template.connections,
            tags=template.environment_tags
        )
        
        return room
    
    def load_scenario(self, scenario_id: str, game_state: GameState):
        """
        Load a scenario blueprint into the game state.
        
        Args:
            scenario_id: Scenario identifier
            game_state: Game state to modify
        """
        scenario = self.scenarios.get(scenario_id)
        if not scenario:
            logger.error(f"Scenario not found: {scenario_id}")
            return
        
        logger.info(f"Loading scenario: {scenario.get('act_name', 'Unnamed')}")
        
        sequence = scenario.get("sequence", [])
        for i, entry in enumerate(sequence):
            loc_id = entry["id"]
            
            # Create linear exits
            exits = {}
            if i < len(sequence) - 1:
                exits["forward"] = sequence[i + 1]["id"]
            if i > 0:
                exits["back"] = sequence[i - 1]["id"]
            
            # Create NPCs
            npcs = []
            for n_def in entry.get("npcs", []):
                npcs.append(NPC(name=n_def["name"], description=n_def["description"]))
            
            # Create Room
            room = Room(
                name=entry["name"],
                description=entry["description"],
                npcs=npcs,
                tags=entry["tags"],
                exits=exits
            )
            
            game_state.rooms[loc_id] = room
            
            # Generate goals from objectives
            for obj_def in entry.get("objectives", []):
                from objective_factory import create_goal_from_blueprint
                goal = create_goal_from_blueprint(obj_def)
                game_state.goal_stack.append(goal)
        
        # Set starting location
        if sequence:
            game_state.current_room = sequence[0]["id"]
    
    def persist_social_graph(self, old_location: str, new_location: str, game_state: GameState):
        """
        Handle social graph persistence during room transitions.
        
        Args:
            old_location: Previous location ID
            new_location: New location ID  
            game_state: Game state containing social graph
        """
        # Social graph is already location-scoped in GameState
        # This method exists for future enhancement if needed
        logger.debug(f"Social graph persisted from {old_location} to {new_location}")
    
    def generate_dynamic_location(self, environment_type: str, location_id: str) -> Room:
        """
        Generate a location dynamically based on environment type.
        
        Args:
            environment_type: "urban", "dungeon", or "wilderness"
            location_id: Unique identifier for the location
            
        Returns:
            Generated Room object
        """
        # This is a placeholder for future procedural generation
        # For now, return a basic room
        return Room(
            name=f"Generated {environment_type.title()} Location",
            description=f"A procedurally generated {environment_type} location.",
            tags=[environment_type],
            exits={},
            npcs=[],
            items=[]
        )


# Export for use by engine
__all__ = ["WorldFactory"]
