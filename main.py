import math
from typing import Literal, Optional
from fastapi import FastAPI
from pydantic import BaseModel, Field

app = FastAPI(title="Sea Villa Climate Simulator API")

SeasonType = Literal["spring", "summer", "autumn", "winter"]

SITE_PROFILES: dict[str, dict] = {
    "site-01": {
        "name": "Coral & Turtle Reef A",
        "bleaching_sensitivity": 1.05,
        "turtle_sensitivity": 1.00,
        "base_turtle_suitability": 0.92,
    },
    "site-02": {
        "name": "Upwelling & Coastal Bay B",
        "bleaching_sensitivity": 0.75,
        "turtle_sensitivity": 1.15,
        "base_turtle_suitability": 0.88,
    },
}

DEFAULT_PROFILE = {
    "name": "Generic Coastal Site",
    "bleaching_sensitivity": 1.0,
    "turtle_sensitivity": 1.0,
    "base_turtle_suitability": 0.90,
}

SEASON_FACTORS: dict[str, dict[str, float]] = {
    "summer": {"heat_multiplier": 1.20, "turtle_activity_weight": 1.10},
    "autumn": {"heat_multiplier": 1.02, "turtle_activity_weight": 1.00},
    "spring": {"heat_multiplier": 0.92, "turtle_activity_weight": 1.05},
    "winter": {"heat_multiplier": 0.65, "turtle_activity_weight": 0.85},
}


class SimulationRequest(BaseModel):
    location_id: str = Field(..., min_length=1)
    year: int = Field(..., ge=1900, le=2200)
    temperature_anomaly: float = Field(..., ge=-5.0, le=10.0)
    season: SeasonType = "summer"
    base_year: int = Field(2025, ge=1900, le=2200)
    end_year: Optional[int] = Field(None, ge=1900, le=2200)
    include_timeseries: bool = True


def _compute_point(
    profile: dict,
    season_cfg: dict[str, float],
    season: str,
    target_year: int,
    base_year: int,
    temperature_anomaly: float,
) -> dict:
    years_elapsed = max(0, target_year - base_year)
    sign = 1.0 if temperature_anomaly >= 0 else -1.0
    effective_anomaly = (sign * (abs(temperature_anomaly) ** 1.15)) * season_cfg["heat_multiplier"]
    positive_heat = max(0.0, effective_anomaly)
    annual_load = positive_heat * profile["bleaching_sensitivity"]
    cumulative_stress = round(min(1.0, max(0.0, 1.0 - math.exp(-(years_elapsed * annual_load) / 55.0))), 3)
    bleaching_rate = round(
        min(100.0, max(0.0, positive_heat * 18.0 * profile["bleaching_sensitivity"] + cumulative_stress * 38.0)),
        2,
    )
    coral_status = (
        "severely_bleached (ruins)"
        if bleaching_rate >= 70.0
        else ("partially_bleached" if bleaching_rate >= 30.0 else "healthy")
    )
    raw_turtle_prob = (
        profile["base_turtle_suitability"] * season_cfg["turtle_activity_weight"]
        - positive_heat * 0.09 * profile["turtle_sensitivity"]
        - cumulative_stress * 0.24 * profile["turtle_sensitivity"]
    )
    turtle_presence = round(min(1.0, max(0.0, raw_turtle_prob)), 3)
    return {
        "year": target_year,
        "years_elapsed": years_elapsed,
        "season": season,
        "effective_temperature_anomaly": round(effective_anomaly, 3),
        "cumulative_stress": cumulative_stress,
        "coral_health": {
            "bleaching_rate_percent": bleaching_rate,
            "status": coral_status,
        },
        "sea_turtle": {
            "presence_probability": turtle_presence,
        },
    }


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/simulate")
def simulate_ecosystem(req: SimulationRequest):
    profile = SITE_PROFILES.get(req.location_id, DEFAULT_PROFILE)
    season_cfg = SEASON_FACTORS[req.season]
    current = _compute_point(
        profile, season_cfg, req.season, req.year, req.base_year, req.temperature_anomaly
    )
    timeseries = None
    if req.include_timeseries:
        start_yr = min(req.base_year, req.year)
        end_yr = req.end_year if req.end_year is not None else max(req.base_year, req.year)
        if end_yr < start_yr:
            start_yr, end_yr = end_yr, start_yr
        timeseries = [
            _compute_point(
                profile, season_cfg, req.season, yr, req.base_year, req.temperature_anomaly
            )
            for yr in range(start_yr, end_yr + 1)
        ]
    br = current["coral_health"]["bleaching_rate_percent"]
    st = current["coral_health"]["status"]
    tp = current["sea_turtle"]["presence_probability"]
    summary = (
        f"{profile['name']}（{req.year}年・{req.season}）では、"
        f"気温偏差 {req.temperature_anomaly:+.1f}°C（実効 {current['effective_temperature_anomaly']:+.2f}°C）と"
        f"{current['years_elapsed']}年間の累積ストレス（{current['cumulative_stress']:.3f}）により、"
        f"サンゴ白化率は {br}%（{st}）、ウミガメ生息確率は {tp} と算出されました。"
    )
    res = {
        "location_id": req.location_id,
        "location_name": profile["name"],
        "year": req.year,
        "base_year": req.base_year,
        "years_elapsed": current["years_elapsed"],
        "season": req.season,
        "temperature_anomaly": req.temperature_anomaly,
        "effective_temperature_anomaly": current["effective_temperature_anomaly"],
        "cumulative_stress": current["cumulative_stress"],
        "coral_health": current["coral_health"],
        "sea_turtle": current["sea_turtle"],
        "summary": summary,
    }
    if timeseries is not None:
        res["timeseries"] = timeseries
    return res
