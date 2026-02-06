"""
Semantic Intent Resolution Engine

Uses sentence embeddings to map natural language player input to structured intents.
Designed for laptop-friendly performance (<50ms on CPU).
"""

from dataclasses import dataclass
from typing import Dict, Optional

import numpy as np
from loguru import logger
from sentence_transformers import SentenceTransformer, util


@dataclass
class IntentMatch:
    """Result of intent resolution with confidence scoring."""
    
    intent_id: str
    description: str
    confidence: float


class IntentLibrary:
    """
    Extensible repository of game intents with exemplar-based matching.
    
    Each intent has:
    - intent_id: Unique identifier (e.g., 'distract', 'force')
    - exemplars: List of concrete action examples for semantic matching
    
    Design: Multiple exemplars increase semantic hit-rate for small models
    by providing diverse action patterns within the same intent category.
    """
    
    def __init__(self):
        self._intents: Dict[str, list[str]] = {}
        self._embeddings: Optional[Dict[str, np.ndarray]] = None
        self._embeddings_stale = True
    
    def add_intent(self, intent_id: str, exemplars: list[str]) -> None:
        """
        Add or update an intent with action exemplars.
        
        Args:
            intent_id: Unique intent identifier
            exemplars: 3-5 concrete action examples (e.g., "Throw a beer", "Kick a table")
        """
        if not exemplars:
            raise ValueError(f"Intent '{intent_id}' must have at least one exemplar")
        
        self._intents[intent_id] = exemplars
        self._embeddings_stale = True
        logger.debug(f"Added intent: {intent_id} with {len(exemplars)} exemplars")
    
    def get_intents(self) -> Dict[str, list[str]]:
        """Return all registered intents with their exemplars."""
        return self._intents.copy()
    
    def mark_embeddings_computed(self, embeddings: Dict[str, np.ndarray]) -> None:
        """Cache precomputed embeddings (called by SemanticResolver)."""
        self._embeddings = embeddings
        self._embeddings_stale = False


class SemanticResolver:
    """
    Maps player input to intents using cosine similarity.
    
    Performance:
    - Model load: ~200ms (one-time)
    - Inference: <50ms per query on CPU
    """
    
    def __init__(
        self,
        intent_library: IntentLibrary,
        model_name: str = 'all-MiniLM-L6-v2',
        confidence_threshold: float = 0.5
    ):
        """
        Initialize semantic resolver.
        
        Args:
            intent_library: Library of intents to match against
            model_name: SentenceTransformer model (default: MiniLM, 80MB)
            confidence_threshold: Minimum similarity score (0-1) to accept match
        """
        self.intent_library = intent_library
        self.confidence_threshold = confidence_threshold
        
        logger.info(f"Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name)
        
        # Pre-compute intent embeddings
        self._update_intent_embeddings()
    
    def _update_intent_embeddings(self) -> None:
        """
        Compute and cache embeddings for all intent exemplars.
        
        For each intent, we compute embeddings for ALL exemplars, allowing
        max-similarity matching during resolution.
        """
        intents = self.intent_library.get_intents()
        
        if not intents:
            logger.warning("Intent library is empty!")
            return
        
        # Compute embeddings per-intent (each intent has multiple exemplars)
        embeddings_dict = {}
        total_exemplars = 0
        
        for intent_id, exemplars in intents.items():
            # Encode all exemplars for this intent
            exemplar_embeddings = self.model.encode(exemplars, convert_to_numpy=True)
            embeddings_dict[intent_id] = exemplar_embeddings
            total_exemplars += len(exemplars)
        
        self.intent_library.mark_embeddings_computed(embeddings_dict)
        logger.info(
            f"Precomputed embeddings for {len(intents)} intents "
            f"({total_exemplars} total exemplars)"
        )
    
    def resolve_intent(self, player_input: str) -> Optional[IntentMatch]:
        """
        Find the best matching intent using max-similarity across exemplars.
        
        Algorithm:
        1. Encode player input
        2. For each intent, compute similarity against ALL exemplars
        3. Take the MAX similarity score for that intent
        4. Select the intent with the highest max score
        5. Fallback to 'improvise' if confidence is too low
        
        Args:
            player_input: Natural language action (e.g., "I kick the table")
        
        Returns:
            IntentMatch if confidence exceeds threshold, otherwise None
        """
        if not player_input.strip():
            logger.warning("Empty input received")
            return None
        
        intents = self.intent_library.get_intents()
        
        if not intents:
            logger.error("Cannot resolve intent: library is empty")
            return None
        
        # Get cached embeddings (or recompute if stale)
        if self.intent_library._embeddings_stale:
            self._update_intent_embeddings()
        
        # Encode player input once
        input_embedding = self.model.encode(player_input, convert_to_numpy=True)
        
        # Find best intent via max-similarity matching
        best_intent_id = None
        best_score = 0.0
        best_exemplar = ""
        
        for intent_id, exemplar_embeddings in self.intent_library._embeddings.items():
            # Compute similarity against all exemplars for this intent
            scores = util.cos_sim(input_embedding, exemplar_embeddings)[0]
            
            # Convert torch tensor to numpy for compatibility
            if hasattr(scores, 'numpy'):
                scores_np = scores.cpu().numpy()
            else:
                scores_np = np.array(scores)
            
            # Take the MAX score (closest exemplar match)
            max_score = float(np.max(scores_np))
            max_idx = int(np.argmax(scores_np))
            
            # Track the best intent across all intents
            if max_score > best_score:
                best_score = max_score
                best_intent_id = intent_id
                best_exemplar = intents[intent_id][max_idx]
        
        if best_intent_id is None:
            logger.error("No intent matched (should not happen)")
            return None
        
        logger.info(
            f"Intent resolution: '{player_input}' → {best_intent_id} "
            f"(confidence: {best_score:.3f}, matched exemplar: '{best_exemplar}')"
        )
        
        # Reject low-confidence matches
        if best_score < self.confidence_threshold:
            logger.warning(
                f"Confidence {best_score:.3f} below threshold "
                f"{self.confidence_threshold}"
            )
            return None
        
        return IntentMatch(
            intent_id=best_intent_id,
            description=best_exemplar,  # Return the matched exemplar
            confidence=best_score
        )
    
    def add_intent(self, intent_id: str, exemplars: list[str]) -> None:
        """Convenience method to add intent and invalidate cache."""
        self.intent_library.add_intent(intent_id, exemplars)


def create_default_intent_library() -> IntentLibrary:
    """
    Create an intent library with action-focused exemplars.
    
    Design Philosophy:
    - 3-5 exemplars per intent (more = semantic bleed)
    - Use concrete action verbs (throw, kick, shout)
    - Cover diverse player phrasings
    - Focus on 4 core D&D pillars: Distract, Force, Finesse, Charm
    """
    library = IntentLibrary()
    
    # ============================================================
    # DISTRACT: Diversions and attention manipulation
    # ============================================================
    library.add_intent(
        "distract",
        [
            "Throw a beer mug at someone to create a distraction",
            "Kick over a table to cause a commotion",
            "Shout loudly to draw attention away",
            "Knock over furniture to cause a scene",
            "Start a fake argument to divert guards"
        ]
    )
    
    # ============================================================
    # FORCE: Direct physical violence or destruction
    # ============================================================
    library.add_intent(
        "force",
        [
            "Attack with a sword or weapon",
            "Punch or kick someone aggressively",
            "Break down a door with force",
            "Tackle someone to the ground",
            "Smash through an obstacle"
        ]
    )
    
    # ============================================================
    # FINESSE: Stealth, precision, and subtlety
    # ============================================================
    library.add_intent(
        "finesse",
        [
            "Sneak past quietly without being noticed",
            "Pick a lock with lockpicks",
            "Pickpocket someone's belongings",
            "Move silently through the shadows",
            "Slip by undetected"
        ]
    )
    
    # ============================================================
    # CHARM: Social manipulation and persuasion
    # ============================================================
    library.add_intent(
        "charm",
        [
            "Convince someone with words and charisma",
            "Negotiate a deal or trade",
            "Flirt or use charm to persuade",
            "Talk your way out of trouble",
            "Offer a bribe to gain cooperation"
        ]
    )
    
    # ============================================================
    # INTIMIDATE: Threats and coercion
    # ============================================================
    library.add_intent(
        "intimidate",
        [
            "Threaten someone with violence",
            "Scare someone into compliance",
            "Loom menacingly to frighten",
            "Show your weapon as a threat",
            "Use harsh words to coerce"
        ]
    )
    
    # ============================================================
    # DECEIVE: Lies, tricks, and misdirection
    # ============================================================
    library.add_intent(
        "deceive",
        [
            "Lie convincingly about your identity",
            "Bluff your way through a situation",
            "Create a false story to mislead",
            "Trick someone with deception",
            "Pretend to be someone else"
        ]
    )
    
    # ============================================================
    # INVESTIGATE: Examination and information gathering
    # ============================================================
    library.add_intent(
        "investigate",
        [
            "Search the room carefully for clues",
            "Examine an object closely",
            "Inspect the area for hidden items",
            "Study a document or text",
            "Look for secret passages"
        ]
    )
    
    # ============================================================
    # USE_ITEM: Inventory and equipment usage
    # ============================================================
    library.add_intent(
        "use_item",
        [
            "Drink a health potion to heal",
            "Use a tool from your inventory",
            "Equip a weapon or armor",
            "Consume a magical item",
            "Apply a potion or salve"
        ]
    )
    
    # ============================================================
    # DEFEND: Protective actions
    # ============================================================
    library.add_intent(
        "defend",
        [
            "Block an incoming attack with a shield",
            "Dodge or parry an enemy strike",
            "Take cover behind an obstacle",
            "Protect yourself from harm",
            "Raise your guard defensively"
        ]
    )
    
    # ============================================================
    # IMPROVISE: Fallback for creative/unusual actions
    # ============================================================
    library.add_intent(
        "improvise",
        [
            "Do something creative and unexpected",
            "Try an unusual or wild action",
            "Attempt something unconventional",
            "Use the environment in a creative way",
            "Take an unorthodox approach"
        ]
    )
    
    return library
