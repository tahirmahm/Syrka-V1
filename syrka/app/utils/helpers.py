"""General utility helper functions."""

import re
import hashlib
from typing import Any, Optional
from datetime import datetime, date
import numpy as np


def generate_hash(text: str) -> str:
    """
    Generate SHA256 hash of a string.

    Args:
        text: Input string to hash

    Returns:
        Hexadecimal hash string
    """
    return hashlib.sha256(text.encode()).hexdigest()


def clean_text(text: str) -> str:
    """
    Clean and normalize text by removing extra whitespace and special characters.

    Args:
        text: Input text

    Returns:
        Cleaned text
    """
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    # Strip leading/trailing whitespace
    text = text.strip()
    return text


def extract_email(text: str) -> Optional[str]:
    """
    Extract email address from text using regex.

    Args:
        text: Input text

    Returns:
        First email found or None
    """
    pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    match = re.search(pattern, text)
    return match.group(0) if match else None


def extract_numbers(text: str) -> list[int]:
    """
    Extract all integer numbers from text.

    Args:
        text: Input text

    Returns:
        List of extracted integers
    """
    return [int(num) for num in re.findall(r'\d+', text)]


def normalize_skill_name(skill: str) -> str:
    """
    Normalize skill name for consistent comparison.

    Args:
        skill: Skill name

    Returns:
        Normalized skill name (lowercase, trimmed)
    """
    return skill.lower().strip()


def parse_salary_range(salary_text: str) -> tuple[Optional[int], Optional[int]]:
    """
    Parse salary range from text.

    Examples:
        "$50,000 - $70,000" -> (50000, 70000)
        "£30k-40k" -> (30000, 40000)
        "$60K per year" -> (60000, 60000)

    Args:
        salary_text: Salary text to parse

    Returns:
        Tuple of (min_salary, max_salary) or (None, None) if parsing fails
    """
    if not salary_text:
        return (None, None)

    # Remove currency symbols and common words
    text = re.sub(r'[$£€,]', '', salary_text)
    text = text.lower().replace('per year', '').replace('annually', '').strip()

    # Find all numbers (handling 'k' for thousands)
    numbers = []
    for match in re.finditer(r'(\d+(?:\.\d+)?)\s*k?', text):
        num_str = match.group(1)
        num = float(num_str)
        if 'k' in match.group(0).lower():
            num *= 1000
        numbers.append(int(num))

    if len(numbers) == 0:
        return (None, None)
    elif len(numbers) == 1:
        return (numbers[0], numbers[0])
    else:
        return (min(numbers), max(numbers))


def calculate_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
    """
    Calculate cosine similarity between two vectors.

    Args:
        vec1: First vector
        vec2: Second vector

    Returns:
        Cosine similarity score (0 to 1)
    """
    if vec1 is None or vec2 is None:
        return 0.0

    # Normalize vectors
    vec1_norm = vec1 / (np.linalg.norm(vec1) + 1e-8)
    vec2_norm = vec2 / (np.linalg.norm(vec2) + 1e-8)

    # Compute cosine similarity
    similarity = np.dot(vec1_norm, vec2_norm)

    # Ensure result is between 0 and 1
    return float(max(0.0, min(1.0, similarity)))


def chunk_list(items: list[Any], chunk_size: int) -> list[list[Any]]:
    """
    Split a list into chunks of specified size.

    Args:
        items: List to chunk
        chunk_size: Size of each chunk

    Returns:
        List of chunks
    """
    return [items[i:i + chunk_size] for i in range(0, len(items), chunk_size)]


def date_to_string(d: date) -> str:
    """
    Convert date to ISO format string.

    Args:
        d: Date object

    Returns:
        ISO format date string
    """
    return d.isoformat()


def datetime_to_string(dt: datetime) -> str:
    """
    Convert datetime to ISO format string.

    Args:
        dt: Datetime object

    Returns:
        ISO format datetime string
    """
    return dt.isoformat()


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate text to maximum length with optional suffix.

    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated

    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix
