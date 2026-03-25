# Source Selection

Bu referans, haftalik sunumu hangi kitap bolumunden ve hangi yardimci dosyalardan besleyecegini secmek icindir.

## Kaynak onceligi

Kaynaklar su sirayla kullanilir:

1. `kitabim_sections/`
2. `kitap sorulari/`
3. `1-hafta-olasilik.tex` ... `6-hafta-olasilik.tex`
4. `temel sunum yapisi.tex`
5. `kitabim.pdf`

Bir ust kaynaktan yeterli cevap geliyorsa alt kaynaga inme.

## Hizli konu-esleme

Asagidaki esleme varsayilan baslangic noktasi olarak kullanilir:

- `olasiliga giris`, `kumeler`, `orneklem uzayi`, `olay`, `kosullu olasilik`, `carpim kurali`, `bagimsizlik`, `toplam olasilik`, `bayes`
  - ana kaynak: `kitabim_sections/2 Probability.pdf`
- `rastgele degisken`, `pmf`, `pdf`, `cdf`, `ayrik`, `surekli`, `dagilim`
  - ana kaynak: `kitabim_sections/3 Random Variables and Probability Distributions.pdf`
- `beklenen deger`, `mathematical expectation`, `varyans`, `standart sapma`, `lineer kombinasyon`, `chebyshev`
  - ana kaynak: `kitabim_sections/4 Mathematical Expectation.pdf`
- `binom`, `poisson`, `geometric`, `hypergeometric`, `negative binomial`
  - ana kaynak: `kitabim_sections/5 Some Discrete Probability Distributions.pdf`
- `uniform`, `normal`, `exponential`, `gamma`, `beta`, `continuous distributions`
  - ana kaynak: `kitabim_sections/6 Some Continuous Probability Distributions.pdf`

## Yakin hafta secimi

Sunum dili ve akisi icin en yakin hafta da mutlaka secilir:

- Hafta 1-3: `2 Probability.pdf` ile birlikte `1-hafta`, `2-hafta`, `3-hafta`
- Hafta 4: `3 Random Variables and Probability Distributions.pdf` ile birlikte `4-hafta`
- Hafta 5: `4 Mathematical Expectation.pdf` ile birlikte `5-hafta`
- Hafta 6 ve sonrasinda surekli dagilimlar:
  - `6-hafta-olasilik.tex`
  - gerekiyorsa destek olarak `4-hafta-olasilik.tex` ve `5-hafta-olasilik.tex`

## Kitaptan ne cekilir

Kitaptan dogrudan su katmanlar cekilir:

- chapter title
- section title
- subsection veya theorem title
- ana tanimlar
- birincil ornekler
- uygun exercise kaliplari

Kitaptan dogrudan cekilmeyen ama kitap mantigina gore uretilen katmanlar:

- kopru frame'leri
- hafta ici motivasyon akisi
- frame bazli Turkce anlatim
- soru metninin ogrenci dostu yeniden yazimi
- OCR duzeltmesi

## Soru kaynagi secimi

Soru icin kaynak onceligi:

1. ayni bolumdeki textbook example
2. ayni bolumdeki exercise
3. `kitap sorulari/` altindaki ilgili hafta veya bolum
4. kitaba sadik yeni soru uretimi

Yeni soru uretilirse su seyler korunur:

- ana kavram
- zorluk seviyesi
- gerekli hesap adimlari
- kitapta gecen notasyon

Yeni soru yaziminda su kalite kurallari zorunludur:

- dogrudan ceviri dili kullanma
- Turk muhendislik lisans ogrencisine dogal gelen bir dil kur
- gercek dunyada karsiligi olan bir baglam sec
- baglam yalnizca sus olmasin; verilenler ve istenenler baglamla tutarli olsun
- ayni konuda yalnizca cok kolay soru ile yetinme; en az bir normal olcucu soru dusun

## OCR veya metin kirigi halinde toparlama

Asagidaki semptomlar OCR sorununa isaret eder:

- kopmus basliklar
- bozuk ligaturler (`fi`, `ff`, `fl`)
- denklem etrafinda anlamsiz bosluklar
- satir ortasinda kirilan kelimeler
- `picture omitted` placeholder'lari
- formula / table / graph sayfalarinda eksik gorsel veya notasyon

Toparlama sirasi:

1. ligaturleri temizle
2. `page_signal_summary`, `ingest_signals`, `ocr_requested`, `ocr_reasons` alanlarini oku
3. satir kiriklarini anlamli cumlelere cevir
4. denklem ve sayisal veriyi sabit tut
5. kavramsal anlami Turkce ders diline cevir

Matematik agirlikli sayfalarda su kural gecerlidir:

- zayif OCR sonucu native extraction'i otomatik olarak yenmez
- native text formula veya tabloyu daha iyi koruyorsa onu tercih et
- grafik sayfalarinda eksen, etiket ve sekil basligini deck'e tasimadan gecme

## Kitaptan sunuma gecis kurali

Kitaptaki section yapisi bire bir slayt listesi degildir.

Donusum mantigi:

- bir uzun section -> bir `\section{}` + 3-5 `\subsection{}`
- bir theorem veya definition -> 1-2 frame
- bir worked example -> 2-3 frame
- bir topic cluster -> en az bir topic sonu soru zinciri

Ilk deck plani `60` frameden kisa kalirsa, kapsam disina cikmadan su genisletmeler uygulanir:

- ayni kavram icin sezgi ve formel sunum ayrilir
- notasyon okuma frame'i eklenir
- worked example sayisi artirilir
- sik hata / karsilastirma / yorum frame'i eklenir
- buyuk topic cluster'larda ikinci soru zinciri dusunulur

Amac PDF'yi yeniden yazmak degil, onu derslikte anlatilabilir bir akisa cevirmektir.
