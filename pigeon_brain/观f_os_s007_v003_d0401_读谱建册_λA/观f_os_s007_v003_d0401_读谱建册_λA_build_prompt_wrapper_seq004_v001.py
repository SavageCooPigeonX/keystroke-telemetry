"""观f_os_s007_v003_d0401_读谱建册_λA_build_prompt_wrapper_seq004_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 004 | VER: v001 | 60 lines | ~630 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────

def build_observer_prompt(observation: dict) -> str:
    """Build a prompt for DeepSeek from observation data.

    Same structure as _build_commit_coaching_prompt in git_plugin
    but targeting execution domain.
    """
    sections = []
    sections.append("# Agent Execution Observation Report\n")

    # Graph stats
    g = observation.get("graph", {})
    sections.append(f"## Graph: {g.get('total_nodes', 0)} nodes, "
                    f"{g.get('total_edges', 0)} edges\n")
    for b in g.get("bottlenecks", [])[:3]:
        sections.append(f"- Bottleneck: **{b['name']}** "
                        f"(in_degree={b['in_degree']})")

    # Death summary
    d = observation.get("deaths", {})
    if d:
        sections.append(f"\n## Deaths: {d.get('total_deaths', 0)} total, "
                        f"{d.get('critical_rate', 0):.0%} critical")
        for node in d.get("worst_nodes", [])[:3]:
            sections.append(f"- **{node['node']}**: {node['deaths']} deaths")
        by_cause = d.get("by_cause", {})
        if by_cause:
            sections.append(f"- Causes: {by_cause}")

    # Loop summary
    lp = observation.get("loops", {})
    if lp and lp.get("recurring_paths"):
        sections.append(f"\n## Loops: {lp.get('internal_loops', 0)} detected")
        for rp in lp.get("recurring_paths", [])[:3]:
            sections.append(f"- `{rp['path']}` — {rp['count']}x "
                            f"(last: {rp['last_status']})")

    # Heat zones
    h = observation.get("heat", {})
    if h and h.get("danger_zones"):
        sections.append(f"\n## Danger Zones")
        for dz in h.get("danger_zones", [])[:3]:
            sections.append(f"- **{dz['node']}**: {dz['deaths']} deaths, "
                            f"death_rate={dz['death_rate']:.0%}, "
                            f"top_cause={dz['top_cause']}")

    # Dual-substrate hotspots (the killer feature)
    dual = observation.get("dual_substrate_hotspots", [])
    if dual:
        sections.append(f"\n## DUAL-SUBSTRATE HOTSPOTS (human + agent failures)")
        for ds in dual:
            sections.append(
                f"- **{ds['node']}**: human_hesitation={ds['human_hesitation']:.3f}, "
                f"electron_deaths={ds['electron_deaths']} — "
                f"DECOMPOSE IMMEDIATELY"
            )

    sections.append("\n---\nGenerate 3-5 specific actions to reduce deaths.")
    return "\n".join(sections)
