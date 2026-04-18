"""tc_profile_seq001_v001_empty_section_decomposed_seq005_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 005 | VER: v001 | 94 lines | ~1,238 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
import ast
import re
import time

def _empty_section() -> dict:
    """Per-section cognition dossier. Accumulates across ALL visits.

    This is not statistics. This is behavioral archaeology.
    Pattern: every field answers "what does the operator DO when they're here?"
    not "what happened" — what they ALWAYS do, what they NEVER do, what they
    lie about doing.
    """
    return {
        'visit_count': 0,
        'total_completions': 0,
        'accepted': 0,
        'first_seen': None,
        'last_seen': None,

        # ── COGNITIVE VITAL SIGNS ──
        # rolling averages SPECIFIC to this section — not global baselines
        'avg_wpm': 0.0,
        'avg_del_ratio': 0.0,
        'avg_hesitation': 0.0,
        'peak_wpm': 0.0,           # fastest they've ever typed here
        'worst_hesitation': 0.0,   # most hesitant they've ever been here

        # ── EMOTIONAL FINGERPRINT ──
        # how they FEEL when they enter this section. not what they say — what
        # the keystroke signal says. dominant_state is the mode, but the
        # transition map is the real gold: "always enters frustrated, leaves focused"
        'state_dist': {},           # state -> count
        'dominant_state': 'unknown',
        'entry_states': [],         # last 10 states when ENTERING this section
        'exit_states': [],          # last 10 states when LEAVING this section
        'state_transitions': {},    # "frustrated->focused" -> count (within section)

        # ── SUPPRESSION MAP ──
        # what they TYPE and then DELETE when in this section. this is the
        # subconscious layer — things they think but decide not to say.
        # high count = they keep circling back to a thought they can't commit to.
        'suppressed_words': {},     # word -> count
        'suppressed_phrases': [],   # last 10 multi-word deletions
        'rewrite_chains': [],       # last 10 (before -> after) rewrites in this section
        'abandon_count': 0,         # times they started typing and gave up entirely

        # ── MODULE HEAT ──
        # what files the operator always gravitates toward in this section.
        # pattern: "when debugging, they always touch git_plugin first"
        'hot_modules': {},          # module_name -> touch_count
        'module_sequences': [],     # last 10 module-touch orderings (first->second->third)

        # ── VOCABULARY FINGERPRINT ──
        # the exact words they use when thinking about this section.
        # "infrastructure" section might have totally different word DNA than "debugging".
        # this lets thought completer match their voice PER SECTION.
        'intent_words': {},         # word -> count
        'catchphrases': [],         # exact multi-word phrases they repeat here
        'question_patterns': [],    # how they phrase questions in this section

        # ── TEMPORAL PATTERNS ──
        # when do they visit this section? correlate with time of day and session depth.
        # "they always debug at 2am after a long session"
        'hour_dist': {},            # hour_utc -> count
        'session_depth_avg': 0.0,   # avg session_n when entering this section
        'avg_visit_duration_s': 0.0,# how long they stay in this section
        'visit_durations': [],      # last 10 visit lengths in seconds

        # ── CONTRADICTION DETECTOR ──
        # tracks what they say vs what they do. if they keep saying "refactor"
        # but never touch the module, that's a contradiction. if they say
        # "this is fine" but deletion ratio is 40%, they're lying.
        'stated_intents': [],       # last 10 things they said they'd do
        'actual_actions': [],       # last 10 things they actually did (modules touched)
        'contradiction_count': 0,   # times stated != actual
        'lying_index': 0.0,         # ratio of contradictions to total visits

        # ── COMPLETION STYLE DNA ──
        # not just accept/reject — what STYLE of completion works in this section.
        # "in debugging they accept short direct completions, in infrastructure
        #  they accept longer architectural ones"
        'avg_accepted_len': 0.0,    # avg char length of accepted completions here
        'avg_rejected_len': 0.0,    # avg char length of rejected completions here
        'working_style': [],        # last 8 accepted (buf_tail, comp_head, len)
        'dead_style': [],           # last 8 rejected
        'code_vs_prose_ratio': 0.0, # what % of accepted completions are code vs prose

        # ── BEHAVIORAL PREDICTIONS ──
        # patterns detected from historical visits. these get injected into the
        # thought completer prompt so it can predict behavior before it happens.
        'predictions': [],          # last 5 generated predictions
        'prediction_accuracy': 0.0, # how often predictions were right
    }
