"""
local_llm.py — Libra's local language model client.

REPLACES the Anthropic API integration. All inference happens on the user's
machine via Ollama. No data leaves the local machine.

ARCHITECTURE:
    User → Streamlit UI → local_llm.generate() → HTTP localhost:11434 → Ollama → Model

PRIVACY GUARANTEES:
    - All network calls go to 127.0.0.1 (localhost) only
    - No telemetry, no usage logging to external servers
    - Connection is refused if Ollama is not running locally
    - Module raises an explicit error if asked to call any non-localhost endpoint

USAGE:
    from local_llm import generate, generate_json, is_available

    if not is_available():
        st.error("Ollama is not running. Start it with: ollama serve")
        st.stop()

    response = generate(
        prompt="Summarise the following clause in 50 words: ...",
        system="You are a legal-tech assistant.",
        max_tokens=512,
    )
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass
from typing import Any, Optional
from urllib.parse import urlparse

import requests

# ════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ════════════════════════════════════════════════════════════════════════════

# Ollama default endpoint. Hardcoded to localhost — see SECURITY note below.
OLLAMA_HOST = "http://127.0.0.1:11434"

# Default model. Change here if hardware constraints require a smaller model.
DEFAULT_MODEL = "mistral:7b-instruct"

# Fallback model for low-RAM machines. Set USE_FALLBACK_MODEL=True in app config.
FALLBACK_MODEL = "phi3:mini"

# Generation defaults — calibrated for legal-text phrasing.
DEFAULT_TEMPERATURE = 0.2  # Low; we want consistent, conservative phrasing
DEFAULT_TOP_P = 0.9
DEFAULT_MAX_TOKENS = 1024

# ── Timeout policy ────────────────────────────────────────────────────────────
# Responses are streamed, so the meaningful limit is "how long with NO output"
# (a stall), not "how long in total". But there are two distinct phases:
#
#   1. PREFILL  — the model ingests the prompt and emits nothing at all. On CPU
#                 with a large prompt this can legitimately take minutes. A short
#                 timeout here kills healthy calls (this was the Drafter bug).
#   2. STREAMING— tokens flow steadily. Once they do, a long silence genuinely
#                 does mean something is stuck.
#
# So we wait generously for the FIRST token, then strictly between subsequent
# ones. A working model is never killed for being slow; a frozen one still is.
CONNECT_TIMEOUT_SECONDS     = 15    # time allowed to establish the connection
FIRST_TOKEN_TIMEOUT_SECONDS = 420   # max wait for the first token (prefill)
STALL_TIMEOUT_SECONDS       = 90    # max silence *between* tokens once flowing
HARD_CEILING_SECONDS        = 1200  # absolute backstop (20 min) — runaway guard

# Retained for backwards compatibility with existing references/messages.
GENERATION_TIMEOUT_SECONDS = HARD_CEILING_SECONDS

logger = logging.getLogger(__name__)


# ════════════════════════════════════════════════════════════════════════════
# SECURITY: enforce localhost-only
# ════════════════════════════════════════════════════════════════════════════

def _assert_localhost(url: str) -> None:
    """
    Raise immediately if the URL is not pointing at localhost.

    This is a defence-in-depth check. If a configuration mistake or malicious
    edit ever points OLLAMA_HOST at a remote server, this function blocks the
    call before any data is transmitted.
    """
    parsed = urlparse(url)
    host = parsed.hostname or ""
    if host not in ("127.0.0.1", "localhost", "::1"):
        raise RuntimeError(
            f"SECURITY: Libra refused to contact non-localhost endpoint: {host}. "
            f"This module is restricted to local-only inference. If you see this "
            f"error, your configuration has been tampered with."
        )


_assert_localhost(OLLAMA_HOST)


# ════════════════════════════════════════════════════════════════════════════
# AVAILABILITY CHECK
# ════════════════════════════════════════════════════════════════════════════

@dataclass
class OllamaStatus:
    available: bool
    error: Optional[str]
    models_installed: list[str]
    default_model_installed: bool


def check_status(model: str = DEFAULT_MODEL) -> OllamaStatus:
    """
    Check whether Ollama is running and the required model is installed.

    Call this at app startup and gate the UI on the result.
    """
    _assert_localhost(OLLAMA_HOST)

    try:
        response = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=5)
        response.raise_for_status()
    except requests.exceptions.ConnectionError:
        return OllamaStatus(
            available=False,
            error=(
                "Cannot connect to Ollama. Ensure Ollama is installed and "
                "running. On macOS/Linux, run: ollama serve. On Windows, "
                "Ollama runs automatically in the background — check the "
                "system tray."
            ),
            models_installed=[],
            default_model_installed=False,
        )
    except requests.exceptions.Timeout:
        return OllamaStatus(
            available=False,
            error="Ollama did not respond within 5 seconds.",
            models_installed=[],
            default_model_installed=False,
        )
    except requests.exceptions.HTTPError as e:
        return OllamaStatus(
            available=False,
            error=f"Ollama returned an HTTP error: {e}",
            models_installed=[],
            default_model_installed=False,
        )

    try:
        data = response.json()
    except ValueError:
        return OllamaStatus(
            available=False,
            error="Ollama returned invalid JSON.",
            models_installed=[],
            default_model_installed=False,
        )

    installed = [m.get("name", "") for m in data.get("models", [])]
    default_present = any(m.startswith(model) for m in installed)

    return OllamaStatus(
        available=True,
        error=None,
        models_installed=installed,
        default_model_installed=default_present,
    )


def is_available(model: str = DEFAULT_MODEL) -> bool:
    """Quick boolean check. Use check_status() for diagnostics."""
    status = check_status(model)
    return status.available and status.default_model_installed


# ════════════════════════════════════════════════════════════════════════════
# CORE GENERATION
# ════════════════════════════════════════════════════════════════════════════

def generate(
    prompt: str,
    system: Optional[str] = None,
    model: str = DEFAULT_MODEL,
    temperature: float = DEFAULT_TEMPERATURE,
    top_p: float = DEFAULT_TOP_P,
    max_tokens: int = DEFAULT_MAX_TOKENS,
    stop: Optional[list[str]] = None,
    timeout: Optional[int] = None,
) -> str:
    """
    Generate a response from the local model.

    Args:
        prompt:        The user prompt.
        system:        Optional system message setting role/context.
        model:         Model name (must already be installed via `ollama pull`).
        temperature:   0.0 = deterministic, 1.0 = creative. Default 0.2 (legal).
        top_p:         Nucleus sampling threshold.
        max_tokens:    Maximum response length.
        stop:          Optional list of stop sequences.

    Returns:
        The model's text response (string). Whitespace-trimmed.

    Raises:
        RuntimeError if Ollama is unreachable or the model is not installed.
    """
    _assert_localhost(OLLAMA_HOST)

    payload: dict[str, Any] = {
        "model": model,
        "prompt": prompt,
        "stream": True,          # stream so slow-but-working calls aren't killed
        "options": {
            "temperature": temperature,
            "top_p": top_p,
            "num_predict": max_tokens,
        },
    }

    if system:
        payload["system"] = system
    if stop:
        payload["options"]["stop"] = stop

    start = time.time()
    chunks: list[str] = []
    response = None
    first_token_at: float | None = None
    last_token_at = start

    # A caller-supplied timeout sets how long we wait for the FIRST token
    # (prompt ingestion). It is floored at the module default so a small
    # per-task value can never reintroduce the premature-kill bug.
    first_token_limit = max(int(timeout), FIRST_TOKEN_TIMEOUT_SECONDS) if timeout else FIRST_TOKEN_TIMEOUT_SECONDS

    try:
        # timeout=(connect, read): with stream=True the READ timeout applies
        # between received chunks. We set it generously enough to cover the
        # PREFILL phase (model ingesting a large prompt, emitting nothing).
        # Once tokens start flowing we enforce a much stricter stall check
        # manually inside the loop.
        response = requests.post(
            f"{OLLAMA_HOST}/api/generate",
            json=payload,
            stream=True,
            timeout=(CONNECT_TIMEOUT_SECONDS, first_token_limit),
        )
        response.raise_for_status()

        for raw_line in response.iter_lines(decode_unicode=True):
            now = time.time()

            # Absolute backstop against a pathological runaway generation.
            if now - start > HARD_CEILING_SECONDS:
                raise requests.exceptions.Timeout("exceeded hard ceiling")

            # Once output has begun, enforce the strict inter-token stall limit.
            if first_token_at is not None and now - last_token_at > STALL_TIMEOUT_SECONDS:
                raise requests.exceptions.Timeout("stalled mid-stream")

            if not raw_line:
                continue  # keep-alive / blank line

            try:
                piece = json.loads(raw_line)
            except ValueError:
                continue  # ignore any malformed line rather than failing outright

            if piece.get("error"):
                raise RuntimeError(f"Ollama returned an error: {piece['error']}")

            token = piece.get("response", "")
            if token:
                if first_token_at is None:
                    first_token_at = now
                    logger.debug(
                        f"First token after {now - start:.1f}s "
                        f"(prompt={len(prompt)} chars, model={model})"
                    )
                last_token_at = now
                chunks.append(token)

            if piece.get("done"):
                break

    except requests.exceptions.ConnectionError as e:
        raise RuntimeError(
            "Lost connection to Ollama mid-request. Is the service still running?"
        ) from e
    except requests.exceptions.Timeout as e:
        produced = len("".join(chunks))
        if first_token_at is None:
            raise RuntimeError(
                f"Model produced no output within {first_token_limit}s "
                f"while reading a {len(prompt)}-character prompt. "
                "The prompt is likely too large for this model on this hardware — "
                "shorten it, or use a smaller model (phi3:3.8b)."
            ) from e
        raise RuntimeError(
            f"Model stalled mid-response — no output for {STALL_TIMEOUT_SECONDS}s "
            f"(produced {produced} characters first). "
            "Try a smaller model (phi3:3.8b) or a shorter prompt."
        ) from e
    except requests.exceptions.HTTPError as e:
        # NOTE: on a streamed response the body has not been consumed, so read
        # it defensively — never let error handling itself hang or raise.
        body = ""
        if response is not None:
            try:
                body = response.content[:500].decode("utf-8", errors="replace")
            except Exception:  # noqa: BLE001 - diagnostics must never crash
                body = "<unavailable>"
        raise RuntimeError(f"Ollama HTTP error: {e}. Body: {body}") from e
    finally:
        if response is not None:
            response.close()

    elapsed = time.time() - start
    text = "".join(chunks).strip()
    logger.debug(
        f"Local LLM streamed {len(text)} chars in {elapsed:.2f}s "
        f"(model={model}, max_tokens={max_tokens})"
    )

    if not text:
        raise RuntimeError(
            "Ollama returned an empty response. It may have been interrupted, "
            "or the prompt may exceed the model's context window."
        )

    return text


# ════════════════════════════════════════════════════════════════════════════
# JSON GENERATION (for structured outputs)
# ════════════════════════════════════════════════════════════════════════════

def generate_json(
    prompt: str,
    system: Optional[str] = None,
    model: str = DEFAULT_MODEL,
    temperature: float = 0.1,  # Even lower for structured outputs
    max_tokens: int = DEFAULT_MAX_TOKENS,
    max_retries: int = 2,
) -> dict[str, Any]:
    """
    Generate a JSON response. Used by PRPP engine for structured scoring.

    The model is instructed to emit ONLY valid JSON. If parsing fails, retries
    up to max_retries times before raising.

    Returns:
        Parsed JSON as a Python dict.

    Raises:
        ValueError if the model never produces valid JSON.
    """
    json_instruction = (
        "\n\nIMPORTANT: Respond with ONLY a valid JSON object. "
        "No preamble, no markdown code fences, no commentary. "
        "Start with { and end with }."
    )
    full_prompt = prompt + json_instruction

    last_error: Optional[Exception] = None
    last_response: str = ""

    for attempt in range(max_retries + 1):
        try:
            text = generate(
                prompt=full_prompt,
                system=system,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            last_response = text

            # Strip common markdown fences if model included them
            cleaned = text.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("```", 2)[1] if "```" in cleaned[3:] else cleaned[3:]
                if cleaned.startswith("json"):
                    cleaned = cleaned[4:]
                cleaned = cleaned.strip().rstrip("`").strip()

            # Find first { and last } — tolerates leading/trailing chatter
            first = cleaned.find("{")
            last = cleaned.rfind("}")
            if first >= 0 and last > first:
                cleaned = cleaned[first : last + 1]

            return json.loads(cleaned)

        except json.JSONDecodeError as e:
            last_error = e
            logger.warning(
                f"JSON parse failed (attempt {attempt + 1}/{max_retries + 1}): {e}"
            )
            continue
        except RuntimeError as e:
            # Don't retry connection errors
            raise

    raise ValueError(
        f"Local model failed to produce valid JSON after {max_retries + 1} attempts. "
        f"Last response (first 300 chars): {last_response[:300]!r}. "
        f"Last parse error: {last_error}"
    )


# ════════════════════════════════════════════════════════════════════════════
# CONVENIENCE: structured rephrasing
# ════════════════════════════════════════════════════════════════════════════

def rephrase_structured(
    structured_data: dict[str, Any],
    instruction: str,
    model: str = DEFAULT_MODEL,
    max_tokens: int = 512,
) -> str:
    """
    Take a structured Python dict and ask the LLM to rephrase it in natural
    English, WITHOUT adding facts not present in the dict.

    This is the architecture pattern we use to constrain hallucination:
    deterministic Python computes facts, LLM only handles phrasing.

    Args:
        structured_data: The Python dict containing all facts.
        instruction:     What to do with the data (e.g. "Summarise for a partner").
        model:           Model name.
        max_tokens:      Maximum response length.

    Returns:
        Natural-language rendering of the structured data.
    """
    system = (
        "You are a legal-writing assistant. You receive structured JSON data "
        "and produce natural English text describing it. CRITICAL RULES:\n"
        "1. Use ONLY facts, citations, case names, and authorities present "
        "in the JSON.\n"
        "2. NEVER invent or add information beyond what the JSON contains.\n"
        "3. NEVER mention statutes, cases, or rules not explicitly listed.\n"
        "4. If the JSON does not contain something, do not assert it.\n"
        "5. Match the formality of UK legal practice (precise, conservative)."
    )

    prompt = (
        f"Structured data:\n```json\n{json.dumps(structured_data, indent=2)}\n```\n\n"
        f"Instruction: {instruction}\n\n"
        f"Produce the natural-language rendering now."
    )

    return generate(
        prompt=prompt,
        system=system,
        model=model,
        temperature=0.15,  # Very low — we want fidelity to source
        max_tokens=max_tokens,
    )


# ════════════════════════════════════════════════════════════════════════════
# SELF-TEST
# ════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    """Run as: python local_llm.py — verifies setup."""
    print("Libra local LLM self-test")
    print("─" * 60)

    print("\n[1/4] Checking Ollama status...")
    status = check_status()
    print(f"  Available:               {status.available}")
    print(f"  Default model installed: {status.default_model_installed}")
    print(f"  Models found:            {status.models_installed}")
    if status.error:
        print(f"  Error:                   {status.error}")
        print("\nResolve the error above before continuing.")
        raise SystemExit(1)

    print("\n[2/4] Testing basic generation...")
    text = generate(
        prompt="Respond with exactly: LIBRA LOCAL LLM IS WORKING",
        max_tokens=50,
    )
    print(f"  Response: {text[:200]}")

    print("\n[3/4] Testing JSON generation...")
    data = generate_json(
        prompt=(
            "Return a JSON object describing the colour 'red'. "
            "Include keys: name (string), hex (string), wavelength_nm (number)."
        )
    )
    print(f"  Parsed:   {data}")

    print("\n[4/4] Testing structured rephrasing...")
    rendering = rephrase_structured(
        structured_data={
            "doctrine": "adverse inference from absent witness",
            "authority": "Wisniewski v Central Manchester HA [1998] EWCA Civ 596",
            "judge": "Brooke LJ",
            "extension_to_documents": "Wetton v Ahmed [2011] EWCA Civ 610",
        },
        instruction="Write a one-paragraph summary suitable for a procedural memo.",
        max_tokens=200,
    )
    print(f"  Rendering:\n{rendering}\n")

    print("─" * 60)
    print("All self-tests passed. Libra is ready to use the local LLM.")
