# KÖZ Atlas — MODIS ve VIIRS Harmonizasyon & Yanma Aktivitesi Takvimi
**NASA Space Apps Challenge 2026 (Batman Yerel Etkinliği)**
**Takım:** Kirvecanlar (Mehmet Halil Kılıç, İbrahim Halil Birlik, Mirze Kara)
**Görev (Challenge):** Harmonization of MODIS and VIIRS Hot Spots

## 1. Problem Tanımı
MODIS (1 km çözünürlük) ve VIIRS (375 m çözünürlük) aktif yangın ürünleri arasında uzamsal çözünürlük, geçiş zamanı ve Yangın Radyatif Gücü (FRP - MW) farkları bulunmaktadır. Ayrıca 2 Kasım 2026 itibarıyla Suomi-NPP NRT akışı sonlanmış, Terra ve Aqua MODIS uydularının ise 2027'de görev süresini tamamlaması planlanmıştır. Ham gözlem sayılarının doğrudan birleştirilmesi tarihsel yangın takviminde yapay sıçramalara yol açmaktadır.

## 2. Metodoloji ve Bilimsel Sınırlar
- **Yörünge Ayrımı (Aqua vs. Terra):** Sabah geçişi yapan Terra MODIS kayıtları ayrıştırılmış; öğleden sonra yörüngesindeki Aqua MODIS ile VIIRS gözlemleri eşleştirilmiştir.
- **Gerçek Uzay-Zaman Eşleştirmesi:** Yuvarlama kaynaklı kenar etkilerini önlemek için Haversine küresel mesafe (0.5 / 1.0 / 2.0 km) ve gerçek UTC zaman farkı (15 / 30 / 60 dk) kullanılmıştır.
- **FRP Birleştirme ve Zaman Bloklu Kalibrasyon:** Bir Aqua gözleminin etrafındaki VIIRS alt piksellerinin FRP değerleri geçiş bazında toplanmış, tarih bloklu (Time-Block Split) log(1 + FRP) Ridge regresyonu ile ortak ölçeğe taşınmıştır.
- **Tekrarlayan ve Statik Kaynak Adayları:** NASA standart arşiv (MCD14ML) verisindeki type=2 (diğer statik kara kaynağı) etiketi ve ~1 km sabit ızgarada çoklu gün/ay tekrarlanma sıklığı kullanılarak sabit ısı kaynakları ayrı raporlanmıştır.
- **Açık Sınırlar:** Boş takvim hücreleri kesin yangın yok anlamına gelmez (bulut örtüsü veya gözlem kapsamı dışı olabilir).

## 3. Kurulum ve Çalıştırma
    pip install -r requirements.txt
    python -m streamlit run app.py
