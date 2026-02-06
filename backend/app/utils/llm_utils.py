import requests
import os

def generate_with_ollama(prompt, model="llama3", url=None):
    """Generate content using Ollama API."""
    if url is None:
        url = os.getenv("OLLAMA_URL", "http://localhost:11434")

    print(f"Generating with Ollama ({model} at {url})...")

    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.3,
            "num_ctx": 4096
        }
    }

    try:
        response = requests.post(f"{url}/api/generate", json=payload, timeout=120)
        response.raise_for_status()
        return response.json().get("response", "")
    except Exception as e:
        print(f"Ollama generation error: {e}")
        return None
