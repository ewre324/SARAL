import os
from pathlib import Path
from typing import Dict, List, Optional
from .sarvam_sdk import SarvamTTS, SarvamTTSError
from .language_service import get_language_code, is_language_supported
import re
import subprocess
import grapheme  # Add this import for proper Unicode grapheme handling

# Try to import pyttsx3, handle if missing
try:
    import pyttsx3
    PYTTSX3_AVAILABLE = True
except ImportError:
    PYTTSX3_AVAILABLE = False
    print("Warning: pyttsx3 not installed. Local TTS will not work.")

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

def generate_audio_local(text: str, output_path: str, language: str = 'en') -> bool:
    """Generate audio using local pyttsx3 engine."""
    if not PYTTSX3_AVAILABLE:
        print("Error: pyttsx3 is not installed.")
        return False

    try:
        engine = pyttsx3.init()

        # Attempt to set properties (optional)
        # engine.setProperty('rate', 150)

        # Verify if output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # Saving to file
        engine.save_to_file(text, output_path)
        engine.runAndWait()

        # Verify file creation
        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            return True
        else:
            print(f"Error: Local TTS generated empty or missing file at {output_path}")
            return False

    except Exception as e:
        print(f"Local TTS generation error: {e}")
        # Hint about system dependencies
        if "libespeak" in str(e) or "driver" in str(e).lower():
            print("Hint: You might be missing system dependencies like 'espeak' or 'ffmpeg'.")
            print("On Ubuntu/Debian: sudo apt-get install espeak ffmpeg")
            print("On Mac: brew install espeak")
        return False

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
) -> List[str]:
    """Generate audio files - simplified approach aligned with Streamlit"""
    
    audio_files = []
    output_dir = f"temp/audio/{paper_id}"
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    use_local_tts = False
    tts_client = None

    if not sarvam_api_key or sarvam_api_key.strip() == "":
        print("Sarvam API key not found. Switching to Local TTS (pyttsx3).")
        use_local_tts = True
    else:
        # Initialize TTS client
        try:
            tts_client = SarvamTTS(api_key=sarvam_api_key)

            # Simple connection test
            if not tts_client.test_connection():
                print("Failed to connect to Sarvam API. Switching to Local TTS.")
                use_local_tts = True
            else:
                print("✓ Connected to Sarvam TTS API")
                voice = voice_selections.get(language, "meera")
                print(f"Using voice: {voice}")
                if voice == "meera":
                    voice = "vidya"
                elif voice == "arjun":
                    voice = "karun"

        except Exception as e:
            print(f"TTS client initialization failed: {e}. Switching to Local TTS.")
            use_local_tts = True

    successful_generations = 0

    try:
        # Generate title audio
        if title_intro_script and title_intro_script.strip():
            print("Generating title audio...")
            title_audio_path = os.path.join(output_dir, "00_title_introduction.wav")
            
            cleaned_text = clean_script_for_tts_and_video(title_intro_script)
            if cleaned_text:
                success = False
                if use_local_tts:
                    success = generate_audio_local(cleaned_text, title_audio_path)
                else:
                    success = tts_client.synthesize_long_text(
                        text=cleaned_text,
                        output_path=title_audio_path,
                        target_language='en-IN',
                        voice=voice,
                        max_chunk_length=500  # Smaller chunks for reliability
                    )
                
                if success:
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
                    success = False
                    if use_local_tts:
                        success = generate_audio_local(cleaned_text, audio_path)
                    else:
                        success = tts_client.synthesize_long_text(
                            text=cleaned_text,
                            output_path=audio_path,
                            target_language='en-IN',
                            voice=voice,
                            max_chunk_length=500
                        )
                    
                    if success:
                        audio_files.append(audio_path)
                        successful_generations += 1
                        print(f"✓ {section_name} audio: {audio_path}")

        if successful_generations == 0:
            raise ValueError("No audio files were generated successfully")

        print(f"✓ Generated {successful_generations} audio files")
        return {
            "audio_files": [Path(f).name for f in audio_files]
        }

    except Exception as e:
        print(f"Audio generation error: {e}")
        raise



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
    """Generate audio files specifically for Hindi scripts"""
    
    audio_files = []
    output_dir = f"temp/audio/{paper_id}"
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    use_local_tts = False
    tts_client = None
    voice = "vidya"

    if not sarvam_api_key or sarvam_api_key.strip() == "":
        print("Sarvam API key not found. Switching to Local TTS (pyttsx3).")
        use_local_tts = True
    else:
        voice = voice_selections.get("Hindi", "vidya")
        print(f"Using Hindi voice: {voice}")

        # Initialize TTS client
        try:
            tts_client = SarvamTTS(api_key=sarvam_api_key)

            # Simple connection test
            if not tts_client.test_connection():
                 print("Failed to connect to Sarvam API. Switching to Local TTS.")
                 use_local_tts = True
            else:
                print("✓ Connected to Sarvam TTS API")

        except Exception as e:
            print(f"TTS client initialization failed: {e}. Switching to Local TTS.")
            use_local_tts = True

    successful_generations = 0
    
    def chunk_hindi_text(text: str, max_chunk_length: int = 450) -> List[str]:
        """Create smaller chunks for Hindi text, respecting sentence boundaries and keeping grapheme clusters intact"""
        # First check if text is shorter than max length
        if grapheme.length(text) <= max_chunk_length:
            return [text]
        
        # Split on sentence boundaries with priority to Devanagari full stops
        # This regex handles Hindi sentence endings (Devanagari danda and double danda) and standard punctuation
        sentences = re.split(r'(?<=[।॥.!?])\s+', text)
        
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            # Check if adding this sentence would exceed max length using grapheme-aware length
            sentence_grapheme_length = grapheme.length(sentence)
            current_chunk_grapheme_length = grapheme.length(current_chunk)
            
            if current_chunk_grapheme_length + sentence_grapheme_length + 1 > max_chunk_length:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                
                # If the sentence itself is longer than max_chunk_length, 
                # break it at word boundaries while respecting grapheme clusters
                if sentence_grapheme_length > max_chunk_length:
                    words = sentence.split()
                    temp_chunk = ""
                    for word in words:
                        word_grapheme_length = grapheme.length(word)
                        temp_chunk_grapheme_length = grapheme.length(temp_chunk)
                        
                        if temp_chunk_grapheme_length + word_grapheme_length + 1 > max_chunk_length:
                            chunks.append(temp_chunk.strip())
                            temp_chunk = word + " "
                        else:
                            temp_chunk += word + " "
                    
                    if temp_chunk:
                        current_chunk = temp_chunk
                else:
                    current_chunk = sentence + " "
            else:
                current_chunk += sentence + " "
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        # Verify no chunk exceeds the maximum length in graphemes
        for i, chunk in enumerate(chunks):
            chunk_len = grapheme.length(chunk)
            if chunk_len > max_chunk_length:
                print(f"Warning: Chunk {i} has {chunk_len} graphemes, which exceeds the maximum of {max_chunk_length}")
        
        return chunks

    try:
        # Generate title audio
        if title_intro_script and title_intro_script.strip():
            print("Generating Hindi title audio...")
            title_audio_path = os.path.join(output_dir, "00_title_introduction.wav")
            
            cleaned_text = title_intro_script
            if cleaned_text:
                if use_local_tts:
                    if generate_audio_local(cleaned_text, title_audio_path, language='hi'):
                        audio_files.append(title_audio_path)
                        successful_generations += 1
                        print(f"✓ Title Hindi audio (Local): {title_audio_path}")
                else:
                    # Original Sarvam Logic
                    hindi_chunks = chunk_hindi_text(cleaned_text)
                    print(f"Processing {len(hindi_chunks)} Hindi chunks for title intro")
                    temp_dir = os.path.join(output_dir, "temp_chunks")
                    Path(temp_dir).mkdir(exist_ok=True)

                    chunk_files = []
                    for j, chunk in enumerate(hindi_chunks):
                        chunk_path = os.path.join(temp_dir, f"00_title_introduction_chunk_{j:03d}.wav")
                        try:
                            audio_bytes = tts_client.synthesize_text(text=chunk, target_language='hi-IN', voice=voice)
                            if audio_bytes and len(audio_bytes) > 0:
                                with open(chunk_path, 'wb') as f: f.write(audio_bytes)
                                chunk_files.append(chunk_path)
                        except Exception as e:
                             print(f"  ⨯ Error generating audio for chunk {j+1}: {e}")

                    if chunk_files:
                        list_file = os.path.join(temp_dir, "00_title_introduction_list.txt")
                        with open(list_file, 'w') as f:
                            for chunk_file in chunk_files: f.write(f"file '{os.path.abspath(chunk_file)}'\n")
                        try:
                            subprocess.run(['ffmpeg', '-y', '-f', 'concat', '-safe', '0', '-i', list_file, '-c', 'copy', title_audio_path], check=True, capture_output=True)
                            audio_files.append(title_audio_path)
                            successful_generations += 1
                            print(f"✓ Title Hindi audio: {title_audio_path}")
                        except subprocess.CalledProcessError:
                             if chunk_files:
                                 import shutil
                                 shutil.copy(chunk_files[0], title_audio_path)
                                 audio_files.append(title_audio_path)
                                 successful_generations += 1

        # Generate section audios
        section_order = ["Introduction", "Methodology", "Results", "Discussion", "Conclusion"]
        
        for i, section_name in enumerate(section_order, start=1):
            if section_name in sections_scripts:
                script_text = sections_scripts[section_name]
                if not script_text or not script_text.strip(): continue

                print(f"Generating Hindi {section_name} audio...")
                audio_path = os.path.join(output_dir, f"{i:02d}_{section_name.lower()}.wav")
                
                cleaned_text = script_text
                if cleaned_text:
                    if use_local_tts:
                        if generate_audio_local(cleaned_text, audio_path, language='hi'):
                            audio_files.append(audio_path)
                            successful_generations += 1
                            print(f"✓ {section_name} Hindi audio (Local): {audio_path}")
                    else:
                        # Original Sarvam Logic
                        hindi_chunks = chunk_hindi_text(cleaned_text)
                        print(f"Processing {len(hindi_chunks)} Hindi chunks for {section_name}")
                        temp_dir = os.path.join(output_dir, "temp_chunks")
                        Path(temp_dir).mkdir(exist_ok=True)
                        chunk_files = []
                        for j, chunk in enumerate(hindi_chunks):
                            chunk_path = os.path.join(temp_dir, f"{i:02d}_{section_name.lower()}_chunk_{j:03d}.wav")
                            try:
                                audio_bytes = tts_client.synthesize_text(text=chunk, target_language='hi-IN', voice=voice)
                                if audio_bytes and len(audio_bytes) > 0:
                                    with open(chunk_path, 'wb') as f: f.write(audio_bytes)
                                    chunk_files.append(chunk_path)
                            except Exception as e:
                                print(f"  ⨯ Error generating audio for chunk {j+1}: {e}")

                        if chunk_files:
                            list_file = os.path.join(temp_dir, f"{i:02d}_{section_name.lower()}_list.txt")
                            with open(list_file, 'w') as f:
                                for chunk_file in chunk_files: f.write(f"file '{os.path.abspath(chunk_file)}'\n")
                            try:
                                subprocess.run(['ffmpeg', '-y', '-f', 'concat', '-safe', '0', '-i', list_file, '-c', 'copy', audio_path], check=True, capture_output=True)
                                audio_files.append(audio_path)
                                successful_generations += 1
                                print(f"✓ {section_name} Hindi audio: {audio_path}")
                            except subprocess.CalledProcessError:
                                if chunk_files:
                                    import shutil
                                    shutil.copy(chunk_files[0], audio_path)
                                    audio_files.append(audio_path)
                                    successful_generations += 1

        if successful_generations == 0:
            raise ValueError("No Hindi audio files were generated successfully")

        print(f"✓ Generated {successful_generations} Hindi audio files")
        return {
            "audio_files": [Path(f).name for f in audio_files]
        }

    except Exception as e:
        print(f"Hindi audio generation error: {e}")
        raise


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
    """Generate audio files for any supported language"""
    
    if not is_language_supported(language):
        raise ValueError(f"Unsupported language: {language}")
    
    language_code = get_language_code(language)
    
    audio_files = []
    output_dir = f"temp/audio/{paper_id}"
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    use_local_tts = False
    tts_client = None
    voice = "vidya"

    if not sarvam_api_key or sarvam_api_key.strip() == "":
        print("Sarvam API key not found. Switching to Local TTS (pyttsx3).")
        use_local_tts = True
    else:
        voice = voice_selections.get(language, "vidya")
        if show_debug: print(f"Using voice for {language}: {voice}")

        try:
            tts_client = SarvamTTS(api_key=sarvam_api_key)
            if not tts_client.test_connection():
                 print("Failed to connect to Sarvam API. Switching to Local TTS.")
                 use_local_tts = True
            elif show_debug:
                print("✓ Connected to Sarvam TTS API")
        except Exception as e:
            print(f"TTS client initialization failed: {e}. Switching to Local TTS.")
            use_local_tts = True

    successful_generations = 0
    
    # ... Helper functions from original code ...
    def get_chunk_size_for_language(lang: str) -> int:
        complex_script_languages = ['hindi', 'bengali', 'marathi', 'nepali', 'gujarati']
        return 450 if lang.lower() in complex_script_languages else 500
    
    def chunk_text_by_language(text: str, language: str, max_chunk_length: int = None) -> List[str]:
        if max_chunk_length is None: max_chunk_length = get_chunk_size_for_language(language)
        complex_script_languages = ['hindi', 'bengali', 'marathi', 'nepali', 'gujarati']
        
        if language.lower() in complex_script_languages:
            if grapheme.length(text) <= max_chunk_length: return [text]
            sentences = re.split(r'(?<=[।॥.!?])\s+', text)
            chunks = []
            current_chunk = ""
            for sentence in sentences:
                sentence_length = grapheme.length(sentence)
                current_length = grapheme.length(current_chunk)
                if current_length + sentence_length + 1 > max_chunk_length:
                    if current_chunk: chunks.append(current_chunk.strip())
                    if sentence_length > max_chunk_length:
                        words = sentence.split()
                        temp_chunk = ""
                        for word in words:
                            word_length = grapheme.length(word)
                            temp_length = grapheme.length(temp_chunk)
                            if temp_length + word_length + 1 > max_chunk_length:
                                chunks.append(temp_chunk.strip())
                                temp_chunk = word + " "
                            else: temp_chunk += word + " "
                        if temp_chunk: current_chunk = temp_chunk
                    else: current_chunk = sentence + " "
                else: current_chunk += sentence + " "
            if current_chunk: chunks.append(current_chunk.strip())
            return chunks
        else:
            if len(text) <= max_chunk_length: return [text]
            sentences = re.split(r'(?<=[.!?])\s+', text)
            chunks = []
            current_chunk = ""
            for sentence in sentences:
                if len(current_chunk) + len(sentence) + 1 > max_chunk_length:
                    if current_chunk: chunks.append(current_chunk.strip())
                    if len(sentence) > max_chunk_length:
                        words = sentence.split()
                        temp_chunk = ""
                        for word in words:
                            if len(temp_chunk) + len(word) + 1 > max_chunk_length:
                                chunks.append(temp_chunk.strip())
                                temp_chunk = word + " "
                            else: temp_chunk += word + " "
                        if temp_chunk: current_chunk = temp_chunk
                    else: current_chunk = sentence + " "
                else: current_chunk += sentence + " "
            if current_chunk: chunks.append(current_chunk.strip())
            return chunks

    def generate_audio_from_chunks(chunks: List[str], language_code, base_filename: str) -> bool:
        temp_dir = os.path.join(output_dir, "temp_chunks")
        Path(temp_dir).mkdir(exist_ok=True)
        chunk_files = []
        for j, chunk in enumerate(chunks):
            chunk_path = os.path.join(temp_dir, f"{base_filename}_chunk_{j:03d}.wav")
            try:
                audio_bytes = tts_client.synthesize_text(text=chunk, target_language=language_code, voice=voice)
                if audio_bytes and len(audio_bytes) > 0:
                    with open(chunk_path, 'wb') as f: f.write(audio_bytes)
                    chunk_files.append(chunk_path)
            except Exception as e:
                if show_debug: print(f"  ⨯ Error generating audio for chunk {j+1}: {e}")
        
        if not chunk_files: return False
        final_path = os.path.join(output_dir, f"{base_filename}.wav")
        if len(chunk_files) == 1:
            import shutil
            shutil.copy(chunk_files[0], final_path)
        else:
            list_file = os.path.join(temp_dir, f"{base_filename}_list.txt")
            with open(list_file, 'w') as f:
                for chunk_file in chunk_files: f.write(f"file '{os.path.abspath(chunk_file)}'\n")
            try:
                subprocess.run(['ffmpeg', '-y', '-f', 'concat', '-safe', '0', '-i', list_file, '-c', 'copy', final_path], check=True, capture_output=True)
            except subprocess.CalledProcessError:
                import shutil
                shutil.copy(chunk_files[0], final_path)
        audio_files.append(final_path)
        if show_debug: print(f"✓ {language} audio: {final_path}")
        return True

    try:
        # Generate title audio
        if title_intro_script and title_intro_script.strip():
            if show_debug: print(f"Generating {language} title audio...")
            cleaned_text = title_intro_script
            if cleaned_text:
                if use_local_tts:
                    title_path = os.path.join(output_dir, "00_title_introduction.wav")
                    if generate_audio_local(cleaned_text, title_path, language=language):
                        audio_files.append(title_path)
                        successful_generations += 1
                else:
                    chunks = chunk_text_by_language(cleaned_text, language)
                    if generate_audio_from_chunks(chunks, language_code, "00_title_introduction"):
                        successful_generations += 1

        # Generate section audios
        section_order = ["Introduction", "Methodology", "Results", "Discussion", "Conclusion"]
        
        for i, section_name in enumerate(section_order, start=1):
            if section_name in sections_scripts:
                script_text = sections_scripts[section_name]
                if not script_text or not script_text.strip(): continue

                if show_debug: print(f"Generating {language} {section_name} audio...")
                cleaned_text = script_text
                if cleaned_text:
                    if use_local_tts:
                         audio_path = os.path.join(output_dir, f"{i:02d}_{section_name.lower()}.wav")
                         if generate_audio_local(cleaned_text, audio_path, language=language):
                            audio_files.append(audio_path)
                            successful_generations += 1
                    else:
                        chunks = chunk_text_by_language(cleaned_text, language)
                        if generate_audio_from_chunks(chunks, language_code, f"{i:02d}_{section_name.lower()}"):
                            successful_generations += 1

        if successful_generations == 0:
            raise ValueError(f"No {language} audio files were generated successfully")

        if show_debug:
            print(f"✓ Generated {successful_generations} {language} audio files")
        
        return {
            "audio_files": [Path(f).name for f in audio_files]
        }

    except Exception as e:
        print(f"{language} audio generation error: {e}")
        raise


def test_sarvam_sdk(api_key: str, voice: str = "meera"):
    """Test function for SDK validation"""
    try:
        tts_client = SarvamTTS(api_key=api_key)
        return tts_client.test_connection()
    except Exception as e:
        print(f"SDK test failed: {e}")
        return False
