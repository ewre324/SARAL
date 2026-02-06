import requests
import json
import re

# Comprehensive language mapping
SUPPORTED_LANGUAGES = {
    'Hindi': 'hi',
    'Bengali': 'bn',
    'Gujarati': 'gu',
    'Kannada': 'kn',
    'Malayalam': 'ml',
    'Marathi': 'mr',
    'Odia': 'or',
    'Punjabi': 'pa',
    'Tamil': 'ta',
    'Telugu': 'te'
}

def get_supported_languages():
    """
    Get list of all supported languages.
    
    Returns:
        dict: Dictionary mapping language names to language codes
    """
    return SUPPORTED_LANGUAGES.copy()

def is_language_supported(language):
    """
    Check if a language is supported.
    
    Args:
        language (str): Language name or code
        
    Returns:
        bool: True if language is supported
    """
    return (language in SUPPORTED_LANGUAGES or 
            language in SUPPORTED_LANGUAGES.values())

def get_language_code(language):
    """
    Get language code for a given language name.
    
    Args:
        language (str): Language name
        
    Returns:
        str: Language code or None if not supported
    """
    if language in SUPPORTED_LANGUAGES:
        return SUPPORTED_LANGUAGES[language]
    elif language in SUPPORTED_LANGUAGES.values():
        return language
    return None

def translate_to_language(english_script, target_language, api_key, mode="code-mixed"):
    """
    Translate English script to target language using local Ollama.

    Args:
        english_script (str): Original English script
        target_language (str): Target language name or code
        api_key (str): API key (unused)
        mode (str): Translation mode (unused)

    Returns:
        str: Translated script or None if translation fails
    """
    if english_script is None or not english_script.strip():
        return None
    
    # Get target language code
    target_code = get_language_code(target_language)
    if not target_code:
        # If not in our list, maybe it's passed as a name not in list or a code?
        # Let's assume user knows what they are doing if it's not None
        pass
    
    # Max chunk size for Ollama
    MAX_CHUNK_SIZE = 4000
    
    if len(english_script) <= MAX_CHUNK_SIZE:
        return _translate_text_ollama(english_script, target_language)
    
    chunks = _split_into_chunks(english_script, MAX_CHUNK_SIZE)
    
    translated_chunks = []
    for chunk in chunks:
        translated_chunk = _translate_text_ollama(chunk, target_language)
        if translated_chunk:
            translated_chunks.append(translated_chunk)
    
    return ' '.join(translated_chunks)

def _translate_text_ollama(text, target_language):
    """Helper function to translate text using local Ollama."""
    url = "http://localhost:11434/api/generate"
    model = "llama3"

    prompt = f"""
Translate the following text to {target_language}.
Rules:
1. Keep technical terms, proper nouns, and difficult words in English (Hinglish/Code-mixed if appropriate).
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
    sentence_delimiters = ['. ', '! ', '? ', '.\n', '!\n', '?\n']
    
    chunks = []
    current_chunk = ""
    
    sentences = []
    remaining_text = text
    
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
    
    for sentence in sentences:
        if len(current_chunk) + len(sentence) <= max_size:
            current_chunk += sentence
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = sentence
    
    if current_chunk:
        chunks.append(current_chunk.strip())
        
    return chunks

# Convenience functions for specific languages
def translate_to_hindi(english_script, api_key):
    return translate_to_language(english_script, 'Hindi', api_key)

def translate_to_bengali(english_script, api_key):
    return translate_to_language(english_script, 'Bengali', api_key)

def translate_to_tamil(english_script, api_key):
    return translate_to_language(english_script, 'Tamil', api_key)

def translate_to_telugu(english_script, api_key):
    return translate_to_language(english_script, 'Telugu', api_key)
