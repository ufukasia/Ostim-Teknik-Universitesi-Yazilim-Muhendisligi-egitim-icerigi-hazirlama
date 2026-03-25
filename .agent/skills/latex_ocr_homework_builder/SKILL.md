---
name: latex_ocr_homework_builder
description: OCR uyumlu LaTeX odevleri hazirlarken tam kapak, ArUco baslik alani ve page-by-page cevap kutusu yerlesimi kurar. Kullanici odev hazirla, OCR cevap kagidi ekle, 2 sikli veya 3 sikli cevap sayfasi kur, kapagi koru, cevap sayfalarini tek tek kaydet gibi isteklerde kullan.
---

# OCR Homework Builder

Bu skill, proje icindeki OCR odev yapisini tekrar kullanmak icin vardir.

## Zorunlu Akis

1. Once `.agent/rules/rules.md`, sonra `.agent/skills/mapping.yaml`, sonra bu skill uygulanir.
2. Global kaynak skill dosyalarini temel referans olarak kullan:
   - `C:/Users/ufuka/.codex/skills/latex-ocr-homework-builder/assets/full-cover-template.tex`
   - `C:/Users/ufuka/.codex/skills/latex-ocr-homework-builder/assets/ocr-preamble.tex`
   - `C:/Users/ufuka/.codex/skills/latex-ocr-homework-builder/assets/page-two-part.tex`
   - `C:/Users/ufuka/.codex/skills/latex-ocr-homework-builder/assets/page-three-part.tex`
   - `C:/Users/ufuka/.codex/skills/latex-ocr-homework-builder/assets/page-diagram-solution.tex`
   - `C:/Users/ufuka/.codex/skills/latex-ocr-homework-builder/assets/odev2-answer-pages.tex`
3. Kullanici tam kapagi istiyorsa kapagi kisaltma; tam blok olarak koru.
4. Kullanici belirli soru yapisi veriyorsa buna uygun sayfa blogunu sec:
   - 2 alt soru icin iki parca sayfa
   - 3 alt soru icin uc parca sayfa
   - cizim + cozum icin diagram/cozum sayfasi
5. OCR etiketlerini `CEVAP-*` ve `SONUC *` semantigiyle koru.
6. Marker kullanan dosyalari `.vscode/settings.json` icindeki XeLaTeX tarifine uygun tut.

## Varsayilanlar

- Her cevap sayfasi bir `tcolorbox` icinde tutulur.
- Cevap alanlari yukaridan asagi okunur sirada dizilir.
- Kullanici aksini istemedikce tam kapak metni ve teslim kurallari korunur.
- Kullanici `page page kaydet` isterse `odev2-answer-pages.tex` mantigi ile her soruyu ayri OCR sayfasina yerlestir.
