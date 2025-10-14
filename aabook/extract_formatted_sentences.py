"""
Extract formatted sentences from processed JSON files and save to text file.

This script takes a JSON file (like chapter_1_full_stitched.json) and extracts
all the formatted_sentence values, writing them to a .txt file with the same base name.

Usage:
    python extract_formatted_sentences.py <input_json_file>
    
Example:
    python extract_formatted_sentences.py novel_2/chapter_1_full_stitched.json
    Output: novel_2/chapter_1_full_stitched.txt
"""

import json
import sys
import os
from pathlib import Path


def extract_formatted_sentences(json_path: str) -> str:
    """
    Extract all formatted sentences from a processed chapter JSON file.
    
    Args:
        json_path: Path to the input JSON file
        
    Returns:
        Path to the output text file
    """
    # Read the JSON file
    print(f"Reading {json_path}...")
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Get sentences dictionary
    sentences = data.get('sentences', {})
    
    if not sentences:
        print("Warning: No sentences found in JSON file.")
        return None
    
    # Sort sentence IDs to maintain order (sentence_0001, sentence_0002, etc.)
    sentence_ids = sorted(sentences.keys())
    
    # Extract formatted sentences
    formatted_sentences = []
    missing_count = 0
    
    for sentence_id in sentence_ids:
        sentence_data = sentences[sentence_id]
        formatted = sentence_data.get('formatted_sentence')
        
        if formatted:
            formatted_sentences.append(formatted)
        else:
            # Fallback to original sentence if formatted_sentence is missing
            original = sentence_data.get('sentence', '')
            formatted_sentences.append(original)
            missing_count += 1
    
    print(f"Extracted {len(formatted_sentences)} formatted sentences")
    if missing_count > 0:
        print(f"Warning: {missing_count} sentences missing formatted_sentence field (used original instead)")
    
    # Create output filename (same name but .txt extension)
    input_path = Path(json_path)
    output_path = input_path.with_suffix('.txt')
    
    # Write to text file
    print(f"Writing to {output_path}...")
    with open(output_path, 'w', encoding='utf-8') as f:
        for sentence in formatted_sentences:
            f.write(sentence + '\n')
    
    print(f"Successfully created {output_path}")
    print(f"   Total lines: {len(formatted_sentences)}")
    
    return str(output_path)


def main():
    """Main function to handle command-line usage."""
    if len(sys.argv) < 2:
        print("Usage: python extract_formatted_sentences.py <input_json_file>")
        print("\nExample:")
        print("  python extract_formatted_sentences.py novel_2/chapter_1_full_stitched.json")
        return 1
    
    json_path = sys.argv[1]
    
    # Check if file exists
    if not os.path.exists(json_path):
        print(f"Error: File not found: {json_path}")
        return 2
    
    # Check if it's a JSON file
    if not json_path.endswith('.json'):
        print(f"Warning: File doesn't have .json extension: {json_path}")
        proceed = input("Continue anyway? (y/N): ").strip().lower()
        if proceed not in ['y', 'yes']:
            return 0
    
    try:
        output_path = extract_formatted_sentences(json_path)
        if output_path:
            return 0
        else:
            return 3
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON file: {e}")
        return 4
    except Exception as e:
        print(f"Error: {e}")
        return 5


if __name__ == "__main__":
    sys.exit(main())

