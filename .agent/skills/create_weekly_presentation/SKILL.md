---
name: create_weekly_presentation
description: Legacy compatibility alias. Yeni haftalık deck üretiminde eski tek parça akış yerine `weekly_deck_orchestrator` ve `deck_architect` zincirini kullan.
---

# Create Weekly Presentation

Bu skill geriye dönük uyumluluk içindir.

## Kullanım

- Kullanıcı eski alışkanlıkla `create_weekly_presentation` mantığında istek verirse bu skill tetiklenebilir.
- Yeni iş akışında doğrudan `weekly_deck_orchestrator` giriş kapısı kabul edilir.

## Yönlendirme

1. `.agent/rules/rules.md` dosyasını oku.
2. `.agent/skills/mapping.yaml` içindeki yeni mimariyi doğrula.
3. `weekly_deck_orchestrator` skill'ine geç.
4. Scope ve plan için `deck_architect`, yazım için `slide_composer`, teslim için `deck_guard` kullan.

## Not

- Bu skill artık tam deck yazım talimatı taşımaz.
- Kaynak seçim, planlama, yazım ve review görevleri yeni ajanlara dağıtılmıştır.
