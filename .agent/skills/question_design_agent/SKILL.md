---
name: question_design_agent
description: Sunumdaki soruları kitapla uyumlu ama doğrudan çeviri olmayan, gerçekçi bağlama sahip, Türk mühendislik lisans öğrencisine doğal gelen ve pedagojik olarak dengeli yapılara dönüştürür; her ana konu için örnek ve soru zincirini denetler.
---

# Question Design Agent

Bu skill soru kalitesi için ayrı kontrol katmanıdır. Soru yazımını yalnızca görsel yerleşim işi olarak görmez; kurgu, bağlam, zorluk ve öğretim değerini denetler.

## Ne zaman kullanılır

- Haftalık deck içinde soru ve örnek akışı kurulurken
- Soru dili mekanik, çevrilmiş veya yapay görünüyorsa
- Her ana konu için örnek ve soru zinciri zorunlu tutulacaksa

## Zorunlu okuma sırası

1. `.agent/rules/rules.md`
2. `.agent/skills/mapping.yaml`
3. `.agent/skills/weekly_deck_orchestrator/references/decision-contract.md`
4. `references/question-quality-checklist.md`
5. `.agent/skills/create_weekly_presentation/references/source-selection.md`

## Görev sınırı

- Yap:
  - her ana konu için en az bir anlatımlı örnek ve bir soru zinciri olup olmadığını denetle
  - soruları kitapla uyumlu ama doğal Türkçe ile yeniden kur
  - gerçekçi mühendislik, veri, üretim, yazılım, kalite, bakım veya ölçüm bağlamı seç
  - zorluk yapısını `ısınma -> ölçücü` mantığında dengele
  - kolay soru varsa yanında en az bir normal zorlukta soru veya çözüm zinciri planla
- Yapma:
  - kitap dışı kavram ekleme
  - literal çeviri soru metni bırakma
  - yapay ve rasyonellikten uzak senaryo üretme

## Handoff

- Varsayılan `handoff_target`: `slide_composer`
