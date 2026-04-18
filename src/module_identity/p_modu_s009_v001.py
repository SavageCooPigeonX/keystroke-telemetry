"""module_identity_seq001_v001_coaching_seq009_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 009 | VER: v001 | 47 lines | ~550 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
import re

def _generate_self_coaching(name: str, entry: dict, lk: dict, code: dict) -> list[str]:
    """File coaches the operator about its own code — what it knows, what's weak."""
    coaching = []
    resolve = lk['_resolve']
    alias = resolve(name)
    graph = lk['graph'].get(name, {})
    if graph.get('degree', 0) == 0 and alias != name:
        graph = lk['graph'].get(alias, {})
    edges_in = graph.get('edges_in', [])
    edges_out = graph.get('edges_out', [])
    tokens = entry.get('tokens', 0)
    ver = entry.get('ver', 1)
    fns = code.get('functions', [])
    deaths = lk['deaths'].get(name, []) or lk['deaths'].get(alias, [])

    # Structural coaching
    if fns:
        public_fns = [f for f in fns if not f['name'].startswith('_')]
        private_fns = [f for f in fns if f['name'].startswith('_')]
        coaching.append(f"I have {len(public_fns)} public and {len(private_fns)} private functions. My API surface is: {', '.join(f['name'] for f in public_fns[:5])}")

    if code.get('classes'):
        for cls in code['classes'][:2]:
            coaching.append(f"Class '{cls['name']}' has {len(cls['methods'])} methods: {', '.join(cls['methods'][:5])}")

    # Dependency coaching
    if edges_in:
        coaching.append(f"My importers: {', '.join(edges_in[:5])}. Breaking my interface affects all of them.")
    if edges_out:
        coaching.append(f"I depend on: {', '.join(edges_out[:5])}. If they change, I might break.")

    # Health coaching
    if tokens > 3000:
        coaching.append(f"At {tokens} tokens I'm bloated. My longest functions are: {', '.join(f['name'] for f in sorted(fns, key=lambda x: -x.get('line', 0))[:3])}")
    if deaths:
        coaching.append(f"I've had {len(deaths)} execution failures. Most recent: {deaths[-1].get('cause', 'unknown')} — {deaths[-1].get('detail', '')[:80]}")
    if ver >= 5:
        coaching.append(f"Version {ver} means heavy churn. The pattern suggests my spec isn't stable yet.")

    # Import coaching
    if code.get('imports'):
        coaching.append(f"My imports: {'; '.join(code['imports'][:6])}")

    return coaching[:6]
