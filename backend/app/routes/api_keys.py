from fastapi import APIRouter, HTTPException, Depends, status
from dotenv import load_dotenv
import os
import requests
from app.auth.dependencies import get_current_user
from app.models.request_models import APIKeysRequest

router = APIRouter()

# Load environment variables from .env file
load_dotenv()

# In-memory storage for API keys
api_keys_storage = {}

@router.post("/setup")
async def setup_api_keys(request: APIKeysRequest):
    """Store API keys securely."""

    # Gemini Setup
    gemini_key = (request.gemini_key or "").strip() or os.getenv("GEMINI_API_KEY")
    if gemini_key:
        try:
            import google.generativeai as genai
            genai.configure(api_key=gemini_key)
            model = genai.GenerativeModel('gemini-2.0-flash')
            model.generate_content("Hello")
            api_keys_storage["gemini_key"] = gemini_key
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid Gemini API key: {str(e)}")

    # Sarvam Setup
    sarvam_key = (request.sarvam_key or "").strip() or os.getenv("SARVAM_API_KEY")
    if sarvam_key:
        api_keys_storage["sarvam_key"] = sarvam_key

    # OpenAI Setup
    if request.openai_key:
        try:
            import openai
            client = openai.OpenAI(api_key=request.openai_key)
            client.models.list()
            api_keys_storage["openai_key"] = request.openai_key
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid OpenAI API key: {str(e)}")

    # Ollama Setup (Check connection)
    ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
    try:
        response = requests.get(f"{ollama_url}/api/tags", timeout=2)
        if response.status_code == 200:
            api_keys_storage["ollama_url"] = ollama_url
            api_keys_storage["ollama_model"] = os.getenv("OLLAMA_MODEL", "llama3")
    except Exception:
        # Don't fail if Ollama isn't running, just don't store it as "active"
        pass

    return {"message": "API keys configured successfully"}

@router.get("/status")
async def get_api_keys_status():
    """Get status of configured API keys."""
    return {
        "gemini_configured": "gemini_key" in api_keys_storage or bool(os.getenv("GEMINI_API_KEY")),
        "sarvam_configured": "sarvam_key" in api_keys_storage or bool(os.getenv("SARVAM_API_KEY")),
        "openai_configured": "openai_key" in api_keys_storage,
        "ollama_configured": "ollama_url" in api_keys_storage or bool(os.getenv("OLLAMA_URL"))
    }

def get_api_keys():
    """Retrieve all configured API keys and LLM settings."""

    # 1. Load Sarvam (Fallback to env)
    if "sarvam_key" not in api_keys_storage or not api_keys_storage["sarvam_key"]:
        sarvam_key = os.getenv("SARVAM_API_KEY")
        if sarvam_key:
            api_keys_storage["sarvam_key"] = sarvam_key

    # 2. Load Ollama (Always check env)
    ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
    ollama_model = os.getenv("OLLAMA_MODEL", "llama3")
    # Simple check if reachable (optional, can skip for speed)
    api_keys_storage["ollama_url"] = ollama_url
    api_keys_storage["ollama_model"] = ollama_model

    # 3. Load Gemini (Handle multiple keys)
    gemini_keys = []
    i = 1
    while True:
        key = os.getenv(f"GEMINI_API_KEY_{i}")
        if key:
            gemini_keys.append(key)
            i += 1
        else:
            break
    if not gemini_keys:
        key = os.getenv("GEMINI_API_KEY")
        if key:
            gemini_keys.append(key)

    # Try to find a working Gemini key
    valid_gemini = False
    for gemini_key in gemini_keys:
        try:
            # We don't validate every call to save time, just ensure one exists
            api_keys_storage["gemini_key"] = gemini_key
            valid_gemini = True
            break
        except Exception:
            continue

    # Return whatever we have; logic in routes/scripts will decide precedence
    return api_keys_storage