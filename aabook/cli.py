import json
import os
import sys
import time
from pathlib import Path
from typing import Optional

# Handle both direct execution and module execution
if __name__ == "__main__":
    # When run directly, add the parent directory to path for absolute imports
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
    
    from llm_client import LLMClient
    from speaker_identification import (
        extract_present_characters,
        label_lines_with_speakers,
    )
else:
    # When run as module, use relative imports
    from .llm_client import LLMClient
    from .speaker_identification import (
        extract_present_characters,
        label_lines_with_speakers,
    )


def select_input_file() -> Optional[str]:
    """Get input file path from user."""
    print("Please provide the path to your chapter text file:")
    
    while True:
        file_path = input("\nInput file path: ").strip()
        if not file_path:
            print("No file path provided. Exiting.")
            return None
        
        # Expand relative paths
        if not os.path.isabs(file_path):
            file_path = os.path.abspath(file_path)
        
        if os.path.exists(file_path):
            return file_path
        else:
            print(f"File not found: {file_path}")
            retry = input("Try again? (y/N): ").strip().lower()
            if retry not in ['y', 'yes']:
                return None


def select_output_location() -> Optional[str]:
    """Get output directory and filename from user."""
    print("\nPlease provide output details:")
    
    while True:
        output_dir = input("\nOutput directory: ").strip()
        if not output_dir:
            print("No output directory provided. Exiting.")
            return None
        
        # Expand relative paths
        if not os.path.isabs(output_dir):
            output_dir = os.path.abspath(output_dir)
        
        filename = input("Output filename (e.g., chapter_labeled.json): ").strip()
        if not filename:
            filename = "chapter_labeled.json"
        
        output_path = os.path.join(output_dir, filename)
        
        # Check if directory exists or can be created
        try:
            os.makedirs(output_dir, exist_ok=True)
            return output_path
        except Exception as e:
            print(f"Error creating directory {output_dir}: {e}")
            retry = input("Try again? (y/N): ").strip().lower()
            if retry not in ['y', 'yes']:
                return None


def get_model_choice() -> str:
    """Get model choice from user."""
    print("\nAvailable models:")
    print("1. gpt-4o-mini (fastest, cheapest)")
    print("2. gpt-4o (more accurate)")
    print("3. gpt-3.5-turbo (legacy)")
    
    while True:
        choice = input("\nSelect model (1-3, default=1): ").strip()
        if not choice:
            return "gpt-4o-mini"
        if choice == "1":
            return "gpt-4o-mini"
        elif choice == "2":
            return "gpt-4o"
        elif choice == "3":
            return "gpt-3.5-turbo"
        else:
            print("Invalid choice. Please enter 1, 2, or 3.")


def main() -> int:
    print("=== Auto-Audiobook Speaker Identification ===")
    print("This tool will identify speakers in your chapter text.\n")
    
    # Select input file
    print("Step 1: Select input file")
    input_file = select_input_file()
    if not input_file:
        print("No input file selected. Exiting.")
        return 1
    
    if not os.path.exists(input_file):
        print(f"Input file not found: {input_file}")
        return 2
    
    print(f"Selected input: {input_file}")
    
    # Select output location
    print("\nStep 2: Select output location")
    output_file = select_output_location()
    if not output_file:
        print("No output location selected. Exiting.")
        return 1
    
    print(f"Output will be saved to: {output_file}")
    
    # Get model choice
    model = get_model_choice()
    print(f"Using model: {model}")
    
    # Confirm before processing
    print(f"\nReady to process:")
    print(f"  Input: {input_file}")
    print(f"  Output: {output_file}")
    print(f"  Model: {model}")
    
    confirm = input("\nProceed? (y/N): ").strip().lower()
    if confirm not in ['y', 'yes']:
        print("Cancelled.")
        return 0
    
    # Process the file
    print(f"\n[1/5] Loading input: {input_file}")
    with open(input_file, "r", encoding="utf-8") as f:
        chapter_text = f.read()
    num_chars = len(chapter_text)
    num_lines = chapter_text.count("\n") + (1 if chapter_text else 0)
    print(f"      Loaded {num_chars} characters across {num_lines} lines.")

    print(f"[2/5] Initializing LLM client (model: {model})")
    t0 = time.perf_counter()
    try:
        llm = LLMClient(model=model)
        print(f"      LLM ready in {time.perf_counter() - t0:.2f}s")
    except Exception as e:
        print(f"      Error initializing LLM: {e}")
        print("      Make sure your OPENAI_API_KEY is set in .env file")
        return 3

    print("[3/5] Extracting present characters...")
    t1 = time.perf_counter()
    try:
        characters = extract_present_characters(chapter_text, llm)
        dt1 = time.perf_counter() - t1
        preview = ", ".join(characters[:10]) + ("..." if len(characters) > 10 else "")
        print(f"      Found {len(characters)} characters: {preview} (in {dt1:.2f}s)")
    except Exception as e:
        print(f"      Error extracting characters: {e}")
        return 4

    print("[4/5] Labeling lines with speakers...")
    t2 = time.perf_counter()
    try:
        lines = label_lines_with_speakers(chapter_text, characters, llm)
        dt2 = time.perf_counter() - t2
        print(f"      Labeled {len(lines)} lines (in {dt2:.2f}s)")
    except Exception as e:
        print(f"      Error labeling lines: {e}")
        return 5

    print("[5/7] Detecting emotions and tones...")
    t3 = time.perf_counter()
    try:
        # Process each line to add emotion and tone detection
        processed_sentences = {}
        for i, line in enumerate(lines):
            sentence_id = f"sentence_{i+1:04d}"
            text = line["text"]
            speaker = line["speaker"]
            
            # Detect emotion and tone
            from speaker_identification import detect_emotion_and_tone, detect_sound_effects
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
        dt3 = time.perf_counter() - t3
        print(f"      Processed {len(processed_sentences)} sentences (in {dt3:.2f}s)")
    except Exception as e:
        print(f"      Error detecting emotions, tones, and sound effects: {e}")
        return 6

    result = {"characters": characters, "sentences": processed_sentences}

    print("[7/7] Writing output")
    try:
        os.makedirs(os.path.dirname(output_file) or ".", exist_ok=True)
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"      Wrote JSON to: {output_file}")
    except Exception as e:
        print(f"      Error writing output: {e}")
        return 7
    
    # Count sentences with SFX
    sfx_count = sum(1 for data in processed_sentences.values() if data["sfx_info"]["has_sfx"])
    
    print("\n✅ Processing complete!")
    print(f"   Characters found: {len(characters)}")
    print(f"   Sentences processed: {len(processed_sentences)}")
    print(f"   Sentences with sound effects: {sfx_count}")
    print(f"   Output saved: {output_file}")
    
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
