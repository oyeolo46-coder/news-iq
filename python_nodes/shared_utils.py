"""
News IQ - Shared Utilities
Compatible with n8n Code nodes (JavaScript mode) and standalone Python
"""

import json
import math
import re
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

# ============================================================================
# UUID GENERATION
# ============================================================================
def generate_uuid() -> str:
    """Generate a UUID v4 string."""
    return str(uuid.uuid4())

# ============================================================================
# TIMESTAMP UTILITIES
# ============================================================================
def now_iso() -> str:
    """Current timestamp in ISO 8601 format."""
    return datetime.utcnow().isoformat() + "Z"

def today_start() -> str:
    """Start of today in ISO format."""
    return datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0).isoformat() + "Z"

def week_start() -> str:
    """Start of current week (Monday) in ISO format."""
    today = datetime.utcnow()
    monday = today - timedelta(days=today.weekday())
    monday = monday.replace(hour=0, minute=0, second=0, microsecond=0)
    return monday.isoformat() + "Z"

def expires_at(days: int = 7) -> str:
    """Expiration timestamp N days from now."""
    return (datetime.utcnow() + timedelta(days=days)).isoformat() + "Z"

# ============================================================================
# COSINE SIMILARITY (for deduplication)
# ============================================================================
def cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
    """
    Calculate cosine similarity between two vectors.
    Returns float between -1 and 1.
    """
    if not vec_a or not vec_b or len(vec_a) != len(vec_b):
        return 0.0

    dot_product = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = math.sqrt(sum(a * a for a in vec_a))
    norm_b = math.sqrt(sum(b * b for b in vec_b))

    if norm_a == 0 or norm_b == 0:
        return 0.0

    return dot_product / (norm_a * norm_b)

def semantic_dedup(
    new_articles: List[Dict],
    existing_embeddings: List[Dict],
    threshold: float = 0.85
) -> Tuple[List[Dict], int, int]:
    """
    Remove semantically duplicate articles.

    Args:
        new_articles: List of articles with 'embedding' field
        existing_embeddings: List of {id, embedding} from DB
        threshold: Similarity threshold (0.0-1.0)

    Returns:
        (deduplicated_articles, unique_count, duplicates_removed)
    """
    deduplicated = []
    duplicates_removed = 0

    for article in new_articles:
        article_embedding = article.get("embedding")

        if article_embedding is None:
            deduplicated.append(article)
            continue

        is_duplicate = False

        for existing in existing_embeddings:
            existing_embedding = existing.get("embedding")
            if existing_embedding is None:
                continue

            similarity = cosine_similarity(article_embedding, existing_embedding)

            if similarity > threshold:
                is_duplicate = True
                duplicates_removed += 1
                break

        if not is_duplicate:
            deduplicated.append(article)

    return deduplicated, len(deduplicated), duplicates_removed

# ============================================================================
# SCRIPT VALIDATION
# ============================================================================
def validate_daily_script(script_text: str) -> Dict[str, Any]:
    """
    Validate a daily short script.

    Returns:
        {valid: bool, word_count: int, duration_seconds: int, errors: List[str]}
    """
    errors = []

    # Clean markers for word count
    clean_text = re.sub(r'\[PAUSE\]', ' ', script_text)
    clean_text = re.sub(r'\[EMPHASIS:([^\]]+)\]', r'\1', clean_text)
    clean_text = re.sub(r'\[EMPHASIS\]', '', clean_text)
    clean_text = re.sub(r'\[SOUND:[^\]]+\]', '', clean_text)
    clean_text = clean_text.strip()

    words = clean_text.split()
    word_count = len(words)

    # ~150 words per minute = 2.5 words per second
    duration_seconds = int((word_count / 150) * 60)

    # Validation rules
    if word_count < 45:
        errors.append(f"Too short: {word_count} words (min 45)")
    if word_count > 150:
        errors.append(f"Too long: {word_count} words (max 150)")

    if duration_seconds < 20:
        errors.append(f"Too short: {duration_seconds}s (min 20)")
    if duration_seconds > 90:
        errors.append(f"Too long: {duration_seconds}s (max 90)")

    # Check for placeholder text
    placeholders = ["[PLACEHOLDER]", "<placeholder>", "TODO", "FIXME"]
    for ph in placeholders:
        if ph.lower() in script_text.lower():
            errors.append(f"Contains placeholder: {ph}")

    # Check for required markers
    if "[PAUSE]" not in script_text:
        errors.append("Missing [PAUSE] markers")

    # Check for hook and CTA
    if not any(hook in script_text.lower() for hook in ["breaking", "just announced", "here's what", "you need to know"]):
        errors.append("Weak hook - consider stronger opening")

    if "subscribe" not in script_text.lower() and "follow" not in script_text.lower():
        errors.append("Missing CTA (subscribe/follow)")

    return {
        "valid": len(errors) == 0,
        "word_count": word_count,
        "duration_seconds": duration_seconds,
        "errors": errors,
        "clean_text": clean_text
    }

def validate_weekly_script(script_text: str) -> Dict[str, Any]:
    """Validate a weekly recap script."""
    errors = []

    clean_text = re.sub(r'\[PAUSE\]', ' ', script_text)
    clean_text = re.sub(r'\[EMPHASIS:([^\]]+)\]', r'\1', clean_text)
    clean_text = re.sub(r'\[EMPHASIS\]', '', clean_text)
    clean_text = re.sub(r'\[SOUND:[^\]]+\]', '', clean_text)
    clean_text = clean_text.strip()

    words = clean_text.split()
    word_count = len(words)
    duration_seconds = int((word_count / 150) * 60)

    if word_count < 750:
        errors.append(f"Too short: {word_count} words (min 750)")
    if word_count > 1500:
        errors.append(f"Too long: {word_count} words (max 1500)")

    if duration_seconds < 300:
        errors.append(f"Too short: {duration_seconds}s (min 300)")
    if duration_seconds > 600:
        errors.append(f"Too long: {duration_seconds}s (max 600)")

    # Check structure
    if "intro" not in script_text.lower() and "welcome" not in script_text.lower():
        errors.append("Missing intro")

    if "outro" not in script_text.lower() and "thanks for watching" not in script_text.lower():
        errors.append("Missing outro")

    # Count segments (should have ~5)
    segment_markers = ["story", "segment", "next up", "moving on"]
    segment_count = sum(1 for m in segment_markers if m in script_text.lower())
    if segment_count < 3:
        errors.append(f"Too few segments detected ({segment_count}, expected ~5)")

    return {
        "valid": len(errors) == 0,
        "word_count": word_count,
        "duration_seconds": duration_seconds,
        "errors": errors,
        "clean_text": clean_text,
        "segment_count": segment_count
    }

# ============================================================================
# TTS TEXT CLEANER
# ============================================================================
def clean_script_for_tts(script_text: str) -> str:
    """
    Remove n8n script markers for text-to-speech processing.

    [PAUSE] -> "... "
    [EMPHASIS:word] -> "word"
    [EMPHASIS] -> ""
    [SOUND:effect] -> ""
    """
    text = script_text
    text = re.sub(r'\[PAUSE\]', '... ', text)
    text = re.sub(r'\[EMPHASIS:([^\]]+)\]', r'\1', text)
    text = re.sub(r'\[EMPHASIS\]', '', text)
    text = re.sub(r'\[SOUND:[^\]]+\]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

# ============================================================================
# LOG FORMATTER
# ============================================================================
def format_log_entry(workflow: str, level: str, message: str, metadata: Dict = None) -> Dict:
    """Format a log entry for database insertion."""
    return {
        "workflow": workflow,
        "level": level,
        "message": message,
        "metadata": json.dumps(metadata or {}),
        "created_at": now_iso()
    }

# ============================================================================
# ERROR RESPONSE BUILDER
# ============================================================================
def build_response(success: bool, data: Dict = None, error: str = None) -> Dict:
    """Build a standardized response for n8n HTTP nodes."""
    response = {"success": success}
    if data:
        response.update(data)
    if error:
        response["error"] = error
    return response

# ============================================================================
# N8N-SPECIFIC HELPERS
# ============================================================================
def n8n_return_items(items: List[Dict]) -> List[Dict]:
    """
    Format items for n8n Code node return.
    n8n expects: [{"json": {...}}]
    """
    return [{"json": item} for item in items]

def n8n_get_input_items(items) -> List[Dict]:
    """
    Extract JSON data from n8n input items.
    Handles both n8n's item format and plain dicts.
    """
    result = []
    for item in items:
        if isinstance(item, dict) and "json" in item:
            result.append(item["json"])
        elif isinstance(item, dict):
            result.append(item)
    return result