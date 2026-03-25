---
name: deck_guard
description: Haftalık deck'i teslim öncesi denetler; scope sızıntısı, pedagojik kopukluk, terminoloji kayması, Türkçe bütünlük ve derleme politikasını kontrol eder ve geçer/kaldır kararı üretir.
---

# Deck Guard

Bu skill review ve teslim kapısıdır. Hata varsa deck'i geri çevirir.

## Ne zaman kullanılır

- Yeni veya ciddi biçimde güncellenmiş bir haftalık deck teslim edileceğinde
- Scope, pedagojik akış veya Türkçe bütünlük şüphesi varsa
- Biber / magic comment / log kontrolü gerekiyorsa

## Zorunlu okuma sırası

1. `.agent/rules/rules.md`
2. `.agent/skills/mapping.yaml`
3. `.agent/skills/weekly_deck_orchestrator/references/decision-contract.md`
4. `references/review-checklist.md`
5. gerekirse `validate_turkish_latex.py`

## Karar mantığı

- Bloklayıcı hata varsa:
  - `handoff_target: slide_composer`
  - `revision_requests` dolu olur
- Bloklayıcı hata yoksa:
  - `handoff_target: weekly_deck_orchestrator`
- Yalnızca "güzel görünmüş" olmak geçiş ölçütü değildir.

## Zorunlu kontroller

- toplam frame sayısı `>= 60`
- kitap kapsamına sadakat
- in-scope / out-of-scope uyumu
- her ana konuda örnek + soru zinciri var mı
- sorular doğal Türkçe ve gerçekçi bağlam taşıyor mu
- kolay soru varsa normal zorlukta ölçücü soru da var mı
- tanım-atlama var mı
- terminoloji ve notasyon tutarlılığı
- extraction warning taşıyan unit'lerde formula, tablo ve grafik içeriği korunmuş mu
- `picture omitted` veya benzeri kayıp sinyalleri deck'te sessizce kaybolmuş mu
- tekrar veya yüzeysellik
- Türkçe karakter bütünlüğü
- `biblatex+biber` ve magic comment politikası

## Teslim koşulu

- Review paketi temiz değilse final teslim yoktur.
