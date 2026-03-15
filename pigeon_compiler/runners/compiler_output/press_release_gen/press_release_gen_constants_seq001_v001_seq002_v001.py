"""press_release_gen_constants_seq001_v001_seq002_v001.py — Pigeon-extracted by compiler."""

LLM_POLISH_PROMPT = """You are a press release writer for an AI reputation intelligence platform.

MUTATION DATA (factual — algorithmically detected):
Entity: {entity_name}
Severity: {severity}/10 | Risk: {risk_level}
Mutations: {mutation_count} detected across {field_count} fields

MUTATION DETAILS:
{mutation_details}

CONTRADICTIONS:
{contradictions}

NEWS CORRELATION:
{news_correlation}

YOUR TASK:
Write a professional press release (400-600 words) that:
1. Opens with a strong headline about the AI perception shift
2. Summarizes what changed and why it matters
3. Details the key contradictions (honest, factual, no spin)
4. Notes any correlated news events
5. Ends with methodology note and call-to-action

Tone: Authoritative, data-driven, slightly urgent for HIGH/CRITICAL risk.
For LOW/STABLE: professional, monitoring-focused.

Output JSON keys: headline, executive_summary, key_findings (array of strings),
  social_headline (under 140 chars), key_stat (one dramatic number or comparison)"""
SOCIAL_POST_TEMPLATE = """🔍 AI PERCEPTION SHIFT: {entity_name}

{headline_short}

{key_stat}

Full report: myaifingerprint.com/directory/entity/{entity_slug}#drift

#AIReputation #MAIF #DigitalFingerprint"""
