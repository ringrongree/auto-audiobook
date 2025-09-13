from typing import Dict, List, Any

from .llm_client import LLMClient


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

LABEL_USER_PROMPT_TEMPLATE = (
    "CHARACTERS: {characters}\n\n"
    "CHAPTER:\n"  # text appended
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


def process_chapter(
    chapter_text: str,
    *,
    model: str = "gpt-4o-mini",
) -> Dict[str, Any]:
    llm = LLMClient(model=model)
    characters = extract_present_characters(chapter_text, llm)
    lines = label_lines_with_speakers(chapter_text, characters, llm)
    return {"characters": characters, "lines": lines}
