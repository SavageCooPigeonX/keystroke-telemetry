"""Quick test of TC intelligence system."""
import sys; sys.path.insert(0, '.')
from pathlib import Path

print('=== TC Intelligence Cycle Test ===')
print()

# 1. Generate a profile from the last few prompts of this session
print('1. Generating profile from session...')
from src.tc_profile import generate_profile_from_journal
profile = generate_profile_from_journal(n_prompts=12)
print('   Profile:', profile)

# 2. Match against the buffer
print()
print('2. Testing profile match...')
from src.tc_manifest import match_intent_profile
test_buffers = [
    'tc manifest prompt box question channel',
    'entropy red layer shedding formula',
    'bug fix error broken',
]
for buf in test_buffers:
    name, p, score = match_intent_profile(buf)
    print(f'   "{buf[:30]}..." -> {name} ({score:.2f})')

# 3. Test question channel
print()
print('3. Testing question channel...')
from src.tc_question_channel import ask_tc, should_ask
result = ask_tc('what file handles trajectory tracking?', 
                context='tc manifest file trajectory', entropy=0.72)
print('   Answered:', result['answered'])
print('   Source:', result['source'])
if result['answered']:
    print('   Answer:', result['answer'])
else:
    print('   Question ID:', result['question_id'])

# 4. Check TC context
print()
print('4. TC Context Summary...')
from src.tc_manifest import get_tc_context
ctx = get_tc_context()
print('   Tasks:', len(ctx['tasks']))
print('   Bugs:', len(ctx['bugs']), '(chronic:', sum(1 for b in ctx['bugs'] if b.get('status')=='chronic'), ')')
print('   Profiles:', len(ctx['profiles']))
print('   Trajectories:', len(ctx.get('trajectories', {})))
print('   Pending questions:', len(ctx.get('pending_questions', [])))

# 5. Get intelligent context for TC
print()
print('5. Intelligent context selection...')
from src.tc_context_agent import get_intelligent_context
intel = get_intelligent_context('orchestration tc manifest profile intent')
print('   Profile match:', intel.get('profile_match'))
print('   Confidence:', round(intel.get('profile_confidence', 0), 2))
print('   Template:', intel.get('template'))
print('   Files:', [f.get('name','?')[:20] for f in intel.get('files', [])][:3])

print()
print('=== TC Intelligence System Ready ===')
