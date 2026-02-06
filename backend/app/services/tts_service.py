import os
from pathlib import Path
from typing import Dict, List, Optional
import pyttsx3
from .language_service import get_language_code, is_language_supported
import re

def clean_script_for_tts_and_video(script_text):
    """Clean script text for TTS processing."""
    if not script_text or not script_text.strip():
        return ""

    script_text = re.sub(r'\*\*([^*]+)\*\*', r'\1', script_text)
    script_text = re.sub(r'\*([^*]+)\*', r'\1', script_text)
    script_text = re.sub(r'#+\s*', '', script_text)
    script_text = re.sub(r'[^\w\s.,!?;:\-()"\']', ' ', script_text)
    script_text = re.sub(r'\s+', ' ', script_text)

    return script_text.strip()

def _generate_audio_pyttsx3(text, output_path, voice_id=None):
    """Helper to generate audio using pyttsx3."""
    try:
        engine = pyttsx3.init()
    except Exception as e:
        print(f"Failed to initialize pyttsx3: {e}")
        raise ValueError(f"Could not initialize local TTS engine. Please ensure 'espeak' or similar is installed. Error: {e}")

    if voice_id:
        try:
            engine.setProperty('voice', voice_id)
        except:
            pass # Ignore if voice not found

    # Adjust rate/volume if needed
    engine.setProperty('rate', 150)

    engine.save_to_file(text, output_path)
    engine.runAndWait()

    return os.path.exists(output_path)

def ensure_audio_is_generated(
    sarvam_api_key: str,
    language: str,
    paper_id: str,
    title_intro_script: str,
    sections_scripts: Dict[str, str],
    voice_selections: Dict[str, str],
    hinglish_iterations: int = 3,
    openai_api_key: Optional[str] = None,
    show_hindi_debug: bool = False
) -> Dict[str, List[str]]:
    """Generate audio files using local pyttsx3."""
    
    audio_files = []
    output_dir = f"temp/audio/{paper_id}"
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    print("Initializing Local TTS (pyttsx3)...")

    successful_generations = 0

    try:
        # Generate title audio
        if title_intro_script and title_intro_script.strip():
            print("Generating title audio...")
            title_audio_path = os.path.join(output_dir, "00_title_introduction.wav")
            
            cleaned_text = clean_script_for_tts_and_video(title_intro_script)
            if cleaned_text:
                if _generate_audio_pyttsx3(cleaned_text, title_audio_path):
                    audio_files.append(title_audio_path)
                    successful_generations += 1
                    print(f"✓ Title audio: {title_audio_path}")

        # Generate section audios
        section_order = ["Introduction", "Methodology", "Results", "Discussion", "Conclusion"]
        
        for i, section_name in enumerate(section_order, start=1):
            if section_name in sections_scripts:
                script_text = sections_scripts[section_name]
                
                if not script_text or not script_text.strip():
                    continue

                print(f"Generating {section_name} audio...")
                audio_path = os.path.join(output_dir, f"{i:02d}_{section_name.lower()}.wav")
                
                cleaned_text = clean_script_for_tts_and_video(script_text)
                if cleaned_text:
                    if _generate_audio_pyttsx3(cleaned_text, audio_path):
                        audio_files.append(audio_path)
                        successful_generations += 1
                        print(f"✓ {section_name} audio: {audio_path}")

        if successful_generations == 0:
            print("Warning: No audio files generated.")

        print(f"✓ Generated {successful_generations} audio files")
        return {
            "audio_files": [Path(f).name for f in audio_files]
        }

    except Exception as e:
        print(f"Audio generation error: {e}")
        raise

# Map other functions to the main one
# Since pyttsx3 is local, we treat all languages similarly (relying on system voices)
# We can just forward the call.

def ensure_hindi_audio_is_generated(
    sarvam_api_key: str,
    paper_id: str,
    title_intro_script: str,
    sections_scripts: Dict[str, str],
    voice_selections: Dict[str, str],
    hinglish_iterations: int = 3,
    openai_api_key: Optional[str] = None,
    show_hindi_debug: bool = False
) -> Dict[str, List[str]]:
    return ensure_audio_is_generated(
        sarvam_api_key=sarvam_api_key,
        language="Hindi",
        paper_id=paper_id,
        title_intro_script=title_intro_script,
        sections_scripts=sections_scripts,
        voice_selections=voice_selections,
        hinglish_iterations=hinglish_iterations,
        openai_api_key=openai_api_key,
        show_hindi_debug=show_hindi_debug
    )

def ensure_language_audio_is_generated(
    sarvam_api_key: str,
    language: str,
    paper_id: str,
    title_intro_script: str,
    sections_scripts: Dict[str, str],
    voice_selections: Dict[str, str],
    hinglish_iterations: int = 3,
    openai_api_key: Optional[str] = None,
    show_debug: bool = False
) -> Dict[str, List[str]]:
    return ensure_audio_is_generated(
        sarvam_api_key=sarvam_api_key,
        language=language,
        paper_id=paper_id,
        title_intro_script=title_intro_script,
        sections_scripts=sections_scripts,
        voice_selections=voice_selections,
        hinglish_iterations=hinglish_iterations,
        openai_api_key=openai_api_key,
        show_hindi_debug=show_debug
    )

def test_sarvam_sdk(api_key: str, voice: str = "meera"):
    """Test function - returns True as we don't depend on it."""
    return True
