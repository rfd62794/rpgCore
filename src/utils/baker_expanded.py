"""
Expanded Semantic Baker: Multi-Asset Vector Compiler

Phase 2: Vectorized World Engine implementation.
Bakes multiple asset classes (Intents, Traits, Lore) for procedural generation.

Usage:
    python -m src.utils.baker_expanded --assets intents traits lore

ROI: Enables Latent Narrative Space with procedural world generation.
"""

import sys
import os
from pathlib import Path
import pickle
import numpy as np
from typing import Dict, List, Optional, Type, Any
from dataclasses import dataclass
from enum import Enum

from loguru import logger
from sentence_transformers import SentenceTransformer

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from semantic_engine import create_default_intent_library
from vector_libraries.trait_library import TraitLibrary


class AssetType(Enum):
    """Types of vectorized assets that can be baked."""
    INTENTS = "intents"
    TRAITS = "traits"
    LORE = "lore"
    INTERACTIONS = "interactions"
    DIALOGUE = "dialogue"


@dataclass
class AssetBundle:
    """Container for baked vector assets."""
    asset_type: AssetType
    vectors: Dict[str, np.ndarray]
    metadata: Dict[str, Any]
    version: str = "1.0"


class ExpandedBaker:
    """
    Multi-asset vector compiler for the Latent Narrative Space.
    
    This is the "DNA Compiler" that transforms text assets into
    mathematical vectors for procedural world generation.
    """
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """Initialize the expanded baker with sentence transformer."""
        self.model_name = model_name
        self.model = None  # Lazy load
        logger.info(f"Expanded Baker initialized with model: {model_name}")
    
    def _ensure_model_loaded(self):
        """Ensure the sentence transformer model is loaded."""
        if self.model is None:
            self.model = SentenceTransformer(self.model_name)
    
    def bake_intents(self, output_path: Path) -> AssetBundle:
        """Bake intent vectors (existing functionality)."""
        self._ensure_model_loaded()
        
        # Load intent library
        intent_library = create_default_intent_library()
        
        # Collect all texts to embed
        texts_to_embed = []
        embedding_keys = []
        
        # Add intent exemplars
        for intent_name, exemplars in intent_library.get_intents().items():
            for i, example in enumerate(exemplars):
                texts_to_embed.append(example)
                embedding_keys.append(f"example_{intent_name}_{i}")
        
        logger.info(f"Baking {len(texts_to_embed)} intent vectors...")
        
        # Batch compute embeddings
        embeddings = self.model.encode(
            texts_to_embed,
            batch_size=32,
            show_progress_bar=True,
            convert_to_numpy=True
        )
        
        # Create mapping dictionary
        vector_map = dict(zip(embedding_keys, embeddings))
        
        # Create asset bundle
        bundle = AssetBundle(
            asset_type=AssetType.INTENTS,
            vectors=vector_map,
            metadata={
                "total_vectors": len(vector_map),
                "model_name": self.model_name,
                "intent_count": len(intent_library.get_intents())
            }
        )
        
        # Save to file
        self._save_asset_bundle(bundle, output_path)
        
        logger.info(f"Successfully baked {len(vector_map)} intent vectors to {output_path}")
        return bundle
    
    def bake_traits(self, output_path: Path) -> AssetBundle:
        """Bake trait vectors for NPC/Location DNA."""
        self._ensure_model_loaded()
        
        # Initialize trait library
        trait_library = TraitLibrary(self.model_name)
        
        # Collect all trait vectors
        vector_map = {}
        for trait_name, trait in trait_library.traits.items():
            vector_map[trait_name] = trait.vector
        
        # Create asset bundle
        bundle = AssetBundle(
            asset_type=AssetType.TRAITS,
            vectors=vector_map,
            metadata={
                "total_vectors": len(vector_map),
                "model_name": self.model_name,
                "categories": {
                    category.value: len(trait_library.get_traits_by_category(category))
                    for category in set(trait.category for trait in trait_library.traits.values())
                }
            }
        )
        
        # Save to file
        self._save_asset_bundle(bundle, output_path)
        
        logger.info(f"Successfully baked {len(vector_map)} trait vectors to {output_path}")
        return bundle
    
    def bake_interactions(self, output_path: Path) -> AssetBundle:
        """Bake specialized interaction vectors for different scenarios."""
        self._ensure_model_loaded()
        
        # Define specialized interaction sets
        interaction_sets = {
            "combat": [
                "parry the incoming attack",
                "riposte with a counter strike", 
                "feint to create an opening",
                "disarm the opponent",
                "grapple and restrain",
                "shield bash to stagger",
                "flank for advantage",
                "overpower with strength"
            ],
            "social": [
                "flatter with genuine compliments",
                "blackmail with threatening information",
                "philosophize about moral questions",
                "bribe with valuable items",
                "negotiate a compromise",
                "intimidate with implied threats",
                "console with empathy",
                "debate with logic"
            ],
            "utility": [
                "pick the complex lock",
                "disarm the trap mechanism",
                "repair the broken device",
                "forge the metal item",
                "brew the healing potion",
                "identify the magical item",
                "track the footprints",
                "survive in the wilderness"
            ],
            "stealth": [
                "shadow the target silently",
                "create a diversion",
                "pickpocket without detection",
                "sneak past the guards",
                "hide in the shadows",
                "muffle the footsteps",
                "disguise the appearance",
                "blend into the crowd"
            ]
        }
        
        # Collect all texts to embed
        texts_to_embed = []
        embedding_keys = []
        
        for category, interactions in interaction_sets.items():
            for i, interaction in enumerate(interactions):
                texts_to_embed.append(interaction)
                embedding_keys.append(f"{category}_{i}")
        
        logger.info(f"Baking {len(texts_to_embed)} interaction vectors...")
        
        # Batch compute embeddings
        embeddings = self.model.encode(
            texts_to_embed,
            batch_size=32,
            show_progress_bar=True,
            convert_to_numpy=True
        )
        
        # Create mapping dictionary
        vector_map = dict(zip(embedding_keys, embeddings))
        
        # Create asset bundle
        bundle = AssetBundle(
            asset_type=AssetType.INTERACTIONS,
            vectors=vector_map,
            metadata={
                "total_vectors": len(vector_map),
                "model_name": self.model_name,
                "categories": {cat: len(interactions) for cat, interactions in interaction_sets.items()}
            }
        )
        
        # Save to file
        self._save_asset_bundle(bundle, output_path)
        
        logger.info(f"Successfully baked {len(vector_map)} interaction vectors to {output_path}")
        return bundle
    
    def bake_lore(self, output_path: Path) -> AssetBundle:
        """Bake lore vectors for long-term campaign memory."""
        self._ensure_model_loaded()
        
        # Define common lore events
        lore_events = [
            "defeated the dragon in the ancient ruins",
            "discovered the hidden treasure vault",
            "saved the village from bandits",
            "broke the curse on the enchanted forest",
            "uncovered the conspiracy in the royal court",
            "found the lost artifact of power",
            "escaped from the dungeon of doom",
            "made peace with the hostile tribe",
            "solved the mystery of the haunted mansion",
            "completed the pilgrimage to the sacred mountain",
            "betrayed the trust of the merchant guild",
            "rescued the kidnapped noble",
            "destroyed the evil wizard's tower",
            "recovered the stolen crown jewels",
            "negotiated the treaty between warring kingdoms"
        ]
        
        logger.info(f"Baking {len(lore_events)} lore vectors...")
        
        # Batch compute embeddings
        embeddings = self.model.encode(
            lore_events,
            batch_size=16,
            show_progress_bar=True,
            convert_to_numpy=True
        )
        
        # Create mapping dictionary
        vector_map = dict(zip([f"lore_{i}" for i in range(len(lore_events))], embeddings))
        
        # Create asset bundle
        bundle = AssetBundle(
            asset_type=AssetType.LORE,
            vectors=vector_map,
            metadata={
                "total_vectors": len(vector_map),
                "model_name": self.model_name,
                "description": "Common campaign events for long-term memory"
            }
        )
        
        # Save to file
        self._save_asset_bundle(bundle, output_path)
        
        logger.info(f"Successfully baked {len(vector_map)} lore vectors to {output_path}")
        return bundle
    
    def bake_all_assets(self, output_dir: Path) -> Dict[AssetType, AssetBundle]:
        """Bake all asset types."""
        bundles = {}
        
        # Create output directory
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Bake each asset type
        asset_methods = {
            AssetType.INTENTS: self.bake_intents,
            AssetType.TRAITS: self.bake_traits,
            AssetType.INTERACTIONS: self.bake_interactions,
            AssetType.LORE: self.bake_lore
        }
        
        for asset_type, method in asset_methods.items():
            output_path = output_dir / f"{asset_type.value}_vectors.safetensors"
            logger.info(f"Baking {asset_type.value} assets...")
            bundle = method(output_path)
            bundles[asset_type] = bundle
        
        logger.info(f"Successfully baked all {len(bundles)} asset bundles")
        return bundles
    
    def _save_asset_bundle(self, bundle: AssetBundle, output_path: Path):
        """Save asset bundle to file."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Try safetensors first, fallback to pickle
        try:
            try:
                import torch
                import safetensors.torch
                # Convert to torch tensors for safetensors
                torch_embeddings = {
                    key: torch.from_numpy(vector) 
                    for key, vector in bundle.vectors.items()
                }
                # Include metadata in the file
                torch_embeddings["__metadata__"] = torch.tensor([0])  # Placeholder for metadata
                safetensors.torch.save_file(torch_embeddings, str(output_path))
                
                # Save metadata separately
                metadata_path = output_path.with_suffix(".metadata.json")
                import json
                with open(metadata_path, 'w') as f:
                    json.dump(bundle.metadata, f, indent=2)
                
                logger.info(f"Saved {bundle.asset_type.value} assets in safetensors format")
            except ImportError:
                logger.warning("safetensors not available, falling back to pickle")
                raise
        except Exception as e:
            logger.warning(f"safetensors save failed: {e}, falling back to pickle")
            # Save vectors and metadata together
            combined_data = {
                "vectors": bundle.vectors,
                "metadata": bundle.metadata
            }
            with open(output_path.with_suffix(".pkl"), 'wb') as f:
                pickle.dump(combined_data, f, protocol=pickle.HIGHEST_PROTOCOL)
            logger.info(f"Saved {bundle.asset_type.value} assets in pickle format")
    
    @staticmethod
    def load_asset_bundle(asset_path: Path) -> AssetBundle:
        """Load asset bundle from file."""
        if not asset_path.exists():
            raise FileNotFoundError(f"Asset bundle not found: {asset_path}")
        
        if asset_path.suffix == ".safetensors":
            try:
                import safetensors.torch
                import torch
                import json
                
                # Load vectors
                torch_data = safetensors.torch.load_file(str(asset_path))
                vectors = {k: v.numpy() for k, v in torch_data.items() if not k.startswith("__metadata__")}
                
                # Load metadata
                metadata_path = asset_path.with_suffix(".metadata.json")
                if metadata_path.exists():
                    with open(metadata_path, 'r') as f:
                        metadata = json.load(f)
                else:
                    metadata = {}
                
                # Determine asset type from filename
                asset_type_name = asset_path.stem.split("_")[0]
                asset_type = AssetType(asset_type_name)
                
                return AssetBundle(
                    asset_type=asset_type,
                    vectors=vectors,
                    metadata=metadata
                )
            except ImportError:
                logger.error("safetensors not available for loading")
                raise
        
        # Default to pickle
        with open(asset_path, 'rb') as f:
            combined_data = pickle.load(f)
        
        # Determine asset type from filename
        asset_type_name = asset_path.stem.split("_")[0]
        asset_type = AssetType(asset_type_name)
        
        return AssetBundle(
            asset_type=asset_type,
            vectors=combined_data["vectors"],
            metadata=combined_data.get("metadata", {})
        )


def main():
    """CLI entry point for expanded baking."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Expanded Semantic Baker - Multi-Asset Vector Compiler")
    parser.add_argument(
        "--assets",
        nargs="+",
        choices=["intents", "traits", "interactions", "lore", "all"],
        default=["intents", "traits"],
        help="Asset types to bake (default: intents traits)"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("assets/vectorized"),
        help="Output directory for baked assets"
    )
    parser.add_argument(
        "--model",
        default="all-MiniLM-L6-v2",
        help="Sentence transformer model to use"
    )
    
    args = parser.parse_args()
    
    # Configure logging
    logger.remove()
    logger.add(
        lambda msg: print(msg, end=""),
        level="INFO",
        format="{time:HH:mm:ss} | {level} | {message}"
    )
    
    # Initialize baker
    baker = ExpandedBaker(model_name=args.model)
    
    # Bake requested assets
    if "all" in args.assets:
        bundles = baker.bake_all_assets(args.output)
        print(f"✅ Successfully baked all {len(bundles)} asset bundles")
    else:
        asset_methods = {
            "intents": baker.bake_intents,
            "traits": baker.bake_traits,
            "interactions": baker.bake_interactions,
            "lore": baker.bake_lore
        }
        
        for asset_type in args.assets:
            output_path = args.output / f"{asset_type}_vectors.safetensors"
            logger.info(f"Baking {asset_type} assets...")
            bundle = asset_methods[asset_type](output_path)
            print(f"✅ Baked {bundle.metadata['total_vectors']} {asset_type} vectors")
    
    print(f"📍 Assets saved to: {args.output}")
    print(f"🚀 Latent Narrative Space ready for procedural generation!")


if __name__ == "__main__":
    main()
