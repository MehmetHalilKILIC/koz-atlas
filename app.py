import streamlit as st
import pandas as pd
import numpy as np
import folium
from streamlit_folium import st_folium
import plotly.express as px
import plotly.graph_objects as go
from engine import (
    parse_and_filter_aoi, fetch_firms_nrt, match_aqua_and_viirs,
    calibrate_frp_time_block, analyze_static_and_recurring_sites
)

st.set_page_config(
    page_title="KÖZ Atlas | NASA Space Apps 2026",
    page_icon="🛰️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- NASA MISSION CONTROL ÖZEL CSS TASARIMI ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    background-color: #070b14;
    color: #e2e8f0;
}

.stApp {
    background: radial-gradient(circle at 15% 10%, #111c33 0%, #070b14 55%, #05080f 100%);
}

/* Üst Hero Banner */
.hero-box {
    background: linear-gradient(135deg, rgba(15, 23, 42, 0.9) 0%, rgba(30, 41, 59, 0.7) 100%);
    border: 1px solid rgba(249, 115, 22, 0.35);
    border-left: 5px solid #f97316;
    border-radius: 14px;
    padding: 22px 28px;
    margin-bottom: 20px;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.45);
}
.hero-badge {
    display: inline-block;
    background: rgba(249, 115, 22, 0.15);
    color: #fb923c;
    border: 1px solid rgba(249, 115, 22, 0.4);
    padding: 3px 10px;
    border-radius: 999px;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    margin-bottom: 8px;
}
.hero-title {
    font-size: 28px;
    font-weight: 800;
    background: linear-gradient(90deg, #ffffff 0%, #fdba74 60%, #f97316 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin: 0 0 6px 0;
}
.hero-sub {
    color: #94a3b8;
    font-size: 13.5px;
    margin: 0;
}

/* Glassmorphism KPI Kartları */
.kpi-card {
    background: rgba(15, 23, 42, 0.72);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(148, 163, 184, 0.16);
    border-radius: 12px;
    padding: 16px 18px;
    transition: transform 0.2s ease, border-color 0.2s ease;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
}
.kpi-card:hover {
    border-color: rgba(249, 115, 22, 0.55);
    transform: translateY(-2px);
}
.kpi-label {
    font-size: 11.5px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: #94a3b8;
    margin-bottom: 6px;
}
.kpi-value {
    font-family: 'JetBrains Mono', monospace;
    font-size: 23px;
    font-weight: 700;
    color: #f8fafc;
}
.kpi-delta {
    font-size: 12px;
    color: #38bdf8;
    margin-top: 4px;
    font-weight: 500;
}

/* Sekme (Tab) Tasarımı */
.stTabs [data-baseweb="tab-list"] {
    gap: 10px;
    background-color: rgba(15, 23, 42, 0.6);
    padding: 6px;
    border-radius: 12px;
    border: 1px solid rgba(148, 163, 184, 0.15);
}
.stTabs [data-baseweb="tab"] {
    border-radius: 8px;
    padding: 10px 18px;
    font-weight: 600;
    color: #94a3b8;
}
.stTabs [aria-selected="true"] {
    background: linear-gradient(90deg, #ea580c 0%, #f97316 100%) !important;
    color: #ffffff !important;
}

/* Yan Menü */
[data-testid="stSidebar"] {
    background-color: #090e1a;
    border-right: 1px solid rgba(148, 163, 184, 0.12);
}
</style>
""", unsafe_allow_html=True)

# --- HERO HEADER ---
st.markdown("""
<div class="hero-box">
    <div class="hero-badge">🛰️ NASA Space Apps Challenge 2026 • Team Kirvecanlar</div>
    <div class="hero-title">KÖZ Atlas — Çoklu Uydu Yangın Harmonizasyon Platformu</div>
    <p class="hero-sub">
        MODIS (1 km) ve VIIRS (375 m) termal anomali verilerini yörünge duyarlı uzay-zaman eşleştirmesi ve zaman-bloklu FRP kalibrasyonu ile tek bir bilimsel yanma takviminde birleştirir.
        <br><span style="color:#64748b; font-size:12px;">Geliştiriciler: Mehmet Halil Kılıç • İbrahim Halil Birlik • Mirze Kara</span>
    </p>
</div>
""", unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("### 📡 1. Telemetri & Veri Kaynağı")
    data_mode = st.radio(
        "Veri Akış Modu:",
        ["Sentetik Boru Hattı Testi (Demo)", "NASA Arşiv CSV Yükle (SP - Bilimsel Analiz)", "NASA FIRMS Canlı API (NRT - Son 5 Gün)"],
        label_visibility="collapsed"
    )
    st.divider()
    st.markdown("### ⚙️ 2. Eşleştirme Parametreleri")
    max_dist_km = st.select_slider("Maksimum Mesafe Eşiği (km)", options=[0.5, 1.0, 2.0, 5.0], value=2.0)
    max_time_min = st.select_slider("Maksimum Zaman Farkı (dk)", options=[15, 30, 60, 120, 240], value=120)
    include_terra = st.checkbox("Terra Sabah Geçişlerini Dahil Et", value=False)
    filter_aoi = st.checkbox("Batman / Güneydoğu TR Pilot Kutusu", value=True)
    st.divider()
    st.caption("ℹ️ **Bilimsel Not:** 2 Kasım 2026 itibarıyla S-NPP NRT akışı durmuş, güncel veriler NOAA-20/21 üzerine taşınmıştır. Boş hücreler bulut/kapsam dışı olabilir.")

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
    m_file = c1.file_uploader("🛰️ MODIS Standart Arşiv CSV (MCD14ML)", type=["csv"])
    v_file = c2.file_uploader("🛰️ VIIRS Standart Arşiv CSV (VNP14IMG)", type=["csv"])
    if m_file and v_file:
        modis_df = parse_and_filter_aoi(pd.read_csv(m_file), "MODIS_SP", filter_bbox=filter_aoi)
        viirs_df = parse_and_filter_aoi(pd.read_csv(v_file), "VIIRS_SP", filter_bbox=filter_aoi)
        status_banner = f"✅ Gerçek NASA Arşiv Verisi Aktif — Sol Dosya Yılları: {sorted(modis_df['year'].dropna().unique().tolist())} | Sağ Dosya Yılları: {sorted(viirs_df['year'].dropna().unique().tolist())}"
    else:
        st.info("Lütfen AYNI YILA AİT MODIS ve VIIRS arşiv CSV dosyalarını yükleyin veya sol menüden Demo modunu seçin.")
        st.stop()
elif data_mode == "NASA FIRMS Canlı API (NRT - Son 5 Gün)":
    api_key = st.sidebar.text_input("NASA FIRMS MAP_KEY", type="password")
    if st.sidebar.button("🚀 Canlı Veriyi Çek (Son 5 Gün)", use_container_width=True):
        m_df, m_stat = fetch_firms_nrt(api_key, "MODIS_NRT", 5)
        v_df, v_stat = fetch_firms_nrt(api_key, "VIIRS_NOAA20_NRT", 5)
        modis_df, viirs_df = m_df, v_df
        status_banner = f"📡 Canlı Akış Durumu -> MODIS: {m_stat} ({len(m_df)} kayıt) | VIIRS NOAA-20: {v_stat} ({len(v_df)} kayıt)"
    else:
        st.info("Sol menüden MAP_KEY anahtarınızı girip 'Canlı Veriyi Çek' butonuna basın.")
        st.stop()
else:
    modis_df, viirs_df = generate_pipeline_test_data()
    status_banner = "🧪 UYARI: Şu an mimari doğrulama için SENTETİK TEST VERİSİ görüntüleniyor. Gerçek analiz için sol menüden NASA CSV yükleyin."

st.caption(status_banner)

pairs_df, summary = match_aqua_and_viirs(modis_df, viirs_df, max_dist_km=max_dist_km, max_time_min=max_time_min, include_terra=include_terra)
if "warning" in summary:
    st.error(summary["warning"])

model, cal_metrics = calibrate_frp_time_block(pairs_df)
sites_df = analyze_static_and_recurring_sites(modis_df)

# --- GLASSMORPHISM KPI KARTLARI ---
k1, k2, k3, k4, k5 = st.columns(5)

with k1:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">MODIS Gözlemleri</div>
        <div class="kpi-value">{summary.get('aqua_records', 0)} / {summary.get('terra_records', 0)}</div>
        <div class="kpi-delta">Aqua (Öğle) / Terra (Sabah)</div>
    </div>""", unsafe_allow_html=True)

with k2:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">VIIRS 375m Piksel</div>
        <div class="kpi-value">{summary.get('viirs_records', 0)}</div>
        <div class="kpi-delta">Yüksek Çözünürlüklü Tespit</div>
    </div>""", unsafe_allow_html=True)

with k3:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">Eşleşen Geçiş</div>
        <div class="kpi-value">{summary.get('matched_aqua_events', 0)}</div>
        <div class="kpi-delta" style="color:#4ade80;">Ortak Tespit: %{summary.get('aqua_codetection_pct', 0)}</div>
    </div>""", unsafe_allow_html=True)

with k4:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">Bağımsız Gün</div>
        <div class="kpi-value">{summary.get('independent_days', 0)} Gün</div>
        <div class="kpi-delta">Medyan Fark: {summary.get('median_time_diff_min', 0)} dk</div>
    </div>""", unsafe_allow_html=True)

with k5:
    if cal_metrics.get("calibrated"):
        mae_val = f"{cal_metrics['raw_mae_mw']} → {cal_metrics['calibrated_mae_mw']}"
        mae_sub = "Test FRP MAE (MW) Düşüşü"
        sub_color = "#4ade80" if cal_metrics.get("better_than_raw") else "#facc15"
    else:
        mae_val = "Ham Ölçek"
        mae_sub = "Örneklem Sınırı Aktif"
        sub_color = "#94a3b8"
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">Kalibrasyon Performansı</div>
        <div class="kpi-value" style="font-size:19px;">{mae_val}</div>
        <div class="kpi-delta" style="color:{sub_color};">{mae_sub}</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<div style='height:18px;'></div>", unsafe_allow_html=True)

# --- ANA SEKMELER ---
tab1, tab2, tab3 = st.tabs([
    "📅 Yanma Aktivitesi Takvimi & Kalibrasyon",
    "🗺️ NASA GIBS Uydu Haritası & Kanıt Kartı",
    "🏭 Tekrarlayan / Statik Isı Kaynağı Adayları"
])

with tab1:
    scale_choice = st.radio(
        "Takvim Ölçeği Seçin:",
        ["Tüm Ham MODIS + VIIRS Gözlemleri (MW)", "Eşleşen Aqua MODIS FRP (MW)", "Kalibre Edilmiş VIIRS -> MODIS Ölçeği (MW)"],
        horizontal=True
    )

    ay_isimleri = {
        1: "Oca", 2: "Şub", 3: "Mar", 4: "Nis", 5: "May", 6: "Haz",
        7: "Tem", 8: "Ağu", 9: "Eyl", 10: "Eki", 11: "Kas", 12: "Ara"
    }

    def render_modern_calendar(df_src, val_col, title_text):
        piv = df_src.groupby(["year", "month"])[val_col].sum().unstack(fill_value=0)
        for m_idx in range(1, 13):
            if m_idx not in piv.columns:
                piv[m_idx] = 0.0
        piv = piv[sorted(piv.columns)]
        piv.columns = [ay_isimleri[m] for m in piv.columns]
        piv.index = piv.index.astype(str)

        fig = px.imshow(
            piv,
            text_auto=".0f",
            labels=dict(x="Ay", y="Yıl", color="FRP (MW)"),
            color_continuous_scale=["#0f172a", "#431407", "#9a3412", "#ea580c", "#fb923c", "#fef08a"],
            aspect="auto"
        )
        fig.update_traces(
            xgap=5,
            ygap=5,
            textfont=dict(size=12, family="JetBrains Mono"),
            hovertemplate="<b>Yıl:</b> %{y}<br><b>Ay:</b> %{x}<br><b>Toplam FRP:</b> %{z:.1f} MW<extra></extra>"
        )
        fig.update_layout(
            title=dict(text=title_text, font=dict(size=16, color="#f8fafc")),
            plot_bgcolor="#070b14",
            paper_bgcolor="rgba(15, 23, 42, 0.55)",
            font=dict(color="#cbd5e1", size=13),
            xaxis=dict(side="top", tickmode="linear", showgrid=False),
            yaxis=dict(tickmode="linear", showgrid=False),
            height=430,
            margin=dict(l=45, r=35, t=80, b=30)
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
    c_map, c_proof = st.columns([1.35, 1])
    with c_map:
        m = folium.Map(location=[37.88, 41.15], zoom_start=8, tiles="CartoDB dark_matter")
        folium.TileLayer(
            tiles="https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/MODIS_Terra_CorrectedReflectance_TrueColor/default/2026-11-01/GoogleMapsCompatible_Level9/{z}/{y}/{x}.jpg",
            attr="NASA EOSDIS GIBS", name="NASA GIBS TrueColor"
        ).add_to(m)
        if not pairs_df.empty:
            for _, r in pairs_df.tail(120).iterrows():
                folium.CircleMarker(
                    location=[r["latitude"], r["longitude"]], radius=6, color="#22c55e", fill=True, fill_opacity=0.85,
                    popup=f"<b>EŞLEŞEN GEÇİŞ</b><br>Tarih: {r['date_str']}<br>Aqua FRP: {r['aqua_frp']:.1f} MW<br>VIIRS Toplam FRP: {r['viirs_frp_sum']:.1f} MW<br>Zaman Farkı: {r['median_time_diff_min']:.1f} dk"
                ).add_to(m)
        else:
            for _, r in modis_df.tail(80).iterrows():
                folium.CircleMarker(location=[r["latitude"], r["longitude"]], radius=5, color="#38bdf8", fill=True, popup=f"MODIS Ham: {r['frp']} MW ({r['date_str']})").add_to(m)
            for _, r in viirs_df.tail(80).iterrows():
                folium.CircleMarker(location=[r["latitude"], r["longitude"]], radius=4, color="#f97316", fill=True, popup=f"VIIRS Ham: {r['frp']} MW ({r['date_str']})").add_to(m)
        st_folium(m, width=680, height=430)

    with c_proof:
        st.markdown("#### 🧾 Bilimsel Kanıt ve Doğrulama Telemetrisi")
        st.caption("Her metriğin kaynağı, eşleşme sayısı ve bağımsız test hatası (MAE) anlık olarak hesaplanır.")
        st.json({"Eşleştirme_Özeti": summary, "Kalibrasyon_Test_Sonucu": cal_metrics})

with tab3:
    st.markdown("#### 🏭 Benzersiz Saha (1 km Grid) Bazında Tekrarlayan Isı Noktaları")
    st.caption("Aynı koordinat hücresindeki çoklu gün/ay tekrarları ve NASA MCD14ML 'Type=2' (Statik Kara Kaynağı) etiketleri tek bir aday saha altında toplanmıştır.")
    if not sites_df.empty:
        st.dataframe(
            sites_df,
            use_container_width=True,
            column_config={
                "site_grid": "1 km Grid ID",
                "center_lat": st.column_config.NumberColumn("Enlem", format="%.4f"),
                "center_lon": st.column_config.NumberColumn("Boylam", format="%.4f"),
                "total_detections": "Toplam Tespit",
                "distinct_days": "Farklı Gün",
                "distinct_months": "Farklı Ay",
                "mean_frp_mw": st.column_config.NumberColumn("Ort. FRP (MW)", format="%.2f"),
                "has_nasa_type2": "NASA Type=2 Etiketi",
                "type2_record_count": "Type=2 Kayıt Sayısı"
            }
        )
    else:
        st.info("Seçilen veri setinde tekrarlayan veya Type=2 statik kaynak adayı bulunamadı.")
