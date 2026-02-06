import requests
import json
import re

def generate_hindi_script_with_google(english_script, api_key=None):
    """
    Generate a natural Hindi script with appropriate English words mixed in using local Ollama.
    The api_key argument is kept for compatibility but not used.

    Args:
        english_script (str): Original English script
        api_key (str): API key (unused)

    Returns:
        str: Hindi script with natural English mixing
    """
    if english_script is None or not english_script.strip():
        return None
    
    # Max chunk size for Ollama (approx characters)
    MAX_CHUNK_SIZE = 4000
    
    if len(english_script) <= MAX_CHUNK_SIZE:
        return _translate_text_ollama(english_script)
    
    chunks = _split_into_chunks(english_script, MAX_CHUNK_SIZE)
    
    translated_chunks = []
    for chunk in chunks:
        translated_chunk = _translate_text_ollama(chunk)
        if translated_chunk:
            translated_chunks.append(translated_chunk)
    
    return ' '.join(translated_chunks)

def _translate_text_ollama(text):
    """Helper function to translate text using local Ollama."""
    # Try to connect to localhost Ollama
    url = "http://localhost:11434/api/generate"
    model = "llama3"

    prompt = f"""
Translate the following text to Hindi.
Rules:
1. Keep technical terms, proper nouns, and difficult words in English (Hinglish).
2. The translation should be natural and conversational.
3. Output ONLY the translated text, no explanations.

Text to translate:
{text}
"""

    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.3
        }
    }

    try:
        response = requests.post(url, json=payload, timeout=120)
        if response.status_code == 200:
             return response.json().get("response", "").strip()
        else:
             print(f"Ollama translation failed: {response.status_code} - {response.text}")
             return None
    except Exception as e:
        print(f"Ollama translation error: {str(e)}")
        return None

def _split_into_chunks(text, max_size):
    """
    Split text into chunks not exceeding max_size, respecting sentence boundaries.
    
    Args:
        text (str): Text to split
        max_size (int): Maximum chunk size
        
    Returns:
        list: List of text chunks
    """
    # Common sentence delimiters
    sentence_delimiters = ['. ', '! ', '? ', '.\n', '!\n', '?\n']
    
    chunks = []
    current_chunk = ""
    
    sentences = []
    remaining_text = text
    
    # Split text into sentences
    while remaining_text:
        delimiter_indices = [(remaining_text.find(delimiter), delimiter) 
                             for delimiter in sentence_delimiters 
                             if remaining_text.find(delimiter) != -1]
        
        if not delimiter_indices:
            sentences.append(remaining_text)
            break
            
        earliest_index, delimiter = min(delimiter_indices, key=lambda x: x[0])
        sentence = remaining_text[:earliest_index + len(delimiter)]
        sentences.append(sentence)
        remaining_text = remaining_text[earliest_index + len(delimiter):]
    
    # Group sentences into chunks
    for sentence in sentences:
        if len(current_chunk) + len(sentence) <= max_size:
            current_chunk += sentence
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = sentence
    
    # Add the last chunk if it's not empty
    if current_chunk:
        chunks.append(current_chunk.strip())
        
    return chunks
