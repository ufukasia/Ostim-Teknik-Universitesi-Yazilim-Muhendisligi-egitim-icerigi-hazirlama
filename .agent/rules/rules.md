---
trigger: always_on
---

# Haftalık Sunum Kuralları

## 1. Amaç

- Kullanıcı bir ders, hafta, konu ve mümkünse temel kitap verdiğinde sistem ilgili haftaya uygun, kitaba zeminlenmiş, pedagojik olarak savunulabilir ve `lutbeamer` uyumlu bir ders sunumu üretir.
- Sistem tek aşamalı "güzel slayt" üreticisi gibi değil, kapsam denetimli bir ders tasarım sistemi gibi davranır.
- Haftalık deck için alt sınır `60` framedir; kitap aynı hafta kapsamında daha fazlasını doğal biçimde destekliyorsa daha uzun deck tercih edilir.

## 2. Yetki Sırası

- Öncelik sırası:
  1. `.agent/rules/rules.md`
  2. `.agent/skills/mapping.yaml`
  3. ilgili orchestrator veya agent skill'i
  4. ilgili reference/example dosyaları
  5. hedef `.tex`
- Haftalık kitap temelli sunumlarda varsayılan giriş noktası `weekly_deck_orchestrator` skill'idir.
- `pdf_book_processor` ve `book_to_slide_source_pipeline` araç katmanıdır; kapsam veya pedagojik karar vermez.
- `latex_presentation_assistant` ve `question_frame_visual_layout` üretim yardımcısıdır; scope otoritesi değildir.

## 3. Minimal Ajan Mimarisi

- Zorunlu akış:
  1. `weekly_deck_orchestrator`
  2. `book_grounder`
  3. `deck_architect`
  4. `slide_composer`
  5. `deck_guard`
- Varsayılan olarak aynı anda yalnızca tek aktif alt ajan çalıştırılır.
- Paralel alt ajan ancak şu iki durumda açılır:
  - chapter seçimi iki güçlü aday arasında belirsizse
  - review yalnızca dar bir alt bölüm için ikinci görüş istiyorsa
- Orchestrator, alt ajanları uzun serbest metinle değil kısa karar nesneleriyle konuşturur.

## 4. Karar Nesnesi Sözleşmesi

- Her alt ajan yalnızca yapılandırılmış ve kısa bir karar nesnesi üretir.
- Zorunlu alanlar:
  - `decision_summary`
  - `required_items`
  - `forbidden_items`
  - `handoff_target`
- İsteğe bağlı alanlar:
  - `risks`
  - `revision_requests`
- Boş alan yazılmaz.
- Her ajan yalnızca önceki aşamadan farklı olan kararları yazar.
- Aynı bilginin paragraf halinde tekrar edilmesi yasaktır.

## 5. Kitap ve Kapsam Kuralları

- Birincil hakikat kaynağı temel kitaptır.
- Sunum yalnızca ilgili hafta kapsamı içinde kalır.
- Sonraki haftanın ana konusu erkenden anlatılmaz.
- Önceki hafta bilgisi yalnızca kısa köprü kurmak için kullanılır.
- Kitapta açıkça bulunmayan çekirdek teori, varsayılan olarak reddedilir.
- Gerekli kaynak sırası:
  1. split manifest / chapter sidecar / relative TOC
  2. `subsection_manifest.json`, `subsection_index.md`, `deck_source_brief.md`
  3. ilgili chunk veya page export dosyaları
  4. yakın hafta `.tex` dosyaları
  5. ham PDF
- Ham PDF'ye doğrudan dönüş istisnadır; önce kaynak paketleri kullanılır.
- Matematik ağırlıklı kitaplarda formül, tablo ve grafik kaybı aktif risk kabul edilir.
- `picture omitted` benzeri placeholder satırları nihai bilgi sayılmaz; varsa ilgili page/chunk export ve extraction sinyalleri okunur.
- Zayıf OCR sonucu native extraction'ı sessizce ezemez.
- Source pack tarafında `page_signal_summary`, `ingest_signals`, `ocr_requested` ve `ocr_reasons` alanları varsa bunlar karar girdisi sayılır.

## 6. Pedagoji Kuralları

- Her frame'in açık pedagojik amacı bulunur.
- Deck planı `60` frameden az olamaz.
- Tanım verilmeden yöntem, örnek veya soru anlatılmaz.
- Kavram sırası öğrenme bağımlılıklarına göre kurulur.
- Notasyon ve terminoloji sunum boyunca tutarlı kalır.
- Her ana konu için varsayılan mikro akış:
  1. kısa köprü veya motivasyon
  2. sezgi
  3. tanım / temel ifade
  4. örnek veya görsel temsil
  5. konu sonu soru
  6. çözüm için durak
  7. çözüm
- Her ayrı konu anlatımının arkasında en az bir anlatımlı örnek ve en az bir soru/çözüm zinciri bulunur.
- Sorular doğrudan çeviri gibi kurulamaz; doğal Türkçe, gerçekçi bağlam ve lisans seviyesi mühendislik aklı taşımalıdır.
- Kolay soru varsa aynı konu için en az bir normal zorlukta ölçücü soru veya çözüm zinciri de bulunur.
- Bir frame tek ana fikir taşır.
- Yüzeysel özet yerine öğretilebilir akış önceliklidir.
- İlk plan `60` frame altında kalıyorsa kapsam dışına çıkmadan şu yollarla genişletilir:
  1. sezgi ile formel tanımı ayrı framelere böl
  2. notasyon ve okuma frame'i ekle
  3. ikinci worked example ekle
  4. karşılaştırma / sık hata / yorum frame'i ekle
  5. ana konu sonuna ek soru zinciri ekle
- Formül veya grafik ağırlıklı birimlerde notasyon okuma, şekil okuma veya tablo yorum frame'i atlanmaz.

## 7. Üretim Kuralları

- Sınıf korunur: `\documentclass[light]{lutbeamer}`
- Açılış zinciri korunur:
  1. kapak
  2. `\maketitle{}`
  3. `İçindekiler`
- Kapanış zinciri mümkün oldukça korunur:
  1. özet veya çıkış bileti
  2. kaynaklar
  3. gerekiyorsa uygulama / kapanış
  4. `plain,noframenumbering`
- Ana anlatım varsayılan olarak kutusuzdur.
- Renkli box'lar yalnızca ikincil semantik vurgu içindir.
- Soru ve çözüm aynı frame'e sıkıştırılmaz.
- Görsel kalite önemlidir; ancak dekoratif içerik akademik doğruluğun önüne geçemez.
- Görseller veri, karşılaştırma, sezgi veya çözüm akışı taşımalıdır.
- Türkçe metinler gerçek Türkçe karakterlerle yazılır; ASCII kaçışı yasaktır.
- Formül, tablo veya grafik sinyali taşıyan kaynak sayfalar deck'e geçince sade paragraf özetine indirgenemez; ilgili matematiksel içerik görünür kalmalıdır.

## 8. Derleme ve Bütünlük

- Türkçe karakter içeren `lutbeamer` sunumlarında varsayılan hat:
  - `latexmk -g -xelatex`
- Bibliyografya varsa:
  - `% !TeX program = xelatex`
  - `% !BIB program = biber`
- `biblatex+biber` kullanan dosyalarda BibTeX'e dönülmez.
- Zorunlu log kontrolü:
  - `rg -n "Missing character|There is no" <log>`
- Mümkünse PDF metni de kontrol edilir:
  - `pdftotext <pdf> -`
- Türkçe bütünlük denetimi başarısızsa teslim yapılmaz.

## 9. Review Gate

- Review aşaması geçmeden final çıktı teslim edilmez.
- `60` frameden kısa deck bloklayıcı hata sayılır.
- Review en az şu riskleri tarar:
  - konu sızıntısı
  - eksik çekirdek kavram
  - gereksiz tekrar
  - tanım-atlama
  - terminoloji kayması
  - pedagojik kopukluk
  - yüzeysellik
  - bağlamsız veya yapay soru kurgusu
  - kolay soru olup ölçücü soru olmaması
  - formül / tablo / grafik kaybı
  - extraction sinyali olan sayfaların deck'te izsiz kaybolması
- Bloklayıcı hata varsa `revision_requests` ile üretime geri dönülür.

## 10. Token Disiplini

- Tüm chapter'ı bağlama sokma; önce manifest ve brief dosyalarını kullan.
- Uzun reference dosyalarını yalnızca gerekli bölüm için aç.
- Aynı bilgiyi her aşamada tekrar etme.
- Orchestrator, tam deck yazımını alt ajanlara bırakır; kendi üstünde gereksiz içerik taşımaz.
- Alt ajan sayısı gösteriş için değil, karar sınırlarını netleştirmek için kullanılır.
