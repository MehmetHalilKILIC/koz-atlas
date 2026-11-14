import os
import io
import requests
import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error

BBOX_BATMAN_TR = (40.0, 37.4, 42.2, 38.6)
BBOX_STR = "40.0,37.4,42.2,38.6"

def parse_and_filter_aoi(df, source_label, filter_bbox=True):
    if df is None or df.empty:
        return pd.DataFrame()
    df = df.copy()
    df["source_label"] = source_label
    if filter_bbox:
        w, s, e, n = BBOX_BATMAN_TR
        df = df[(df["longitude"] >= w) & (df["longitude"] <= e) &
                (df["latitude"] >= s) & (df["latitude"] <= n)].copy()
    if df.empty:
        return df
    t_str = df["acq_time"].astype(str).str.zfill(4)
    df["observed_at_utc"] = pd.to_datetime(
        df["acq_date"].astype(str) + " " + t_str.str[:2] + ":" + t_str.str[2:],
        utc=True, errors="coerce"
    )
    df["year"] = df["observed_at_utc"].dt.year
    df["month"] = df["observed_at_utc"].dt.month
    df["date_str"] = df["acq_date"].astype(str)
    df["site_grid"] = (df["latitude"].round(2)).astype(str) + "_" + (df["longitude"].round(2)).astype(str)
    return df

def fetch_firms_nrt(map_key, source="VIIRS_NOAA20_NRT", days=5):
    if not map_key or len(map_key.strip()) < 10:
        return pd.DataFrame(), "API_KEY_EKSIK"
    url = f"https://firms.modaps.eosdis.nasa.gov/api/area/csv/{map_key.strip()}/{source}/{BBOX_STR}/{days}"
    try:
        r = requests.get(url, timeout=25)
        if r.status_code != 200:
            return pd.DataFrame(), f"HTTP_HATA_{r.status_code}"
        if "latitude" not in r.text:
            return pd.DataFrame(), f"API_MESAJI: {r.text[:80].strip()}"
        df = pd.read_csv(io.StringIO(r.text))
        return parse_and_filter_aoi(df, source, filter_bbox=True), "BASARILI"
    except Exception as e:
        return pd.DataFrame(), f"BAGLANTI_HATASI: {str(e)[:60]}"

def haversine_km(lat1, lon1, lat2, lon2):
    r = 6371.0
    phi1, phi2 = np.radians(lat1), np.radians(lat2)
    dphi = np.radians(lat2 - lat1)
    dlambda = np.radians(lon2 - lon1)
    a = np.sin(dphi / 2.0) ** 2 + np.cos(phi1) * np.cos(phi2) * np.sin(dlambda / 2.0) ** 2
    return 2.0 * r * np.arcsin(np.sqrt(a))

def match_aqua_and_viirs(modis_df, viirs_df, max_dist_km=2.0, max_time_min=180.0, include_terra=False):
    if modis_df.empty or viirs_df.empty:
        return pd.DataFrame(), {"status": "Veri setlerinden biri bos."}

    sat_col = modis_df["satellite"].astype(str).str.upper()
    aqua_mask = sat_col.isin(["A", "AQUA"])
    aqua_count = int(aqua_mask.sum())
    terra_count = int(len(modis_df) - aqua_count)

    target_modis = modis_df.copy().reset_index(drop=True) if include_terra else modis_df[aqua_mask].copy().reset_index(drop=True)
    viirs_df = viirs_df.copy().reset_index(drop=True)

    m_years = sorted(target_modis["year"].dropna().unique().tolist())
    v_years = sorted(viirs_df["year"].dropna().unique().tolist())
    common_dates = set(target_modis["date_str"]).intersection(set(viirs_df["date_str"]))

    merged = pd.merge(target_modis, viirs_df, on=["date_str"], suffixes=("_aqua", "_viirs"))

    if merged.empty:
        return pd.DataFrame(), {
            "total_modis": len(modis_df), "aqua_records": aqua_count, "terra_records": terra_count,
            "viirs_records": len(viirs_df), "modis_years": m_years, "viirs_years": v_years,
            "common_dates_count": len(common_dates), "matched_aqua_events": 0, "independent_days": 0,
            "warning": "Iki dosyada ortak tarih bulunamadi! Lutfen AYNI YILIN MODIS ve VIIRS dosyalarini yukleyin."
        }

    merged["time_diff_min"] = (merged["observed_at_utc_viirs"] - merged["observed_at_utc_aqua"]).abs().dt.total_seconds() / 60.0
    merged["dist_km"] = haversine_km(
        merged["latitude_aqua"].values, merged["longitude_aqua"].values,
        merged["latitude_viirs"].values, merged["longitude_viirs"].values
    )

    valid = merged[(merged["dist_km"] <= max_dist_km) & (merged["time_diff_min"] <= max_time_min)].copy()

    if valid.empty:
        return pd.DataFrame(), {
            "total_modis": len(modis_df), "aqua_records": aqua_count, "terra_records": terra_count,
            "viirs_records": len(viirs_df), "modis_years": m_years, "viirs_years": v_years,
            "common_dates_count": len(common_dates), "matched_aqua_events": 0, "independent_days": 0,
            "min_dist_found_km": round(float(merged["dist_km"].min()), 2),
            "min_time_found_min": round(float(merged["time_diff_min"].min()), 1)
        }

    pairs = valid.groupby(
        ["date_str", "latitude_aqua", "longitude_aqua", "frp_aqua", "year_aqua", "month_aqua"],
        as_index=False
    ).agg(
        viirs_frp_sum=("frp_viirs", "sum"),
        viirs_subpixel_count=("frp_viirs", "count"),
        min_dist_km=("dist_km", "min"),
        median_time_diff_min=("time_diff_min", "median")
    ).rename(columns={
        "frp_aqua": "aqua_frp", "year_aqua": "year", "month_aqua": "month",
        "latitude_aqua": "latitude", "longitude_aqua": "longitude"
    })

    matched_viirs_unique = valid[["latitude_viirs", "longitude_viirs", "observed_at_utc_viirs"]].drop_duplicates()

    summary = {
        "total_modis": len(modis_df),
        "aqua_records": aqua_count,
        "terra_records": terra_count,
        "viirs_records": len(viirs_df),
        "modis_years": m_years,
        "viirs_years": v_years,
        "common_dates_count": len(common_dates),
        "matched_aqua_events": len(pairs),
        "matched_viirs_unique_pixels": len(matched_viirs_unique),
        "aqua_codetection_pct": round(len(pairs) / max(len(target_modis), 1) * 100, 1),
        "viirs_codetection_pct": round(len(matched_viirs_unique) / max(len(viirs_df), 1) * 100, 1),
        "independent_days": int(pairs["date_str"].nunique()),
        "median_time_diff_min": round(float(pairs["median_time_diff_min"].median()), 1)
    }
    return pairs, summary

def calibrate_frp_time_block(pairs_df):
    if pairs_df.empty or pairs_df["date_str"].nunique() < 3 or len(pairs_df) < 8:
        return None, {"calibrated": False, "reason": "Bagimsiz gozlem gunu (<3) veya eslesme (<8) yetersiz."}
    pairs_sorted = pairs_df.sort_values("date_str").reset_index(drop=True)
    split_idx = int(len(pairs_sorted) * 0.75)
    train = pairs_sorted.iloc[:split_idx]
    test = pairs_sorted.iloc[split_idx:]
    X_train = np.log1p(train[["viirs_frp_sum"]].values)
    y_train = np.log1p(train["aqua_frp"].values)
    X_test = np.log1p(test[["viirs_frp_sum"]].values)
    y_test = test["aqua_frp"].values
    model = Ridge(alpha=1.0)
    model.fit(X_train, y_train)
    pred_frp = np.expm1(model.predict(X_test))
    raw_mae = mean_absolute_error(y_test, test["viirs_frp_sum"].values)
    cal_mae = mean_absolute_error(y_test, pred_frp)
    return model, {
        "calibrated": True,
        "train_events": len(train),
        "test_events": len(test),
        "test_independent_days": int(test["date_str"].nunique()),
        "raw_mae_mw": round(float(raw_mae), 2),
        "calibrated_mae_mw": round(float(cal_mae), 2),
        "better_than_raw": bool(cal_mae < raw_mae)
    }

def analyze_static_and_recurring_sites(df):
    if df.empty:
        return pd.DataFrame()
    df = df.copy()
    if "type" not in df.columns:
        df["type"] = -1
    sites = df.groupby("site_grid", as_index=False).agg(
        center_lat=("latitude", "mean"),
        center_lon=("longitude", "mean"),
        total_detections=("frp", "count"),
        distinct_days=("acq_date", "nunique"),
        distinct_months=("month", "nunique"),
        mean_frp_mw=("frp", "mean"),
        has_nasa_type2=("type", lambda s: bool((s == 2).any())),
        type2_record_count=("type", lambda s: int((s == 2).sum()))
    )
    return sites[(sites["distinct_days"] >= 2) | (sites["has_nasa_type2"])].sort_values(["distinct_months", "distinct_days"], ascending=False).reset_index(drop=True)
