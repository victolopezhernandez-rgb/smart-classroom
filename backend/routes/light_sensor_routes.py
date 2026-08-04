from __future__ import annotations
from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from agents.light_sensor import light_sensor, VALID_WEATHER
from shared.thresholds import NATURAL_LIGHT_OFF_THRESHOLD, NATURAL_LIGHT_DIM_THRESHOLD

router = APIRouter(prefix="/api/light", tags=["light-sensor"])


@router.get("/levels")
def get_levels():
    """Natural light level (0.0–1.0) per zone + weather + hour."""
    return light_sensor.get_levels()


@router.get("/thresholds")
def get_thresholds():
    """Current ON/DIM/OFF decision thresholds."""
    return {
        "off_threshold":  NATURAL_LIGHT_OFF_THRESHOLD,
        "dim_threshold":  NATURAL_LIGHT_DIM_THRESHOLD,
        "description": {
            f">= {NATURAL_LIGHT_OFF_THRESHOLD}": "Lights OFF (enough sunlight)",
            f">= {NATURAL_LIGHT_DIM_THRESHOLD}": "Lights DIM (50% power)",
            f"<  {NATURAL_LIGHT_DIM_THRESHOLD}": "Lights ON  (full power)",
        },
    }


@router.get("/weather-options")
def get_weather_options():
    """List valid weather conditions."""
    return {"options": VALID_WEATHER, "current": light_sensor.weather}


class WeatherRequest(BaseModel):
    weather: str


@router.post("/weather")
def set_weather(body: WeatherRequest):
    """Change weather condition: 'clear' | 'cloudy' | 'overcast' | 'rainy'."""
    try:
        light_sensor.set_weather(body.weather)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    levels = light_sensor.get_levels()
    return {"weather": body.weather, "levels": levels}


class TimeRequest(BaseModel):
    hour: Optional[float] = None  # None = use real time


@router.post("/time")
def set_time(body: TimeRequest):
    """
    Simulate any time of day.
    hour: 0.0–23.99  (e.g., 12.0 = noon, 18.0 = dusk)
    Pass null to reset to real time.
    """
    if body.hour is not None and not (0.0 <= body.hour <= 23.99):
        raise HTTPException(status_code=400, detail="hour must be between 0.0 and 23.99")
    light_sensor.set_simulated_time(body.hour)
    levels = light_sensor.get_levels()
    return {
        "simulated_hour": body.hour,
        "using_real_time": body.hour is None,
        "levels": levels,
    }
