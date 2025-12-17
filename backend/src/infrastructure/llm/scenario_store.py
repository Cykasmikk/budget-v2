from typing import List, Dict, Any, Optional
import structlog
import chromadb
from chromadb.config import Settings
from src.application.ai.embedding_service import EmbeddingService

logger = structlog.get_logger()

class ScenarioStore:
    """
    RAG Store for Simulator Scenarios.
    Stores pairs of (scenario_description, simulator_action_json).
    Used for few-shot prompting and semantic caching.
    """
    def __init__(self, embedding_service: EmbeddingService, persist_path: str = "./chrome_db"):
        self.embedding_service = embedding_service
        # Use simple local persistence
        self.client = chromadb.PersistentClient(path=persist_path)
        
        self.collection = self.client.get_or_create_collection(
            name="scenario_examples",
            metadata={"hnsw:space": "cosine"}
        )
        logger.info("scenario_store_initialized", path=persist_path)

    def add_example(self, scenario_text: str, action_json: Dict[str, Any]):
        """
        Add a scenario example to the store.
        """
        vector = self.embedding_service.encode(scenario_text)
        # Chroma expects list of floats
        if hasattr(vector, "tolist"):
             vector = vector.tolist()
        
        # Ensure we store valid JSON string
        import json
        action_str = json.dumps(action_json)
             
        self.collection.add(
            embeddings=[vector],
            documents=[scenario_text],
            metadatas=[{"action": action_str}], 
            ids=[str(hash(scenario_text))]
        )
        
    def retrieve_similar(self, query: str, k: int = 3) -> List[Dict[str, Any]]:
        """
        Retrieve K most similar scenarios.
        Returns: List of {"scenario": str, "action": dict, "distance": float}
        """
        vector = self.embedding_service.encode(query)
        if hasattr(vector, "tolist"):
             vector = vector.tolist()
             
        results = self.collection.query(
            query_embeddings=[vector],
            n_results=k
        )
        
        output = []
        if not results['documents']:
            return []
            
        for i in range(len(results['documents'][0])):
            doc = results['documents'][0][i]
            meta = results['metadatas'][0][i]
            dist = results['distances'][0][i]
            
            # Retrieve Action and parse JSON
            action_str = meta.get("action")
            action_dict = {}
            if action_str:
                try:
                    action_dict = json.loads(action_str)
                except:
                    pass
                    
            output.append({
                "scenario": doc,
                "action": action_dict,
                "distance": dist
            })
            
        return output
