"""
Wrapper for gemini_agent.py to integrate with the chatbot API.
Provides async functions to call Gemini with conversation history and tool support.
"""

import sys
from pathlib import Path
from typing import AsyncGenerator, Dict, Any, List, Optional
import asyncio
from datetime import datetime

# Add parent directory to path to import gemini_agent
sys.path.insert(0, str(Path(__file__).parent.parent))

from google import genai
from google.genai import types

# Import functions from gemini_agent.py
from gemini_agent import (
    build_cli_function_declarations,
    build_cli_tools,
    build_system_prompt,
    execute_cli_function,
    find_function_call_parts,
    make_function_response_part,
    load_api_key,
    load_env_files,
)

from api.config import config


class GeminiAgent:
    """Wrapper for Gemini agent with session-based conversation management."""

    def __init__(self, model: str = None):
        """
        Initialize Gemini agent.

        Args:
            model: Gemini model to use (defaults to config.GEMINI_MODEL)
        """
        # Load environment variables
        load_env_files()

        # Initialize client
        api_key = load_api_key()
        self.client = genai.Client(api_key=api_key)
        self.model = model or config.GEMINI_MODEL

        # Build tools and system prompt
        self.tools = build_cli_tools()
        self.system_prompt = build_system_prompt()

    def get_initial_history(self) -> List[types.Content]:
        """
        Get initial conversation history with system prompt.

        Returns:
            List of Content objects with system prompt exchange
        """
        return [
            types.Content(
                role="user",
                parts=[types.Part(text=self.system_prompt)]
            ),
            types.Content(
                role="model",
                parts=[types.Part(text="I understand. I'm ready to help you with any task using my available functions. What can I do for you?")]
            ),
        ]

    async def generate_response(
        self,
        history: List[types.Content],
        user_message: str,
        max_iterations: int = 5
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Generate response with function calling loop.

        Args:
            history: Conversation history
            user_message: New user message
            max_iterations: Maximum function calling iterations

        Yields:
            Dict messages for client:
            - {"type": "function_call", "name": str, "args": dict}
            - {"type": "function_result", "name": str, "result": dict}
            - {"type": "text_chunk", "text": str}
            - {"type": "complete", "history": List[Content]}
        """
        # Add user message to history
        history.append(
            types.Content(role="user", parts=[types.Part(text=user_message)])
        )

        iteration = 0
        while iteration < max_iterations:
            iteration += 1

            # Call Gemini API
            config_obj = types.GenerateContentConfig(tools=self.tools)

            # Run in thread pool since genai.Client is sync
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.client.models.generate_content(
                    model=self.model,
                    contents=history,
                    config=config_obj,
                )
            )

            # Check for function calls
            function_calls = find_function_call_parts(response)

            if not function_calls:
                # No function calls, extract text and finish
                text = self._extract_text_from_response(response)
                if text:
                    yield {
                        "type": "text_chunk",
                        "text": text,
                        "timestamp": datetime.now().timestamp()
                    }

                # Add assistant response to history
                if response.candidates and response.candidates[0].content:
                    history.append(response.candidates[0].content)

                # Check for grounding metadata
                grounding_info = self._extract_grounding_info(response)
                if grounding_info:
                    yield {
                        "type": "grounding",
                        "sources": grounding_info,
                        "timestamp": datetime.now().timestamp()
                    }

                break

            # Execute function calls
            function_response_parts = []

            for func_name, func_args in function_calls:
                # Notify client about function call
                yield {
                    "type": "function_call",
                    "name": func_name,
                    "args": func_args,
                    "status": "executing",
                    "timestamp": datetime.now().timestamp()
                }

                # Execute function in thread pool (since it's sync subprocess)
                result = await loop.run_in_executor(
                    None,
                    lambda: execute_cli_function(func_name, func_args)
                )

                # Notify client about result
                yield {
                    "type": "function_result",
                    "name": func_name,
                    "success": result.get("ok", False),
                    "output": result.get("stdout", ""),
                    "error": result.get("stderr", ""),
                    "timestamp": datetime.now().timestamp()
                }

                # Create function response part for next iteration
                function_response_parts.append(
                    make_function_response_part(func_name, result)
                )

            # Add function call and responses to history
            if response.candidates and response.candidates[0].content:
                history.append(response.candidates[0].content)

            history.append(
                types.Content(role="user", parts=function_response_parts)
            )

        # Send completion message with updated history
        yield {
            "type": "complete",
            "history": history,
            "timestamp": datetime.now().timestamp()
        }

    def _extract_text_from_response(self, response) -> str:
        """Extract text from response parts."""
        try:
            parts = response.candidates[0].content.parts if response.candidates else []
        except Exception:
            return ""

        text_chunks = []
        for part in parts:
            if hasattr(part, "text") and part.text:
                text_chunks.append(part.text)

        return "\n".join(text_chunks) if text_chunks else ""

    def _extract_grounding_info(self, response) -> Optional[List[Dict[str, str]]]:
        """Extract grounding/source information if available."""
        try:
            meta = response.candidates[0].grounding_metadata
        except Exception:
            return None

        if not meta or not hasattr(meta, "grounding_chunks"):
            return None

        sources = []
        for chunk in meta.grounding_chunks:
            try:
                web = getattr(chunk, "web", None)
                if web:
                    uri = getattr(web, "uri", None)
                    title = getattr(web, "title", None)
                    if uri:
                        sources.append({
                            "title": title or "Untitled",
                            "url": uri
                        })
            except Exception:
                continue

        return sources if sources else None


# Global agent instance (lazy initialization)
_agent_instance: Optional[GeminiAgent] = None


def get_agent(model: str = None) -> GeminiAgent:
    """
    Get or create global Gemini agent instance.

    Args:
        model: Optional model override

    Returns:
        GeminiAgent instance
    """
    global _agent_instance
    if _agent_instance is None or (model and model != _agent_instance.model):
        _agent_instance = GeminiAgent(model=model)
    return _agent_instance
