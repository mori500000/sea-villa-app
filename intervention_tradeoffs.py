import math
from typing import Optional
from pydantic import BaseModel, Field


class InterventionParams(BaseModel):
    wind_power_gw: float = Field(0.0)
    aerosol_injection_mt: float = Field(0.0)
    cdr_gt: float = Field(0.0)


def _clamp01(val: float) -> float:
    return min(1.0, max(0.0, val))


def _sanitize_unbounded(val: float, limit: float = 1e15) -> float:
    if math.isnan(val) or math.isinf(val):
        return 0.0
    return max(-limit, min(limit, float(val)))


def evaluate_interventions(
    interventions: Optional[InterventionParams],
    years_elapsed: int,
) -> dict:
    src = interventions or InterventionParams()
    wind_raw = _sanitize_unbounded(src.wind_power_gw)
    aerosol_raw = _sanitize_unbounded(src.aerosol_injection_mt)
    cdr_raw = _sanitize_unbounded(src.cdr_gt)

    wind_pos = max(0.0, wind_raw)
    aerosol_pos = max(0.0, aerosol_raw)
    cdr_pos = max(0.0, cdr_raw)

    time_scale = _clamp01(0.25 + (years_elapsed / 40.0) * 0.75)

    wind_cooling_c = 0.35 * (1.0 - math.exp(-wind_pos / 500.0))
    aerosol_cooling_c = 1.85 * (1.0 - math.exp(-aerosol_pos / 40.0))
    cdr_cooling_c = 1.60 * (1.0 - math.exp(-cdr_pos / 150.0)) * time_scale

    total_sst_cooling_c = round(wind_cooling_c + aerosol_cooling_c + cdr_cooling_c, 3)
    total_air_cooling_c = round(
        wind_cooling_c * 0.5 + aerosol_cooling_c * 1.15 + cdr_cooling_c * 1.05, 3
    )

    wind_risk = round(_clamp01(1.0 - math.exp(-wind_pos / 2500.0)), 3)
    aerosol_risk = round(_clamp01(1.0 - math.exp(-aerosol_pos / 80.0)), 3)
    cdr_risk = round(_clamp01(1.0 - math.exp(-cdr_pos / 600.0)), 3)

    light_dimming_stress = round(
        _clamp01(0.80 * aerosol_risk + 0.15 * wind_risk + 0.05 * cdr_risk), 3
    )
    ecosystem_side_effect_risk = round(
        _clamp01(0.45 * aerosol_risk + 0.30 * wind_risk + 0.25 * cdr_risk), 3
    )
    net_benefit_index = round(
        _clamp01(0.5 + (total_sst_cooling_c / 3.0) - (ecosystem_side_effect_risk * 0.75)),
        3,
    )

    return {
        "inputs": {
            "wind_power_gw": wind_raw,
            "aerosol_injection_mt": aerosol_raw,
            "cdr_gt": cdr_raw,
        },
        "effective_inputs": {
            "wind_power_gw": wind_pos,
            "aerosol_injection_mt": aerosol_pos,
            "cdr_gt": cdr_pos,
        },
        "cooling_effects": {
            "sst_cooling_c": total_sst_cooling_c,
            "air_temp_cooling_c": total_air_cooling_c,
            "breakdown_sst_cooling_c": {
                "wind_power": round(wind_cooling_c, 3),
                "aerosol_dispersion": round(aerosol_cooling_c, 3),
                "carbon_sequestration": round(cdr_cooling_c, 3),
            },
        },
        "tradeoffs": {
            "light_dimming_stress": light_dimming_stress,
            "ecosystem_side_effect_risk": ecosystem_side_effect_risk,
            "net_benefit_index": net_benefit_index,
            "component_risks": {
                "wind_risk": wind_risk,
                "aerosol_risk": aerosol_risk,
                "cdr_risk": cdr_risk,
            },
        },
    }
