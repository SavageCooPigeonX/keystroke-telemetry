"""tc_sim_seq001_v001_replay_seq008_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 008 | VER: v002 | 82 lines | ~959 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: chore_pigeon_rename_cascade
# LAST:   2026-04-20 @ c61fc91
# SESSIONS: 1
# ──────────────────────────────────────────────
import json
import re
import sys
import time

def replay_pause_live(pause: PausePoint, use_historical_ctx: bool = False) -> SimResult:
    """Actually call Gemini for one pause point and score the result.
    
    Args:
        use_historical_ctx: If True, reconstruct context from the pause's time
                           instead of using live context. This fixes the major
                           bug where sim uses today's conversation to predict
                           a pause from last week.
    """
    from src.tc_gemini_seq001_v003_d0420__gemini_api_call_system_prompt_lc_chore_pigeon_rename_cascade import call_gemini, _build_user_prompt, SYSTEM_PROMPT
    from src.tc_trajectory_seq001_v001 import format_trajectory_for_prompt
    import json, urllib.request
    from src.tc_constants_seq001_v001 import GEMINI_MODEL, GEMINI_TIMEOUT
    from src.tc_gemini_seq001_v003_d0420__gemini_api_call_system_prompt_lc_chore_pigeon_rename_cascade import _load_api_key, _strip_signal_echo
    
    t0 = time.time()
    
    if use_historical_ctx:
        # Build context AND trajectory from the pause's time period, not live
        ctx, trajectory = _build_historical_context(pause)
        turns_n = len(trajectory.get('turns', []))
        print(f'[historical] {turns_n} turns in trajectory')
        if turns_n > 0:
            for i, t in enumerate(trajectory['turns'][:3]):
                print(f'  turn {i+1}: {t["prompt"][:50]}...')
        if not trajectory.get('turns'):
            # Fall back to live if no historical data
            prediction, ctx_files = call_gemini(pause.buffer)
        else:
            # Call Gemini with historical context + trajectory
            api_key = _load_api_key()
            if not api_key:
                return SimResult(pause=pause)
            
            # Build prompt with historical trajectory (the key fix!)
            user_prompt = _build_user_prompt(pause.buffer, ctx, None, trajectory=trajectory)
            url = (
                f'https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}'
                f':generateContent?key={api_key}'
            )
            body = json.dumps({
                'system_instruction': {'parts': [{'text': SYSTEM_PROMPT}]},
                'contents': [{'role': 'user', 'parts': [{'text': user_prompt}]}],
                'generationConfig': {'temperature': 0.7, 'maxOutputTokens': 150, 'topP': 0.9},
            }).encode('utf-8')
            try:
                req = urllib.request.Request(url, data=body, headers={'Content-Type': 'application/json'})
                with urllib.request.urlopen(req, timeout=GEMINI_TIMEOUT) as resp:
                    data = json.loads(resp.read().decode('utf-8'))
                    parts_resp = data['candidates'][0]['content']['parts']
                    prediction = ''
                    for part in parts_resp:
                        if 'text' in part:
                            prediction = part['text'].strip()
                            break
                    prediction = _strip_signal_echo(prediction, pause.buffer)
            except Exception as e:
                print(f'[sim] gemini error: {e}')
                prediction = ''
            ctx_files = []
    else:
        prediction, ctx_files = call_gemini(pause.buffer)
    
    latency = int((time.time() - t0) * 1000)
    result = score_prediction(pause, prediction)
    result.latency_ms = latency
    result.context_files = ctx_files
    return result
