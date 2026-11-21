def _clamp01(val: float) -> float:
    return min(1.0, max(0.0, val))


def simulate_midlatitude_wetland_point(
    *,
    lat: float,
    season: str,
    years_elapsed: int,
    projected_sst_c: float,
    projected_air_c: float,
    positive_heat: float,
    cumulative_stress: float,
    activity_weight: float,
) -> dict:
    abs_lat = abs(lat)
    # 温帯〜中緯度帯（緯度20〜50度付近）での適合度重み
    midlat_suitability = round(_clamp01(1.0 - max(0.0, abs(abs_lat - 33.0) - 12.0) * 0.04), 3)

    season_shorebird_bonus = {
        "spring": 0.14,
        "autumn": 0.14,
        "summer": 0.02,
        "winter": -0.06,
    }.get(season, 0.0)

    warmth_load = _clamp01((projected_sst_c - 18.0) / 14.0) + _clamp01((projected_air_c - 18.0) / 16.0) * 0.5

    # シギ・チドリ（渡り・干潟・沿岸湿地利用）
    sandpiper_plover_prob = round(
        _clamp01(
            midlat_suitability
            * (0.82 + season_shorebird_bonus)
            * activity_weight
            - positive_heat * 0.07
            - cumulative_stress * 0.22
            - warmth_load * 0.12
        ),
        3,
    )

    # 湿地のカニ（干潟・汽水・湿地底生環境）
    wetland_crabs_index = round(
        _clamp01(
            midlat_suitability
            * 0.88
            * activity_weight
            - positive_heat * 0.075
            - cumulative_stress * 0.24
            - warmth_load * 0.14
        ),
        3,
    )

    # イルカ（中緯度沿岸〜外洋の回遊・出現適性）
    dolphins_prob = round(
        _clamp01(
            midlat_suitability
            * 0.85
            * activity_weight
            - positive_heat * 0.065
            - cumulative_stress * 0.19
            - _clamp01((projected_sst_c - 26.0) / 10.0) * 0.15
        ),
        3,
    )

    # アシカ（やや涼しい中緯度〜移行帯の沿岸・岩礁利用適性）
    cool_midlat_factor = _clamp01(0.55 + max(0.0, abs_lat - 30.0) * 0.035)
    sea_lions_prob = round(
        _clamp01(
            midlat_suitability
            * cool_midlat_factor
            * 0.82
            * activity_weight
            - positive_heat * 0.08
            - cumulative_stress * 0.23
            - _clamp01((projected_sst_c - 16.0) / 12.0) * 0.25
        ),
        3,
    )

    return {
        "midlatitude_suitability": midlat_suitability,
        "season": season,
        "years_elapsed": years_elapsed,
        "shorebirds_sandpiper_plover": {"presence_probability": sandpiper_plover_prob},
        "wetland_crabs": {"habitat_index": wetland_crabs_index},
        "dolphins": {"presence_probability": dolphins_prob},
        "sea_lions": {"presence_probability": sea_lions_prob},
    }


def format_midlatitude_wetland_summary(
    site_name: str,
    lat: float,
    lon: float,
    year: int,
    season: str,
    sst_c: float,
    air_c: float,
    cum_stress: float,
    data: dict,
) -> str:
    return (
        f"{site_name}（lat={lat}, lon={lon} / {year}年・{season}）では、"
        f"推定水温 {sst_c:.2f}°C・気温 {air_c:.2f}°C、"
        f"累積ストレス {cum_stress:.3f} により、"
        f"シギ・チドリ {data['shorebirds_sandpiper_plover']['presence_probability']}、"
        f"湿地のカニ {data['wetland_crabs']['habitat_index']}、"
        f"イルカ {data['dolphins']['presence_probability']}、"
        f"アシカ {data['sea_lions']['presence_probability']} と算出されました。"
    )
