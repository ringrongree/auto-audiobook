# auto-audiobook

LLM-powered audiobook generator. MVP: identify speakers from a chapter and label each line with a speaker (including Narrator).

## Setup

1) Python 3.10+
2) Create virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

3) Install dependencies:

```bash
pip install -r requirements.txt
```

4) Provide your OpenAI API key (choose one):

- Option A: .env file (recommended; auto-loaded)
  - Create a file named `.env` in the project root with:
    ```bash
    OPENAI_API_KEY=sk-...your-key...
    ```
  - `.env` is already gitignored.

- Option B: shell environment variable
  ```bash
  export OPENAI_API_KEY=sk-...your-key...
  ```

## Usage

Given a chapter text file `chapter.txt`:

```bash
python -m aabook.cli --input chapter.txt --output chapter_labeled.json --model gpt-4o-mini
```

- Output JSON structure:

```json
{
  "characters": ["Alice", "Bob", "Narrator"],
  "lines": [
    {"speaker": "Narrator", "text": "It was late afternoon when Alice arrived."},
    {"speaker": "Alice", "text": "Hello? Is anyone here?"},
    {"speaker": "Bob", "text": "Over here!"}
  ]
}
```

## Notes
- The system auto-loads `.env` using python-dotenv.
- Only characters detected for this chapter plus "Narrator" are used for attribution.
- Tweak the `--model` argument if needed.