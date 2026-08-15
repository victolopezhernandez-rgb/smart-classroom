# Shared constants used across all agents

NATURAL_LIGHT_OFF_THRESHOLD  = 0.75   # Above this: turn zone lights OFF
NATURAL_LIGHT_DIM_THRESHOLD  = 0.40   # Above this: DIM the lights (50% power)
HIGH_CONSUMPTION_ALERT_WATTS = 280.0  # Alert if consumption exceeds this
DECISION_INTERVAL_SECONDS = 5        # How often the orchestrator runs
BASELINE_WATTS = 320.0               # All 8 fixtures on
WATTS_PER_ZONE_ON = 80.0             # 2 × 40W fixtures per zone
WATTS_PER_ZONE_DIM = 40.0
WATTS_PER_ZONE_OFF = 0.0
MIN_PEOPLE_TO_KEEP_LIGHTS_ON = 1     # Zone needs at least 1 person for lights to stay on
TARGET_SAVINGS_PERCENT       = 40    # Goal: save at least 40% vs baseline

# ── Live camera vision ────────────────────────────────────────────────────────
LIVE_STALE_SECONDS = 8.0             # No camera data for this long → back to simulation
ROOM_WIDTH_M = 10.0                  # Classroom width  (x axis, meters)
ROOM_DEPTH_M = 8.0                   # Classroom depth  (y axis, meters)
MAX_LIVE_DETECTIONS = 20             # Sanity cap per frame from the browser
