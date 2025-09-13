import argparse
import json
import os
import sys
import time
from typing import Optional

from .llm_client import LLMClient
from .speaker_identification import (
    extract_present_characters,
    label_lines_with_speakers,
)


def parse_args(argv: Optional[list] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Identify speakers and narrator lines for a chapter using an LLM.",
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Path to a text file containing the chapter.",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Optional path to write JSON output. Defaults to stdout.",
    )
    parser.add_argument(
        "--model",
        default="gpt-4o-mini",
        help="OpenAI model to use (default: gpt-4o-mini)",
    )
    return parser.parse_args(argv)


def main(argv: Optional[list] = None) -> int:
    args = parse_args(argv)

    if not os.path.exists(args.input):
        print(f"Input file not found: {args.input}", file=sys.stderr)
        return 2

    print(f"[1/5] Loading input: {args.input}")
    with open(args.input, "r", encoding="utf-8") as f:
        chapter_text = f.read()
    num_chars = len(chapter_text)
    num_lines = chapter_text.count("\n") + (1 if chapter_text else 0)
    print(f"      Loaded {num_chars} characters across {num_lines} lines.")

    print(f"[2/5] Initializing LLM client (model: {args.model})")
    t0 = time.perf_counter()
    llm = LLMClient(model=args.model)
    print(f"      LLM ready in {time.perf_counter() - t0:.2f}s")

    print("[3/5] Extracting present characters...")
    t1 = time.perf_counter()
    characters = extract_present_characters(chapter_text, llm)
    dt1 = time.perf_counter() - t1
    preview = ", ".join(characters[:10]) + ("..." if len(characters) > 10 else "")
    print(f"      Found {len(characters)} characters: {preview} (in {dt1:.2f}s)")

    print("[4/5] Labeling lines with speakers...")
    t2 = time.perf_counter()
    lines = label_lines_with_speakers(chapter_text, characters, llm)
    dt2 = time.perf_counter() - t2
    print(f"      Labeled {len(lines)} lines (in {dt2:.2f}s)")

    result = {"characters": characters, "lines": lines}

    print("[5/5] Writing output")
    payload = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(payload)
        print(f"      Wrote JSON to: {args.output}")
    else:
        print(payload)
    print("Done.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
