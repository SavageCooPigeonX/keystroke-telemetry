"""层w_sl_s007_v003_d0317_读唤任_λΠ_live_dashboard_seq011_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 011 | VER: v001 | 72 lines | ~787 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────

class LiveDashboard:
    """Terminal-based live dashboard that prints rolling stats."""

    def __init__(self, aggregator: EventAggregator, metrics: MetricsCollector,
                 alerts: AlertEngine, pool: ConnectionPool):
        self.aggregator = aggregator
        self.metrics = metrics
        self.alerts = alerts
        self.pool = pool
        self._refresh_count = 0

    def render(self) -> str:
        self._refresh_count += 1
        snap = self.aggregator.get_snapshot()
        summary = self.metrics.get_summary()
        alert_list = self.alerts.get_alerts(5)
        clients = self.pool.client_count()

        lines = []
        lines.append("╔══════════════════════════════════════════════════════╗")
        lines.append("║         KEYSTROKE TELEMETRY — LIVE DASHBOARD        ║")
        lines.append(f"║  Refresh #{self._refresh_count:<6}  Clients: {clients:<4}  "
                     f"Events: {summary['total_events']:<8} ║")
        lines.append("╠══════════════════════════════════════════════════════╣")

        # Rolling windows
        for ws_key, ws_data in snap.get("windows", {}).items():
            ws_sec = int(ws_key) // 1000
            lines.append(f"║  [{ws_sec}s window] events={ws_data['event_count']:<5} "
                         f"wpm={ws_data['estimated_wpm']:<6} "
                         f"del%={ws_data['deletion_ratio']:<5}   ║")

        lines.append("╠══════════════════════════════════════════════════════╣")

        # Percentiles
        dp = summary.get("delta_percentiles", {})
        lines.append(f"║  Delta P50={dp.get('p50',0):<5} P90={dp.get('p90',0):<5} "
                     f"P99={dp.get('p99',0):<8}        ║")

        wp = summary.get("wpm_percentiles", {})
        lines.append(f"║  WPM   P50={wp.get('p50',0):<5} P90={wp.get('p90',0):<5} "
                     f"P99={wp.get('p99',0):<8}        ║")

        lines.append(f"║  Submit rate: {summary.get('submit_rate', 0):<6} "
                     f"Avg hesitation: {summary.get('avg_hesitation', 0):<6}    ║")

        # Alerts
        if alert_list:
            lines.append("╠══════════════════════════════════════════════════════╣")
            lines.append("║  ALERTS:                                             ║")
            for a in alert_list[-3:]:
                sev = a["severity"].upper()[:4]
                msg = a["message"][:40]
                lines.append(f"║  [{sev}] {msg:<45} ║")

        lines.append("╚══════════════════════════════════════════════════════╝")
        return "\n".join(lines)

    def print_dashboard(self):
        output = self.render()
        # Clear terminal and print
        print("\033[2J\033[H" + output)

    def render_compact(self) -> str:
        snap = self.aggregator.get_snapshot()
        w5 = snap.get("windows", {}).get("5000", {})
        return (f"[LIVE] events={w5.get('event_count', 0)} "
                f"wpm={w5.get('estimated_wpm', 0)} "
                f"del%={w5.get('deletion_ratio', 0)} "
                f"clients={self.pool.client_count()}")
