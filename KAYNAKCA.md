# KAYNAKÇA

Kirvecanlar · KÖZ Atlas · NASA Space Apps Challenge 2026 (Batman) · "Harmonization of MODIS and VIIRS Hot Spots"

Bu belge projede kullanılan veri, belge ve servisleri listeler. NASA dışı kaynaklar Bölüm 3'te ayrıca belirtilmiştir. "Erişim" alanı, bağlantının açılıp içeriğinin kontrol edildiği tarihi gösterir.

---

## 1. NASA veri ve servisleri

**[1] NASA FIRMS (Fire Information for Resource Management System)**
- Yayıncı: NASA / LANCE
- URL: https://firms.modaps.eosdis.nasa.gov/
- Erişim: [TODO: tarayıcıda açıp tarih ekleyin]
- Projede kullanım: MODIS ve VIIRS aktif yangın tespit verisi; arşiv indirme (MCD14ML, VNP14IMG) ve canlı veri.

**[2] FIRMS Area API**
- Yayıncı: NASA / LANCE
- URL: https://firms.modaps.eosdis.nasa.gov/api/area/
- Erişim: [TODO: tarayıcıda açıp tarih ekleyin]
- Projede kullanım: `fetch_firms_nrt()` ile MODIS_NRT ve VIIRS_NOAA20_NRT canlı verisi (son 5 gün). Ücretsiz MAP_KEY gerektirir; anahtar kodda veya depoda tutulmaz.

**[3] Transitioning from Suomi NPP VIIRS & OMPS: What FIRMS Users Need to Know**
- Yazar/Yayıncı: FIRMS Team, NASA Earthdata (blog, 27 Ekim 2026)
- URL: https://www.earthdata.nasa.gov/news/blog/transitioning-from-suomi-npp-viirs-omps-what-firms-users-need-know
- Erişim: 14 Kasım 2026
- Projede kullanım: Suomi NPP'den yeni FIRMS verisi üretiminin 2 Kasım 2026 13:00 UTC'de sona ermesi ve NOAA-20 / NOAA-21'e geçiş. Aynı yazı, Terra MODIS'in tek sabah geçişini sağladığını ve Aqua'dan yaklaşık 3 saat önce geçtiğini belirtir.

**[4] Reminder: New Suomi NPP Observations to Cease on November 2, 2026**
- Yayıncı: NASA Earthdata, Data Alerts
- URL: https://www.earthdata.nasa.gov/data/alerts-outages/reminder-new-suomi-npp-observations-cease-november-2-2026
- Erişim: [TODO: tarayıcıda açıp tarih ekleyin]
- Projede kullanım: [3] ile aynı geçişin resmi duyurusu.

**[5] Transition from MODIS to VIIRS**
- Yayıncı: NASA Earthdata, Data Alerts (yayın tarihi: 2 Mayıs 2025)
- URL: https://www.earthdata.nasa.gov/data/alerts-outages/transition-from-modis-viirs
- Erişim: [TODO: tarayıcıda açıp tarih ekleyin]
- Projede kullanım: Terra ve Aqua platformlarının 2026 sonu / 2027 başında kapanmaya başlayacağı bilgisi.

**[6] Active Fire Data Attributes for MODIS and VIIRS**
- Yayıncı: NASA Earthdata
- URL: https://www.earthdata.nasa.gov/data/tools/firms/active-fire-data-attributes-modis-viirs
- Erişim: 14 Kasım 2026
- Projede kullanım: `scan`, `track`, `confidence`, `daynight`, `frp`, `bright_ti4`, `bright_ti5`, `type` alanlarının tanımları. `type` alanı (0 = bitki örtüsü yangını, 1 = aktif volkan, 2 = diğer statik kara kaynağı, 3 = deniz üstü) yalnızca MCD14ML (standart kalite) verisinde bulunur.

**[7] VIIRS I-Band 375 m Active Fire Data**
- Yayıncı: NASA Earthdata
- URL: https://www.earthdata.nasa.gov/data/instruments/viirs/viirs-i-band-375-m-active-fire-data
- Erişim: 14 Kasım 2026
- Projede kullanım: VIIRS 375 m aktif yangın ürününün tanımı. Sayfada anılan ürünler: VNP14IMGTDL_NRT (Suomi NPP), VJ114IMGTDL_NRT (NOAA-20), VJ214IMGTDL_NRT (NOAA-21).

**[8] Global Imagery Browse Services (GIBS) APIs**
- Yayıncı: NASA Earthdata
- URL: https://www.earthdata.nasa.gov/engage/open-data-services-software/earthdata-developer-portal/gibs-api
- Geliştirici belgeleri: https://nasa-gibs.github.io/gibs-api-docs/
- Erişim: 14 Kasım 2026 (ilk adres); [TODO: ikinci adres için tarih ekleyin]
- Projede kullanım: Haritadaki WMTS altlığı (MODIS_Terra_CorrectedReflectance_TrueColor).
- GIBS teşekkür metni: [TODO: [8] numaralı sayfanın "Data Use Guidance and Acknowledgements" bölümündeki cümleyi aynen kopyalayın; uygulamada, README'de ve videoda gösterin.]

---

## 2. Bilimsel yayınlar ve kullanıcı kılavuzları

**[9] Giglio, L., Schroeder, W., & Justice, C. O. (2016).** The collection 6 MODIS active fire detection algorithm and fire products. *Remote Sensing of Environment*, 178, 31–41. doi:10.1016/j.rse.2016.02.054
- Erişim: [TODO: DOI bağlantısını açıp tarih ekleyin]

**[10] Schroeder, W., Oliva, P., Giglio, L., & Csiszar, I. (2014).** The New VIIRS 375 m active fire detection data product: Algorithm description and initial assessment. *Remote Sensing of Environment*, 143. doi:10.1016/j.rse.2013.12.008
- Erişim: [TODO: DOI bağlantısını açıp tarih ekleyin]

**[11] Giglio, L., Schroeder, W., Hall, J. V., & Justice, C. O. (2021).** MODIS Collection 6 and Collection 6.1 Active Fire Product User's Guide, Version 1.0. University of Maryland / NOAA, Mayıs 2021.
- URL: https://earthdata.nasa.gov/s3fs-public/2023-09/MODIS_C6_C6.1_Fire_User_Guide_1.0.pdf
- LP DAAC'ta "MOD14 User Guide V61" adıyla yayımlanan sürüm: https://LPDAAC.USGS.GOV/documents/1005/MOD14_User_Guide_V61.pdf
- Erişim: [TODO: açıp tarih ekleyin]
- Projede kullanım: MODIS güven (confidence) sınıflarının eşikleri için "Detection Confidence" bölümü; MCD14ML ürünü.

**[12] VIIRS 375 m Active Fire Algorithm User Guide, Version 1.2 (Haziran 2025).** NASA Earthdata.
- URL: https://www.earthdata.nasa.gov/s3fs-public/2025-06/VIIRS_C2_AF-375m_User_Guide_1.2.pdf
- Erişim: [TODO: açıp tarih ekleyin]

**[13] MODIS Active Fire and Burned Area Products.** University of Maryland.
- URL: https://modis-fire.umd.edu/
- Erişim: [TODO: açıp tarih ekleyin]
- Projede kullanım: MODIS aktif yangın ve yanmış alan ürünlerine genel bakış.

---

## 3. NASA dışı kaynaklar (yalnızca harita altlığı)

Bu katmanlar analizde kullanılmaz; sadece görsel bağlam sağlar.

**[14] OpenStreetMap**
- Atıf: © OpenStreetMap contributors
- URL: https://www.openstreetmap.org/copyright
- Erişim: [TODO: açıp tarih ekleyin]

**[15] Esri World Imagery**
- [TODO: Sağlayıcının kendi sayfasından resmi ürün adını, kullanım şartlarını ve zorunlu atıf metnini ekleyin; atıf haritada görünür olmalı.]

---

## 4. Not

Bu listedeki her bağlantı, projede bir veri alanını veya iddiayı desteklemek için kullanılır. Projeye yeni bir ürün eklenirse (ör. MCD12Q1 arazi örtüsü), ürünün resmi sayfası ve sürümü bu listeye eklenmelidir.
