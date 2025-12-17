import os
import google.generativeai as genai
import structlog
from typing import AsyncIterator, List, Dict
from src.application.ports import LLMProvider
import asyncio

logger = structlog.get_logger()

class GeminiAdapter(LLMProvider):
    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("GEMINI_API_KEY is required")
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-3-pro-preview')
        logger.info("gemini_adapter_initialized", model="gemini-3-pro-preview")

    def _build_prompt(self, prompt: str, context: str, conversation_history: List[Dict[str, str]] = []) -> str:
        """Build the full prompt with context and conversation history."""
        history_section = ""
        if conversation_history and len(conversation_history) > 0:
            # Format conversation history
            history_lines = []
            for msg in conversation_history[-10:]:  # Limit to last 10 messages to manage tokens
                role = msg.get('role', 'user')
                content = msg.get('content', '')
                if role == 'user':
                    history_lines.append(f"User: {content}")
                elif role == 'assistant':
                    history_lines.append(f"Assistant: {content}")
            if history_lines:
                history_section = f"\n\nPREVIOUS CONVERSATION:\n" + "\n".join(history_lines) + "\n"
        
        return f"""
            You are a helpful financial assistant for a budget dashboard.
            
            CONTEXT DATA:
            {context}
            {history_section}
            CURRENT USER QUESTION:
            {prompt}
            
            Instructions:
            - Answer the user's question based strictly on the provided context data.
            - Use the conversation history to understand references like "that project", "it", "the previous expense", etc.
            - Be concise and professional.
            - Format currency as $X,XXX.XX.
            - If the answer is not in the context, say so.
            """

    async def generate_response(self, prompt: str, context: str, conversation_history: List[Dict[str, str]] = []) -> str:
        try:
            full_prompt = self._build_prompt(prompt, context, conversation_history)
            
            # Run in executor because google-generativeai is synchronous (mostly)
            import asyncio
            loop = asyncio.get_running_loop()
            
            response = await loop.run_in_executor(None, self.model.generate_content, full_prompt)
            
            try:
                text = response.text
                logger.info("gemini_response_generated", length=len(text))
                return text
            except ValueError:
                # Occurs if response was blocked by safety filters
                logger.warning("gemini_response_blocked", feedback=str(response.prompt_feedback))
                return "I'm sorry, I cannot answer that due to safety guidelines."
            
        except Exception as e:
            logger.error("gemini_generation_failed", error=str(e))
            return "I encountered an error connecting to the AI service. Please try again later."

    async def generate_response_stream(self, prompt: str, context: str, conversation_history: List[Dict[str, str]] = []) -> AsyncIterator[str]:
        """
        Generate a streaming response, yielding tokens as they are generated.
        Uses a queue to bridge the synchronous iterator to async generator.
        """
        try:
            full_prompt = self._build_prompt(prompt, context, conversation_history)
            loop = asyncio.get_running_loop()
            queue = asyncio.Queue()
            done = asyncio.Event()
            
            def iterate_stream():
                """Run the synchronous stream iteration in a thread."""
                try:
                    response_stream = self.model.generate_content(full_prompt, stream=True)
                    for chunk in response_stream:
                        if chunk.text:
                            # Put chunks in queue (blocking call, but in thread)
                            asyncio.run_coroutine_threadsafe(
                                queue.put(chunk.text), loop
                            )
                except Exception as e:
                    logger.error("gemini_stream_iteration_failed", error=str(e))
                    asyncio.run_coroutine_threadsafe(
                        queue.put("I encountered an error connecting to the AI service. Please try again later."),
                        loop
                    )
                finally:
                    # Signal completion (set() is synchronous, not a coroutine)
                    loop.call_soon_threadsafe(done.set)
            
            # Start the stream iteration in a thread
            loop.run_in_executor(None, iterate_stream)
            
            # Yield chunks from the queue until done
            while not done.is_set() or not queue.empty():
                try:
                    # Wait for either a chunk or completion, with timeout
                    chunk = await asyncio.wait_for(queue.get(), timeout=0.1)
                    yield chunk
                except asyncio.TimeoutError:
                    # Check if we're done
                    if done.is_set() and queue.empty():
                        break
                    continue
                    
        except Exception as e:
            logger.error("gemini_streaming_failed", error=str(e))
            yield "I encountered an error connecting to the AI service. Please try again later."
