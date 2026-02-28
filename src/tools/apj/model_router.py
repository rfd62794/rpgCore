"""Route requests to appropriate layer based on availability"""

from typing import Dict, Optional, Tuple
from .ollama_layer import OllamaLayer

class ModelRouter:
    """Route decisions to appropriate layer"""
    
    def __init__(self):
        self.ollama = OllamaLayer()
        self.local_available = self.ollama.available
    
    def analyze_blockers(self, blockers: list, context: str) -> Tuple[Dict, str]:
        """Analyze blockers - returns (result, layer_used)"""
        if self.local_available:
            result = self.ollama.analyze_blockers(blockers, context)
            if "error" not in result:
                return result, "Layer 3: Ollama (Local)"
            # Fall through to layer 2
        
        # Layer 2: Return raw blockers for local analysis
        return {"blockers": blockers, "context": context}, "Layer 2: Local Analysis"
    
    def phase_strategy(self, phase_num: int, phase_data: Dict) -> Tuple[Dict, str]:
        """Analyze phase - returns (result, layer_used)"""
        if self.local_available:
            result = self.ollama.phase_strategy(phase_num, phase_data)
            if "error" not in result:
                return result, "Layer 3: Ollama (Local)"
        
        # Layer 2: Return phase data for local analysis
        return phase_data, "Layer 2: Local Analysis"
    
    def get_layer_cost(self, layer: str) -> str:
        """Get cost descriptor for layer"""
        costs = {
            "Layer 1: Data Files": "FREE",
            "Layer 2: Local Analysis": "FREE",
            "Layer 3: Ollama (Local)": "FREE/CHEAP",
            "Layer 4: Remote (OpenRouter)": "EXPENSIVE"
        }
        return costs.get(layer, "UNKNOWN")
