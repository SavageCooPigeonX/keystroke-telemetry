"""dynamic_prompt_seq017_cot_constants_seq009_v001.py — Auto-extracted by Pigeon Compiler."""
import json, re, subprocess

_COT = {
    'frustrated': 'Operator is frustrated. Think step-by-step but keep output SHORT. Lead with the fix. Skip explanations unless asked. If unsure, say so in one line then give your best option.',
    'hesitant':   'Operator is uncertain. Think through what they MIGHT mean. Offer 2 interpretations and address both. End with a clarifying question.',
    'flow':       'Operator is in flow. Match their speed \u2014 technical depth, no preamble. Assume expertise. Go deeper than they asked.',
    'restructuring': 'Operator is rewriting/restructuring. Be precise. Use numbered steps and headers. Match the effort they put into their prompt.',
    'abandoned':  'Operator previously abandoned a message. They may be re-approaching. Be direct and welcoming.',
}
