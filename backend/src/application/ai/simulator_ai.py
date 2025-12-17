from typing import Optional, Literal, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
import structlog
import os
import json
from src.infrastructure.llm.scenario_store import ScenarioStore

logger = structlog.get_logger()

# Try to import google.generativeai, but handle if not installed (though it should be)
try:
    import google.generativeai as genai
except ImportError:
    logger.error("google_genai_missing")
    genai = None

class SimulatorAction(BaseModel):
    """
    Structured output from the LLM representing a simulation action.
    """
    model_config = ConfigDict(strict=True)
    
    action: Literal["reduce", "increase", "set"] = Field(..., description="The type of modification")
    target: str = Field(..., description="The category, project, or entity to modify")
    amount: float = Field(..., description="The numeric value of the modification")
    unit: Literal["percent", "absolute"] = Field(..., description="The unit of the amount")
    explanation: str = Field(..., description="Reasoning for the action")


class SimulatorAI:
    """
    LLM-based parser for Simulator scenarios using Google Gemini.
    """
    
    def __init__(self, api_key: Optional[str] = None, scenario_store: Optional[ScenarioStore] = None):
        self.scenario_store = scenario_store
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            logger.warning("google_api_key_missing", component="SimulatorAI")
            self.model = None
            return

        if genai:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-3-pro-preview') # Use experimental flash for 2025
        else:
            self.model = None

    async def parse_scenario(self, prompt_text: str) -> Optional[SimulatorAction]:
        """
        Parses a natural language scenario into a structured action.
        """
        # 0. Check Semantic Cache & Retrieve Examples (RAG)
        examples_context = ""
        if self.scenario_store:
            matches = self.scenario_store.retrieve_similar(prompt_text, k=3)
            if matches:
                best = matches[0]
                # Semantic Cache Hit
                if best['distance'] < 0.1: 
                    try:
                        # matches return parsed dict in 'action' due to ScenarioStore update
                        action_data = best.get('action') 
                        if action_data:
                            logger.info("simulator_cache_hit", scenario=prompt_text)
                            return SimulatorAction(**action_data)
                    except Exception as e:
                        logger.warning("simulator_cache_parse_failed", error=str(e))
                
                # Build Few-Shot Context
                examples_context = "Similar Examples:\n"
                for m in matches:
                    examples_context += f"- Input: \"{m['scenario']}\"\n  Output: {json.dumps(m['action'])}\n"

        if not self.model:
            logger.warning("simulator_ai_disabled_no_model")
            return None

        prompt = f"""
        You are a financial assistant. Parse the following scenario into a JSON action.
        
        {examples_context}

        Scenario: "{prompt_text}"
        
        Output Schema (JSON only):
        {{
            "action": "reduce" | "increase" | "set",
            "target": "Category Name",
            "amount": float,
            "unit": "percent" | "absolute",
            "explanation": "Brief reason"
        }}
        
        Example: "Cut eating out by 50%" -> {{"action": "reduce", "target": "Eating Out", "amount": 50.0, "unit": "percent", "explanation": "Targeted reduction."}}
        """

        try:
            # 1. Define Schema using Pydantic
            # The latest google-generativeai SDK supports response_schema directly.
            
            # 2. Call Gemini with Structured Output Config
            response = await self.model.generate_content_async(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    response_mime_type="application/json",
                    response_schema=SimulatorAction
                )
            )
            
            # 3. Parse Response
            # The SDK ensures JSON valid against schema, so simply load and parse.
            text = response.text
            # Clean generic markdown if any (though mime_type json should avoid it)
            if text.startswith("```json"):
                text = text.split("```json")[1].split("```")[0]
                
            data = json.loads(text.strip())
            action = SimulatorAction(**data)
            
            # 4. Save to Cache (Async or fire-and-forget?)
            # Valid action produced -> store it for future
            if self.scenario_store:
                 try:
                     self.scenario_store.add_example(prompt_text, action.model_dump())
                 except Exception as e:
                     logger.warning("scenario_cache_write_failed", error=str(e))
                     
            return action
            
        except Exception as e:
            logger.error("simulator_parsing_failed", error=str(e), prompt=prompt_text)
            return None
