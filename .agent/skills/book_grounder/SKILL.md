---
name: book_grounder
description: Kitabı deck üretimine uygun kaynak pakete çevirir; split manifest, chapter/subsection context ve slide source pack üretir. Scope kararı vermez, deck yazmaz.
---

# Book Grounder

Bu skill ham kitabı deck yazımına uygun küçük kaynak birimlerine indirger.

## Ne zaman kullanılır

- Chapter export veya `kitabim_sections/` hazır değilse
- `subsection_manifest.json`, `subsection_index.md` veya `deck_source_brief.md` üretilecekse
- Ham PDF yerine source pack ile ilerlemek isteniyorsa

## Zorunlu okuma sırası

1. `.agent/rules/rules.md`
2. `.agent/skills/mapping.yaml`
3. `.agent/skills/weekly_deck_orchestrator/references/decision-contract.md`
4. gerekirse `.agent/skills/book_to_slide_source_pipeline/SKILL.md`
5. gerekirse `.agent/skills/pdf_book_processor/SKILL.md`

## Görev sınırı

- Yap:
  - outline / relative TOC / sidecar metadata üret
  - chapter context çıkar
  - subsection veya micro-chunk context çıkar
  - `deck_source_manifest.json` ve `deck_source_brief.md` üret
  - matematik yoğun sayfalarda extraction sinyallerini taşı
- Yapma:
  - hafta kapsamını kendi başına belirleme
  - pedagojik sıra kurma
  - slayt metni yazma

## Matematik extraction disiplini

- Formula, tablo veya grafik kaybı görülen sayfalarda `page_signal_summary` alanını koru.
- `picture omitted` placeholder'ı bırakıp geçme; native text ve OCR denemesini source pack'e yansıt.
- Zayıf OCR sonucu native extraction'dan daha kötü ise onu tercih etme.
- `deck_source_brief.md` içinde extraction attention gerektiren unit'leri görünür bırak.

## Çıktı

- Kısa karar nesnesi
- Mümkünse şu artefact'lar:
  - `outline_manifest.json`
  - `subsection_manifest.json`
  - `subsection_index.md`
  - `deck_source_manifest.json`
  - `deck_source_brief.md`

## Handoff

- Varsayılan `handoff_target`: `deck_architect`
