"""streaming_layer/ — Pigeon-compliant module."""
from streaming_layer._resolve import sl_import

EventAggregator = sl_import("streaming_layer_aggregator_seq006", "EventAggregator")
AlertEngine = sl_import("streaming_layer_alerts_seq008", "AlertEngine")
ConnectionPool = sl_import("streaming_layer_connection_pool_seq005", "ConnectionPool")
(AGGREGATION_INTERVALS, ALERT_COOLDOWN_MS, ALERT_THRESHOLDS, COMPACT_SEPARATOR,
 CSV_SEPARATOR, DASHBOARD_REFRESH_MS, DEFAULT_PORT, EVENT_BUFFER_SIZE,
 HEARTBEAT_INTERVAL_MS, MAX_CLIENTS, MAX_REPLAY_EVENTS, PERCENTILE_TARGETS,
 SLIDING_WINDOW_MS, STREAM_FORMATS) = sl_import(
    "streaming_layer_constants_seq001",
    "AGGREGATION_INTERVALS", "ALERT_COOLDOWN_MS", "ALERT_THRESHOLDS",
    "COMPACT_SEPARATOR", "CSV_SEPARATOR", "DASHBOARD_REFRESH_MS", "DEFAULT_PORT",
    "EVENT_BUFFER_SIZE", "HEARTBEAT_INTERVAL_MS", "MAX_CLIENTS",
    "MAX_REPLAY_EVENTS", "PERCENTILE_TARGETS", "SLIDING_WINDOW_MS", "STREAM_FORMATS")
LiveDashboard = sl_import("streaming_layer_dashboard_seq010", "LiveDashboard")
AggregationBucket = sl_import("streaming_layer_dataclasses_seq004", "AggregationBucket")
StreamClient = sl_import("streaming_layer_dataclasses_seq005", "StreamClient")
Alert = sl_import("streaming_layer_dataclasses_seq006", "Alert")
StreamFormatter = sl_import("streaming_layer_formatter_seq004", "StreamFormatter")
TelemetryHTTPHandler = sl_import("streaming_layer_http_handler_seq011", "TelemetryHTTPHandler")
MetricsCollector = sl_import("streaming_layer_metrics_seq007", "MetricsCollector")
StreamingTelemetryServer = sl_import("streaming_layer_orchestrator_seq016", "StreamingTelemetryServer")
run_demo = sl_import("streaming_layer_orchestrator_seq017", "run_demo")
SessionReplay = sl_import("streaming_layer_replay_seq009", "SessionReplay")
