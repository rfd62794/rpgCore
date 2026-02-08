"""
LLM Narrative Generator - Legendary Pilot Stories
Transforms combat performance data into compelling pilot narratives
"""

import json
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum

from loguru import logger


class NarrativeStyle(Enum):
    """Different narrative styles for pilot stories"""
    MILITARY_REPORT = "military_report"
    HEROIC_EPIC = "heroic_epic"
    TECHNICAL_BRIEFING = "technical_briefing"
    PERSONAL_JOURNAL = "personal_journal"
    AFTER_ACTION_REPORT = "after_action_report"


@dataclass
class NarrativeTemplate:
    """Template for generating pilot narratives"""
    style: NarrativeStyle
    system_prompt: str
    user_prompt_template: str
    output_format: str = "json"
    max_tokens: int = 500
    temperature: float = 0.7


class LLMPromptGenerator:
    """Generates LLM prompts for legendary pilot narrative creation"""
    
    def __init__(self):
        self.templates = self._initialize_templates()
        logger.debug("📖 LLM Prompt Generator initialized")
    
    def _initialize_templates(self) -> Dict[NarrativeStyle, NarrativeTemplate]:
        """Initialize narrative templates for different styles"""
        templates = {
            NarrativeStyle.MILITARY_REPORT: NarrativeTemplate(
                style=NarrativeStyle.MILITARY_REPORT,
                system_prompt="""You are a military intelligence analyst writing concise pilot performance reports. 
                Focus on tactical effectiveness, combat statistics, and strategic value. 
                Use formal military terminology. Be factual and data-driven.""",
                user_prompt_template="""Generate a military performance report for pilot {pilot_name}, a {role} from generation {generation}.
                
                COMBAT RECORD:
                - Skirmishes Survived: {skirmishes_survived}
                - Victories Achieved: {victories_achieved}
                - Win Rate: {win_rate:.1%}
                - Total Damage Dealt: {damage_dealt:.0f}
                - MVP Awards: {mvp_awards}
                
                COMBAT STYLE:
                - Accuracy: {accuracy:.1%}
                - Survival Rate: {survival_rate:.1%}
                - Average Damage per Skirmish: {avg_damage_per_skirmish:.0f}
                
                NARRATIVE SEED: {narrative_seed}
                
                Provide a concise military assessment focusing on tactical capabilities and recommendations.""",
                output_format="json",
                max_tokens=400,
                temperature=0.3
            ),
            
            NarrativeStyle.HEROIC_EPIC: NarrativeTemplate(
                style=NarrativeStyle.HEROIC_EPIC,
                system_prompt="""You are a space opera chronicler writing heroic tales of legendary pilots.
                Focus on courage, skill, and dramatic moments. Use epic language and vivid imagery.
                Emphasize the pilot's personality and legendary status.""",
                user_prompt_template="""Write an epic tale of the legendary pilot {pilot_name}, known throughout the fleet as a formidable {role} from generation {generation}.
                
                LEGENDARY STATS:
                - {victories_achieved} glorious victories out of {skirmishes_survived} battles survived
                - Win Rate: {win_rate:.1%}
                - {damage_dealt:.0f} total damage dealt to enemies of the fleet
                - {mvp_awards} times named Most Valuable Pilot
                
                COMBAT PROWESS:
                - Deadly accuracy: {accuracy:.1%}
                - Legendary survival: {survival_rate:.1%}
                - Average devastation per battle: {avg_damage_per_skirmish:.0f}
                
                LEGEND BEGINS: {narrative_seed}
                
                Craft a heroic narrative that captures the essence of this pilot's legend and inspires future generations.""",
                output_format="json",
                max_tokens=600,
                temperature=0.8
            ),
            
            NarrativeStyle.TECHNICAL_BRIEFING: NarrativeTemplate(
                style=NarrativeStyle.TECHNICAL_BRIEFING,
                system_prompt="""You are a combat systems analyst providing technical briefings on pilot performance.
                Focus on technical metrics, system efficiency, and combat patterns. Use precise technical language.
                Include performance analysis and optimization recommendations.""",
                user_prompt_template="""Generate a technical combat analysis for pilot {pilot_name}, {role} class, generation {generation}.
                
                PERFORMANCE METRICS:
                - Mission Success Rate: {win_rate:.1%} ({victories_achieved}/{skirmishes_survived})
                - Total Damage Output: {damage_dealt:.0f} units
                - Damage Per Engagement: {avg_damage_per_skirmish:.0f} units
                - Weapon Accuracy: {accuracy:.1%}
                - Survival Probability: {survival_rate:.1%}
                - MVP Recognition Events: {mvp_awards}
                
                OPERATIONAL NOTES: {narrative_seed}
                
                Provide technical analysis covering combat efficiency, targeting patterns, and system performance recommendations.""",
                output_format="json",
                max_tokens=500,
                temperature=0.2
            ),
            
            NarrativeStyle.PERSONAL_JOURNAL: NarrativeTemplate(
                style=NarrativeStyle.PERSONAL_JOURNAL,
                system_prompt="""You are writing from the perspective of a seasoned pilot reflecting on their career.
                Use personal, introspective language. Focus on emotions, experiences, and personal growth.
                Include doubts, triumphs, and the human side of combat.""",
                user_prompt_template="""Write a personal journal entry from the perspective of pilot {pilot_name}, reflecting on their journey as a {role} pilot.
                
                CAREER HIGHLIGHTS:
                - Survived {skirmishes_survived} skirmishes
                - Achieved {victories_achieved} victories
                - Success rate: {win_rate:.1%}
                - Dealt {damage_dealt:.0f} damage to hostiles
                - Earned {mvp_awards} MVP commendations
                
                PERSONAL STATS:
                - Shot accuracy: {accuracy:.1%}
                - Still flying after {survival_rate:.1%} of engagements
                - Typical damage output: {avg_damage_per_skirmish:.0f} per battle
                
                REFLECTION PROMPT: {narrative_seed}
                
                Write in first person, capturing the pilot's voice, feelings about their service, and thoughts on their legacy.""",
                output_format="json",
                max_tokens=550,
                temperature=0.6
            ),
            
            NarrativeStyle.AFTER_ACTION_REPORT: NarrativeTemplate(
                style=NarrativeStyle.AFTER_ACTION_REPORT,
                system_prompt="""You are a debriefing officer writing after-action reports on pilot performance.
                Focus on mission outcomes, tactical decisions, and lessons learned. Use clear, structured reporting.
                Include recommendations for future operations.""",
                user_prompt_template="""Generate an after-action report for pilot {pilot_name}, {role} specialist, generation {generation}.
                
                MISSION SUMMARY:
                - Total Engagements: {skirmishes_survived}
                - Successful Outcomes: {victories_achieved}
                - Mission Success Rate: {win_rate:.1%}
                - Total Hostile Damage: {damage_dealt:.0f}
                - MVP Citations: {mvp_awards}
                
                PERFORMANCE ANALYSIS:
                - Weapons Accuracy: {accuracy:.1%}
                - Survival Rate: {survival_rate:.1%}
                - Average Engagement Damage: {avg_damage_per_skirmish:.0f}
                
                OPERATIONAL NOTES: {narrative_seed}
                
                Structure as a formal debriefing with mission outcomes, performance assessment, and recommendations.""",
                output_format="json",
                max_tokens=450,
                temperature=0.4
            )
        }
        
        return templates
    
    def generate_prompt(self, pilot_data: Dict[str, Any], 
                       style: NarrativeStyle = NarrativeStyle.MILITARY_REPORT) -> Dict[str, Any]:
        """Generate LLM prompt for pilot narrative creation"""
        try:
            template = self.templates.get(style)
            if not template:
                raise ValueError(f"Unknown narrative style: {style}")
            
            # Format user prompt with pilot data
            user_prompt = template.user_prompt_template.format(**pilot_data)
            
            # Create complete prompt package
            prompt_package = {
                "system_prompt": template.system_prompt,
                "user_prompt": user_prompt,
                "output_format": template.output_format,
                "max_tokens": template.max_tokens,
                "temperature": template.temperature,
                "pilot_data": pilot_data,
                "narrative_style": style.value
            }
            
            logger.debug(f"📖 Generated {style.value} prompt for pilot {pilot_data.get('pilot_name', 'Unknown')}")
            return prompt_package
            
        except Exception as e:
            logger.error(f"📖 Failed to generate prompt: {e}")
            return {}
    
    def generate_batch_prompts(self, pilot_data_list: List[Dict[str, Any]], 
                             style: NarrativeStyle = NarrativeStyle.MILITARY_REPORT) -> List[Dict[str, Any]]:
        """Generate prompts for multiple pilots"""
        prompts = []
        
        for pilot_data in pilot_data_list:
            prompt = self.generate_prompt(pilot_data, style)
            if prompt:
                prompts.append(prompt)
        
        logger.info(f"📖 Generated {len(prompts)} {style.value} prompts")
        return prompts
    
    def create_mvp_spotlight_prompt(self, mvp_data: Dict[str, Any], 
                                  skirmish_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create special prompt for MVP spotlight narrative"""
        try:
            # Combine MVP and skirmish data
            combined_data = {
                **mvp_data,
                "skirmish_outcome": skirmish_data.get("outcome", "victory"),
                "team_performance": skirmish_data.get("team_performance", {}),
                "mvp_performance": skirmish_data.get("mvp_performance", {}),
                "command_context": skirmish_data.get("command_context", {})
            }
            
            # Use heroic epic style for MVP spotlights
            template = self.templates[NarrativeStyle.HEROIC_EPIC]
            
            # Custom MVP prompt
            mvp_prompt = f"""Write an epic spotlight story celebrating pilot {combined_data.get('pilot_name')} as the Most Valuable Pilot of their latest engagement.
            
            MVP PERFORMANCE:
            - Damage Dealt: {combined_data.get('mvp_performance', {}).get('damage_dealt', 0)}
            - Accuracy: {combined_data.get('mvp_performance', {}).get('accuracy', 0):.1%}
            - Survival: {'Survived' if combined_data.get('mvp_performance', {}).get('survived', False) else 'Lost'}
            - Damage Contribution: {combined_data.get('mvp_performance', {}).get('damage_contribution', 0):.1%}
            
            BATTLE CONTEXT:
            - Outcome: {combined_data.get('skirmish_outcome', 'victory').title()}
            - Team Efficiency: {combined_data.get('team_performance', {}).get('efficiency', 0):.1%}
            - Battle Duration: {combined_data.get('team_performance', {}).get('duration', 0)}s
            
            CAREER HIGHLIGHTS:
            - Total Victories: {combined_data.get('victories_achieved', 0)}
            - MVP Awards: {combined_data.get('mvp_awards', 0)}
            - Win Rate: {combined_data.get('win_rate', 0):.1%}
            
            Create a thrilling narrative that captures this pilot's heroic moment and cements their legend in the fleet's history."""
            
            prompt_package = {
                "system_prompt": template.system_prompt,
                "user_prompt": mvp_prompt,
                "output_format": template.output_format,
                "max_tokens": template.max_tokens + 100,  # Extra for MVP stories
                "temperature": template.temperature,
                "pilot_data": combined_data,
                "narrative_style": NarrativeStyle.HEROIC_EPIC.value,
                "special_type": "mvp_spotlight"
            }
            
            logger.debug(f"📖 Generated MVP spotlight for {combined_data.get('pilot_name', 'Unknown')}")
            return prompt_package
            
        except Exception as e:
            logger.error(f"📖 Failed to generate MVP spotlight: {e}")
            return {}
    
    def get_available_styles(self) -> List[str]:
        """Get list of available narrative styles"""
        return [style.value for style in NarrativeStyle]
    
    def get_style_template(self, style: NarrativeStyle) -> Optional[NarrativeTemplate]:
        """Get template information for a specific style"""
        return self.templates.get(style)


# Factory function for easy initialization
def create_prompt_generator() -> LLMPromptGenerator:
    """Create an LLM prompt generator instance"""
    return LLMPromptGenerator()


# Global instance
prompt_generator = create_prompt_generator()
