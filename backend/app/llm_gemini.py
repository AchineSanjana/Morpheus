import os
from typing import Optional, List
try:
    import google.generativeai as genai
except Exception:
    genai = None

# Configure the Gemini client with the API key from the .env file
api_key = os.getenv("GEMINI_API_KEY")
if api_key and genai:
    try:
        genai.configure(api_key=api_key)
    except Exception:
        # ignore configuration errors at import time
        pass

# Preferred model can be overridden via env; default to gemini-2.5-flash
# Sequential fallback order (by default):
#   1) gemini-2.5-flash (preferred)
#   2) gemini-2.0-flash
#   3) gemini-2.0-flash-exp
#   4) gemini-1.5-flash
#   5) gemini-1.5-flash-8b
# You can prepend additional models via GEMINI_FALLBACK_MODELS (comma-separated), which will be tried after the preferred model and before the defaults above.
DEFAULT_PREFERRED_MODEL = os.getenv("GEMINI_PREFERRED_MODEL") or "gemini-2.5-flash"

def gemini_ready() -> bool:
    """Return True when the Gemini API key is configured and client is usable."""
    return bool(api_key and genai)

def _fallback_model_list(preferred: str, env_val: Optional[str]) -> List[str]:
    """Build the ordered list of models to try, starting with preferred, then fallbacks.
    You can override fallbacks via env var GEMINI_FALLBACK_MODELS as a comma-separated list.
    """
    # Default fallbacks chosen for broad availability (non-pro models only)
    # Requested order: prefer 2.0 stable before 2.0 experimental.
    defaults = [
        "gemini-2.0-flash",
        "gemini-2.0-flash-exp",
        "gemini-1.5-flash",
        "gemini-1.5-flash-8b",
    ]
    if env_val:
        env_models = [m.strip() for m in env_val.split(",") if m.strip()]
    else:
        env_models = []

    ordered = [preferred] + env_models + defaults
    # Deduplicate preserving order
    seen = set()
    final: List[str] = []
    for m in ordered:
        if m and m not in seen:
            final.append(m)
            seen.add(m)
    return final


async def generate_gemini_text(
    prompt: str,
        model_name: str = DEFAULT_PREFERRED_MODEL,
    fallback_models: Optional[List[str]] = None,
) -> Optional[str]:
    """Generate text with Gemini, trying fallbacks when the preferred model fails.

        - model_name: preferred model to try first (default comes from GEMINI_PREFERRED_MODEL or 'gemini-2.5-flash')
        - fallback_models: optional list of model names to try next; if not provided,
            falls back to env GEMINI_FALLBACK_MODELS or sensible non-pro defaults (2.0-flash, 2.0-flash-exp, 1.5-flash, 1.5-flash-8b).
    """
    if not api_key or not genai:
        print("GEMINI_API_KEY not found or google.generativeai not available. Skipping LLM call.")
        return None

    # Build list of models to attempt
    env_fallbacks = os.getenv("GEMINI_FALLBACK_MODELS")
    to_try = [model_name] + [m for m in (fallback_models or []) if m]
    if not fallback_models:
        to_try = _fallback_model_list(model_name, env_fallbacks)

    last_error: Optional[Exception] = None
    for m in to_try:
        try:
            model = genai.GenerativeModel(m)
            resp = await model.generate_content_async(prompt)
            text = getattr(resp, "text", None)
            if text and text.strip():
                print(f"Gemini model '{m}' succeeded.")
                return text
            else:
                # Try next model if empty/invalid
                print(f"Gemini model '{m}' returned empty text; trying next fallback (if any)...")
        except Exception as e:
            last_error = e
            print(f"Error calling Gemini model '{m}': {e}")
            continue

    if last_error:
        print(f"All Gemini models failed; last error: {last_error}")
    return None
