"""pigeon_compiler.integrations.deepseek_adapter — DeepSeek API client.

Standalone adapter for the Pigeon Code Compiler.
Requires DEEPSEEK_API_KEY environment variable.

DeepSeek Pricing (per 1M tokens):
  deepseek-chat:     $0.14 input / $0.28 output (cache: $0.014)
  deepseek-reasoner: $0.55 input / $2.19 output
"""

# ── pigeon ────────────────────────────────────
# SEQ: 001 | VER: v006 | 135 lines | ~1,180 tokens
# DESC:   deepseek_api_client
# INTENT: stage_78_hook
# LAST:   2026-03-22 @ 276af14
# SESSIONS: 2
# ──────────────────────────────────────────────
import os
import time
import logging
import httpx

logger = logging.getLogger(__name__)

DEEPSEEK_API_URL = "https://api.deepseek.com/chat/completions"
DEEPSEEK_TIMEOUT = httpx.Timeout(connect=10.0, read=300.0, write=30.0, pool=10.0)
DEEPSEEK_MAX_RETRIES = 3
DEEPSEEK_RETRY_DELAY = 1.5


def deepseek_query(
    prompt: str,
    model: str = "deepseek-chat",
    system: str = None,
    temperature: float = 0.0,
    max_tokens: int = 1500,
    messages: list = None,
) -> dict:
    """Query DeepSeek with automatic retry.

    Returns: {content, citations, tool_calls, cost, tokens, finish_reason, truncated}
    """
    api_key = os.getenv("DEEPSEEK_API_KEY", "")
    if not api_key:
        raise ValueError("DEEPSEEK_API_KEY not set — add it to your .env or environment")

    if messages is None:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": False,
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    PRICING = {
        "deepseek-chat": {"input": 0.14, "output": 0.28},
        "deepseek-reasoner": {"input": 0.55, "output": 2.19},
    }

    last_error = None
    for attempt in range(1, DEEPSEEK_MAX_RETRIES + 1):
        t0 = time.time()
        try:
            response = httpx.post(
                DEEPSEEK_API_URL,
                headers=headers,
                json=payload,
                timeout=DEEPSEEK_TIMEOUT,
            )
            elapsed = time.time() - t0

            if 400 <= response.status_code < 500:
                logger.error(f"[DeepSeek] Client error {response.status_code}: {response.text[:200]}")
                response.raise_for_status()

            if response.status_code >= 500:
                logger.warning(f"[DeepSeek] Server error {response.status_code} (attempt {attempt}/{DEEPSEEK_MAX_RETRIES})")
                last_error = Exception(f"Server error {response.status_code}")
                if attempt < DEEPSEEK_MAX_RETRIES:
                    time.sleep(DEEPSEEK_RETRY_DELAY * attempt)
                    continue
                response.raise_for_status()

            data = response.json()
            choice = data.get("choices", [{}])[0]
            text = choice.get("message", {}).get("content", "")
            finish_reason = choice.get("finish_reason", "stop")
            usage = data.get("usage", {})

            prices = PRICING.get(model, PRICING["deepseek-chat"])
            cost = (
                usage.get("prompt_tokens", 0) * prices["input"]
                + usage.get("completion_tokens", 0) * prices["output"]
            ) / 1_000_000

            was_truncated = finish_reason == "length"
            if was_truncated:
                logger.warning(f"[DeepSeek] TRUNCATED — max_tokens={max_tokens} insufficient")

            return {
                "content": text,
                "citations": [],
                "tool_calls": 0,
                "cost": round(cost, 6),
                "finish_reason": finish_reason,
                "truncated": was_truncated,
                "tokens": {
                    "input": usage.get("prompt_tokens", 0),
                    "output": usage.get("completion_tokens", 0),
                    "total": usage.get("total_tokens", 0),
                },
            }

        except (httpx.TimeoutException, httpx.ConnectError) as e:
            elapsed = time.time() - t0
            last_error = e
            logger.warning(f"[DeepSeek] {type(e).__name__} attempt {attempt}/{DEEPSEEK_MAX_RETRIES} ({elapsed:.1f}s)")
            if attempt < DEEPSEEK_MAX_RETRIES:
                time.sleep(DEEPSEEK_RETRY_DELAY * attempt)
                continue
            raise type(e)(f"DeepSeek failed after {DEEPSEEK_MAX_RETRIES} attempts: {e}") from e

    if last_error:
        raise last_error
    raise RuntimeError("DeepSeek query failed unexpectedly")
