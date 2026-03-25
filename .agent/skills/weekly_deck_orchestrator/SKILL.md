---
name: weekly_deck_orchestrator
description: Kitap temelli haftalık ders sunumu üretiminde minimal ajan zincirini yönetir; kaynak paketini doğrular, deck planını doğru ajana dağıtır, review kapısını işletir ve final teslimi koordine eder.
---

# Weekly Deck Orchestrator

Bu skill haftalık deck üretiminin giriş kapısıdır. Kendisi tam deck yazmaz; işi doğru sırayla doğru alt ajana böler.

## Ne zaman kullanılır

- Kullanıcı hafta, konu ve kitap verip tek promptla deck istediğinde
- Mevcut hafta dosyası kitaba daha sıkı bağlanacak şekilde yeniden kurulacağında
- Kapsam, plan, yazım ve review tek akışta yönetileceğinde

## Zorunlu okuma sırası

1. `.agent/rules/rules.md`
2. `.agent/skills/mapping.yaml`
3. `references/decision-contract.md`
4. `.agent/skills/create_weekly_presentation/references/source-selection.md`
5. `.agent/skills/create_weekly_presentation/references/deck-pattern.md`
6. ihtiyaca göre ilgili alt ajan skill'i

## Akış

1. Kullanıcı girdisinden ders, hafta, konu, kitap ve varsa hedef `.tex` dosyasını çıkar.
2. Source pack, manifest veya chapter export hazır mı kontrol et.
3. Hazır değilse `book_grounder` çağır.
4. Kapsam ve pedagojik plan için `deck_architect` çağır.
5. `deck_architect` planı `60` frameden kısa dönerse aynı hafta kapsamı içinde genişletme iste.
6. Soru kalitesi, bağlamı ve zorluk yapısı için `question_design_agent` çağır.
7. Yazım için `slide_composer` çağır.
8. Teslim öncesi `deck_guard` çağır.
9. Guard revizyon isterse yalnızca gerekli en yakın aşamayı tekrar çalıştır.
10. Source pack `Extraction note` veya benzeri uyarı taşıyorsa bunu `deck_architect`, `slide_composer` ve `deck_guard` girdisine ekle.

## Token disiplini

- Aynı anda birden fazla aktif alt ajan açma; varsayılan tek zincirdir.
- Uzun PDF yerine manifest, `deck_source_brief.md` ve ilgili chunk'larla ilerle.
- Alt ajanlara yalnızca görev için gerekli kısa bağlamı ver.
- Scope kararı olmadan deck yazımına geçme.
- Soru kalite kararı alınmadan soru framelerini son haline getirme.
- Extraction risk işareti olan birimleri sessizce sadeleştirip geçme.

## Teslim koşulu

- `deck_guard` geçmeden final teslim yoktur.
- `60` frameden kısa deck teslim edilemez.
- Review sonucu temizse orchestrator yalnızca sonucu özetler ve deck'i teslim eder.
