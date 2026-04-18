"""Debug: trace why prediction_scorer scores so high.
Updated to use weighted mentions (the fix)."""
import json, sys
sys.path.insert(0, '.')
from src.tc_context_seq001_v001_seq001_v001_agent_seq001_v001_seq001_v001 import _extract_mentions, _score_module, _name_segment_match, _load_registry
from src.tc_context_seq001_v001_seq001_v001 import load_context

# Test buffers from the sim
test_buffers = [
    'would it make sense for the thought completer to have awarness',
    'yes but i think the real trick is is that',
    'woah highher scores when editing context select',
    'i want to get a transcript of simulation',
    'copilot context needs to be injexted into context select agent',
]

ctx = load_context()
hot_mods = [m.get('module', '').lower() for m in ctx.get('hot_modules', [])]
heat_mods = [h.get('mod', '').lower() for h in ctx.get('heat_map', []) if h.get('heat', 0) > 0.1]
print(f'hot_mods: {hot_mods[:5]}')
print(f'heat_mods: {heat_mods[:5]}')

reg = _load_registry()
for buf in test_buffers:
    # Build weighted mentions the same way select_context_files does now
    buffer_mentions = _extract_mentions(buf)
    weighted = [(m, 1.0) for m in buffer_mentions]
    # Context padding at 0.3
    ctx_text = ''
    for thread in ctx.get('unsaid_threads', [])[-3:]:
        ctx_text += ' ' + thread
    for p in ctx.get('recent_prompts', [])[-2:]:
        ctx_text += ' ' + p.get('msg', '')
    for sm in ctx.get('session_messages', [])[-3:]:
        ctx_text += ' ' + sm.get('text', '')
    seen = set(buffer_mentions)
    for m in _extract_mentions(ctx_text):
        if m not in seen:
            weighted.append((m, 0.3))
            seen.add(m)

    print(f'\n=== buffer: "{buf[:50]}" ===')
    buf_words = [m for m, w in weighted if w == 1.0]
    ctx_words = [m for m, w in weighted if w < 1.0]
    print(f'  buffer mentions ({len(buf_words)}): {buf_words}')
    print(f'  context mentions ({len(ctx_words)}): {ctx_words[:10]}')

    # Score all modules, show top 5
    scored = []
    for mod in reg:
        s = _score_module(mod, weighted, hot_mods, heat_mods, 'frustrated')
        if s > 0:
            scored.append((mod.get('name', ''), s, mod.get('desc', '')[:60]))
    scored.sort(key=lambda x: x[1], reverse=True)
    for name, score, desc in scored[:5]:
        # Trace WHY
        reasons = []
        for m, w in weighted:
            if _name_segment_match(m, name.lower()):
                reasons.append(f'seg~"{m}"*{w}={3.0*w:.1f}')
            elif '_' in m and m in desc.lower():
                reasons.append(f'desc_u~"{m}"*{w}={1.0*w:.1f}')
            elif m in desc.lower():
                reasons.append(f'desc~"{m}"*{w}={0.3*w:.2f}')
        if name.lower() in hot_mods:
            reasons.append('hot+.5')
        if name.lower() in heat_mods:
            reasons.append('heat+.6')
        print(f'  {score:.1f} {name}: {" | ".join(reasons[:6])}')
