"""
Test script to demonstrate the new sentence formatting with inline annotations.
"""

import os
import sys

# Add the aabook module to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from aabook.speaker_identification import format_sentence_with_annotations

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
    
    print("\n" + "="*80)
    print("✅ Formatting test complete!")
    print("\nFormat explanation:")
    print("  [emotion, tone] text text [sound effect] text text")
    print("\nThe emotion/tone always appears at the start.")
    print("Sound effects are inserted right after their trigger phrases.")
    print("="*80)

if __name__ == "__main__":
    test_formatting()

