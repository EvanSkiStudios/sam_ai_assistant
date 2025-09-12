import re
import json
from pathlib import Path

# Load patterns from JSON file
_patterns_file = Path(__file__).with_name("search_patterns.json")
with open(_patterns_file, "r", encoding="utf-8") as f:
    SEARCH_PATTERNS = json.load(f)

PATTERNS = [re.compile(p, re.I) for p in SEARCH_PATTERNS]


def is_search_request(text: str) -> bool:
    text = (text or "").strip()
    if not text:
        return False
    for pat in PATTERNS:
        if pat.search(text):
            return True
    return False

