"""TC Question Channel — routes uncertainty to TC for resolution.

When Copilot is uncertain (high entropy), it emits a question.
TC checks if existing profiles can answer. If yes, answer immediately.
If no, queue the question for operator and learn from the answer.

The loop:
1. Copilot detects high entropy → calls ask_tc()
2. TC checks profiles for matching answer
3. If match: return answer (no operator needed)
4. If no match: queue question, return None
5. Operator answers → answer_question() → TC learns new profile

This is the "intent amplification loop" — TC becomes smarter every time
it can't answer, because the operator answer becomes a new profile.
"""
from __future__ import annotations
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from .tc_constants_seq001_v001 import ROOT

QUESTIONS_LOG = ROOT / 'logs' / 'tc_questions.jsonl'
ENTROPY_THRESHOLD = 0.65  # above this, we should ask TC


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def ask_tc(question: str, context: str = '', entropy: float = 0.0,
           module: str = '') -> dict:
    """Ask TC a question. Returns answer if profile matches, else queues for operator.
    
    Args:
        question: The question text (what Copilot is uncertain about)
        context: Buffer/file context for matching
        entropy: Current entropy score (0-1)
        module: Module being edited (for profile matching)
    
    Returns:
        {
            'answered': bool,
            'answer': str or None,
            'source': 'profile' | 'pending' | 'error',
            'question_id': str (if queued for operator),
            'profile_used': str (if answered by profile),
        }
    """
    result = {
        'answered': False,
        'answer': None,
        'source': 'pending',
        'question_id': None,
        'profile_used': None,
    }
    
    try:
        from .tc_manifest_seq001_v001 import match_intent_profile, parse_questions, add_question
        
        # Try to match against profiles using context
        search_text = f"{question} {context} {module}"
        name, profile, score = match_intent_profile(search_text)
        
        if name and score > 0.6:
            # Profile matched! Try to synthesize an answer
            answer = _synthesize_answer(question, profile)
            if answer:
                result['answered'] = True
                result['answer'] = answer
                result['source'] = 'profile'
                result['profile_used'] = name
                _log_question(question, context, entropy, module, 
                             answered=True, answer=answer, profile=name)
                return result
        
        # No profile match — queue for operator
        question_id = add_question(question)
        result['question_id'] = question_id
        _log_question(question, context, entropy, module,
                     answered=False, question_id=question_id)
        
    except Exception as e:
        result['source'] = 'error'
        result['answer'] = f'TC error: {e}'
    
    return result


def _synthesize_answer(question: str, profile: dict) -> str | None:
    """Try to synthesize an answer from a profile.
    
    This is pattern-based, not LLM — we answer from learned patterns.
    """
    triggers = profile.get('trigger', [])
    files = profile.get('files', [])
    template = profile.get('template', '')
    
    # Common question patterns we can answer
    q_lower = question.lower()
    
    # File location questions
    if any(w in q_lower for w in ['where', 'which file', 'what file', 'find']):
        if files:
            return f"Based on past patterns, check: {', '.join(files[:3])}"
    
    # Template/mode questions
    if any(w in q_lower for w in ['template', 'mode', 'approach']):
        if template:
            return f"Similar work used {template} mode"
    
    # Intent/meaning questions
    if any(w in q_lower for w in ['mean', 'what is', 'define']):
        if triggers:
            return f"In this context, it relates to: {', '.join(triggers[:5])}"
    
    return None


def _log_question(question: str, context: str, entropy: float, 
                  module: str, answered: bool, answer: str = None,
                  profile: str = None, question_id: str = None):
    """Log a question for tracking and learning."""
    QUESTIONS_LOG.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        'ts': _now(),
        'question': question[:200],
        'context': context[:100],
        'entropy': entropy,
        'module': module,
        'answered': answered,
        'answer': answer,
        'profile': profile,
        'question_id': question_id,
    }
    with open(QUESTIONS_LOG, 'a', encoding='utf-8') as f:
        f.write(json.dumps(entry, ensure_ascii=False) + '\n')


def answer_question(question_id: str, answer: str,
                    create_profile: bool = True) -> bool:
    """Record operator answer to a queued question.
    
    If create_profile=True, creates a new intent profile from the Q&A pair.
    This is how TC learns from every unanswered question.
    """
    try:
        from .tc_manifest_seq001_v001 import answer_question as manifest_answer
        from .tc_manifest_seq001_v001 import update_intent_profile
        
        # Mark answered in manifest
        manifest_answer(question_id, answer)
        
        # Find the original question in the log
        if QUESTIONS_LOG.exists():
            entries = []
            target = None
            for line in QUESTIONS_LOG.read_text('utf-8', errors='ignore').strip().splitlines():
                try:
                    e = json.loads(line)
                    if e.get('question_id') == question_id:
                        target = e
                        e['answered'] = True
                        e['answer'] = answer
                    entries.append(e)
                except Exception:
                    continue
            
            # Rewrite log with updated entry
            with open(QUESTIONS_LOG, 'w', encoding='utf-8') as f:
                for e in entries:
                    f.write(json.dumps(e, ensure_ascii=False) + '\n')
            
            # Create profile if requested
            if create_profile and target:
                question = target.get('question', '')
                context = target.get('context', '')
                module = target.get('module', '')
                
                # Extract trigger words from question + context
                words = set(re.findall(r'[a-zA-Z_][a-zA-Z0-9_]+', 
                                       f"{question} {context}".lower()))
                stopwords = {'the', 'and', 'for', 'with', 'this', 'that', 'what', 
                            'how', 'where', 'when', 'file', 'module', 'code'}
                triggers = [w for w in words if len(w) > 3 and w not in stopwords][:8]
                
                if triggers and len(triggers) >= 2:
                    profile_name = f"qa_{question_id.lower().replace('-', '_')}"
                    update_intent_profile(
                        name=profile_name,
                        trigger=triggers,
                        files=[module] if module else [],
                        template='/debug',
                        confidence=0.6,
                        hit=True
                    )
        
        return True
    except Exception:
        return False


def should_ask(entropy: float, hedges: int = 0, 
               recent_errors: int = 0) -> bool:
    """Determine if we should ask TC given current entropy signals.
    
    Args:
        entropy: Current entropy score (0-1)
        hedges: Number of hedge words in recent output
        recent_errors: Number of recent errors in this module
    
    Returns:
        True if we should emit a question to TC
    """
    # Base threshold
    if entropy > ENTROPY_THRESHOLD:
        return True
    
    # Lower threshold if there are hedges
    if hedges > 2 and entropy > 0.5:
        return True
    
    # Lower threshold if there were recent errors  
    if recent_errors > 0 and entropy > 0.4:
        return True
    
    return False


def get_pending_questions() -> list[dict]:
    """Get all pending questions awaiting operator answers."""
    try:
        from .tc_manifest_seq001_v001 import parse_questions
        return [q for q in parse_questions() if q.get('status') == 'pending']
    except Exception:
        return []


def format_questions_for_display() -> str:
    """Format pending questions for injection into prompts.
    
    This goes into copilot-instructions.md so the operator sees what TC is stuck on.
    """
    pending = get_pending_questions()
    if not pending:
        return ''
    
    lines = ['## TC Questions (waiting for operator)', '']
    for q in pending[:5]:  # max 5
        lines.append(f"- **{q['id']}**: {q['question']}")
    
    lines.append('')
    lines.append('*Answer with: "TC Q-001: your answer here"*')
    return '\n'.join(lines)


# ══════════════════════════════════════════════════════════════════════════════
# HIGH-LEVEL API — for integration with thought_completer and copilot flow
# ══════════════════════════════════════════════════════════════════════════════

def check_entropy_and_ask(buffer: str, entropy: float, 
                          module: str = '', hedges: int = 0) -> dict | None:
    """Check if entropy warrants asking TC, and ask if so.
    
    This is the main integration point. Call it during completion generation
    when uncertainty is detected.
    
    Returns:
        - dict with answer if TC could answer
        - dict with question_id if queued for operator
        - None if entropy is low enough to proceed without asking
    """
    if not should_ask(entropy, hedges):
        return None
    
    # Construct a question from the context
    question = _infer_question(buffer, entropy, hedges)
    if not question:
        return None
    
    return ask_tc(question, context=buffer, entropy=entropy, module=module)


def _infer_question(buffer: str, entropy: float, hedges: int) -> str | None:
    """Infer what question to ask based on context.
    
    This is heuristic-based question generation.
    """
    buf_lower = buffer.lower()
    
    # File-related uncertainty
    if any(w in buf_lower for w in ['file', 'module', 'import']):
        return f"Which file handles: {buffer[:50]}"
    
    # Architecture uncertainty
    if any(w in buf_lower for w in ['how', 'architecture', 'structure', 'design']):
        return f"What's the architecture for: {buffer[:50]}"
    
    # Implementation uncertainty
    if any(w in buf_lower for w in ['implement', 'add', 'create', 'build']):
        return f"Implementation approach for: {buffer[:50]}"
    
    # High entropy without clear signal
    if entropy > 0.75:
        return f"High uncertainty about: {buffer[:60]}"
    
    return None


def process_operator_inline_answer(message: str) -> bool:
    """Process an inline answer from operator like "TC Q-001: answer here".
    
    Call this on every operator message to check for TC answers.
    Returns True if a TC answer was processed.
    """
    m = re.match(r'TC (Q-\d+):\s*(.+)', message, re.IGNORECASE)
    if not m:
        return False
    
    question_id = m.group(1).upper()
    answer = m.group(2).strip()
    
    if answer:
        return answer_question(question_id, answer, create_profile=True)
    return False
