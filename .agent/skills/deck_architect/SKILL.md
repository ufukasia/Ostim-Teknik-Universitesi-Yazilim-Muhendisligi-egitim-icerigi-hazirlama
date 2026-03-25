---
name: deck_architect
description: Hafta kapsamını ve pedagojik akışı kurar; in-scope ve out-of-scope sınırlarını belirler, section/subsection/frame planını yazar ve deck'i öğretilebilir bir iskelete dönüştürür.
---

# Deck Architect

Bu skill token tasarrufu için `BookScope` ve `PedagogyBlueprint` rollerini birleştirir. Kapsamı ve pedagojik planı tek karar paketinde üretir.

## Ne zaman kullanılır

- Haftaya hangi chapter/section/subsection girecek belirlenirken
- In-scope ve out-of-scope listesi çıkarılırken
- Section / subsection / frame planı kurulurken

## Zorunlu okuma sırası

1. `.agent/rules/rules.md`
2. `.agent/skills/mapping.yaml`
3. `.agent/skills/weekly_deck_orchestrator/references/decision-contract.md`
4. `references/blueprint-pattern.md`
5. `.agent/skills/create_weekly_presentation/references/source-selection.md`
6. `.agent/skills/create_weekly_presentation/references/deck-pattern.md`

## Görev sınırı

- Yap:
  - ilgili hafta için kitap kapsamını seç
  - in-scope ve out-of-scope listesi üret
  - kavram bağımlılıklarını sırala
  - section / subsection / frame planını çıkar
  - her frame için pedagojik amacı tanımla
- Yapma:
  - tam LaTeX deck yazma
  - source pack yoksa ham PDF'den uzun alıntılarla çalışma
  - kapsam belirsizken sonraki haftanın ana konusunu içeri alma

## Plan kuralları

- Frame bütçesi için alt sınır `60`tır.
- Tanım verilmeden yöntem veya örnek planlama.
- Her ana konu için en az bir örnek ve en az bir soru zinciri planla.
- Kritik veya uzun konuda `ısınma + ölçücü` soru yapısını düşün.
- Her ana konu sonunda varsayılan zincir:
  - soru
  - çözüm için durak
  - çözüm
- İlk plan `60` altında kalırsa kapsam dışına çıkmadan şu genişletmeleri uygula:
  - sezgi ve formel anlatımı ayır
  - notasyon / okuma frame'i ekle
  - ikinci örnek veya uygulama ekle
  - sık hata / karşılaştırma frame'i ekle
  - büyük konu kümelerinde ikinci soru zinciri planla
- `deck_source_brief.md` veya manifest tarafında extraction attention görünen unit'lerde notasyon, tablo okuma veya grafik yorum frame'i planla.
- `required_items` içine kısa ama uygulanabilir öğeler yaz:
  - `scope:`
  - `section:`
  - `subsection:`
  - `frame: [amaç=...] ...`

## Handoff

- Varsayılan `handoff_target`: `question_design_agent`
