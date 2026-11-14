import json
import logging
import re
from typing import Dict, Any, List, Optional, Tuple
import httpx
from app.core.config import settings

logger = logging.getLogger(__name__)

# Preferred models in priority order
MODEL_PRIORITIES = ["qwen2.5-coder:7b", "llama3:latest", "llama3.2:3b"]


class OllamaClient:
    def __init__(self, base_url: Optional[str] = None):
        self.base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self._active_model: Optional[str] = None

    async def get_best_available_model(self) -> str:
        """
        Discovers models installed on the local Ollama instance and selects the best one.
        """
        if self._active_model:
            return self._active_model

        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                res = await client.get(f"{self.base_url}/api/tags")
                if res.status_code == 200:
                    data = res.json()
                    installed = [m.get("name") for m in data.get("models", [])]
                    for preferred in MODEL_PRIORITIES:
                        for m in installed:
                            if m == preferred or m.startswith(preferred.split(":")[0]):
                                self._active_model = m
                                logger.info("Selected Ollama model: %s", self._active_model)
                                return self._active_model

                    if installed:
                        self._active_model = installed[0]
                        return self._active_model
        except Exception as e:
            logger.warning("Could not reach Ollama at %s: %s", self.base_url, str(e))

        # Default fallback preference
        self._active_model = settings.LLM_INSTRUCTION_MODEL or "llama3.2:3b"
        return self._active_model

    async def generate_structured_json(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        timeout: float = 30.0,
        retries: int = 2
    ) -> Tuple[Optional[Dict[str, Any]], str, bool]:
        """
        Executes an inference call expecting structured JSON.
        Returns: (parsed_json_dict_or_none, model_used, is_fallback)
        """
        model = await self.get_best_available_model()

        payload = {
            "model": model,
            "prompt": prompt,
            "format": "json",
            "stream": False,
            "options": {
                "temperature": 0.1,
                "top_p": 0.9,
            }
        }
        if system_prompt:
            payload["system"] = system_prompt

        for attempt in range(1, retries + 2):
            try:
                async with httpx.AsyncClient(timeout=timeout) as client:
                    response = await client.post(f"{self.base_url}/api/generate", json=payload)
                    if response.status_code == 200:
                        raw_data = response.json()
                        raw_text = raw_data.get("response", "").strip()
                        
                        # Strip markdown fences if present
                        if raw_text.startswith("```"):
                            raw_text = re.sub(r"^```(?:json)?\n?", "", raw_text)
                            raw_text = re.sub(r"\n?```$", "", raw_text)

                        parsed = json.loads(raw_text)
                        return (parsed, model, False)
                    else:
                        logger.warning(
                            "Ollama returned HTTP %d on attempt %d: %s",
                            response.status_code, attempt, response.text
                        )
            except Exception as e:
                logger.warning("Ollama call failed on attempt %d: %s", attempt, str(e))

        logger.error("All Ollama inference attempts failed. Switching to deterministic fallback.")
        return (None, "deterministic_fallback", True)

    async def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        timeout: float = 30.0,
        retries: int = 1
    ) -> Tuple[str, str, bool]:
        """
        Executes an inference call for natural text generation (e.g., mentor chat, explanations).
        Returns: (response_text, model_used, is_fallback)
        """
        model = await self.get_best_available_model()

        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.4,
                "top_p": 0.9,
            }
        }
        if system_prompt:
            payload["system"] = system_prompt

        for attempt in range(1, retries + 2):
            try:
                async with httpx.AsyncClient(timeout=timeout) as client:
                    response = await client.post(f"{self.base_url}/api/generate", json=payload)
                    if response.status_code == 200:
                        raw_data = response.json()
                        text = raw_data.get("response", "").strip()
                        if text:
                            return (text, model, False)
            except Exception as e:
                logger.warning("Ollama text generation failed on attempt %d: %s", attempt, str(e))

        return ("", "deterministic_fallback", True)


ollama_client = OllamaClient()
