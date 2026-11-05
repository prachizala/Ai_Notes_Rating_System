"""
Provider-Agnostic LLM Client for NoteIQ.
Supports Gemini (Google GenAI), OpenAI, Anthropic, and Fake provider for tests.
"""

import json
import time
from typing import Any, Dict, List, Optional
import httpx

from app.core.config import settings
from app.core.logging import logger


class LLMError(Exception):
    pass


class BaseLLMAdapter:
    def generate_json(self, system: str, user: str, schema: Optional[Dict[str, Any]] = None, model: Optional[str] = None) -> Dict[str, Any]:
        raise NotImplementedError

    def generate_text(self, system: str, messages: List[Dict[str, Any]], tools: Optional[List[Dict[str, Any]]] = None, model: Optional[str] = None) -> Dict[str, Any]:
        raise NotImplementedError


class GeminiAdapter(BaseLLMAdapter):
    """Google Gemini Adapter using REST / google-genai SDK."""
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"

    def generate_json(self, system: str, user: str, schema: Optional[Dict[str, Any]] = None, model: Optional[str] = None) -> Dict[str, Any]:
        target_model = model or settings.LLM_MODEL_ANALYSIS or "gemini-2.5-flash"
        url = f"{self.base_url}/models/{target_model}:generateContent?key={self.api_key}"
        
        payload: Dict[str, Any] = {
            "system_instruction": {"parts": [{"text": system}]},
            "contents": [{"role": "user", "parts": [{"text": user}]}],
            "generationConfig": {
                "temperature": 0.1,
                "responseMimeType": "application/json",
            }
        }
        if schema:
            payload["generationConfig"]["responseSchema"] = schema

        for attempt in range(2):
            start = time.time()
            try:
                with httpx.Client(timeout=60.0) as client:
                    resp = client.post(url, json=payload)
                    resp.raise_for_status()
                    data = resp.json()
                    
                    text_content = data["candidates"][0]["content"]["parts"][0]["text"]
                    parsed = json.loads(text_content)
                    latency = round(time.time() - start, 2)
                    logger.info(f"Gemini generate_json completed in {latency}s on model {target_model}")
                    return parsed
            except Exception as e:
                logger.warning(f"Gemini generate_json attempt {attempt + 1} failed: {e}")
                if attempt == 1:
                    raise LLMError(f"Gemini generate_json failed after retry: {e}")
        raise LLMError("Gemini generate_json failed.")

    def generate_text(self, system: str, messages: List[Dict[str, Any]], tools: Optional[List[Dict[str, Any]]] = None, model: Optional[str] = None) -> Dict[str, Any]:
        target_model = model or settings.LLM_MODEL_CHAT or "gemini-2.5-flash"
        url = f"{self.base_url}/models/{target_model}:generateContent?key={self.api_key}"

        contents = []
        for m in messages:
            role = "user" if m.get("role") == "user" else "model"
            contents.append({"role": role, "parts": [{"text": m.get("content", "")}]})

        payload: Dict[str, Any] = {
            "system_instruction": {"parts": [{"text": system}]},
            "contents": contents,
            "generationConfig": {"temperature": 0.2},
        }

        with httpx.Client(timeout=60.0) as client:
            resp = client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            text = data["candidates"][0]["content"]["parts"][0]["text"]
            return {"content": text, "tool_calls": []}


class OpenAIAdapter(BaseLLMAdapter):
    """OpenAI Adapter."""
    def __init__(self, api_key: str):
        self.api_key = api_key

    def generate_json(self, system: str, user: str, schema: Optional[Dict[str, Any]] = None, model: Optional[str] = None) -> Dict[str, Any]:
        target_model = model or settings.LLM_MODEL_ANALYSIS or "gpt-4o-mini"
        url = "https://api.openai.com/v1/chat/completions"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        payload = {
            "model": target_model,
            "temperature": 0.1,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }
        for attempt in range(2):
            try:
                with httpx.Client(timeout=60.0) as client:
                    resp = client.post(url, headers=headers, json=payload)
                    resp.raise_for_status()
                    content = resp.json()["choices"][0]["message"]["content"]
                    return json.loads(content)
            except Exception as e:
                if attempt == 1:
                    raise LLMError(f"OpenAI generate_json failed: {e}")
        raise LLMError("OpenAI call failed.")

    def generate_text(self, system: str, messages: List[Dict[str, Any]], tools: Optional[List[Dict[str, Any]]] = None, model: Optional[str] = None) -> Dict[str, Any]:
        target_model = model or settings.LLM_MODEL_CHAT or "gpt-4o-mini"
        url = "https://api.openai.com/v1/chat/completions"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        chat_msgs = [{"role": "system", "content": system}] + messages
        payload = {"model": target_model, "temperature": 0.2, "messages": chat_msgs}
        with httpx.Client(timeout=60.0) as client:
            resp = client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            text = resp.json()["choices"][0]["message"]["content"]
            return {"content": text, "tool_calls": []}


class AnthropicAdapter(BaseLLMAdapter):
    """Anthropic Claude Adapter."""
    def __init__(self, api_key: str):
        self.api_key = api_key

    def generate_json(self, system: str, user: str, schema: Optional[Dict[str, Any]] = None, model: Optional[str] = None) -> Dict[str, Any]:
        target_model = model or settings.LLM_MODEL_ANALYSIS or "claude-3-5-haiku-latest"
        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        prompt = f"{user}\n\nRespond ONLY with valid JSON."
        payload = {
            "model": target_model,
            "max_tokens": 4096,
            "system": system,
            "messages": [{"role": "user", "content": prompt}],
        }
        for attempt in range(2):
            try:
                with httpx.Client(timeout=60.0) as client:
                    resp = client.post(url, headers=headers, json=payload)
                    resp.raise_for_status()
                    content = resp.json()["content"][0]["text"]
                    # Extract JSON block if wrapped
                    if "```json" in content:
                        content = content.split("```json")[1].split("```")[0].strip()
                    elif "```" in content:
                        content = content.split("```")[1].split("```")[0].strip()
                    return json.loads(content)
            except Exception as e:
                if attempt == 1:
                    raise LLMError(f"Anthropic generate_json failed: {e}")
        raise LLMError("Anthropic call failed.")

    def generate_text(self, system: str, messages: List[Dict[str, Any]], tools: Optional[List[Dict[str, Any]]] = None, model: Optional[str] = None) -> Dict[str, Any]:
        target_model = model or settings.LLM_MODEL_CHAT or "claude-3-5-haiku-latest"
        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        payload = {
            "model": target_model,
            "max_tokens": 2048,
            "system": system,
            "messages": messages,
        }
        with httpx.Client(timeout=60.0) as client:
            resp = client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            text = resp.json()["content"][0]["text"]
            return {"content": text, "tool_calls": []}


class FakeLLMAdapter(BaseLLMAdapter):
    """Deterministic Mock Adapter for CI and local unit tests."""
    def generate_json(self, system: str, user: str, schema: Optional[Dict[str, Any]] = None, model: Optional[str] = None) -> Dict[str, Any]:
        # Return realistic evaluation output matching Phase 6 schema
        return {
            "scores": {
                "accuracy": {"score": 4.5, "justification": "Statements and formulas are scientifically accurate.", "evidence": ["Page 1"]},
                "explanation": {"score": 4.0, "justification": "Clear terminology and logical flow.", "evidence": ["Page 1"]},
                "depth": {"score": 4.0, "justification": "Covers fundamental principles at undergraduate semester level.", "evidence": ["Page 1"]},
                "examples": {"score": 3.5, "justification": "Good illustrative code examples included.", "evidence": ["Page 1"]},
            },
            "topics_identified": [
                {"name": "Pointer Fundamentals", "note": "Detailed explanation of memory addresses."},
                {"name": "Dynamic Memory Allocation", "note": "Covers malloc, free, and pointer arithmetic."},
            ],
            "strengths": [
                "Clear memory diagram illustrations",
                "Concise code snippets demonstrating pointer dereferencing",
            ],
            "improvements": [
                "Could include more edge cases regarding dangling pointers",
            ],
            "missing_concepts": [
                "Double pointers and function pointers",
            ],
            "errors_found": [],
            "syllabus_coverage": None,
            "confidence": "high",
            "confidence_reason": "Clear and readable digital text extracted directly from slides.",
            "summary": "High-quality undergraduate reference notes explaining pointer fundamentals and dynamic memory allocation with clean syntax.",
        }

    def generate_text(self, system: str, messages: List[Dict[str, Any]], tools: Optional[List[Dict[str, Any]]] = None, model: Optional[str] = None) -> Dict[str, Any]:
        last_message = messages[-1]["content"] if messages else ""
        return {
            "content": f"Based on the uploaded course notes: {last_message}. Please refer to the cited notes.",
            "tool_calls": [],
        }


def get_llm_client() -> BaseLLMAdapter:
    provider = settings.LLM_PROVIDER.lower()
    if provider == "fake" or settings.ENVIRONMENT == "test" or not settings.LLM_API_KEY:
        return FakeLLMAdapter()
    if provider == "gemini":
        return GeminiAdapter(api_key=settings.LLM_API_KEY)
    elif provider == "openai":
        return OpenAIAdapter(api_key=settings.LLM_API_KEY)
    elif provider == "anthropic":
        return AnthropicAdapter(api_key=settings.LLM_API_KEY)
    return FakeLLMAdapter()
