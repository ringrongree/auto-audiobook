from typing import Dict, List, Any
import sys
import os

# Handle both direct execution and module execution
# Check if we're being imported by a direct execution of cli.py
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir in sys.path:
    # We're being imported by direct execution, use absolute imports
    from llm_client import LLMClient
else:
    # Normal module execution, use relative imports
    try:
        from .llm_client import LLMClient
    except ImportError:
        # Fallback to absolute import if relative fails
        from llm_client import LLMClient


CHARACTER_SYSTEM_PROMPT = (
    "You are a precise literary analysis assistant. Given a chapter's raw text, "
    "identify the distinct characters who are present and could plausibly speak.\n"
    "Rules:\n"
    "- Return a JSON object: {\"characters\": [string]} only.\n"
    "- Use canonical names (e.g., \"Mr. Darcy\" not \"Darcy\" if both appear).\n"
    "- Include \"Narrator\" as a special non-character for descriptive narration.\n"
    "- Exclude generic groups (e.g., \"crowd\", \"villagers\") unless named/recurring.\n"
    "- Limit to the set present within the provided text (do not infer outside cast).\n"
    "- Cap list at 20 names."
)

CHARACTER_USER_PROMPT_TEMPLATE = (
    "Return characters present in the following chapter text.\n\n"
    "CHAPTER:\n"  # text appended
)

LABEL_SYSTEM_PROMPT = (
    "You are a dialogue attribution assistant.\n"
    "Given a chapter's raw text and a list of present characters, segment the text into an ordered array of lines.\n"
    "Each line should be either spoken dialogue attributed to a specific character or narrator text attributed to \"Narrator\".\n"
    "Rules:\n"
    "- Return JSON only: {\"lines\": [{\"speaker\": string, \"text\": string}]}.\n"
    "- Preserve the original order of the text.\n"
    "- Preserve punctuation and wording for each line as it appears in the text.\n"
    "- Only use speaker names from the provided character list, plus \"Narrator\".\n"
    "- Prefer \"Narrator\" for exposition, descriptions, or unidentified speech.\n"
    "- If a block contains multiple speakers, split into multiple lines.\n"
    "- If the text uses quotation marks or dashes to denote dialogue, use those cues.\n"
    "- Avoid adding inferred content that does not appear in the text."
)

EMOTION_SYSTEM_PROMPT = (
    "You are an emotion detection assistant.\n"
    "Given a piece of text and its speaker, analyze the emotional content and tone.\n"
    "Rules:\n"
    "- Return JSON only: {\"emotion\": string, \"tone\": string}.\n"
    "- For emotion, choose from: neutral, happy, sad, angry, fearful, surprised, disgusted, excited, anxious, calm, frustrated, hopeful, disappointed, confused, determined, suspicious, relieved, guilty, proud, ashamed, jealous, grateful, lonely, content, overwhelmed, bored, curious, embarrassed, confident, vulnerable.\n"
    "- For tone, choose from: formal, informal, casual, serious, playful, sarcastic, sincere, ironic, dramatic, matter-of-fact, urgent, gentle, harsh, encouraging, critical, supportive, condescending, respectful, disrespectful, friendly, hostile, warm, cold, enthusiastic, indifferent, optimistic, pessimistic, confident, uncertain, authoritative, submissive, assertive, passive, aggressive, defensive, apologetic, accusatory, questioning, declarative, exclamatory, narrative, descriptive, persuasive, informative.\n"
    "- Consider the context, word choice, punctuation, and speaker characteristics.\n"
    "- For narrator text, focus on the emotional atmosphere being described.\n"
    "- For dialogue, consider both the literal meaning and implied emotional undertones."
)

LABEL_USER_PROMPT_TEMPLATE = (
    "CHARACTERS: {characters}\n\n"
    "CHAPTER:\n"  # text appended
)

EMOTION_USER_PROMPT_TEMPLATE = (
    "SPEAKER: {speaker}\n"
    "TEXT: {text}\n\n"
    "Analyze the emotion and tone of this text."
)

SFX_SYSTEM_PROMPT = (
    "You are a sound effects detection assistant for audiobook production.\n"
    "Given a piece of text, identify if there are any actions that would produce sounds and describe the sound effect needed.\n"
    "Rules:\n"
    "- Return JSON only: {\"has_sfx\": boolean, \"sfx_description\": string}.\n"
    "- Set has_sfx to true only if there are clear actions that would produce audible sounds.\n"
    "- For sfx_description, provide a concise description of the sound effect (e.g., \"glass breaking\", \"footsteps on gravel\", \"door slamming\", \"water splashing\").\n"
    "- Focus on physical actions, movements, impacts, or environmental sounds.\n"
    "- Ignore internal thoughts, emotions, or non-audible actions.\n"
    "- If no clear sound-producing action is present, set has_sfx to false and sfx_description to empty string.\n"
    "- Be specific about the type of sound (e.g., \"metal clanging\" not just \"clanging\").\n"
    "- Consider the context and objects involved in the action."
)

SFX_USER_PROMPT_TEMPLATE = (
    "TEXT: {text}\n\n"
    "Identify any sound effects needed for this text."
)


def extract_present_characters(chapter_text: str, llm: LLMClient) -> List[str]:
    result = llm.chat_json(
        system_prompt=CHARACTER_SYSTEM_PROMPT,
        user_prompt=CHARACTER_USER_PROMPT_TEMPLATE + chapter_text,
        temperature=0.1,
        max_tokens=700,
    )
    characters = result.get("characters", [])
    # Ensure Narrator is included
    if "Narrator" not in characters:
        characters.append("Narrator")
    return characters


def label_lines_with_speakers(
    chapter_text: str,
    characters: List[str],
    llm: LLMClient,
) -> List[Dict[str, str]]:
    user_prompt = LABEL_USER_PROMPT_TEMPLATE.format(characters=characters) + chapter_text
    result = llm.chat_json(
        system_prompt=LABEL_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        temperature=0.2,
        max_tokens=4000,
    )
    lines = result.get("lines", [])
    # Normalize and filter
    normalized: List[Dict[str, str]] = []
    allowed = set(characters) | {"Narrator"}
    for item in lines:
        text = (item.get("text") or "").strip()
        speaker = (item.get("speaker") or "Narrator").strip()
        if not text:
            continue
        if speaker not in allowed:
            speaker = "Narrator"
        normalized.append({"speaker": speaker, "text": text})
    return normalized


def detect_emotion_and_tone(
    text: str,
    speaker: str,
    llm: LLMClient,
) -> Dict[str, str]:
    """Detect emotion and tone for a given text and speaker."""
    user_prompt = EMOTION_USER_PROMPT_TEMPLATE.format(speaker=speaker, text=text)
    result = llm.chat_json(
        system_prompt=EMOTION_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        temperature=0.3,
        max_tokens=200,
    )
    return {
        "emotion": result.get("emotion", "neutral"),
        "tone": result.get("tone", "neutral")
    }


def detect_sound_effects(
    text: str,
    llm: LLMClient,
) -> Dict[str, Any]:
    """Detect sound effects needed for a given text."""
    user_prompt = SFX_USER_PROMPT_TEMPLATE.format(text=text)
    result = llm.chat_json(
        system_prompt=SFX_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        temperature=0.2,
        max_tokens=150,
    )
    return {
        "has_sfx": result.get("has_sfx", False),
        "sfx_description": result.get("sfx_description", "")
    }


def process_chapter(
    chapter_text: str,
    *,
    model: str = "gpt-4o-mini",
) -> Dict[str, Any]:
    llm = LLMClient(model=model)
    characters = extract_present_characters(chapter_text, llm)
    lines = label_lines_with_speakers(chapter_text, characters, llm)
    
    # Process each line to add emotion, tone, and SFX detection
    processed_sentences = {}
    for i, line in enumerate(lines):
        sentence_id = f"sentence_{i+1:04d}"
        text = line["text"]
        speaker = line["speaker"]
        
        # Detect emotion and tone
        emotion_data = detect_emotion_and_tone(text, speaker, llm)
        
        # Detect sound effects
        sfx_data = detect_sound_effects(text, llm)
        
        processed_sentences[sentence_id] = {
            "sentence": text,
            "speaker_info": {
                "speaker": speaker,
                "emotion": emotion_data["emotion"],
                "tone": emotion_data["tone"]
            },
            "sfx_info": {
                "has_sfx": sfx_data["has_sfx"],
                "sfx_description": sfx_data["sfx_description"]
            }
        }
    
    return {
        "characters": characters,
        "sentences": processed_sentences
    }
