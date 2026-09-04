"""
Fuzzy String Matching for Movie Title Matching
===============================================
Uses fuzzywuzzy for robust IMDB-MovieLens title matching.
"""

from fuzzywuzzy import fuzz
from typing import Tuple


def clean_title(title: str) -> str:
    """Clean movie title for matching."""
    if pd.isna(title):
        return ""
    title = str(title).lower().strip()
    title = title.split('(')[0].strip()
    return title


def fuzzy_match_title(title: str, search_text: str, threshold: int = 80) -> bool:
    """
    Fuzzy match movie title against search text.

    Args:
        title: Movie title to match
        search_text: Text to search in (e.g., review text)
        threshold: Match score threshold (0-100), default 80

    Returns:
        True if similarity > threshold, False otherwise
    """
    clean_title_str = clean_title(title)

    if not clean_title_str or len(clean_title_str) < 2:
        return False

    search_text_lower = str(search_text).lower()

    # Use token_set_ratio for partial matches
    score = fuzz.token_set_ratio(clean_title_str, search_text_lower)

    return score > threshold


def find_best_match(query: str, candidates: list, threshold: int = 80) -> Tuple[str, int]:
    """
    Find best matching candidate using fuzzy matching.

    Args:
        query: String to match
        candidates: List of candidate strings
        threshold: Minimum match score (0-100)

    Returns:
        (best_match, best_score) tuple
    """
    query_clean = clean_title(query)
    best_match = None
    best_score = 0

    for candidate in candidates:
        candidate_clean = clean_title(candidate)
        score = fuzz.token_set_ratio(query_clean, candidate_clean)

        if score > best_score:
            best_score = score
            best_match = candidate

    if best_score >= threshold:
        return best_match, best_score
    else:
        return None, best_score


if __name__ == "__main__":
    # Test fuzzy matching
    print("Testing Fuzzy Matching:")
    print(f"'The Matrix' in 'I watched The Matrix yesterday': {fuzzy_match_title('The Matrix', 'I watched The Matrix yesterday')}")
    print(f"'Inception' in 'incepton is a great movie': {fuzzy_match_title('Inception', 'incepton is a great movie')}")
