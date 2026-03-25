# Weekly Deck Pattern

Bu referans, `1-hafta-olasilik.tex` ile `6-hafta-olasilik.tex` arasinda gozlenen ortak iskeleti toplar.

## Iki gecisli uretim mantigi

Bu projede sunum bir anda frame frame doldurulmaz.

Once:

- tum deck icin haftanin kapsamiyla uyumlu icerik haritasi cikarilir
- section / subsection / frame sirasi netlestirilir

Sonra:

- section 1 bastan sona doldurulur
- section 2 bastan sona doldurulur
- bu sira kapanisa kadar devam eder

Bu mantik iki seyi garanti eder:

- tum hafta butunlu bir akis kazanir
- erken section'lar fazla yer kaplayip son section'lari ezmez
- deck alt siniri olan `60` frame daha plan asamasinda yakalanir

## Acilis kalibi

Varsayilan acilis zinciri:

1. tam gorsel kapak
2. `\maketitle{}`
3. `Icindekiler`

Section baslarinda `\AtBeginSection[]{...}` ile otomatik plan frame'i korunur.

## Govde kalibi

Hafta 1-5 incelendiginde govde akisi tipik olarak su sekildedir:

1. onceki haftadan kopru veya motivasyon
2. haftanin kavram haritasi veya hedefleri
3. ana konu 1
4. ana konu 1 sonu soru/cozum
5. ana konu 2
6. ana konu 2 sonu soru/cozum
7. gerekiyorsa ana konu 3+
8. kapanis ozeti

Bu govde akisi haftaya gore kisa, orta veya uzun olabilir; sabit bir frame bandina zorlanmaz.
Ancak alt sinir vardir: deck `60` frameden kisa kalamaz. Kitap ayni hafta kapsaminda daha zengin akis destekliyorsa daha uzun plan tercih edilir.

## Tipik page budget

Guvenli varsayilan:

- toplam alt sinir: 60 frame
- acilis: 3-4 frame
- kopru / hedef / motivasyon: 4-8 frame
- her ana konu: 10-16 frame
- kapanis: 5-8 frame

Ilk plan 60'in altindaysa plan eksik sayilir; deck kapsam disina cikmadan ayni haftanin alt kavramlari, ek ornekleri, karsilastirmalari ve ek soru zincirleriyle genisletilir.

Ana konu icindeki 10-16 frame genelde su dagilimi izler:

- 4-6 anlatim frame'i
- 2-3 ornek frame'i
- 3 soru/cozum frame'i
- 1-2 sik hata / karsilastirma / detay frame'i
- 1 mini ozet veya gecis frame'i

## Bir ana konu icindeki mikro akis

Her ana konu icinde tipik sira:

1. sezgisel giris
2. tanim veya teorem
3. sayisal ya da gorsel ornek
4. sik hata / dikkat / yorum
5. konu sonu soru
6. cozum icin durak
7. cozum

Uzun soru varsa `Detayli Cozum` eklenebilir.
Deck 60 frame altina dusuyorsa uzun sorularda `Detayli Cozum` varsayilan genisletme araclarindan biridir.

## Frame tipleri

Sik gorulen frame aileleri:

- kopru / hatirlatma
- motivasyon / ikonik ornek
- tanim / teorem
- kavramsal karsilastirma
- sayisal ornek
- uygulama veya muhendislik baglami
- soru
- cozum icin durak
- cozum
- sik hata / yanilgi
- ozet / mini-quiz / cikis bileti

## Baslik kurallari

- frame basligi kisa olur
- tek frame tek ana fikir tasir
- ayni baslik frame ve box icinde tekrar edilmez
- kitap basligini dogrudan kopyalamak yerine sinifta okunabilir Turkce baslik yazilir

## Kapanis kalibi

Tipik kapanis:

1. kavram haritasi veya ozet
2. mini quiz veya cikis bileti
3. kaynaklar
4. NotebookLM veya gerekiyorsa haftalik uygulama
5. son `plain,noframenumbering` frame

## Uygulama notu

Haftalar arasinda ton ve yogunluk degisir; ancak su uc sey sabit kalir:

- acilis ve kapanis omurgasi
- kutusuz ana anlatim
- soru -> durak -> cozum zinciri
