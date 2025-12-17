from typing import List, Optional
import structlog
import os
import json
from pydantic import BaseModel
from src.application.ai.simulator_ai import SimulatorAction, SimulatorAI

logger = structlog.get_logger()

class ScenarioPlan(BaseModel):
    actions: List[SimulatorAction]
    explanation: str

class ScenarioPlanner:
    """
    Agentic Planner that decomposes high-level goals into a sequence of SimulatorActions.
    Example: "Save $500 for vacation" -> [Reduce Dining Out by $200, Reduce Shopping by $300]
    """
    def __init__(self, simulator_ai: SimulatorAI, embedding_service = None):
        self.simulator = simulator_ai
        self.embedding_service = embedding_service
        self.model = simulator_ai.model 
        
    async def generate_plan(self, user_goal: str, context_entities: List[str] = None) -> Optional[ScenarioPlan]:
        """
        Decomposes the user goal into a list of actions and performs entity resolution.
        """
        if not self.model:
             return None
             
        # Cat 2.2: RAG - Inject available entities into prompt using Semantic Selection
        entity_context_str = ""
        if context_entities:
            top_entities = []
            # 1. Try Semantic Ranking (Top-K)
            try:
                if self.embedding_service:
                    goal_emb = self.embedding_service.encode(user_goal)
                    
                    # Limit candidates for performance (encode max 200) or assume cached?
                    # For this implementation, we'll encode up to 200 passed entities.
                    candidate_pool = context_entities[:200] 
                    if candidate_pool:
                        pool_embs = self.embedding_service.model.encode(candidate_pool)
                        
                        from sklearn.metrics.pairwise import cosine_similarity
                        import numpy as np
                        
                        g_vec = np.array(goal_emb).reshape(1, -1)
                        scores = cosine_similarity(g_vec, pool_embs)[0]
                        
                        # Get indices of top 50
                        top_k_indices = scores.argsort()[-50:][::-1]
                        top_entities = [candidate_pool[i] for i in top_k_indices]
            except Exception as e:
                logger.warning("rag_ranking_failed", error=str(e))
                top_entities = []

            # 2. Fallback to simple slice if RAG failed or Service missing
            if not top_entities:
                top_entities = context_entities[:50] 
                
            entity_context_str = f"Available Budget Entities (Use these exact names if possible): {', '.join(top_entities)}"
             
        prompt = f"""
        You are a financial planning agent.
        Break down the user's goal into a sequence of specific budget adjustments (actions).
        
        {entity_context_str}
        
        User Goal: "{user_goal}"
        
        Output a JSON object with this schema:
        {{
            "actions": [
                {{
                    "action": "reduce" | "increase" | "set",
                    "target": "Category Name" | "Merchant Name" | "Project Name",
                    "amount": float,
                    "unit": "percent" | "absolute",
                    "explanation": "Reason for this specific step",
                    "resolution_method": "ai_generated" | "exact" | "fuzzy" | "semantic",
                    "confidence": float (0.0 to 1.0)
                }}
            ],
            "explanation": "Overall strategy explanation"
        }}
        """
        
        try:
            import google.generativeai as genai
            
            response = await self.model.generate_content_async(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    response_mime_type="application/json"
                )
            )
            
            text = response.text
            if text.startswith("```json"):
                text = text.split("```json")[1].split("```")[0]
                
            data = json.loads(text.strip())
            plan = ScenarioPlan(**data)
            
            # Entity Resolution
            if context_entities and self.embedding_service:
                await self._resolve_targets(plan, context_entities)
                
            return plan
            
        except Exception as e:
            logger.error("plan_generation_failed", error=str(e))
            # Fallback
            single_action = await self.simulator.parse_scenario(user_goal)
            if single_action:
                plan = ScenarioPlan(actions=[single_action], explanation="Single step action parsed.")
                if context_entities and self.embedding_service:
                    await self._resolve_targets(plan, context_entities)
                return plan
            return None

    async def _resolve_targets(self, plan: ScenarioPlan, entities: List[str]):
        """
        Resolves action targets against available entities using EmbeddingService.
        """
        if not entities:
            return
            
        import difflib
        
        for action in plan.actions:
            target = action.target
            
            # Default metadata if not set
            if not getattr(action, "resolution_method", None):
                 action.resolution_method = "ai_generated"
                 action.confidence = 0.5
            
            # 1. Exact Match (Case Insensitive)
            exact_match = next((e for e in entities if e.lower() == target.lower()), None)
            if exact_match:
                action.target = exact_match
                action.resolution_method = "exact"
                action.confidence = 1.0
                continue
                
            # 2. Fuzzy Match (Difflib)
            matches = difflib.get_close_matches(target, entities, n=1, cutoff=0.7)
            if matches:
                action.target = matches[0]
                action.resolution_method = "fuzzy"
                # Calculate ratio for confidence
                ratio = difflib.SequenceMatcher(None, target, matches[0]).ratio()
                action.confidence = round(ratio, 2)
                continue
                
            # 3. Semantic Match (Embeddings)
            try:
                if self.embedding_service:
                    target_emb = self.embedding_service.encode(target)
                    
                    best_match = None
                    best_score = -1.0
                    
                    if len(entities) < 200:
                        candidate_embs = self.embedding_service.model.encode(entities)
                        
                        from sklearn.metrics.pairwise import cosine_similarity
                        import numpy as np
                        
                        t_vec = np.array(target_emb).reshape(1, -1)
                        scores = cosine_similarity(t_vec, candidate_embs)[0]
                        max_idx = np.argmax(scores)
                        best_score = scores[max_idx]
                        
                        if best_score > 0.6: 
                            best_match = entities[max_idx]
                    
                    if best_match:
                         logger.info("entity_resolved_semantic", target=target, resolved=best_match, score=float(best_score))
                         action.target = best_match
                         action.resolution_method = "semantic"
                         action.confidence = round(float(best_score), 2)
                         continue

            except Exception as e:
                logger.warning("semantic_resolution_failed", error=str(e))

            # 4. Acronym Fallback (Manual Heuristic)
            acronyms = {
                "gcp": "Google Cloud Platform",
                "aws": "Amazon Web Services",
                "azure": "Microsoft Azure",
                "ocean": "DigitalOcean"
            }
            if target.lower() in acronyms:
                expansion = acronyms[target.lower()]
                
                # 1. Try Exact Match First (Normalized entity should match expansion)
                exact_expansion_match = next((e for e in entities if e.lower() == expansion.lower()), None)
                
                if exact_expansion_match:
                    action.target = exact_expansion_match
                    action.resolution_method = "acronym_exact"
                    action.confidence = 1.0
                else:
                    # 2. Fallback to Substring Match
                    match = next((e for e in entities if expansion.lower() in e.lower()), None)
                    if match:
                        action.target = match
                        action.resolution_method = "acronym_substring"
                        action.confidence = 0.9

            # 6. Validation Layer
            # Verify if the final target actually exists in the provided entities
            # We do a case-insensitive check against the entities list
            is_valid = any(e.lower() == action.target.lower() for e in entities)
            if not is_valid:
                logger.warning("entity_validation_failed", target=action.target, method=action.resolution_method)
                # Penalize confidence if we couldn't verify it against the DB
                current_conf = action.confidence if action.confidence is not None else 0.5
                action.confidence = round(current_conf * 0.5, 2)
            else:
                # Slight boost if verified and not already 1.0
                if action.confidence is None: action.confidence = 0.8
                elif action.confidence < 1.0: action.confidence = min(1.0, action.confidence + 0.1)
