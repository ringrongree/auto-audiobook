"""
Test script to demonstrate the new SFX detection process.
This shows how actions and possible_sounds are now extracted separately.
"""

import os
import sys

# Add the aabook module to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from aabook.llm_client import LLMClient
from aabook.speaker_identification import detect_sound_effects

def test_sfx_detection():
    """Test the new SFX detection with sample sentences."""
    
    # Initialize LLM client
    print("Initializing LLM client...")
    llm = LLMClient(model="gpt-4o-mini")
    
    # Test sentences
    test_sentences = [
        "He slammed the door and walked away quickly.",
        "She was thinking about the conversation while sipping her coffee.",
        "The glass shattered on the floor as footsteps echoed down the hallway.",
        "A frail-looking young man was sitting on a rusty bench.",
    ]
    
    print("\n" + "="*70)
    print("Testing New SFX Detection Process")
    print("="*70)
    
    for i, sentence in enumerate(test_sentences, 1):
        print(f"\n[Test {i}]")
        print(f"Sentence: {sentence}")
        print("-" * 70)
        
        # Detect SFX
        result = detect_sound_effects(sentence, llm)
        
        # Display results
        print(f"Actions found: {len(result['actions'])}")
        for action in result['actions']:
            print(f"  - {action}")
        
        print(f"\nSound events: {len(result['sound_events'])}")
        for event in result['sound_events']:
            sound = event.get('sound', 'N/A')
            trigger = event.get('trigger_phrase', 'N/A')
            print(f"  🔊 {sound}")
            print(f"     Trigger: \"{trigger}\"")
        
        if not result['sound_events']:
            print("  (No distinctive sounds detected)")
        
        print()
    
    print("="*70)
    print("✅ Test complete!")

if __name__ == "__main__":
    test_sfx_detection()

