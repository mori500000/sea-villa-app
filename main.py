import math
from typing import Literal, Optional
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from sst_provider import get_base_sst_c
from polar_ecosystem import (
    POLAR_PROFILES,
    format_polar_summary,
    is_polar_site,
    simulate_polar_point,
)

app = FastAPI(title="Sea Villa Climate Simulator API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

SeasonType = Literal["spring", "summer", "autumn", "winter"]

SITE_PROFILES: dict[str, dict] = {
    "site-01": {
        "name": "Coral & Turtle Reef A",
        "lat": 26.2124,
        "lon": 127.6809,
        "base_sst_c": 26.5,
        "base_air_temp_c": 24.0,
        "bleaching_sensitivity": 1.05,
        "turtle_sensitivity": 1.00,
        "base_turtle_suitability": 0.92,
    },
    "site-02": {
        "name": "Upwelling & Coastal Bay B",
        "lat": 31.5602,
        "lon": 130.5581,
        "base_sst_c": 22.8,
        "base_air_temp_c": 19.5,
        "bleaching_sensitivity": 0.80,
        "turtle_sensitivity": 1.10,
        "base_turtle_suitability": 0.88,
    },
}

SEASON_FACTORS: dict[str, dict[str, float]] = {
    "summer": {"sst_offset_c": 2.2, "air_offset_c": 4.5, "heat_multiplier": 1.20, "activity_weight": 1.10},
    "autumn": {"sst_offset_c": 0.5, "air_offset_c": 0.5, "heat_multiplier": 1.02, "activity_weight": 1.00},
    "spring": {"sst_offset_c": -0.6, "air_offset_c": -0.5, "heat_multiplier": 0.92, "activity_weight": 1.05},
    "winter": {"sst_offset_c": -2.4, "air_offset_c": -5.0, "heat_multiplier": 0.65, "activity_weight": 0.85},
}


class SimulationRequest(BaseModel):
    location_id: str = Field("custom-point", min_length=1)
    lat: Optional[float] = Field(None, ge=-90.0, le=90.0)
    lon: Optional[float] = Field(None, ge=-180.0, le=180.0)
    base_sst_c: Optional[float] = Field(None, ge=-3.0, le=40.0)
    base_air_temp_c: Optional[float] = Field(None, ge=-60.0, le=55.0)
    year: int = Field(2050, ge=1900, le=2200)
    temperature_anomaly: float = Field(1.5, ge=-10.0, le=15.0)
    sea_temp_anomaly: Optional[float] = Field(None, ge=-10.0, le=15.0)
    season: SeasonType = "summer"
    base_year: int = Field(2025, ge=1900, le=2200)
    end_year: Optional[int] = Field(None, ge=1900, le=2200)
    include_timeseries: bool = True


def _clamp01(val: float) -> float:
    return min(1.0, max(0.0, val))


def _resolve_site(req: SimulationRequest) -> dict:
    preset = SITE_PROFILES.get(req.location_id) or POLAR_PROFILES.get(req.location_id)
    lat = req.lat if req.lat is not None else (preset["lat"] if preset else 26.5)
    lon = req.lon if req.lon is not None else (preset["lon"] if preset else 127.7)
    abs_lat = abs(lat)

    inferred_sst = round(max(-1.5, 29.5 - 0.58 * max(0.0, abs_lat - 10.0)), 2)
    inferred_air = round(inferred_sst - 2.5, 2)

    if req.base_sst_c is not None:
        base_sst = req.base_sst_c
        sst_source = "manual"
    elif preset and req.lat is None and req.lon is None:
        base_sst = preset["base_sst_c"]
        sst_source = "preset"
    else:
        sst_info = get_base_sst_c(lat, lon)
        base_sst = sst_info["base_sst_c"]
        sst_source = sst_info["source"]
    base_air = (
        req.base_air_temp_c
        if req.base_air_temp_c is not None
        else (preset["base_air_temp_c"] if preset and req.lat is None else inferred_air)
    )

    name = preset["name"] if preset and req.lat is None and req.lon is None else (
        preset["name"] if preset else f"Point ({lat:.4f}, {lon:.4f})"
    )
    bleaching_sens = preset.get("bleaching_sensitivity", 1.0) if preset else 1.0
    turtle_sens = preset.get("turtle_sensitivity", 1.0) if preset else 1.0
    base_turtle = preset.get("base_turtle_suitability", 0.90) if preset else 0.90
    coral_viability = round(_clamp01(1.15 - max(0.0, abs_lat - 24.0) * 0.035), 3)

    return {
        "name": name,
        "lat": round(lat, 6),
        "lon": round(lon, 6),
        "base_sst_c": round(base_sst, 2),
        "sst_source": sst_source,
        "base_air_temp_c": round(base_air, 2),
        "bleaching_sensitivity": bleaching_sens,
        "turtle_sensitivity": turtle_sens,
        "base_turtle_suitability": base_turtle,
        "coral_viability": coral_viability,
    }


def _compute_point(
    site: dict,
    season_cfg: dict[str, float],
    season: str,
    target_year: int,
    base_year: int,
    air_anomaly: float,
    sst_anomaly: float,
) -> dict:
    years_elapsed = max(0, target_year - base_year)

    seasonal_sst_c = site["base_sst_c"] + season_cfg["sst_offset_c"]
    seasonal_air_c = site["base_air_temp_c"] + season_cfg["air_offset_c"]

    trend_factor = 1.0 + min(0.45, years_elapsed * 0.014)
    current_sst_anomaly = sst_anomaly * trend_factor
    current_air_anomaly = air_anomaly * trend_factor

    projected_sst_c = round(seasonal_sst_c + current_sst_anomaly, 2)
    projected_air_c = round(seasonal_air_c + current_air_anomaly, 2)

    sign = 1.0 if current_sst_anomaly >= 0 else -1.0
    curved_sst_anom = sign * (abs(current_sst_anomaly) ** 1.15)
    effective_heat_stress = curved_sst_anom * season_cfg["heat_multiplier"]
    positive_heat = max(0.0, effective_heat_stress)

    annual_load = positive_heat * site["bleaching_sensitivity"]
    cumulative_stress = round(_clamp01(1.0 - math.exp(-(years_elapsed * annual_load) / 60.0)), 3)

    raw_bleaching = (
        positive_heat * 17.5 * site["bleaching_sensitivity"] + cumulative_stress * 36.0
    ) * site["coral_viability"]
    bleaching_rate = round(min(100.0, max(0.0, raw_bleaching)), 2)

    if bleaching_rate >= 70.0:
        coral_status = "severely_bleached (ruins)"
    elif bleaching_rate >= 30.0:
        coral_status = "partially_bleached"
    else:
        coral_status = "healthy"

    coral_intactness = 1.0 - (bleaching_rate / 100.0)
    clownfish_prob = round(
        _clamp01(
            site["coral_viability"]
            * (0.35 + 0.65 * coral_intactness)
            * season_cfg["activity_weight"]
            - positive_heat * 0.08
            - cumulative_stress * 0.20
        ),
        3,
    )

    turtle_prob = round(
        _clamp01(
            site["base_turtle_suitability"] * season_cfg["activity_weight"]
            - positive_heat * 0.085 * site["turtle_sensitivity"]
            - cumulative_stress * 0.22 * site["turtle_sensitivity"]
        ),
        3,
    )

    degradation = min(1.0, (bleaching_rate / 100.0) * 0.7 + cumulative_stress * 0.3)
    if degradation >= 0.65:
        appearance_state = "murky_algae_shifted"
        hex_color = "#5E6B48"
    elif degradation >= 0.30:
        appearance_state = "fading_turquoise"
        hex_color = "#38A3A5"
    else:
        appearance_state = "vibrant_coral_lagoon"
        hex_color = "#00B4D8"

    point = {
        "year": target_year,
        "years_elapsed": years_elapsed,
        "season": season,
        "environment": {
            "projected_sst_c": projected_sst_c,
            "projected_air_temp_c": projected_air_c,
            "effective_sst_anomaly_c": round(current_sst_anomaly, 3),
            "effective_air_temp_anomaly_c": round(current_air_anomaly, 3),
        },
        "cumulative_stress": cumulative_stress,
        "coral_health": {
            "bleaching_rate_percent": bleaching_rate,
            "status": coral_status,
            "coral_viability": site["coral_viability"],
        },
        "clownfish": {"presence_probability": clownfish_prob},
        "sea_turtle": {"presence_probability": turtle_prob},
        "sea_appearance": {"state": appearance_state, "hex_color": hex_color},
    }

    if is_polar_site(site["lat"]):
        point["polar_ecosystem"] = simulate_polar_point(
            lat=site["lat"],
            season=season,
            years_elapsed=years_elapsed,
            projected_sst_c=projected_sst_c,
            positive_heat=positive_heat,
            cumulative_stress=cumulative_stress,
            activity_weight=season_cfg["activity_weight"],
        )

    return point


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/simulate")
def simulate_ecosystem(req: SimulationRequest):
    site = _resolve_site(req)
    season_cfg = SEASON_FACTORS[req.season]

    air_anom = req.temperature_anomaly
    sst_anom = req.sea_temp_anomaly if req.sea_temp_anomaly is not None else round(req.temperature_anomaly * 0.85, 3)

    current = _compute_point(
        site=site,
        season_cfg=season_cfg,
        season=req.season,
        target_year=req.year,
        base_year=req.base_year,
        air_anomaly=air_anom,
        sst_anomaly=sst_anom,
    )

    timeseries = None
    if req.include_timeseries:
        start_yr = min(req.base_year, req.year)
        end_yr = req.end_year if req.end_year is not None else max(req.base_year, req.year)
        if end_yr < start_yr:
            start_yr, end_yr = end_yr, start_yr
        timeseries = [
            _compute_point(
                site=site,
                season_cfg=season_cfg,
                season=req.season,
                target_year=yr,
                base_year=req.base_year,
                air_anomaly=air_anom,
                sst_anomaly=sst_anom,
            )
            for yr in range(start_yr, end_yr + 1)
        ]

    env = current["environment"]
    if "polar_ecosystem" in current:
        summary = format_polar_summary(
            site_name=site["name"],
            lat=site["lat"],
            lon=site["lon"],
            year=req.year,
            season=req.season,
            sst_c=env["projected_sst_c"],
            air_c=env["projected_air_temp_c"],
            cum_stress=current["cumulative_stress"],
            polar=current["polar_ecosystem"],
        )
    else:
        summary = (
            f"{site['name']}（lat={site['lat']}, lon={site['lon']} / {req.year}年・{req.season}）では、"
            f"推定水温 {env['projected_sst_c']:.2f}°C・気温 {env['projected_air_temp_c']:.2f}°C、"
            f"累積ストレス {current['cumulative_stress']:.3f} により、"
            f"サンゴ白化率 {current['coral_health']['bleaching_rate_percent']}%（{current['coral_health']['status']}）、"
            f"クマノミ {current['clownfish']['presence_probability']}、ウミガメ {current['sea_turtle']['presence_probability']}、"
            f"海色 {current['sea_appearance']['state']}（{current['sea_appearance']['hex_color']}）と算出されました。"
        )

    res = {
        "location_id": req.location_id,
        "location_name": site["name"],
        "coordinates": {"lat": site["lat"], "lon": site["lon"]},
        "baseline_climate": {
            "base_sst_c": site["base_sst_c"],
        "sst_source": site["sst_source"],
            "base_air_temp_c": site["base_air_temp_c"],
            "base_year": req.base_year,
        },
        "year": req.year,
        "years_elapsed": current["years_elapsed"],
        "season": req.season,
        "environment": env,
        "cumulative_stress": current["cumulative_stress"],
        "coral_health": current["coral_health"],
        "clownfish": current["clownfish"],
        "sea_turtle": current["sea_turtle"],
        "sea_appearance": current["sea_appearance"],
        "summary": summary,
    }
    if "polar_ecosystem" in current:
        res["polar_ecosystem"] = current["polar_ecosystem"]
    if timeseries is not None:
        res["timeseries"] = timeseries
    return res
