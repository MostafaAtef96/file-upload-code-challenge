from collections import Counter


def most_frequent_letter(text: str) -> str:
    """
    Finds the most frequent letter in a string, with special handling for
    ties and strings without letters.

    - Ignores case.
    - If no letters are present, returns "N/A".
    - If all present letters occur with the same frequency (and there's more
      than one type of letter), returns "Tie".
    - Otherwise, returns the most frequent letter.
    """
    letters = [char.lower() for char in text if char.isalpha()]
    if not letters:
        return "N/A"

    counts = Counter(letters)
    if len(counts) > 1 and len(set(counts.values())) == 1:
        return "Tie"

    return counts.most_common(1)[0][0]