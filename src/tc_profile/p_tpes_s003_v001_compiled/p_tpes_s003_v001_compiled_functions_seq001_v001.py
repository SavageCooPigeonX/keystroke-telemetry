"""p_tpes_s003_v001_compiled_functions_seq001_v001.py — Auto-extracted by Pigeon Compiler."""
from datetime import datetime, timezone
import ast
import re
import time

def _empty_profile() -> dict:
    return {
        'version': 1,
        'created': datetime.now(timezone.utc).isoformat(),
        'updated': None,
        'samples': 0,
        'shards': {
            'voice': {
                'top_words': {},       # word -> count (top 50)
                'bigrams': {},         # "w1 w2" -> count (top 30)
                'avg_words_per_msg': 0,
                'uses_caps': False,
                'punct_rate': 0.0,     # how often they use punctuation
                'catchphrases': [],    # recurring 3+ word phrases
                'filler_words': {},    # "like", "also", "just" etc
            },
            'rhythm': {
                'avg_wpm': 0,
                'wpm_p25': 0,
                'wpm_p75': 0,
                'avg_del_ratio': 0,
                'peak_hours_utc': [],
                'session_lengths': [], # recent session durations in minutes
                'avg_pause_before_send_ms': 0,
            },
            'deletions': {
                'deleted_words': {},   # word fragment -> count
                'rewrite_patterns': [], # (before_pattern, after_pattern)
                'abandon_rate': 0,     # % of started messages never sent
                'top_unsaid': [],      # most deleted complete words
            },
            'topics': {
                'module_mentions': {}, # module_name -> mention_count
                'concept_clusters': [],# groups of co-occurring words
                'recent_focus': [],    # last 5 dominant topics
                'recurring_themes': {},# theme -> count
            },
            'decisions': {
                'accept_rate': 0,
                'reward_rate': 0,
                'total_completions': 0,
                'accepted_patterns': [],  # buffer patterns that led to accepts
                'rejected_patterns': [],  # buffer patterns that led to rejects
                'sweet_spot_len': 0,      # buffer length most likely to accept
            },
            'code_style': {
                'preferred_quotes': 'single',
                'uses_type_hints': False,
                'import_style': 'from_x',  # from_x | import_x | mixed
                'naming_convention': 'snake_case',
                'avg_func_length': 0,
                'common_patterns': [],     # recurring code structures
            },
            'emotions': {
                'state_distribution': {},  # state -> percentage
                'frustration_triggers': [],# modules/topics that cause frustration
                'flow_triggers': [],       # what puts them in flow
                'state_transitions': {},   # "focused->frustrated" -> count
                'avg_hesitation': 0,
            },
            'predictions': {
                'working_templates': [],   # completion patterns that got accepted
                'dead_templates': [],      # patterns that always get rejected
                'topic_to_completion': {}, # topic -> successful completion style
                'operator_phrases': [],    # exact phrases they tend to type
            },
            # CIA shard: per-section cognition fingerprint.
            # sections = intent clusters (infrastructure, debugging, telemetry, etc.)
            # Each accumulates the operator's cognitive DNA when visiting that section.
            # The goal: operator reads this and says "what the fuck, how does it know that"
            'sections': {},  # section_name -> SectionProfile (see _empty_section())
            # INTELLIGENCE FILE — grows forever. Discovered secrets about the operator.
            # Not statistics. Deductions. Things THEY don't know about themselves.
            # Each secret has a confidence score and evidence chain.
            'intelligence': {
                'secrets': [],             # list of Secret objects (see below)
                'behavioral_laws': [],     # invariants: "ALWAYS does X when Y"
                'contradictions': [],      # "says X but does Y" with evidence
                'predictions_log': [],     # predictions made + whether they came true
                'operator_model': {        # the system's running theory of who this person is
                    'work_style': None,    # deduced: "sprinter" / "marathoner" / "binge-refactorer"
                    'decision_speed': None,# deduced: "impulsive" / "deliberate" / "paralyzed"
                    'honesty_index': 1.0,  # 0-1: how often stated intent matches actual behavior
                    'comfort_zones': [],   # sections where they perform best (low hes, high accept)
                    'avoidance_zones': [], # sections they circle but never enter deeply
                    'growth_edges': [],    # sections where they're getting better over time
                    'regression_zones': [],# sections where performance is declining
                    'time_personality': None,  # "night owl" / "morning person" / "chaos schedule"
                    'deletion_personality': None,  # "editor" (high del, refines) / "committer" (low del, ships fast) / "abandoner" (high del, gives up)
                    'frustration_response': None,  # "pushes through" / "switches context" / "abandons session"
                },
                'secret_count': 0,
                'last_deduction': None,    # ISO timestamp of last secret discovery
            },
        },
    }
