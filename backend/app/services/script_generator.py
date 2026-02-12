import re
import unicodedata
import requests


def extract_paper_metadata(file_path):
    """Extract paper metadata from LaTeX or PDF text file."""
    metadata = {
        "title": "Research Paper",
        "authors": "Author",
        "date": "2024"
    }

    if file_path.endswith('.txt'):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            lines = content.split('\n')
            for line in lines[:10]:
                if line.strip():
                    metadata["title"] = line.strip()
                    break
            author_found = False
            for line in lines[1:20]:
                if not line.strip():
                    continue
                if re.search(r'\babstract\b|\bintroduction\b|\bsection\b', line.lower()):
                    break
                if not author_found and not line.startswith(('http', 'www', '@')):
                    if ',' in line or 'university' in line.lower() or 'department' in line.lower():
                        metadata["authors"] = line.strip()
                        author_found = True
        except Exception as e:
            print(f"Error extracting metadata from text file: {e}")
        return metadata

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        title_match = re.search(r'\\title\{([^}]+)\}', content)
        if title_match:
            metadata["title"] = title_match.group(1).strip()
        author_match = re.search(r'\\author\{([^}]+)\}', content)
        if author_match:
            metadata["authors"] = author_match.group(1).strip()
        date_match = re.search(r'\\date\{([^}]+)\}', content)
        if date_match:
            metadata["date"] = date_match.group(1).strip()
    except Exception as e:
        print(f"Error extracting metadata from LaTeX file: {e}")

    return metadata


def extract_text_from_file(file_path):
    """Extract clean text from LaTeX or text file."""
    if file_path.endswith('.txt'):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"Error extracting text from text file: {e}")
            return ""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        content = re.sub(r'%.*?\n', '\n', content)
        content = re.sub(r'\\[a-zA-Z]+\*?(\[[^\]]*\])?(\{[^}]*\})*', ' ', content)
        content = re.sub(r'\{[^}]*\}', ' ', content)
        content = re.sub(r'\s+', ' ', content)
        return content.strip()
    except Exception as e:
        print(f"Error extracting text from LaTeX file: {e}")
        return ""


def clean_text(text):
    """Clean unicode characters from text."""
    text = text.replace('“', '"').replace('”', '"').replace('’', "'").replace('‘', "'")
    text = text.replace('–', '-').replace('—', '-')
    text = unicodedata.normalize('NFKD', text)
    return text


# --- Local Ollama Generation Helpers ---
def generate_with_ollama(prompt, config):
    """Generate content using Ollama API."""
    url = config.get("ollama_url", "http://localhost:11434")
    model = config.get("ollama_model", "llama3")

    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.7,
            "num_ctx": 4096
        }
    }

    response = requests.post(f"{url.rstrip('/')}/api/generate", json=payload, timeout=120)
    response.raise_for_status()
    return response.json().get("response", "")


def generate_full_script_with_ollama(api_config, input_text):
    """Generate presentation script using local Ollama."""

    prompt = f"""
Create a script for a 3-5 minute educational video based on this research paper.
STRUCTURE:
Create scripts for exactly these 5 sections:
**Introduction**
**Methodology**
**Results**
**Discussion**
**Conclusion**
Important rules:
1. Each section MUST start with its exact heading as shown above
2. Keep content clear and focused - about 2-3 paragraphs per section
3. Focus on explaining the research in simple terms
4. Avoid technical jargon where possible
5. Make it engaging for a general audience
6. DO NOT include any video/animation directions or [Narrator:] tags
7. Make sure that you do not use contracted words, for example: we'll, we're.
Here’s the paper text to base the script on:
Research Paper Content:
{input_text}

Please generate the complete presentation script with clear section headers:
"""

    return generate_with_ollama(prompt, api_config)


def generate_bullet_points_with_ollama(api_config, section_text):
    """Generate bullet points using local Ollama."""

    prompt = f"""
Convert this presentation script into 3-5 clear, concise bullet points for a slide.
REQUIREMENTS:
- Each bullet point should be one clear, complete thought
- Use action-oriented language when possible
- Make bullet points parallel in structure
- Avoid sub-bullets or nested items
- Keep each bullet to 1-2 lines maximum
- Use specific, concrete language rather than vague terms

Script text to convert:
{section_text}

Generate exactly 3-5 bullet points in this format:
• Point 1
• Point 2
• Point 3
"""

    try:
        response_text = generate_with_ollama(prompt, api_config)
        bullets = []
        for line in response_text.split('\n'):
            line = line.strip()
            if line and (line.startswith('•') or line.startswith('-') or line.startswith('*')):
                bullet = re.sub(r'^[•\-*·]\s*', '', line).strip()
                if bullet:
                    bullets.append(bullet)

        if not bullets and section_text:
            sentences = [s.strip() for s in section_text.split('.') if s.strip()]
            bullets = sentences[:4]

        if not bullets:
            bullets = ["Key information from this section"]
        return bullets[:5]
    except Exception as e:
        print(f"Error generating bullet points: {e}")
        return ["Key information from this section"]


def generate_all_bullet_points_with_ollama(api_config, sections_scripts):
    """Generate bullet points for all sections using local Ollama."""

    sections_text = ""
    for section_name, script_text in sections_scripts.items():
        if script_text and script_text.strip():
            sections_text += f"\n## {section_name}\n{script_text}\n"

    prompt = f"""You are a research summarization assistant.
TASK: For each section provided, generate 3–5 concise, informative bullet points.
INPUT: {sections_text}
OUTPUT FORMAT (strictly follow this layout):
[SECTION_NAME]
• Bullet point 1
...
[NEXT_SECTION_NAME]
• Bullet point 1
...
"""

    try:
        bullet_text = generate_with_ollama(prompt, api_config)
        sections_bullets = {}
        current_section = None

        for line in bullet_text.split('\n'):
            line = line.strip()
            if not line:
                continue

            section_name = None
            if line.startswith('[') and line.endswith(']'):
                section_name = line[1:-1].strip()
            elif line.startswith('**') and line.endswith('**'):
                section_name = line[2:-2].strip()
            elif line.startswith('##'):
                section_name = line[2:].strip()

            if section_name:
                for standard_name in sections_scripts.keys():
                    if standard_name.lower() in section_name.lower():
                        current_section = standard_name
                        sections_bullets[current_section] = []
                        break
            elif current_section and (line.startswith('•') or line.startswith('-')):
                bullet = re.sub(r'^[•\-*·]\s*', '', line).strip()
                if bullet:
                    sections_bullets[current_section].append(bullet)

        for section_name in sections_scripts.keys():
            if section_name not in sections_bullets or not sections_bullets[section_name]:
                sections_bullets[section_name] = ["Key information from this section"]

        return sections_bullets
    except Exception as e:
        print(f"Error generating all bullets: {e}")
        return {k: ["Key info"] for k in sections_scripts}


# Backward-compatible aliases for existing imports.
def generate_full_script_with_gemini(api_config, input_text):
    return generate_full_script_with_ollama(api_config, input_text)


def generate_bullet_points_with_gemini(api_config, section_text):
    return generate_bullet_points_with_ollama(api_config, section_text)


def generate_all_bullet_points_with_gemini(api_config, sections_scripts):
    return generate_all_bullet_points_with_ollama(api_config, sections_scripts)


def split_script_into_sections(full_script):
    sections = {
        "Introduction": "", "Methodology": "", "Results": "", "Discussion": "", "Conclusion": ""
    }
    current_section = None
    for line in full_script.split('\n'):
        line = line.strip()
        if not line:
            continue
        for section_name in sections.keys():
            if section_name.lower() in line.lower() and (line.startswith('#') or line.startswith('**') or line.isupper() or ':' in line):
                current_section = section_name
                break
        else:
            if current_section:
                sections[current_section] += line + " "

    for section in sections:
        sections[section] = sections[section].strip()
        if not sections[section]:
            sections[section] = f"Content for {section} needs to be added."
    return sections


def clean_script_for_tts_and_video(script_text):
    script_text = re.sub(r'\*\*([^*]+)\*\*', r'\1', script_text)
    script_text = re.sub(r'\*([^*]+)\*', r'\1', script_text)
    script_text = re.sub(r'#+\s*', '', script_text)
    script_text = re.sub(r'[^\w\s.,!?;:\-()"]', ' ', script_text)
    return re.sub(r'\s+', ' ', script_text).strip()


def generate_title_introduction(title, authors, date):
    if ',' in authors:
        first_author = authors.split(',')[0].strip()
        authors = f"{first_author} et al."
    return f"""
Welcome to this presentation on "{title}".
This research was conducted by {authors} and published in {date}.
Today, we'll explore the key findings and contributions of this important work.
Let's begin by understanding the problem this research addresses.
"""
