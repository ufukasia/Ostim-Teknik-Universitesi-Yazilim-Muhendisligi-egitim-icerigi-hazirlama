# Decision Contract

Tüm aktif ajanlar aynı kısa karar nesnesini kullanır.

## Zorunlu alanlar

- `decision_summary`
- `required_items`
- `forbidden_items`
- `handoff_target`

## İsteğe bağlı alanlar

- `risks`
- `revision_requests`

## Kurallar

- Boş alan yazma.
- Aynı bilgiyi paragraf halinde tekrar etme.
- Yalnızca önceki aşamadan farklı kararları yaz.
- `required_items` ve `forbidden_items` kısa, taranabilir ve eyleme dönük olsun.

## Örnek: scope veya plan paketi

```yaml
decision_summary: "Hafta 5 için Chapter 4.1-4.3 temelli expectation odağı seçildi."
required_items:
  - "source: temp/ch4-slide-pack/deck_source_brief.md"
  - "scope: beklenen değer tanımı, ayrık durumda hesap, lineerlik"
  - "frame: [amaç=tanim] Beklenen değer sezgisi"
  - "frame: [amaç=uygulama] Ayrık beklenti örneği"
forbidden_items:
  - "variance ayrıntılı ispatı"
  - "moment generating function"
handoff_target: "slide_composer"
risks:
  - "Chapter 4.3 varyans ön izlemesi içeriyor; hafta kapsamı teyit edilmezse sızıntı riski var."
```

## Örnek: review paketi

```yaml
decision_summary: "Deck kapsam olarak doğru, ancak iki frame tanım-atlama nedeniyle bloklanıyor."
required_items:
  - "koru: Section 1 ve Section 2 akışı"
forbidden_items:
  - "tanımsız kullanılan lineerlik cümlesi"
handoff_target: "slide_composer"
revision_requests:
  - "Beklenen değer formülünden önce rastgele değişken hatırlatması ekle."
  - "Son örnekte notasyon X yerine aynı deck boyunca kullanılan Y ile hizalansın."
```
