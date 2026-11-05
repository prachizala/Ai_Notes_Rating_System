"""
Name normalization utility for NoteIQ subjects and topics.
Rule: normalized_name = lowercase, trimmed, collapsed whitespace, punctuation stripped.
Example: 'C  Programming!!' -> 'c programming'
"""

import re
import string

# Characters to strip: standard punctuation
PUNCTUATION_REGEX = re.compile(f"[{re.escape(string.punctuation)}]")
WHITESPACE_REGEX = re.compile(r"\s+")


def normalize_name(name: str) -> str:
    if not name:
        return ""
    # Strip punctuation
    text = PUNCTUATION_REGEX.sub(" ", name)
    # Lowercase
    text = text.lower()
    # Collapse multiple whitespaces and trim
    text = WHITESPACE_REGEX.sub(" ", text).strip()
    return text
