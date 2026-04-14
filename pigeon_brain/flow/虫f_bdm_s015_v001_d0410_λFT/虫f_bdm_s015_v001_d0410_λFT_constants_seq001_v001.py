"""虫f_bdm_s015_v001_d0410_λFT_constants_seq001_v001.py — Auto-extracted by Pigeon Compiler."""
import json

REGISTRY_PATH = "pigeon_registry.json"

VEINS_PATH = "pigeon_brain/context_veins.json"

NODE_MEMORY_PATH = "pigeon_brain/node_memory.json"

BUG_MANIFEST_LOG = "pigeon_brain/bug_manifest_chain.jsonl"


BUG_SEVERITY = {
    "oc": 0.8,   # over hard cap — blocks context window
    "hi": 0.7,   # hardcoded import — breaks on rename
    "hc": 0.6,   # high coupling — amplifies blast radius
    "de": 0.4,   # dead export — dead weight
    "dd": 0.3,   # duplicate docstring — noise
    "qn": 0.2,   # query noise — minor fog
}


_BETA_RE = __import__("re").compile(r"_β(\w+?)(?:_|\.py$|$)")


_SEQ_RE = __import__("re").compile(r"_s(\d+)_")
