---
name: pdf_book_processor
description: PDF kitabın outline yapısını okuyup chapter/section export, relative TOC ve sidecar metadata üreten yardımcı araç skill'i. Haftalık deck için tek başına karar vermez.
---

# PDF Book Processor

Bu skill yalnızca kaynak hazırlama işinde kullanılır.

## Kullanım

- Büyük kitabı chapter veya section PDF'lerine böl
- `outline_manifest.json` üret
- Export edilen parçalara relative TOC ve sidecar metadata yaz

## Kural

- LaTeX deck yazma
- Pedagojik sıra kurma
- Scope kararı verme

Bu skill tipik olarak `book_grounder` tarafından çağrılır.
