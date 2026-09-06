---
trigger: always
---

# KEFE Antigravity Rule: Invariants & Architecture

Bu kural, KEFE projesinde çalışan TÜM yapay zeka modelleri için ZORUNLU ve TAVİZSİZ ilkeleri tanımlar.

## 1. Otorite ve Belge Hiyerarşisi
- `docs/ecosystem_v3.3/.../ACTIVE` altındaki **18 onaylı resmî doküman** (özellikle `KEFE_Master_Product_Document_v1.2.0 Canonical`, `KEFE_Product_Bible_v1.4.0 Working Baseline` ve `KEFE_Engineering_Blueprint_v0.6.0`) tek ve mutlak gerçektir (Single Source of Truth).
- **Yeni bağımsız manifesto / kural uydurmak YASAKTIR.**
- Otorite sıralaması:
  1. Onaylı Anayasal Dokümanlar (18 Belge)
  2. Onaylı ADR'ler (`docs/adr/`) ve JSON Kontratları (`docs/contracts/`)
  3. Canlı Kod, Testler ve CI Doğrulamaları
  4. `docs/status/CURRENT.md` ve `.ai/STATUS.md`
  5. `docs/roadmap/capability-portfolio.v1.tsv`
  - Chat geçmişi ASLA mühendislik gerçeği sayılamaz.

## 2. Dokunulmaz Çekirdek İlkeler (Core Invariants)
- **Commit First:** Kullanıcı kendi kararını mühürleyip kilitlemeden önce toplum, ülke veya uzman sonucunu ASLA göremez.
- **CaseVersion İmmutability:** Yayımlanan vaka versiyonu kesinlikle yerinde değiştirilemez; yeni gelişme yeni versiyon veya oturum üretir.
- **Generic Case Flow:** named vaka tipleri yerine format bazlı jenerik vaka akışı (`DILEMMA`, `DECIDE`, `CALL`, `TODAY`, `RETRO`).
- **My KEFE Gözlemseldir:** Asla ideolojik, psikometrik etiketleme veya kişilik analizi yapılmaz; tarafsız bir vicdan aynasıdır.
- **Kolektif Sonuç != Sinyal:** Toplum sonucu doğrudan resmi gerçek, sinyal veya mutlak doğru sayılamaz.

## 3. Katman ve Ekran Ayrımı
- **Tüketici Mobil Ekranı vs. Admin/Denetim Katmanı:**
  - Kamu ihale denetimi, lobi radarı, kriz kararnamesi, yargı bağımsızlığı gibi kavramlar bağımsız mobil ana sayfa kartı OLAMAZ.
  - Bunların yeri: Vaka içindeki "Bağlam ve Kanıtlar (Context Lens)" sekmesi, "Tartım Sonrası Reveal Analizleri" veya "Admin Studio (Web)" panelidir.
- **Keşfet (Explore) Ekranının Kutsallığı:**
  - Keşfet yalnızca vaka arama, kategori/format filtreleri, Günün Kefesi ve trend vakalardan oluşur.
  - Keşfet'in içine yapay "Showcase" blokları veya denetim kartları yığmak KESİNLİKLE YASAKTIR.
- **Formatlar Ekran Değil, Vaka Tipidir:**
  - `DECIDE` (Simülatör), `CALL` (Jüri/Hakem), `TODAY` (Haber), `DILEMMA` (İkilem) vakanın formatıdır ve vaka tıklandığında karar akışının içinde çalışır.
