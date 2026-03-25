---
name: question_frame_visual_layout
description: Soru framelerinde görsel düzen ve iki aşamalı çözüm akışı için yardımcı moddur; bağımsız haftalık deck ajanı değil, `slide_composer` altında soru standardını uygular.
---

# Question Frame Visual Layout

Bu skill soru yerleşimi için yardımcı moddur.

## Ana kurallar

- Soru frame'i üst hizalı başlar.
- Soru gövdesi varsayılan olarak kutusuzdur.
- Gerekirse sağ sütunda veri taşıyan görsel kullanılır.
- Çözüm zinciri:
  1. `Soru`
  2. `Çözüm için durak`
  3. `Çözüm`

## Ne zaman kullanılır

- `question_design_agent` soru kurgusunu onayladıktan sonra görsel akışı yerleştirirken
- `slide_composer` soru içeren bir bölüm yazarken
- Var olan deck'te soru/çözüm akışı iyileştirilirken

## Ne zaman kullanılmaz

- Hafta kapsamı belirlemek için
- Bağımsız orchestrator gibi davranmak için
