"""Core council utilities: model querying, anonymization, chairman selection."""

import asyncio
import json
import os
import random
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from typing import Optional

import httpx

from backend.settings import get_settings, ModelConfig, ModelSettings


# --- CLI detection (no API key when using CLI) ---

def _find_cli(name: str) -> Optional[str]:
    """Find CLI executable; check .cmd on Windows."""
    if sys.platform == "win32":
        cmd_name = f"{name}.cmd"
        if shutil.which(cmd_name):
            return cmd_name
    return shutil.which(name)


CODEX_CLI = _find_cli("codex")
GEMINI_CLI = _find_cli("gemini")
CLAUDE_CLI = _find_cli("claude")


def _run_codex_cli_sync(prompt: str, timeout: int = 180) -> tuple[bool, str, str]:
    """Run Codex CLI synchronously. Returns (success, response_text, error)."""
    if not CODEX_CLI:
        return False, "", "codex CLI not found"
    cmd = [
        CODEX_CLI, "exec",
        "--full-auto",
        "--json",
        "--sandbox", "read-only",
        "--skip-git-repo-check",
        "--cd", os.getcwd(),
        prompt,
    ]
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=os.getcwd(),
        )
        response_text = ""
        for line in (result.stdout or "").strip().split("\n"):
            if not line:
                continue
            try:
                event = json.loads(line)
                if event.get("type") == "message" and event.get("role") == "assistant":
                    response_text = event.get("content", "")
                elif "message" in event:
                    response_text = event.get("message", "")
            except json.JSONDecodeError:
                response_text = line
        if not response_text and result.stdout:
            response_text = result.stdout.strip()
        if result.returncode == 0 and response_text:
            return True, response_text, ""
        return False, response_text, result.stderr or "Codex returned no response"
    except subprocess.TimeoutExpired:
        return False, "", f"Timeout after {timeout}s"
    except Exception as e:
        return False, "", str(e)


def _run_gemini_cli_sync(prompt: str, timeout: int = 180) -> tuple[bool, str, str]:
    """Run Gemini CLI synchronously. Returns (success, response_text, error)."""
    if not GEMINI_CLI:
        return False, "", "gemini CLI not found"
    cmd = [
        GEMINI_CLI,
        prompt,
        "--output-format", "json",
        "--approval-mode", "yolo",
    ]
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=os.getcwd(),
        )
        response_text = ""
        if result.stdout:
            try:
                data = json.loads(result.stdout)
                response_text = data.get("response", data.get("text", json.dumps(data)))
            except json.JSONDecodeError:
                response_text = result.stdout.strip()
        if result.returncode == 0 and response_text:
            return True, response_text, ""
        return False, response_text, result.stderr or "Gemini returned no response"
    except subprocess.TimeoutExpired:
        return False, "", f"Timeout after {timeout}s"
    except Exception as e:
        return False, "", str(e)


def _run_claude_cli_sync(prompt: str, timeout: int = 180) -> tuple[bool, str, str]:
    """Run Claude Code CLI synchronously. Returns (success, response_text, error)."""
    if not CLAUDE_CLI:
        return False, "", "claude CLI not found"
    cmd = [
        CLAUDE_CLI,
        "--print",
        "--dangerously-skip-permissions",
        prompt,
    ]
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=os.getcwd(),
        )
        response_text = (result.stdout or "").strip()
        if result.returncode == 0 and response_text:
            return True, response_text, ""
        return False, response_text, result.stderr or "Claude returned no response"
    except subprocess.TimeoutExpired:
        return False, "", f"Timeout after {timeout}s"
    except Exception as e:
        return False, "", str(e)


async def _run_codex_cli_async(prompt: str, timeout: int) -> tuple[bool, str, str]:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _run_codex_cli_sync, prompt, timeout)


async def _run_gemini_cli_async(prompt: str, timeout: int) -> tuple[bool, str, str]:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _run_gemini_cli_sync, prompt, timeout)


async def _run_claude_cli_async(prompt: str, timeout: int) -> tuple[bool, str, str]:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _run_claude_cli_sync, prompt, timeout)


@dataclass
class ModelResponse:
    model_name: str
    response: str
    latency_ms: float
    tokens_used: int = 0
    error: Optional[str] = None


ANONYMOUS_IDS = [
    "Response A", "Response B", "Response C",
    "Response D", "Response E", "Response F",
]

_chairman_index = 0


def anonymize_responses(
    responses: list[ModelResponse],
    prefix: str = "Response",
) -> tuple[dict[str, str], list[tuple[str, str]]]:
    """Anonymize responses. Returns (mapping, anonymized) where mapping is {anon_id: model_name}."""
    valid = [r for r in responses if not r.error]
    shuffled = list(valid)
    random.shuffle(shuffled)

    mapping: dict[str, str] = {}
    anonymized: list[tuple[str, str]] = []

    for i, resp in enumerate(shuffled):
        anon_id = f"{prefix} {chr(65 + i)}"
        mapping[anon_id] = resp.model_name
        anonymized.append((anon_id, resp.response))

    return mapping, anonymized


def select_chairman(models: list[ModelConfig]) -> ModelConfig:
    """Select chairman model based on strategy."""
    global _chairman_index
    settings = get_settings()
    strategy = settings.council.chairman_strategy

    if strategy == "fixed" and settings.council.chairman_fixed_model:
        for m in models:
            if m.name == settings.council.chairman_fixed_model:
                return m

    chairman = models[_chairman_index % len(models)]
    _chairman_index += 1
    return chairman


def get_enabled_models() -> list[ModelConfig]:
    return [m for m in get_settings().models if m.enabled]


async def query_model(
    model: ModelConfig,
    prompt: str,
    system_prompt: Optional[str] = None,
) -> ModelResponse:
    """Query a single model. Tries CLI first for openai/google/anthropic (no API key), then HTTP API."""
    settings = get_settings()
    ms = settings.model_settings
    timeout = ms.timeout_seconds
    start = time.time()
    full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt

    # Try CLI first for supported providers (no API key needed)
    if model.provider == "openai" and CODEX_CLI:
        success, response_text, err = await _run_codex_cli_async(full_prompt, timeout)
        if success:
            return ModelResponse(
                model_name=model.name,
                response=response_text,
                latency_ms=(time.time() - start) * 1000,
            )
        # CLI failed; fall through to HTTP API
    elif model.provider == "google" and GEMINI_CLI:
        success, response_text, err = await _run_gemini_cli_async(full_prompt, timeout)
        if success:
            return ModelResponse(
                model_name=model.name,
                response=response_text,
                latency_ms=(time.time() - start) * 1000,
            )
    elif model.provider == "anthropic" and CLAUDE_CLI:
        success, response_text, err = await _run_claude_cli_async(full_prompt, timeout)
        if success:
            return ModelResponse(
                model_name=model.name,
                response=response_text,
                latency_ms=(time.time() - start) * 1000,
            )

    # Fall back to HTTP API (requires API key)
    api_key = os.environ.get(model.api_key_env, "")
    if not api_key:
        return ModelResponse(
            model_name=model.name, response="", latency_ms=0,
            error=f"Missing API key: {model.api_key_env} (CLI not used or failed)",
        )

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            if model.provider == "openai" or model.provider == "minimax":
                text = await _call_openai(client, model, prompt, system_prompt, api_key, ms)
            elif model.provider == "google":
                text = await _call_google(client, model, prompt, system_prompt, api_key, ms)
            elif model.provider == "anthropic":
                text = await _call_anthropic(client, model, prompt, system_prompt, api_key, ms)
            elif model.provider == "deepseek":
                text = await _call_deepseek(client, model, prompt, system_prompt, api_key, ms)
            else:
                return ModelResponse(
                    model_name=model.name, response="", latency_ms=0,
                    error=f"Unknown provider: {model.provider}",
                )
            return ModelResponse(
                model_name=model.name,
                response=text,
                latency_ms=(time.time() - start) * 1000,
            )
    except Exception as e:
        return ModelResponse(
            model_name=model.name, response="",
            latency_ms=(time.time() - start) * 1000,
            error=str(e),
        )


async def parallel_query(
    models: list[ModelConfig],
    prompt: str,
    system_prompt: Optional[str] = None,
) -> list[ModelResponse]:
    """Query all models in parallel."""
    tasks = [query_model(m, prompt, system_prompt) for m in models]
    return list(await asyncio.gather(*tasks))


# --- Provider implementations ---

async def _call_openai(
    client: httpx.AsyncClient, model: ModelConfig,
    prompt: str, system_prompt: Optional[str],
    api_key: str, ms: ModelSettings,
) -> str:
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})
    resp = await client.post(
        model.endpoint,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={"model": model.model, "messages": messages,
              "max_tokens": ms.max_tokens, "temperature": ms.temperature},
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


async def _call_google(
    client: httpx.AsyncClient, model: ModelConfig,
    prompt: str, system_prompt: Optional[str],
    api_key: str, ms: ModelSettings,
) -> str:
    full = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
    resp = await client.post(
        f"{model.endpoint}?key={api_key}",
        headers={"Content-Type": "application/json"},
        json={
            "contents": [{"parts": [{"text": full}]}],
            "generationConfig": {"maxOutputTokens": ms.max_tokens, "temperature": ms.temperature},
        },
    )
    resp.raise_for_status()
    return resp.json()["candidates"][0]["content"]["parts"][0]["text"]


async def _call_anthropic(
    client: httpx.AsyncClient, model: ModelConfig,
    prompt: str, system_prompt: Optional[str],
    api_key: str, ms: ModelSettings,
) -> str:
    body: dict = {
        "model": model.model,
        "max_tokens": ms.max_tokens,
        "messages": [{"role": "user", "content": prompt}],
    }
    if system_prompt:
        body["system"] = system_prompt
    resp = await client.post(
        model.endpoint,
        headers={"x-api-key": api_key, "anthropic-version": "2023-06-01",
                 "Content-Type": "application/json"},
        json=body,
    )
    resp.raise_for_status()
    return resp.json()["content"][0]["text"]


async def _call_deepseek(
    client: httpx.AsyncClient, model: ModelConfig,
    prompt: str, system_prompt: Optional[str],
    api_key: str, ms: ModelSettings,
) -> str:
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})
    resp = await client.post(
        model.endpoint,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={"model": model.model, "messages": messages,
              "max_tokens": ms.max_tokens, "temperature": ms.temperature},
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]
