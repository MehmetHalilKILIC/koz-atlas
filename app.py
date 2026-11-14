import streamlit as st
import pandas as pd
import numpy as np
import folium
from streamlit_folium import st_folium
import plotly.express as px
from engine import (
    parse_and_filter_aoi, fetch_firms_nrt, match_aqua_and_viirs,
    calibrate_frp_time_block, analyze_static_and_recurring_sites
)

st.set_page_config(page_title="KÖZ Atlas — Kirvecanlar", layout="wide")

st.title("🔥 KÖZ Atlas — MODIS & VIIRS Yanma Aktivitesi Takvimi ve Kanıt Platformu")
st.caption("NASA Space Apps Challenge 2026 | Takım: Kirvecanlar (Mehmet Halil Kılıç, İbrahim Halil Birlik, Mirze Kara)")

with st.sidebar:
    st.header("1. Veri Kaynağı Seçimi")
    data_mode = st.radio(
        "Çalışma Modu:",
        ["Sentetik Boru Hattı Testi (Demo)", "NASA Arşiv CSV Yükle (SP - Bilimsel Analiz)", "NASA FIRMS Canlı API (NRT - Son 5 Gün)"]
    )
    st.divider()
    st.header("2. Eşleştirme Parametreleri (Deneysel)")
    max_dist_km = st.select_slider("Maksimum Mesafe Eşiği (km)", options=[0.5, 1.0, 2.0, 5.0], value=2.0)
    max_time_min = st.select_slider("Maksimum Zaman Farkı (dk)", options=[15, 30, 60, 120, 240], value=120)
    include_terra = st.checkbox("Terra Sabah Geçişlerini de Dahil Et", value=False)
    filter_aoi = st.checkbox("Sadece Batman/Güneydoğu TR Kutusunu Filtrele", value=True)

@st.cache_data
def generate_pipeline_test_data():
    np.random.seed(42)
    dates = pd.date_range("2021-05-01", "2025-10-15", freq="7D")
    m_rows, v_rows = [], []
    for d in dates:
        d_str = d.strftime("%Y-%m-%d")
        lat, lon = 37.88 + np.random.uniform(-0.25, 0.25), 41.15 + np.random.uniform(-0.35, 0.35)
        aqua_frp = np.random.gamma(2.2, 18.0)
        m_rows.append({"acq_date": d_str, "acq_time": "1045", "satellite": "Terra", "latitude": lat+0.08, "longitude": lon, "frp": aqua_frp*0.8, "daynight": "D", "type": 0})
        m_rows.append({"acq_date": d_str, "acq_time": "1330", "satellite": "Aqua", "latitude": lat, "longitude": lon, "frp": aqua_frp, "daynight": "D", "type": 0})
        v_rows.append({"acq_date": d_str, "acq_time": "1338", "satellite": "N20", "latitude": lat+0.002, "longitude": lon-0.002, "frp": aqua_frp*0.75, "daynight": "D", "type": 0})
        v_rows.append({"acq_date": d_str, "acq_time": "1338", "satellite": "N20", "latitude": lat-0.002, "longitude": lon+0.001, "frp": aqua_frp*0.55, "daynight": "D", "type": 0})
        m_rows.append({"acq_date": d_str, "acq_time": "1330", "satellite": "Aqua", "latitude": 37.865, "longitude": 41.155, "frp": 19.5, "daynight": "D", "type": 2})
    return parse_and_filter_aoi(pd.DataFrame(m_rows), "MODIS_SYNTH"), parse_and_filter_aoi(pd.DataFrame(v_rows), "VIIRS_SYNTH")

modis_df, viirs_df = pd.DataFrame(), pd.DataFrame()
status_banner = ""

if data_mode == "NASA Arşiv CSV Yükle (SP - Bilimsel Analiz)":
    c1, c2 = st.columns(2)
    m_file = c1.file_uploader("MODIS Standart Arşiv CSV (MCD14ML)", type=["csv"])
    v_file = c2.file_uploader("VIIRS Standart Arşiv CSV (VNP14IMG)", type=["csv"])
    if m_file and v_file:
        modis_df = parse_and_filter_aoi(pd.read_csv(m_file), "MODIS_SP", filter_bbox=filter_aoi)
        viirs_df = parse_and_filter_aoi(pd.read_csv(v_file), "VIIRS_SP", filter_bbox=filter_aoi)
        status_banner = f"✅ Yüklenen Yıllar -> Sol Dosya: {sorted(modis_df['year'].dropna().unique().tolist())} | Sağ Dosya: {sorted(viirs_df['year'].dropna().unique().tolist())}"
    else:
        st.warning("Lütfen AYNI YILA AİT MODIS ve VIIRS arşiv CSV dosyalarını yükleyin.")
        st.stop()
elif data_mode == "NASA FIRMS Canlı API (NRT - Son 5 Gün)":
    api_key = st.sidebar.text_input("NASA FIRMS MAP_KEY", type="password")
    if st.sidebar.button("Son 5 Günü Çek"):
        m_df, m_stat = fetch_firms_nrt(api_key, "MODIS_NRT", 5)
        v_df, v_stat = fetch_firms_nrt(api_key, "VIIRS_NOAA20_NRT", 5)
        modis_df, viirs_df = m_df, v_df
        status_banner = f"NRT Durumu -> MODIS: {m_stat} ({len(m_df)} kayıt) | VIIRS NOAA-20: {v_stat} ({len(v_df)} kayıt)"
    else:
        st.info("Sol menüden MAP_KEY girip 'Son 5 Günü Çek' butonuna basın.")
        st.stop()
else:
    modis_df, viirs_df = generate_pipeline_test_data()
    status_banner = "🧪 UYARI: Şu an kod doğrulaması için SENTETİK TEST VERİSİ gösteriliyor."

st.info(status_banner)

pairs_df, summary = match_aqua_and_viirs(modis_df, viirs_df, max_dist_km=max_dist_km, max_time_min=max_time_min, include_terra=include_terra)
if "warning" in summary:
    st.error(summary["warning"])

model, cal_metrics = calibrate_frp_time_block(pairs_df)
sites_df = analyze_static_and_recurring_sites(modis_df)

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("MODIS Kayıt (Aqua / Terra)", f"{summary.get('aqua_records', 0)} / {summary.get('terra_records', 0)}")
k2.metric("VIIRS Ham Piksel Kaydı", f"{summary.get('viirs_records', 0)}")
k3.metric("Eşleşen Geçiş Sayısı", f"{summary.get('matched_aqua_events', 0)}", f"Oran: %{summary.get('aqua_codetection_pct', 0)}")
k4.metric("Bağımsız Gözlem Günü", f"{summary.get('independent_days', 0)} Gün")
if cal_metrics.get("calibrated"):
    k5.metric("Test FRP MAE (Ham -> Kalibre)", f"{cal_metrics['raw_mae_mw']} -> {cal_metrics['calibrated_mae_mw']} MW")
else:
    k5.metric("Kalibrasyon Durumu", "Ham Ölçek", "Örneklem Sınırı")

tab1, tab2, tab3 = st.tabs(["📅 Yanma Aktivitesi Takvimi & Kalibrasyon", "🗺️ NASA GIBS Harita & Kanıt Kartı", "🏭 Tekrarlayan / Statik Kaynak Adayları"])

with tab1:
    scale_choice = st.radio(
        "Takvim Gösterim Modu:",
        ["Tüm Ham MODIS + VIIRS Gözlemleri (MW)", "Eşleşen Aqua MODIS FRP (MW)", "Kalibre Edilmiş VIIRS -> MODIS Ölçeği (MW)"],
        horizontal=True
    )

    ay_isimleri = {
        1: "Oca", 2: "Şub", 3: "Mar", 4: "Nis", 5: "May", 6: "Haz",
        7: "Tem", 8: "Ağu", 9: "Eyl", 10: "Eki", 11: "Kas", 12: "Ara"
    }

    def render_modern_calendar(df_src, val_col, title_text):
        piv = df_src.groupby(["year", "month"])[val_col].sum().unstack(fill_value=0)
        # 1'den 12'ye tüm ayların eksiksiz görünmesini sağla
        for m_idx in range(1, 13):
            if m_idx not in piv.columns:
                piv[m_idx] = 0.0
        piv = piv[sorted(piv.columns)]
        piv.columns = [ay_isimleri[m] for m in piv.columns]
        piv.index = piv.index.astype(str)

        fig = px.imshow(
            piv,
            text_auto=".0f",  # Kutuların içine tam sayı olarak FRP değerini yazar
            labels=dict(x="Ay", y="Yıl", color="FRP (MW)"),
            color_continuous_scale=["#161b22", "#3b1d14", "#8c2d04", "#d94801", "#f16913", "#fdd0a2"],
            aspect="auto",
            title=title_text
        )
        fig.update_traces(
            xgap=4,  # Kutular arasına modern boşluk ekler
            ygap=4,
            hovertemplate="<b>Yıl:</b> %{y}<br><b>Ay:</b> %{x}<br><b>Toplam FRP:</b> %{z:.1f} MW<extra></extra>"
        )
        fig.update_layout(
            plot_bgcolor="#0e1117",
            paper_bgcolor="#0e1117",
            font=dict(color="#e6edf3", size=13),
            xaxis=dict(side="top", tickmode="linear"),
            yaxis=dict(tickmode="linear"),
            height=420,
            margin=dict(l=40, r=40, t=70, b=30)
        )
        st.plotly_chart(fig, use_container_width=True)

    if scale_choice == "Tüm Ham MODIS + VIIRS Gözlemleri (MW)":
        comb_raw = pd.concat([modis_df[["year", "month", "frp"]], viirs_df[["year", "month", "frp"]]], ignore_index=True)
        if not comb_raw.empty:
            render_modern_calendar(comb_raw, "frp", "🔥 Yıllık ve Aylık Yanma Aktivitesi Yoğunluğu (Ham Toplam FRP - MW)")
    elif not pairs_df.empty:
        if model is not None:
            pairs_df["calibrated_frp"] = np.expm1(model.predict(np.log1p(pairs_df[["viirs_frp_sum"]].values)))
        else:
            pairs_df["calibrated_frp"] = pairs_df["viirs_frp_sum"]
        col_name = "aqua_frp" if "Aqua" in scale_choice else "calibrated_frp"
        render_modern_calendar(pairs_df, col_name, f"🛰️ {scale_choice}")
    else:
        st.warning("Eşleşen geçiş bulunamadı. Lütfen iki kutuya da AYNI YILIN MODIS ve VIIRS dosyalarını yüklediğinizden emin olun.")
with tab2:
    c_map, c_proof = st.columns([1.3, 1])
    with c_map:
        m = folium.Map(location=[37.88, 41.15], zoom_start=8, tiles="CartoDB dark_matter")
        folium.TileLayer(
            tiles="https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/MODIS_Terra_CorrectedReflectance_TrueColor/default/2026-11-01/GoogleMapsCompatible_Level9/{z}/{y}/{x}.jpg",
            attr="NASA EOSDIS GIBS", name="NASA GIBS TrueColor"
        ).add_to(m)
        if not pairs_df.empty:
            for _, r in pairs_df.tail(100).iterrows():
                folium.CircleMarker(
                    location=[r["latitude"], r["longitude"]], radius=6, color="lime", fill=True,
                    popup=f"EŞLEŞEN GEÇİŞ<br>Tarih: {r['date_str']}<br>MODIS FRP: {r['aqua_frp']:.1f} MW<br>VIIRS FRP: {r['viirs_frp_sum']:.1f} MW"
                ).add_to(m)
        else:
            for _, r in modis_df.tail(80).iterrows():
                folium.CircleMarker(location=[r["latitude"], r["longitude"]], radius=5, color="cyan", fill=True, popup=f"MODIS Ham: {r['frp']} MW ({r['date_str']})").add_to(m)
            for _, r in viirs_df.tail(80).iterrows():
                folium.CircleMarker(location=[r["latitude"], r["longitude"]], radius=4, color="orange", fill=True, popup=f"VIIRS Ham: {r['frp']} MW ({r['date_str']})").add_to(m)
        st_folium(m, width=620, height=400)
    with c_proof:
        st.subheader("🧾 Bilimsel Kanıt ve Doğrulama Kartı")
        st.json({"Eşleştirme_Özeti": summary, "Kalibrasyon_Test_Sonucu": cal_metrics})

with tab3:
    st.subheader("Benzersiz Saha (1 km Grid) Bazında Tekrarlayan Isı Noktaları")
    if not sites_df.empty:
        st.dataframe(sites_df, use_container_width=True)
    else:
        st.write("Tekrarlayan veya Type=2 statik kaynak adayı bulunamadı.")
