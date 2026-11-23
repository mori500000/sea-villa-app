import math
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Optional

ERDDAP_BASE_URL = "https://coastwatch.pfeg.noaa.gov/erddap/griddap/ncdcOisst21Agg_LonPM180.csv"
CACHE_TTL_SECONDS = 3600

_CACHE: dict[tuple[float, float], tuple[float, Optional[float], str]] = {}


def _fallback_sst(lat: float) -> float:
    abs_lat = abs(lat)
    return round(max(-1.5, 29.5 - 0.58 * max(0.0, abs_lat - 10.0)), 2)


def _normalize_lon_180(lon: float) -> float:
    wrapped = ((lon + 180.0) % 360.0) - 180.0
    return round(wrapped, 4)


def _query_erddap_sst(lat: float, lon: float, timeout_sec: float = 10.0) -> Optional[float]:
    target_lat = round(max(-89.875, min(89.875, lat)), 4)
    target_lon = _normalize_lon_180(lon)

    query = f"sst[(last)][(0.0)][({target_lat})][({target_lon})]"
    url = f"{ERDDAP_BASE_URL}?{urllib.parse.quote(query, safe="[](),:")}"

    req = urllib.request.Request(url, headers={"User-Agent": "sea-villa-app/1.0"})
    with urllib.request.urlopen(req, timeout=timeout_sec) as resp:
        body = resp.read().decode("utf-8", errors="replace").strip()

    lines = [line.strip() for line in body.splitlines() if line.strip()]
    if len(lines) < 3:
        return None

    last_cols = [c.strip() for c in lines[-1].split(",")]
    if not last_cols:
        return None

    val_str = last_cols[-1]
    if val_str in ("", "NaN", "nan", "NULL", "null"):
        return None

    val = float(val_str)
    if math.isnan(val) or math.isinf(val):
        return None
    return round(val, 2)


def get_base_sst_c(lat: float, lon: float) -> dict:
    key = (round(lat, 2), round(lon, 2))
    now = time.monotonic()

    cached = _CACHE.get(key)
    if cached and (now - cached[0]) < CACHE_TTL_SECONDS:
        return {
            "base_sst_c": cached[1] if cached[1] is not None else _fallback_sst(lat),
            "source": cached[2],
            "cached": True,
        }

    try:
        sst = _query_erddap_sst(lat=lat, lon=lon)
    except (urllib.error.URLError, TimeoutError, ValueError):
        sst = None

    if sst is not None:
        _CACHE[key] = (now, sst, "erddap_oisst")
        return {"base_sst_c": sst, "source": "erddap_oisst", "cached": False}

    fb = _fallback_sst(lat)
    _CACHE[key] = (now, fb, "fallback_latitude")
    return {"base_sst_c": fb, "source": "fallback_latitude", "cached": False}
