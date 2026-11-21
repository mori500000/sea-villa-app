import math

POLAR_PROFILES: dict[str, dict] = {
    "arctic-01": {
        "name": "Arctic Ice & Cold Water North",
        "lat": 74.0,
        "lon": 19.0,
        "base_sst_c": 2.0,
        "base_air_temp_c": -4.0,
    },
    "antarctic-01": {
        "name": "Southern Ocean Krill & Penguin South",
        "lat": -64.5,
        "lon": -62.0,
        "base_sst_c": 0.5,
        "base_air_temp_c": -3.5,
    },
}


def _clamp01(val: float) -> float:
    return min(1.0, max(0.0, val))


def is_polar_site(lat: float, threshold_deg: float = 45.0) -> bool:
    return abs(lat) >= threshold_deg


def simulate_polar_point(
    *,
    lat: float,
    season: str,
    years_elapsed: int,
    projected_sst_c: float,
    positive_heat: float,
    cumulative_stress: float,
    activity_weight: float,
) -> dict:
    abs_lat = abs(lat)
    hemisphere = "north" if lat >= 0 else "south"
    polar_weight = round(_clamp01((abs_lat - 42.0) / 18.0), 3)

    warmth_stress = _clamp01((projected_sst_c + 1.0) / 10.0) + positive_heat * 0.14 + cumulative_stress * 0.25

    krill_abundance = round(
        _clamp01(polar_weight * (0.95 - warmth_stress * 0.55) * activity_weight),
        3,
    )
    clione_prob = round(
        _clamp01(polar_weight * (0.90 - warmth_stress * 0.60 - cumulative_stress * 0.18)),
        3,
    )
    seal_prob = round(
        _clamp01(polar_weight * (0.88 - warmth_stress * 0.45 - cumulative_stress * 0.25) * activity_weight),
        3,
    )
    penguin_base = 0.92 if hemisphere == "south" else 0.0
    penguin_prob = round(
        _clamp01(polar_weight * penguin_base * (1.0 - warmth_stress * 0.48 - cumulative_stress * 0.22)),
        3,
    )

    return {
        "hemisphere": hemisphere,
        "polar_weight": polar_weight,
        "season": season,
        "years_elapsed": years_elapsed,
        "krill": {"abundance_index": krill_abundance},
        "clione": {"presence_probability": clione_prob},
        "seal": {"presence_probability": seal_prob},
        "penguin": {"presence_probability": penguin_prob},
    }


def format_polar_summary(site_name: str, lat: float, lon: float, year: int, season: str, sst_c: float, air_c: float, cum_stress: float, polar: dict) -> str:
    return (
        f"{site_name}（lat={lat}, lon={lon} / {year}年・{season}）では、"
        f"推定水温 {sst_c:.2f}°C・気温 {air_c:.2f}°C、"
        f"累積ストレス {cum_stress:.3f} により、"
        f"オキアミ {polar['krill']['abundance_index']}、クリオネ {polar['clione']['presence_probability']}、"
        f"アザラシ {polar['seal']['presence_probability']}、ペンギン {polar['penguin']['presence_probability']} と算出されました。"
    )
