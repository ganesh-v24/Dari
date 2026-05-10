import re
from typing import List

def tokenize(text: str) -> List[str]:
    """Extract lower-case alphanumeric tokens from text."""
    return re.findall(r"[a-z0-9_]+", text.lower())

def slugify(text: str) -> str:
    """Convert text to a URL-friendly slug."""
    text = re.sub(r"[^\w\s-]", "", text.lower())
    text = re.sub(r"[\s_-]+", "-", text.strip())
    return text

def keyword_score(text: str, keywords: List[str]) -> float:
    """
    Return a 0.0-1.0 score for how many keywords appear in text.
    Useful for fast intent classification without an LLM.
    """
    tokens = set(tokenize(text))
    if not tokens or not keywords:
        return 0.0
    matches = sum(1 for kw in keywords if kw.lower() in tokens)
    return matches / len(keywords)

def extract_place_names(text: str) -> List[str]:
    """
    Naive place-name extraction: capitalised words that are >3 chars long.
    Returns a list of candidate place names in order of appearance.
    """
    # Match capitalised sequences (e.g., "New York", "Bangalore")
    pattern = re.compile(r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b")
    candidates = pattern.findall(text)
    # Filter out common false positives
    skip = {"I", "The", "A", "An", "This", "That", "You", "We", "They"}
    return [c for c in candidates if c not in skip and len(c) > 3]

def truncate(text: str, max_chars: int = 200, suffix: str = "…") -> str:
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rsplit(" ", 1)[0] + suffix

def clean_query(text: str) -> str:
    """Strip extra whitespace and normalise punctuation."""
    text = re.sub(r"\s+", " ", text.strip())
    text = re.sub(r"\?{2,}", "?", text)
    return text
