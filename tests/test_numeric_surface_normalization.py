import json
import tempfile
import unittest
from pathlib import Path
from src._resolve import src_import

intent_numeric = src_import("intent_numeric_seq001")
self_score = src_import("file_sim_seq001", "self_score")
canonicalize_file_key, normalize_prompt_text = src_import("intent_numeric_seq001", "canonicalize_file_key", "normalize_prompt_text")


class NumericSurfaceNormalizationTests(unittest.TestCase):
    def test_normalize_prompt_text_recovers_key_terms(self):
        raw = (
            'ppprororompmpmpttt   neneneurururmmmeeerririiccc '
            'e eenncnccoododdiiinng ng g   dddeececcodododiiinng ng g '
            'ttoouucucchheheess s'
        )

        normalized = normalize_prompt_text(raw)

        self.assertIn('prompt', normalized)
        self.assertIn('numeric', normalized)
        self.assertIn('encoding', normalized)
        self.assertIn('decoding', normalized)
        self.assertIn('touches', normalized)

    def test_normalize_prompt_text_fixes_close_typos(self):
        normalized = normalize_prompt_text('prompt neurmeric encoding')

        self.assertIn('numeric', normalized)

    def test_canonicalize_file_key_preserves_file_sim(self):
        self.assertEqual(canonicalize_file_key('file_sim_seq001_v001'), 'file_sim')
        self.assertEqual(canonicalize_file_key('tc_sim_engine_seq001_v001'), 'tc_sim_engine')

    def test_self_score_reads_matrix_and_heat_schemas(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'logs').mkdir(parents=True, exist_ok=True)

            (root / 'logs' / 'intent_matrix.json').write_text(
                json.dumps({
                    'matrix': {
                        'file_sim': {'1': 0.8},
                    },
                    'touch_counts': {'file_sim': 5},
                }),
                encoding='utf-8',
            )
            (root / 'logs' / 'intent_vocab.json').write_text(
                json.dumps({
                    'word_to_id': {'file': 1},
                    'next_id': 2,
                }),
                encoding='utf-8',
            )
            (root / 'file_heat_map.json').write_text(
                json.dumps({
                    'file_sim': {'heat': 0.9},
                }),
                encoding='utf-8',
            )

            score = self_score('file_sim_seq001_v001', {'1': 1.0}, root=root)

            self.assertGreater(score, 0.3)

    def test_predict_files_uses_lexical_prior_for_matching_file_names(self):
        old_state = {
            'vocab': intent_numeric._vocab.copy(),
            'vocab_inverse': intent_numeric._vocab_inverse.copy(),
            'next_id': intent_numeric._next_id,
            'vocab_loaded': intent_numeric._vocab_loaded,
            'matrix': {k: v.copy() for k, v in intent_numeric._matrix.items()},
            'touch_counts': intent_numeric._touch_counts.copy(),
            'matrix_loaded': intent_numeric._matrix_loaded,
            'surface_healed': intent_numeric._surface_healed,
            'lexicon_cache': None if intent_numeric._lexicon_cache is None else set(intent_numeric._lexicon_cache),
            'save_vocab': intent_numeric._save_vocab,
        }
        try:
            intent_numeric._vocab = {'make': 1, 'effective': 2, 'file': 3, 'sim': 4}
            intent_numeric._vocab_inverse = {wid: word for word, wid in intent_numeric._vocab.items()}
            intent_numeric._next_id = 5
            intent_numeric._vocab_loaded = True
            intent_numeric._matrix = {
                'push_narrative': {1: 0.5, 2: 0.5},
                'file_sim': {},
            }
            intent_numeric._touch_counts = {'push_narrative': 50, 'file_sim': 1}
            intent_numeric._matrix_loaded = True
            intent_numeric._surface_healed = True
            intent_numeric._lexicon_cache = {'make', 'effective', 'file', 'sim'}
            intent_numeric._save_vocab = lambda: None

            predictions = intent_numeric.predict_files('make file sim effective', top_n=2)

            self.assertEqual(predictions[0][0], 'file_sim')
            self.assertGreater(predictions[0][1], predictions[1][1])
        finally:
            intent_numeric._vocab = old_state['vocab']
            intent_numeric._vocab_inverse = old_state['vocab_inverse']
            intent_numeric._next_id = old_state['next_id']
            intent_numeric._vocab_loaded = old_state['vocab_loaded']
            intent_numeric._matrix = old_state['matrix']
            intent_numeric._touch_counts = old_state['touch_counts']
            intent_numeric._matrix_loaded = old_state['matrix_loaded']
            intent_numeric._surface_healed = old_state['surface_healed']
            intent_numeric._lexicon_cache = old_state['lexicon_cache']
            intent_numeric._save_vocab = old_state['save_vocab']


if __name__ == '__main__':
    unittest.main()