import math

SUNRISE_HOUR = 6.0
SUNSET_HOUR  = 18.0

WEATHER_MULTIPLIERS = {
    "clear":    1.00,
    "cloudy":   0.55,
    "overcast": 0.30,
    "rainy":    0.15,
}

# Windows are on the LEFT WALL (x=0); zones A and C face them directly
WINDOW_EXPOSURE = {
    "zone_A": 1.00,
    "zone_C": 0.70,
    "zone_B": 0.40,
    "zone_D": 0.20,
}


def calculate_sun_intensity(hour: float) -> float:
    """
    Returns sun intensity (0.0–1.0) for a given hour.
    Uses a sine curve that peaks at solar noon (12:00).
    Returns 0.0 before sunrise and after sunset.
    """
    if hour < SUNRISE_HOUR or hour > SUNSET_HOUR:
        return 0.0
    normalized = (hour - SUNRISE_HOUR) / (SUNSET_HOUR - SUNRISE_HOUR)
    return round(max(0.0, min(1.0, math.sin(normalized * math.pi))), 3)


def calculate_light_levels(hour: float, weather: str) -> dict:
    """
    Returns natural light level (0.0–1.0) per classroom zone.

    Args:
        hour:    Current hour (0.0–23.99)
        weather: "clear" | "cloudy" | "overcast" | "rainy"

    Returns:
        {"zone_A": 0.82, "zone_B": 0.31, "zone_C": 0.55, "zone_D": 0.18}
    """
    sun = calculate_sun_intensity(hour)
    weather_factor = WEATHER_MULTIPLIERS.get(weather, 1.0)

    return {
        zone: round(max(0.0, min(1.0, sun * weather_factor * exposure)), 3)
        for zone, exposure in WINDOW_EXPOSURE.items()
    }
