"""
Simple test to demonstrate the sentence formatting logic without dependencies.
This is a standalone version of the format_sentence_with_annotations function.
"""

from typing import List, Dict


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


def test_formatting():
    """Test the sentence formatting with various examples."""
    
    print("="*80)
    print("Testing Sentence Formatting with Inline Annotations")
    print("="*80)
    
    # Test 1: Sentence with one sound effect
    print("\n[Test 1: Single sound effect]")
    sentence1 = "He slammed the door and walked away quickly."
    sound_events1 = [
        {"sound": "door slamming", "trigger_phrase": "slammed the door"}
    ]
    formatted1 = format_sentence_with_annotations(sentence1, "angry", "aggressive", sound_events1)
    print(f"Original:  {sentence1}")
    print(f"Formatted: {formatted1}")
    
    # Test 2: Sentence with multiple sound effects
    print("\n[Test 2: Multiple sound effects]")
    sentence2 = "The glass shattered on the floor as footsteps echoed down the hallway."
    sound_events2 = [
        {"sound": "glass breaking", "trigger_phrase": "glass shattered"},
        {"sound": "footsteps echoing", "trigger_phrase": "footsteps echoed"}
    ]
    formatted2 = format_sentence_with_annotations(sentence2, "fearful", "dramatic", sound_events2)
    print(f"Original:  {sentence2}")
    print(f"Formatted: {formatted2}")
    
    # Test 3: Sentence with no sound effects
    print("\n[Test 3: No sound effects]")
    sentence3 = "She was thinking about the conversation while sipping her coffee."
    sound_events3 = []
    formatted3 = format_sentence_with_annotations(sentence3, "anxious", "matter-of-fact", sound_events3)
    print(f"Original:  {sentence3}")
    print(f"Formatted: {formatted3}")
    
    # Test 4: Narration with sound
    print("\n[Test 4: Narrative with sound]")
    sentence4 = "A frail-looking young man sat on a rusty bench that creaked under his weight."
    sound_events4 = [
        {"sound": "metal creaking", "trigger_phrase": "creaked"}
    ]
    formatted4 = format_sentence_with_annotations(sentence4, "sad", "descriptive", sound_events4)
    print(f"Original:  {sentence4}")
    print(f"Formatted: {formatted4}")
    
    # Test 5: Multiple sounds in sequence
    print("\n[Test 5: Multiple sequential sounds]")
    sentence5 = "She knocked on the door, heard a click, and pushed it open with a creak."
    sound_events5 = [
        {"sound": "knocking", "trigger_phrase": "knocked on the door"},
        {"sound": "lock clicking", "trigger_phrase": "click"},
        {"sound": "door creaking", "trigger_phrase": "creak"}
    ]
    formatted5 = format_sentence_with_annotations(sentence5, "curious", "cautious", sound_events5)
    print(f"Original:  {sentence5}")
    print(f"Formatted: {formatted5}")
    
    print("\n" + "="*80)
    print("✅ Formatting test complete!")
    print("\nFormat explanation:")
    print("  [emotion, tone] text text [sound effect] text text")
    print("\nThe emotion/tone always appears at the start.")
    print("Sound effects are inserted right after their trigger phrases.")
    print("="*80)


if __name__ == "__main__":
    test_formatting()

