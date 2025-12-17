from typing import List, Dict, Any
from src.application.neuro_symbolic.hybrid_reasoner import ReasoningResult

class ProofGenerator:
    """
    Generates human-readable proofs / explanations for reasoning results.
    """
    
    def generate_proof(self, result: ReasoningResult) -> Dict[str, Any]:
        """
        Convert result into structured proof object.
        """
        proof = {
            "conclusion": result.category,
            "confidence": result.confidence,
            "method": result.source,
            "steps": []
        }
        
        if result.source == "symbolic_override":
            proof["steps"].append(f"Found strict rule matching pattern in description.")
            proof["steps"].append(f"Applied Rule Category: {result.category}")
            proof["verified"] = True
            
        elif result.source == "graph_inference":
            proof["steps"].append("Low confidence in neural model.")
            proof["steps"].append("Consulted Knowledge Graph.")
            if result.graph_path:
                path_str = " -> ".join(result.graph_path)
                proof["steps"].append(f"Found path: {path_str}")
            proof["verified"] = False
            
        elif result.source == "neural":
             proof["steps"].append(f"Neural Model prediction with confidence {result.confidence:.2f}")
             proof["verified"] = False
             
        return proof
