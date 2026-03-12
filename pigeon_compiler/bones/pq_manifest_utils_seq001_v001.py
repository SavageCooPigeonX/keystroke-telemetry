"""pigeon_compiler/bones/pq_manifest_utils_seq001_v001.py

BONE MODULE — Extracted from hush_pre_query_seq001_v001.py (v4.9.13)
Origin: Lines 68-152, last modified 2026-02-14 (never changed since creation)

CS Agent manifest CRUD — per-user tracking of backups, keywords, dates.
Pure filesystem + JSON operations. Zero LLM calls. Zero session mutation.
"""
import json
import time
import logging
from pathlib import Path

logger = logging.getLogger('hush')

PROJECT_ROOT = Path(__file__).parent.parent.parent
MANIFESTS_DIR = PROJECT_ROOT / 'maif_whisperer' / 'memory' / 'manifests'

# Loop threshold — after N context selects in a session, trigger backup
CS_LOOP_BACKUP_THRESHOLD = 3


def get_manifest_path(user_id: str) -> Path:
    """Get path to per-user CS agent manifest."""
    uid = user_id or 'operator'
    d = MANIFESTS_DIR / uid
    d.mkdir(parents=True, exist_ok=True)
    return d / 'cs_agent_manifest.json'


def load_manifest(user_id: str) -> dict:
    """Load CS agent manifest — per-user backup paths, remember keywords, dates."""
    path = get_manifest_path(user_id)
    if path.exists():
        try:
            return json.loads(path.read_text(encoding='utf-8'))
        except Exception:
            pass
    return {
        'backup_paths': [],
        'remember_keywords': [],
        'remember_dates': [],
        'cs_loop_count': 0,
        'last_backup_ts': 0,
        'serper_fire_count': 0,
    }


def save_manifest(user_id: str, manifest: dict):
    """Save CS agent manifest."""
    path = get_manifest_path(user_id)
    try:
        path.write_text(json.dumps(manifest, indent=2, default=str), encoding='utf-8')
    except Exception as e:
        logger.warning(f"[CS-AGENT] Manifest save failed: {e}")


def update_manifest_remember(user_id: str, remember_list: list, intent: str = ''):
    """Index REMEMBER keywords from reasoning model guidance into manifest."""
    if not remember_list:
        return
    manifest = load_manifest(user_id)
    now = time.time()
    for kw in remember_list:
        existing = [r['keyword'] for r in manifest['remember_keywords']]
        if kw not in existing:
            manifest['remember_keywords'].append({
                'keyword': kw,
                'ts': now,
                'source_intent': intent,
            })
    manifest['remember_keywords'] = manifest['remember_keywords'][-100:]
    save_manifest(user_id, manifest)
    logger.info(f"[CS-AGENT] Indexed {len(remember_list)} keywords for {user_id}")


def record_backup_path(user_id: str, shard_id: str, reason: str = ''):
    """Record a shard backup event in the manifest."""
    manifest = load_manifest(user_id)
    manifest['backup_paths'].append({
        'shard_id': shard_id,
        'ts': time.time(),
        'reason': reason,
    })
    manifest['last_backup_ts'] = time.time()
    manifest['backup_paths'] = manifest['backup_paths'][-50:]
    save_manifest(user_id, manifest)


def increment_cs_loop(user_id: str) -> int:
    """Increment CS loop count, return new count."""
    manifest = load_manifest(user_id)
    manifest['cs_loop_count'] = manifest.get('cs_loop_count', 0) + 1
    save_manifest(user_id, manifest)
    return manifest['cs_loop_count']


def increment_serper_count(user_id: str) -> int:
    """Track serper fire count for dynamic depth control."""
    manifest = load_manifest(user_id)
    manifest['serper_fire_count'] = manifest.get('serper_fire_count', 0) + 1
    save_manifest(user_id, manifest)
    return manifest['serper_fire_count']
