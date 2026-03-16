"""unsaid_extract_topic_seq004_v001.py — Auto-extracted by Pigeon Compiler."""
import re

def _extract_topic(text: str) -> str:
    """Extract a rough topic label from text (first few meaningful words)."""
    words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
    stopwords = {'the', 'and', 'for', 'that', 'this', 'with', 'from', 'are', 'was', 'you', 'can', 'how'}
    meaningful = [w for w in words if w not in stopwords][:4]
    return ' '.join(meaningful) if meaningful else text[:30].strip()
