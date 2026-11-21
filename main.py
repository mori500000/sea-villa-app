from typing import Literal
from fastapi import FastAPI
from pydantic import BaseModel, Field

app = FastAPI(title="Sea Villa Climate Simulator API")

SeasonType = Literal["spring", "summer", "autumn", "winter"]

SITE_PROFILES: dict[str, dict] = {
    "site-01": {
        "name": "Coral & Turtle Reef A",
        "bleaching_sensitivity": 1.15,
        "turtle_sensitivity": 1.10,
        "base_turtle_suitability": 0.92,
    },
    "site-02": {
        "name": "Upwelling & Coastal Bay B",
        "bleaching_sensitivity": 0.85,
        "turtle_sensitivity": 1.25,
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
    "summer": {"heat_multiplier": 1.25, "turtle_activity_weight": 1.15},
    "autumn": {"heat_multiplier": 1.05, "turtle_activity_weight": 1.00},
    "spring": {"heat_multiplier": 0.95, "turtle_activity_weight": 1.05},
    "winter": {"heat_multiplier": 0.70, "turtle_activity_weight": 0.80},
}


class SimulationRequest(BaseModel):
    location_id: str = Field(..., min_length=1)
    year: int = Field(..., ge=1900, le=2200)
    temperature_anomaly: float = Field(..., ge=-5.0, le=10.0)
    season: SeasonType = "summer"
    base_year: int = Field(2025, ge=1900, le=2200)


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/simulate")
def simulate_ecosystem(req: SimulationRequest):
    profile = SITE_PROFILES.get(req.location_id, DEFAULT_PROFILE)
    season_cfg = SEASON_FACTORS[req.season]

    years_elapsed = max(0, req.year - req.base_year)
    effective_anomaly = req.temperature_anomaly * season_cfg["heat_multiplier"]

    annual_pressure = max(0.0, effective_anomaly) * profile["bleaching_sensitivity"]
    cumulative_stress = min(1.0, (years_elapsed * max(0.0, annual_pressure)) / 45.0)

    instant_bleaching = max(0.0, annual_pressure * 36.0)
    cumulative_bleaching_boost = cumulative_stress * 35.0
    bleaching_rate = round(min(100.0, instant_bleaching + cumulative_bleaching_boost), 2)

    if bleaching_rate >= 70.0:
        coral_status = "severely_bleached (ruins)"
    elif bleaching_rate >= 30.0:
        coral_status = "partially_bleached"
    else:
        coral_status = "healthy"

    heat_penalty = max(0.0, effective_anomaly) * 0.18 * profile["turtle_sensitivity"]
    cumulative_penalty = cumulative_stress * 0.35 * profile["turtle_sensitivity"]
    raw_turtle_prob = (
        profile["base_turtle_suitability"]
        * season_cfg["turtle_activity_weight"]
        - heat_penalty
        - cumulative_penalty
    )
    turtle_presence = round(min(1.0, max(0.0, raw_turtle_prob)), 3)

    summary = (
        f"{profile['name']}（{req.year}年・{req.season}）では、"
        f"気温偏差 {req.temperature_anomaly:+.1f}°C（実効 {effective_anomaly:+.2f}°C）と"
        f"{years_elapsed}年間の累積ストレス（{cumulative_stress:.2f}）により、"
        f"サンゴ白化率は {bleaching_rate}%（{coral_status}）、"
        f"ウミガメ生息確率は {turtle_presence} と算出されました。"
    )

    return {
        "location_id": req.location_id,
        "location_name": profile["name"],
        "year": req.year,
        "base_year": req.base_year,
        "years_elapsed": years_elapsed,
        "season": req.season,
        "temperature_anomaly": req.temperature_anomaly,
        "effective_temperature_anomaly": round(effective_anomaly, 3),
        "cumulative_stress": round(cumulative_stress, 3),
        "coral_health": {
            "bleaching_rate_percent": bleaching_rate,
            "status": coral_status,
        },
        "sea_turtle": {
            "presence_probability": turtle_presence,
        },
        "summary": summary,
    }
