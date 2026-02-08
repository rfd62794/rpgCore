"""
DGT Narrative Bridge - ADR 128 Implementation
Generates LLM-powered origin stories for legendary turtles

Creates narrative connection between tournament results and genetic evolution
Provides flavor text and legendary status tracking
"""

import time
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from pathlib import Path
import random

from loguru import logger
from .genetics import TurboGenome
from .roster import TurtleRecord


@dataclass
class NarrativeStory:
    """Generated narrative story for a turtle"""
    turtle_id: str
    story_type: str  # "origin", "victory", "legendary"
    title: str
    content: str
    generated_at: float
    tags: List[str]
    is_legendary: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            'turtle_id': self.turtle_id,
            'story_type': self.story_type,
            'title': self.title,
            'content': self.content,
            'generated_at': self.generated_at,
            'tags': self.tags,
            'is_legendary': self.is_legendary
        }


class NarrativeGenerator:
    """Generates narrative content for turtle achievements"""
    
    def __init__(self):
        self.story_templates = self._load_story_templates()
        self.legendary_threshold = 5  # 5 wins for legendary status
        
        logger.info("📖 Narrative Generator initialized")
    
    def _load_story_templates(self) -> Dict[str, List[str]]:
        """Load story templates for different narrative types"""
        return {
            'origin': [
                "Born in the {terrain} regions, {name} emerged with exceptional {trait} that set them apart from their kin.",
                "The {color}-shelled hatchling showed remarkable {trait} from their first race, dominating the {terrain} trials.",
                "From humble beginnings in the {terrain} wetlands, {name} developed an uncanny ability to {action}.",
                "Genetic fortune smiled upon {name}, granting them superior {trait} and a destiny for greatness.",
                "In the competitive world of turtle racing, {name} stood out with their extraordinary {trait}."
            ],
            'victory': [
                "With a burst of {trait}, {name} surged ahead to claim victory in the {terrain} championship.",
                "The crowd roared as {name} dominated the final stretch, their {trait} proving unstoppable.",
                "Victory belonged to {name}, whose superior {trait} carried them through the challenging {terrain} course.",
                "In a stunning display of {trait}, {name} crossed the finish line first, etching their name in history.",
                "The {terrain} track favored {name}'s exceptional {trait}, leading to a triumphant finish."
            ],
            'legendary': [
                "Legend speaks of {name}, the {color} titan whose {trait} became the stuff of racing mythology.",
                "Through countless victories, {name} ascended to legendary status, their {trait} unmatched by any challenger.",
                "The archives will forever remember {name}, the {color} phantom who mastered every {terrain} with supernatural {trait}.",
                "A true champion, {name} carved their legacy with exceptional {trait} and an unbreakable will to win.",
                "The tale of {name} echoes through generations - a {color} warrior whose {trait} defied the limits of possibility."
            ]
        }
    
    def generate_origin_story(self, turtle: TurtleRecord) -> NarrativeStory:
        """Generate origin story for a turtle"""
        # Extract key traits from genetics
        dominant_trait = self._get_dominant_trait(turtle.genome)
        color = self._get_color_description(turtle.genome)
        terrain = self._get_preferred_terrain(turtle.genome)
        
        # Select template
        template = random.choice(self.story_templates['origin'])
        
        # Fill template
        story_content = template.format(
            name=turtle.name,
            trait=dominant_trait,
            color=color,
            terrain=terrain,
            action=self._get_action_description(dominant_trait)
        )
        
        return NarrativeStory(
            turtle_id=turtle.turtle_id,
            story_type="origin",
            title=f"The Origins of {turtle.name}",
            content=story_content,
            generated_at=time.time(),
            tags=[dominant_trait, color, terrain],
            is_legendary=False
        )
    
    def generate_victory_story(self, turtle: TurtleRecord, tournament_name: str) -> NarrativeStory:
        """Generate victory story for tournament win"""
        dominant_trait = self._get_dominant_trait(turtle.genome)
        color = self._get_color_description(turtle.genome)
        terrain = self._get_preferred_terrain(turtle.genome)
        
        template = random.choice(self.story_templates['victory'])
        
        story_content = template.format(
            name=turtle.name,
            trait=dominant_trait,
            color=color,
            terrain=terrain
        )
        
        return NarrativeStory(
            turtle_id=turtle.turtle_id,
            story_type="victory",
            title=f"{turtle.name} Conquers {tournament_name}",
            content=story_content,
            generated_at=time.time(),
            tags=["victory", dominant_trait, color],
            is_legendary=False
        )
    
    def generate_legendary_story(self, turtle: TurtleRecord) -> NarrativeStory:
        """Generate legendary ascension story"""
        dominant_trait = self._get_dominant_trait(turtle.genome)
        color = self._get_color_description(turtle.genome)
        terrain = self._get_preferred_terrain(turtle.genome)
        
        template = random.choice(self.story_templates['legendary'])
        
        story_content = template.format(
            name=turtle.name,
            trait=dominant_trait,
            color=color,
            terrain=terrain
        )
        
        return NarrativeStory(
            turtle_id=turtle.turtle_id,
            story_type="legendary",
            title=f"The Legend of {turtle.name}",
            content=story_content,
            generated_at=time.time(),
            tags=["legendary", dominant_trait, color, "ascension"],
            is_legendary=True
        )
    
    def _get_dominant_trait(self, genome: TurboGenome) -> str:
        """Extract dominant trait from genome"""
        traits = {
            'speed': genome.speed,
            'stamina': genome.stamina,
            'intelligence': genome.intelligence,
            'swimming': genome.swim,
            'climbing': genome.climb
        }
        
        dominant = max(traits.items(), key=lambda x: x[1])
        
        trait_names = {
            'speed': 'blazing speed',
            'stamina': 'unwavering stamina',
            'intelligence': 'strategic intelligence',
            'swimming': 'aquatic mastery',
            'climbing': 'climbing prowess'
        }
        
        return trait_names.get(dominant[0], 'exceptional ability')
    
    def _get_color_description(self, genome: TurboGenome) -> str:
        """Get color description from genome"""
        shell_color = genome.get_dominant_shell_color()
        r, g, b = shell_color
        
        # Color classification
        if r > 200 and g < 100 and b < 100:
            return "crimson"
        elif r < 100 and g > 200 and b < 100:
            return "emerald"
        elif r < 100 and g < 100 and b > 200:
            return "sapphire"
        elif r > 200 and g > 200 and b < 100:
            return "golden"
        elif r > 200 and g < 100 and b > 200:
            return "violet"
        elif r < 100 and g > 200 and b > 200:
            return "azure"
        elif r > 150 and g > 150 and b > 150:
            return "silver"
        else:
            return "mystic"
    
    def _get_preferred_terrain(self, genome: TurboGenome) -> str:
        """Get preferred terrain from genome adaptations"""
        adaptations = {
            'water': genome.swim,
            'rocks': genome.climb,
            'grass': genome.speed,
            'sand': genome.stamina
        }
        
        preferred = max(adaptations.items(), key=lambda x: x[1])
        
        terrain_names = {
            'water': 'aquatic',
            'rocks': 'mountain',
            'grass': 'plains',
            'sand': 'desert'
        }
        
        return terrain_names.get(preferred[0], 'diverse')
    
    def _get_action_description(self, trait: str) -> str:
        """Get action description for trait"""
        actions = {
            'blazing speed': 'outpace any competitor',
            'unwavering stamina': 'endure the longest races',
            'strategic intelligence': 'navigate optimal paths',
            'aquatic mastery': 'dominate water segments',
            'climbing prowess': 'conquer rocky terrain'
        }
        
        return actions.get(trait, 'excel in all conditions')
    
    def should_generate_legendary_story(self, turtle: TurtleRecord) -> bool:
        """Check if turtle should receive legendary status"""
        return turtle.wins >= self.legendary_threshold
    
    def generate_llm_enhanced_story(self, base_story: NarrativeStory, turtle: TurtleRecord) -> NarrativeStory:
        """Enhance story with LLM generation (placeholder for future integration)"""
        # In a full implementation, this would call an LLM API
        # For now, we'll enhance the base story with additional details
        
        enhanced_content = f"{base_story.content}\n\n"
        enhanced_content += f"With {turtle.wins} victories and {turtle.total_races} races, "
        enhanced_content += f"{turtle.name} has earned {turtle.earnings:.0f} credits in prize money. "
        enhanced_content += f"Their genetic signature '{turtle.genome.genetic_signature}' represents "
        enhanced_content += f"a lineage of excellence spanning {turtle.generation} generations."
        
        # Update the story
        base_story.content = enhanced_content
        base_story.tags.extend(['enhanced', 'lineage', 'credits'])
        
        return base_story


class NarrativeBridge:
    """Bridge between tournament results and narrative generation"""
    
    def __init__(self, storage_path: Optional[Path] = None):
        self.storage_path = storage_path or Path(__file__).parent.parent.parent.parent / "data" / "narratives.json"
        self.generator = NarrativeGenerator()
        self.narratives: Dict[str, List[NarrativeStory]] = {}
        
        self._load_existing_narratives()
        
        logger.info("🌉 Narrative Bridge initialized")
    
    def _load_existing_narratives(self):
        """Load existing narratives from storage"""
        if self.storage_path.exists():
            try:
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)
                
                for turtle_id, stories in data.items():
                    self.narratives[turtle_id] = []
                    for story_data in stories:
                        story = NarrativeStory(
                            turtle_id=story_data['turtle_id'],
                            story_type=story_data['story_type'],
                            title=story_data['title'],
                            content=story_data['content'],
                            generated_at=story_data['generated_at'],
                            tags=story_data['tags'],
                            is_legendary=story_data['is_legendary']
                        )
                        self.narratives[turtle_id].append(story)
                
                logger.info(f"🌉 Loaded {len(self.narratives)} turtle narratives")
                
            except Exception as e:
                logger.warning(f"🌉 Failed to load narratives: {e}")
    
    def _save_narratives(self):
        """Save narratives to storage"""
        try:
            data = {}
            for turtle_id, stories in self.narratives.items():
                data[turtle_id] = [story.to_dict() for story in stories]
            
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.storage_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.debug(f"🌉 Saved {len(data)} turtle narratives")
            
        except Exception as e:
            logger.error(f"🌉 Failed to save narratives: {e}")
    
    def process_tournament_result(self, turtle: TurtleRecord, tournament_name: str, position: int) -> Optional[NarrativeStory]:
        """Process tournament result and generate narrative if appropriate"""
        story = None
        
        # Generate victory story for winners
        if position == 1:
            story = self.generator.generate_victory_story(turtle, tournament_name)
            self._add_narrative(story)
            
            logger.info(f"🌉 Generated victory story for {turtle.name}")
        
        # Check for legendary ascension
        if self.generator.should_generate_legendary_story(turtle):
            # Check if legendary story already exists
            existing_stories = self.narratives.get(turtle.turtle_id, [])
            has_legendary = any(s.is_legendary for s in existing_stories)
            
            if not has_legendary:
                legendary_story = self.generator.generate_legendary_story(turtle)
                enhanced_story = self.generator.generate_llm_enhanced_story(legendary_story, turtle)
                self._add_narrative(enhanced_story)
                
                logger.info(f"🌉 Generated legendary story for {turtle.name}")
                
                return enhanced_story
        
        return story
    
    def _add_narrative(self, story: NarrativeStory):
        """Add narrative to storage"""
        if story.turtle_id not in self.narratives:
            self.narratives[story.turtle_id] = []
        
        self.narratives[story.turtle_id].append(story)
        
        # Auto-save
        self._save_narratives()
    
    def generate_origin_story_if_needed(self, turtle: TurtleRecord) -> Optional[NarrativeStory]:
        """Generate origin story for new turtles"""
        existing_stories = self.narratives.get(turtle.turtle_id, [])
        
        if not existing_stories:
            origin_story = self.generator.generate_origin_story(turtle)
            self._add_narrative(origin_story)
            
            logger.info(f"🌉 Generated origin story for {turtle.name}")
            return origin_story
        
        return None
    
    def get_turtle_narratives(self, turtle_id: str) -> List[NarrativeStory]:
        """Get all narratives for a turtle"""
        return self.narratives.get(turtle_id, [])
    
    def get_legendary_turtles(self) -> List[Tuple[str, NarrativeStory]]:
        """Get all legendary turtles and their stories"""
        legendary_turtles = []
        
        for turtle_id, stories in self.narratives.items():
            for story in stories:
                if story.is_legendary:
                    legendary_turtles.append((turtle_id, story))
                    break  # Only need one legendary story per turtle
        
        return legendary_turtles
    
    def get_narrative_summary(self) -> Dict[str, Any]:
        """Get summary of all narratives"""
        total_stories = sum(len(stories) for stories in self.narratives.values())
        legendary_count = len(self.get_legendary_turtles())
        
        story_types = {}
        for stories in self.narratives.values():
            for story in stories:
                story_type = story.story_type
                story_types[story_type] = story_types.get(story_type, 0) + 1
        
        return {
            'total_turtles': len(self.narratives),
            'total_stories': total_stories,
            'legendary_turtles': legendary_count,
            'story_types': story_types,
            'storage_path': str(self.storage_path)
        }


# Global narrative bridge instance
narrative_bridge = NarrativeBridge()
