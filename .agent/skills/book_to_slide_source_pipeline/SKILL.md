---
name: book_to_slide_source_pipeline
description: Kitabı modern extraction ve OCR ile slide source pack'e hazırlayan yardımcı skill. Final içerik yazmaz; `book_grounder` altında veya doğrudan extraction görevlerinde kullanılır.
---

# Book To Slide Source Pipeline

Bu skill araç katmanıdır.

## Ne zaman kullanılır

- Ham PDF'den chapter/subsection context çıkarılacaksa
- `deck_source_brief.md` ve `deck_source_manifest.json` üretilecekse
- OCR rescue gerekliyse

## Görev

1. Gerekirse outline ve export katmanını `pdf_book_processor` ile hazırla.
2. Chapter context çıkar.
3. Subsection veya micro-chunk context çıkar.
4. `build_slide_source_pack.py` ile slide source pack üret.

## Kural

- Ham PDF'den doğrudan slayt yazma.
- Native extraction yeterliyse zayıf OCR sonucunu kabul etme.
- Yerel `glm-ocr` çağrısı varsa görüntüyü gerçekten modele gönder; dosya yolunu düz prompt gibi bırakma.
- Formula, tablo ve grafik riski taşıyan sayfaları `page_signal_summary` ve source-pack brief içinde işaretle.
- `picture omitted` placeholder'ı görülen sayfalar için native text fallback'ini kaybetme.
- Bu skill scope belirlemez ve deck yazmaz.
