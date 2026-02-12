from fastapi import APIRouter, HTTPException
from dotenv import load_dotenv
import os
import requests
from app.models.request_models import APIKeysRequest

router = APIRouter()

# Load environment variables from .env file
load_dotenv()

# In-memory storage for active runtime configuration
api_keys_storage = {}


def _validate_ollama_config(ollama_url: str, ollama_model: str) -> None:
    """Validate that Ollama is reachable and the selected model exists."""
    try:
        response = requests.get(f"{ollama_url.rstrip('/')}/api/tags", timeout=3)
        response.raise_for_status()
        models = [m.get("name", "") for m in response.json().get("models", [])]
        if not any(name.split(":")[0] == ollama_model for name in models):
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Model '{ollama_model}' was not found in local Ollama. "
                    "Pull it first with: ollama pull <model_name>."
                ),
            )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Unable to connect to Ollama at {ollama_url}: {exc}",
        ) from exc


@router.post("/setup")
async def setup_api_keys(request: APIKeysRequest):
    """Store local Ollama configuration (no cloud API keys required)."""
    ollama_url = (request.ollama_url or os.getenv("OLLAMA_URL") or "http://localhost:11434").strip()
    ollama_model = (request.ollama_model or os.getenv("OLLAMA_MODEL") or "llama3").strip()

    _validate_ollama_config(ollama_url, ollama_model)

    api_keys_storage["ollama_url"] = ollama_url
    api_keys_storage["ollama_model"] = ollama_model

    return {"message": "Ollama configured successfully", "ollama_url": ollama_url, "ollama_model": ollama_model}


@router.get("/status")
async def get_api_keys_status():
    """Get status of local Ollama configuration."""
    return {
        "ollama_configured": "ollama_url" in api_keys_storage or bool(os.getenv("OLLAMA_URL")),
        "ollama_model": api_keys_storage.get("ollama_model") or os.getenv("OLLAMA_MODEL", "llama3"),
    }


def get_api_keys():
    """Retrieve local runtime configuration."""
    api_keys_storage["ollama_url"] = api_keys_storage.get("ollama_url") or os.getenv("OLLAMA_URL", "http://localhost:11434")
    api_keys_storage["ollama_model"] = api_keys_storage.get("ollama_model") or os.getenv("OLLAMA_MODEL", "llama3")

    # Keep compatibility with existing callers that expect these keys.
    api_keys_storage.setdefault("sarvam_key", "")
    api_keys_storage.setdefault("openai_key", "")

    return api_keys_storage
