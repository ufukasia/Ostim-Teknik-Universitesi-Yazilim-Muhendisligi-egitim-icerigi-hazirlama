---
name: slide_composer
description: Scope ve blueprint paketini gerçek LaTeX/lutbeamer deck'ine çevirir; kutusuz anlatım, görsel disiplin ve soru-durak-çözüm zinciriyle haftalık sunum gövdesini üretir.
---

# Slide Composer

Bu skill gerçek deck yazım katmanıdır. Scope veya plan belirsizse tahmin etmez; eksik karar için geri döner.

## Ne zaman kullanılır

- Blueprint paketinden `.tex` dosyası üretileceğinde
- Mevcut hafta deck'i scopea sadık biçimde doldurulacağında
- Görsel düzen, örnek ve soru zinciri yazılacağında

## Zorunlu okuma sırası

1. `.agent/rules/rules.md`
2. `.agent/skills/mapping.yaml`
3. `.agent/skills/weekly_deck_orchestrator/references/decision-contract.md`
4. `.agent/skills/question_design_agent/references/question-quality-checklist.md`
5. `.agent/skills/latex_presentation_assistant/SKILL.md`
6. soru varsa `.agent/skills/question_frame_visual_layout/SKILL.md`
7. gerekli example snippet dosyaları

## Yazım kuralları

- Ana anlatım varsayılan olarak kutusuzdur.
- Görsel kullanıyorsan öğretim yükü taşımalıdır.
- `lutbeamer` açılış ve kapanış omurgasını bozma.
- Blueprint `60` frameden kısaysa deck'i sıkıştırarak kapatma; planı genişletmek için `deck_architect`e geri dön veya aynı scope içindeki ayrıştırılmış anlatımı yaz.
- Soru metnini kelime kelime çeviri gibi bırakma; question tasarım paketindeki bağlam ve zorluk kararını uygula.
- Her ana konu bloğunda örnek ve soru zinciri görünür olmalı.
- `deck_source_brief.md`, chunk dosyaları veya page exports extraction warning taşıyorsa ilgili formula, tablo ve grafik içeriğini görünür biçimde işle.
- `picture omitted` görülen kaynakları sade paragrafla geçiştirme; native text, sekil etiketi veya tablo verisini deck'e taşı.
- Soru çözüm zinciri:
  1. `Soru`
  2. `Çözüm için durak`
  3. `Çözüm`
- Scope paketinde olmayan kavramı "güzel olur" diye ekleme.
- Türkçe karakterleri gerçek haliyle yaz.

## Çıktı

- Hedef `.tex` dosyasında güncel deck
- Ardından kısa karar nesnesi:
  - neyin yazıldığı
  - hangi risklerin kaldığı
  - `handoff_target: deck_guard`
