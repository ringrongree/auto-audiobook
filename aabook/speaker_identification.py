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
    "Given a piece of text, extract ALL actions that occur in the sentence, describe each action, and identify any sound effects.\n"
    "Rules:\n"
    "- Return JSON only: {\"actions\": [string], \"action_description\": [string], \"sound_events\": [{\"sound\": string, \"trigger_phrase\": string}]}.\n"
    "- In 'actions', list ALL actions that occur in the text, whether they produce sound or not (e.g., \"sitting\", \"walking\", \"thinking\", \"breaking glass\", \"opening door\", \"typing on a keyboard\", \"savouring tea\", \"enjoying dinner\").\n"
    "- In 'action_description', provide a descriptive phrase for EACH action listed in 'actions'. Each description should be a clear verb-noun phrase (e.g., \"person sitting on bench\", \"glass breaking on floor\", \"door opening slowly\"). The number of action descriptions must match the number of actions.\n"
    "- In 'sound_events', try to match a sound effects to each action_description. This should exclude onomatopoeias.\n"
    "- Each sound_event should have:\n"
    "  - 'sound': a specific description of the sound effect (e.g., \"glass breaking\", \"footsteps on gravel\", \"door creaking open\")\n"
    "  - 'trigger_phrase': the exact phrase from the text where this sound occurs (e.g., \"slammed the door\", \"footsteps echoed\", \"glass shattered\")\n"
    "- Focus on physical actions, movements, impacts, or environmental sounds that have audio characteristics.\n"
    "- Ignore internal thoughts and emotions in sound_events (but still list them in actions if they're actions).\n"
    "- Consider the context and objects involved when describing sounds.\n"
    "- The trigger_phrase should be a substring of the original text that clearly indicates where the sound occurs.\n"
    "- ALWAYS provide action_description for every action, even if there are no sound_events."
)

SFX_USER_PROMPT_TEMPLATE = (
    "TEXT: {text}\n\n"
    "Extract all actions from this text, provide descriptive phrases for each action, and identify any sound effects that occur."
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
    """Detect actions and their associated sound effects for a given text."""
    user_prompt = SFX_USER_PROMPT_TEMPLATE.format(text=text)
    result = llm.chat_json(
        system_prompt=SFX_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        temperature=0.2,
        max_tokens=400,
    )
    return {
        "actions": result.get("actions", []),
        "action_description": result.get("action_description", []),
        "sound_events": result.get("sound_events", [])
    }


def format_sentence_with_annotations(
    sentence: str,
    emotion: str,
    tone: str,
    sound_events: List[Dict[str, str]],
) -> str:
    """
    Format a sentence with inline emotion/tone and sound effect annotations.
    
    Format: [emotion, tone] word word [sound] word word
    """
    # Start with emotion and tone annotation
    formatted = f"[{emotion}, {tone}] {sentence}"
    
    # Insert sound effects at their trigger points
    if sound_events:
        # Sort sound events by their position in the sentence (last to first to preserve indices)
        events_with_pos = []
        for event in sound_events:
            trigger = event.get("trigger_phrase", "")
            sound = event.get("sound", "")
            if trigger and sound:
                # Find position of trigger phrase in sentence (case-insensitive)
                pos = sentence.lower().find(trigger.lower())
                if pos != -1:
                    # Calculate the end position of the trigger phrase
                    end_pos = pos + len(trigger)
                    events_with_pos.append((end_pos, sound, trigger))
        
        # Sort by position (descending) to insert from end to start
        events_with_pos.sort(reverse=True, key=lambda x: x[0])
        
        # Insert sound annotations after trigger phrases
        result = sentence
        for end_pos, sound, trigger in events_with_pos:
            result = result[:end_pos] + f" [{sound}]" + result[end_pos:]
        
        formatted = f"[{emotion}, {tone}] {result}"
    
    return formatted


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
        
        # Format sentence with inline annotations
        formatted_sentence = format_sentence_with_annotations(
            text,
            emotion_data["emotion"],
            emotion_data["tone"],
            sfx_data["sound_events"]
        )
        
        processed_sentences[sentence_id] = {
            "sentence": text,
            "formatted_sentence": formatted_sentence,
            "speaker_info": {
                "speaker": speaker,
                "emotion": emotion_data["emotion"],
                "tone": emotion_data["tone"]
            },
            "sfx_info": {
                "actions": sfx_data["actions"],
                "action_description": sfx_data["action_description"],
                "sound_events": sfx_data["sound_events"]
            }
        }
    
    return {
        "characters": characters,
        "sentences": processed_sentences
    }
