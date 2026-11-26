import math
from typing import Any


def _clamp(val: float, low: float, high: float) -> float:
    return max(low, min(high, val))


def _clamp01(val: float) -> float:
    return _clamp(val, 0.0, 1.0)


def compute_effective_viability(base_viability: float, base_sst_c: float) -> float:
    """
    緯度ベースの生息適性度と基準水温（base_sst_c）から、地点ごとの実効適性度を算出する。
    低水温域（寒流・湧昇・高緯度）では適性度が低下し、高温域でも熱限界に応じて変化する。
    """
    cold_suitability = _clamp01((base_sst_c - 18.5) / 8.5)
    warm_suitability = _clamp(1.05 - max(0.0, base_sst_c - 27.5) * 0.08, 0.45, 1.05)
    return round(_clamp01(base_viability * cold_suitability * warm_suitability), 4)


def compute_coral_heat_metrics(
    *,
    base_sst_c: float,
    base_air_temp_c: float,
    season_cfg: dict[str, float],
    summer_sst_offset_c: float,
    sst_anomaly: float,
    air_anomaly: float,
    years_elapsed: int,
    sst_cooling_c: float,
    air_cooling_c: float,
    dimming_stress: float,
    eco_risk: float,
    bleaching_sensitivity: float,
    coral_viability: float,
) -> dict[str, Any]:
    """
    地点の基準水温・季節・最暖月基準（MMM相当）・介入効果をもとに、
    推定水温/気温、HotSpot、白化率、累積ダメージ指標を算出する。
    """
    years = max(0, int(years_elapsed))

    seasonal_sst_c = base_sst_c + season_cfg.get("sst_offset_c", 0.0)
    seasonal_air_c = base_air_temp_c + season_cfg.get("air_offset_c", 0.0)
    mmm_sst_c = base_sst_c + summer_sst_offset_c

    trend_factor = 1.0 + min(0.45, years * 0.014)

    current_sst_anomaly = (sst_anomaly * trend_factor) - sst_cooling_c
    current_air_anomaly = (air_anomaly * trend_factor) - air_cooling_c

    projected_sst_c = round(seasonal_sst_c + current_sst_anomaly, 2)
    projected_air_c = round(seasonal_air_c + current_air_anomaly, 2)

    # 基準水温・季節オフセットに応じた熱ストレス応答の違い
    sst_regime_factor = _clamp(0.65 + (base_sst_c - 20.0) * 0.055, 0.45, 1.35)
    season_heat_factor = _clamp(0.75 + season_cfg.get("sst_offset_c", 0.0) * 0.12, 0.55, 1.25)

    hotspot_c = max(0.0, projected_sst_c - mmm_sst_c)
    heat_mult = season_cfg.get("heat_multiplier", 1.0)
    positive_heat = (hotspot_c ** 1.15) * heat_mult * sst_regime_factor * season_heat_factor

    effective_viability = compute_effective_viability(coral_viability, base_sst_c)

    annual_load = positive_heat * bleaching_sensitivity
    cumulative_stress = round(
        _clamp01(1.0 - math.exp(-(years * annual_load) / 45.0) + eco_risk * 0.25),
        3,
    )

    acute_bleaching_component = positive_heat * 22.0 * bleaching_sensitivity
    chronic_bleaching_component = cumulative_stress * 38.0
    dimming_bleaching_component = dimming_stress * 12.0

    raw_bleaching = (
        acute_bleaching_component
        + chronic_bleaching_component
        + dimming_bleaching_component
    ) * effective_viability
    bleaching_rate = round(_clamp(raw_bleaching, 0.0, 100.0), 2)

    raw_damage = (
        cumulative_stress * 55.0
        + max(0.0, hotspot_c - 1.0) * 14.0 * bleaching_sensitivity
        + eco_risk * 20.0
    ) * effective_viability
    mortality_risk_percent = round(_clamp(raw_damage, 0.0, 100.0), 2)

    return {
        "mmm_sst_c": round(mmm_sst_c, 2),
        "current_sst_anomaly": current_sst_anomaly,
        "current_air_anomaly": current_air_anomaly,
        "projected_sst_c": projected_sst_c,
        "projected_air_c": projected_air_c,
        "hotspot_c": round(hotspot_c, 3),
        "positive_heat": positive_heat,
        "effective_viability": effective_viability,
        "cumulative_stress": cumulative_stress,
        "bleaching_rate": bleaching_rate,
        "mortality_risk_percent": mortality_risk_percent,
        "breakdown": {
            "acute_heat": round(acute_bleaching_component * effective_viability, 2),
            "cumulative_stress": round(chronic_bleaching_component * effective_viability, 2),
            "light_dimming": round(dimming_bleaching_component * effective_viability, 2),
        },
    }
