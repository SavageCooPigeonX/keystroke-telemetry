"""node_memory_seq008_constants_seq001_v001.py — Auto-extracted by Pigeon Compiler."""

DECAY_ALPHA = 0.1          # new signal weight (1 - alpha = memory weight)

MIN_CONFIDENCE_SAMPLES = 5  # entries before policy is "confident"

MAX_RAW_ENTRIES = 200       # cap per node to prevent unbounded growth

MEMORY_FILE = "node_memory.json"
