# arthurozmowy.pl · treści pod Astro, Netlify i Sveltia CMS

## Budowa witryny (WITRYNA)

- **Astro 5**: strony buduje `src/components/Strona.astro` z plików w `src/content/`, wygląd jest w `src/styles/witryna.css`. Szablony są w modelu blokowym makiety V2: jeden typ bloku to jeden komponent w `src/components/bloki/`.
- **Netlify** buduje poleceniem z `netlify.toml`: sprawdzenie treści (błąd zatrzymuje publikację), pliki pochodne (JSON-LD, `llms.txt`, mapa strony), Astro. Podgląd wersji roboczej z panelu buduje się także przy błędzie, a wynik sprawdzenia pokazuje na stronie `/sprawdzenie` i w plakietce na każdej stronie podglądu.
- **Adres tymczasowy:** każda strona ma `noindex`, nagłówek `X-Robots-Tag` i `robots.txt` blokujący roboty. Przy starcie na arthurozmowy.pl: zmienna `PUBLIKACJA=tak` na Netlify (włącza docelowy `narzedzia/robots-docelowy.txt` i indeksowanie) i usunięcie bloku `X-Robots-Tag` z `netlify.toml`.
- **Formularze** (okienka „Porozmawiaj z Arthurem” i „Napisz do nas”) są nieaktywne do oceny skutków dla ochrony danych (Z6). `/regulamin-strony`, `/regulamin-uslugi`, `/prywatnosc` i `/pliki-cookie` to strony „w przygotowaniu”.
- **Okienko zgód na pliki cookie** (`src/components/Zgody.astro`, własne, decyzja z 19.11.2026): pokazuje się przy pierwszej wizycie i po przycisku „Ustawienia plików cookie” w stopce. Trzy kategorie: niezbędne, statystyki (GA4), reklamy (Google Ads i Meta). Skrypt w `<head>` ustawia Consent Mode v2 na „brak zgody”, zanim ruszy GTM, a wybór z okienka zapisuje w przeglądarce na rok (`src/lib/zgody.ts`). Teksty są w panelu, w Elementach wspólnych. GTM i licznik bez cookies ładują się tylko na produkcji, gdy ich pola w Pomiarze nie są puste.
- **Redakcja `/admin`** (Sveltia CMS 0.259.0): układ paneli opisuje dokument projektu `claude/CMS_panele_redakcji_v1.md`. Zapis tworzy wersję roboczą (pull request z podglądem Netlify), a „Opublikuj” wysyła ją na witrynę. Logowanie osobistym tokenem GitHub (fine-grained, tylko to repozytorium; Contents i Pull requests: read and write, Commit statuses: read).
- **Budowanie kontrolne** na GitHubie (`.github/workflows/podglad.yml`) odkłada log i zbudowaną stronę na gałąź `podglad-wynik`.

Treści w tym repozytorium są w stanie z 17.11.2026 (makieta V2, stały termin rozmów o dowolnej porze, pakiety liczone tygodniami, raport co tydzień ze wzorem). Wszystkie teksty witryny są rozpisane na pliki stron i na pola, które redaktor zmienia w Sveltia CMS. Strony, ich rozdziały i nazwy pokazuje dokument projektu `claude/Mapa_witryny_v1.md`, a moduły makiety i zadania dla szablonów `claude/Przekazanie_WITRYNA.md`.

## Co jest w repozytorium (część treści)

```
src/content/
  strony/                 10 plików, po jednym na stronę (treść, SEO, GEO, zdjęcia, bloki)
    strona-glowna.yml (Jej sprawy)  o-nas.yml  jak-dziala-arthur.yml  jak-korzystac.yml
    jak-rozmawiac-z-mama.yml  czego-nie-obiecujemy.yml  pytania.yml  kontakt.yml  404.yml
  kampanie/               strony kampanii pod reklamy, poza menu, mapą strony i llms.txt (dodaje je redaktor)
  pytania/baza.yml        24 pytania i odpowiedzi, jedno źródło dla strony Pytania i akordeonów
  ustawienia/witryna.yml  belka górna, lista stron, przyciski CTA, dwa okienka, pakiety, dane firmy, stopka, okienko zgód, pomiar
src/content.config.ts     schemat kolekcji Astro 5
public/images/strony/     20 zdjęć stron (21 plików: wejście strony głównej ma dwa kadry)
public/images/og/         3 obrazy do udostępniania (JPG 1200 × 630)
public/images/marka/      logo (SVG i PNG) i ikony 192 i 512 px do manifestu
public/admin/config.yml   konfiguracja Sveltia, generowana skryptem
public/llms.txt           streszczenie witryny dla modeli AI (generowane)
public/llms-full.txt      pełne teksty widocznych stron bez zaślepek (generowane)
public/sitemap-index.xml  mapa strony i sitemap-0.xml z adresami stron z menu (generowane)
narzedzia/                trzy skrypty: konfiguracja CMS, sprawdzenie treści, pliki pochodne
docs/podglad/             tekst każdej strony w kolejności wyświetlania, z nazwą modułu i pola CMS
docs/mapa-pol.md          mapa: strona → rozdział → bloki → pola w CMS
docs/lista-grafik.md      pliki graficzne: miejsce, nazwa, alt, format, stan
docs/jsonld/              dane strukturalne każdej strony
```

Najprościej zacząć od `docs/podglad/`: tam widać każdą stronę tak, jak ją przeczyta córka, a przy każdym elemencie stoi nazwa modułu i ścieżka pola, np. `sekcje[3].bloki[1]`.

## Model treści (makieta V2)

Strona to **wejście** i **rozdziały**. Wejście i każdy rozdział mają nagłówek, zdjęcie, lid i listę **bloków** w kolejności wyświetlania. Jeden typ bloku to jeden moduł makiety, więc szablon potrzebuje jednego komponentu na typ.

| Pole | Moduł makiety | Uwagi |
|---|---|---|
| `strona.nazwa` | Nazwa strony | wielkimi literami nad H1; ta sama nazwa w menu, stopce i linkach |
| `wejscie.h1`, `sekcje[].h2` | Nagłówek H1, Nagłówek H2 | jeden H1 na stronę; H2 to pełne zdanie |
| `wejscie.zdjecie`, `sekcje[].zdjecie` | Plik graficzny HERO, H1, H2 | `plik`, `plik_telefon` (tylko wejście strony głównej), `alt`, `widoczne` |
| `wejscie.lid`, `sekcje[].lid` | Lid H1, Lid H2 | jeden akapit kursywą |
| `sekcje[].kotwica`, `etykieta` | rozdział w menu („Na stronie …”) | puste `etykieta` = rozdziału nie ma w menu |
| `sekcje[].ton` | tło rozdziału | t1–t5, jak dotąd |

| Typ bloku (`typ`) | Moduł makiety | Pola |
|---|---|---|
| `tekst` | Tekst akapitu | `tekst` (akapity oddzielone pustą linią) |
| `glos` | Voice aside | `tekst` |
| `lista` | lista w tekście | `naglowek`, `numerowana`, `punkty` |
| `zasady` | H3, Lid H3, Tekst akapitu | `zasady[]`: `naglowek`, `lid`, `tekst` (numer dopisuje szablon) |
| `cytat` | Karta cytatu | `widoczny`, `etykieta`, `wstep`, `repliki[]`: `kto` (Mama, Arthur, Ty albo puste), `kwestia` |
| `cennik` | Karty ceny | bez pól; pakiety z Ustawień: cena, `rytm`, `opis` i wspólne zdanie `pakiety.dlugosc` |
| `link` | Link wewnętrzny (tekst, nie przycisk; przed nazwą `nawigacja.wiecej`) | `tekst`, `adres`, `aktywny` |
| `wezwanie` | Przycisk CTA | `rodzaj`: `glowne`, `zakupowe` albo `napisz`; `objasnienie` (zdanie pod przyciskiem) |
| `pytania` | Karta pytania | `pytania[]` z bazy; tylko strona Pytania, karty stale rozwinięte |
| `faq` | FAQ (akordeon) | dokładnie 3 `pytania[]` z bazy; pod akordeonem link „Wszystkie pytania” (bez „Więcej:”) → /pytania |

W tekstach działają znaczniki `{firma}`, `{email}`, `{telefon}` i `{godziny}` (dane z Ustawień → Dane firmy), pogrubienie `**…**` i linki `[tekst](/adres)`.

## Nawigacja i nazwy

- **Jeden temat, jedna nazwa, jedno miejsce.** Nazwa strony brzmi tak samo w menu, w stopce, w linkach wewnętrznych i w spisie treści strony głównej. Rozdział nazwany jak strona stoi tylko na stronie głównej i prowadzi do tej strony. Skrypt sprawdzający pilnuje tej zasady.
- **Strony (9):** Jej sprawy (strona główna, adres `/`), O nas, Jak działa Arthur, Jak korzystać, Jak rozmawiać z mamą, Czego nie obiecujemy, Bezpieczeństwo, Pytania, Kontakt. Stare adresy `/jak-to-dziala`, `/jak-skorzystac`, `/regulamin` i adres `/jej-sprawy` mają przekierowania 301 w `netlify.toml`.
- **Belka górna:** logo, przycisk „Menu”, linki „Cena” (`/#cena`) i „Kontakt”, przycisk „Zamów online” (zamówienie) i „Panel klienta”. Menu to jedna lista: strony jako główny poziom, a rozdziały pod stroną oglądaną albo wskazaną.
- **Stopka:** trzy przyciski CTA, lista stron, zdanie o plikach cookie, dane firmy z adresem e-mail, cztery linki prawne i przycisk „Ustawienia plików cookie”.
- **Trzy przyciski CTA** stoją raz, w Ustawieniach: „Porozmawiaj z Arthurem” (okienko z formularzem rozmowy), „Umów mamie próbne arthurozmowy” (zamówienie) i „Napisz do nas” (okienko z formularzem kontaktu). Oba okienka włączamy po ocenie skutków dla ochrony danych (Z6).

## Jak redaktor pracuje w CMS

| Panel w CMS | Plik | Co redaktor zmienia |
|---|---|---|
| Strony | `src/content/strony/*.yml` | wejście strony i treść rozdziałów, SEO, streszczenie dla AI; układ rozdziałów i bloków jest zablokowany |
| Strony kampanii | `src/content/kampanie/*.yml` | strony pod reklamy: dodaje je, układa z tych samych bloków i usuwa |
| Pytania i odpowiedzi | `src/content/pytania/baza.yml` | treść pytań, odpowiedzi i linków pod nimi |
| Elementy wspólne | `src/content/ustawienia/witryna.yml` | pakiety i ceny, przyciski CTA, okienka, belka, lista stron, dane firmy, stopka, okienko zgód, pomiar, marka |

Na stronach z menu redaktor zmienia treść rozdziałów i bloków, ukrywa zdjęcie albo kartę cytatu i wybiera pytania do akordeonu; układ zmienia paczka z WITRYNY. Adresy linków wybiera z listy stron i rozdziałów, którą `generuj_config.py` buduje z plików treści. Zmiana ceny w Elementach wspólnych zmienia karty ceny na obu stronach, dane strukturalne i `llms.txt`. Zapis w panelu usuwa z pliku komentarze YAML i układa pola w kolejności panelu.

## SEO i GEO

- **Adres** (`seo.adres`): małe litery bez polskich znaków. Zmiana adresu wymaga przekierowania 301 w `netlify.toml`.
- **Tytuł** (`seo.tytul`): najlepiej do 60 znaków, twarda granica 70. **Opis** (`seo.opis`): 110–155 znaków.
- **Nagłówki:** jeden H1 na stronę, H2 w każdym rozdziale, zasady i pytania jako H3.
- **Dane strukturalne** (`seo.schemat`): JSON-LD powstaje w `docs/jsonld/`. FAQPage stoi tylko na stronie Pytania, HowTo na stronie Jak rozmawiać z mamą (siedem kroków), AboutPage i Person na O nas, ContactPage na Kontakcie, a Organization, WebSite i Service z trzema ofertami na stronie głównej. Autor i data aktualizacji (`seo.autor`, `seo.zaktualizowano`) trafiają do danych strukturalnych.
- **Definicja arthurozmów** stoi słowo w słowo tak samo w Ustawieniach, w odpowiedzi „Czym są arthurozmowy?”, w JSON-LD i w `llms.txt`. Skrypt sprawdzający pilnuje tej zgodności.
- `geo.streszczenie` to kilka zdań faktów z danej strony w trzeciej osobie; trafia do `llms.txt`. Strona z zaślepkami (dziś O nas) nie trafia do `llms-full.txt`.

## Zdjęcia

Jedyna lista zdjęć to `docs/lista-grafik.md` (generowana z plików stron) i jej odpowiednik w Notion.

- **Zasada:** strona główna ma 4 zdjęcia (wejście i 3 w rozdziałach), każda podstrona 2 (wejście i 1 w rozdziale), strona 404 żadnego. Razem 20 zdjęć.
- **Nazwy plików:** `arthurozmowy-{strona}-{treść}-{format}.webp` w `public/images/strony/`. Wejście strony głównej: `-21x9` i osobny kadr `-4x3` na telefon. Wejście podstrony: `-1x1` (1200 × 1200). Zdjęcie w rozdziale: `-4x3` (1200 × 900). Nowa treść zdjęcia dostaje nową nazwę.
- **Alt:** to, co naprawdę widać, słowami strony („mama”, „córka”, „rozmowa”). Jedno zdanie, 50–125 znaków. Nigdy „Arthur”, „arthurozmowy” ani „AI” przy zdjęciu człowieka.
- **Obróbka zdjęć:** każde zdjęcie przechodzi przez jeden prompt „Xiaomi – Huawei Style” z Księgi (rozdz. 17): retusz jak w kampanii premium, bez odmładzania.
- **Zdjęcie `arthurozmowy-o-nas-eksperci-4x3.webp`** to zdjęcie robocze z modelami w roli ekspertów. Stoi tylko na stronie roboczej, z oznaczeniem „[zdjęcie przykładowe]” w tekście alternatywnym, obok przykładowych danych ekspertki. Nawias kwadratowy blokuje wyjście strony O nas na arthurozmowy.pl.
- Skrypt sprawdzający zgłasza błąd przy złej liczbie zdjęć, braku pliku, złym formacie w nazwie albo złych proporcjach pliku.

## Karta cytatu

Przykładowy dialog mamy z Arthurem ma zawsze etykietę „Przykład rozmowy”, bo jest wymyślony (skrypt tego pilnuje). W karcie nigdy nie stoi fragment prawdziwej rozmowy z mamą. Karta z przykładem raportu na stronie Jak działa Arthur pokazuje wzór z Księgi (rozdz. 13): pola „kto” są tu nagłówkami części raportu („Kiedy rozmawiali”, „O czym rozmawiali”, „Do czego mama wraca”), a ostatnia linia nie ma nagłówka.

## Narzędzia

Uruchamiasz je z katalogu głównego repozytorium (Python 3 z biblioteką PyYAML).

```
python3 narzedzia/generuj_config.py
```

```
python3 narzedzia/sprawdz_tresci.py
```

```
python3 narzedzia/buduj_pochodne.py
```

`generuj_config.py` tworzy `public/admin/config.yml`; model treści zmieniasz w skrypcie i w `src/content.config.ts`, nie w pliku wynikowym. `sprawdz_tresci.py` sprawdza, czy każde pole treści ma pole w CMS, długości tytułów i opisów, nagłówki, kotwice i linki, bloki, akordeony, słowa zakazane (z wyjątkiem „seniora” w cudzysłowie na O nas), pisownię „Arthur” i „arthurozmowy”, znaczniki, zgodność definicji i cen, zasadę „jeden temat, jedna nazwa”, zdjęcia, a na końcu wypisuje zaślepki. Z opcją `--podglad` zapisuje też stronę `public/sprawdzenie.html` i plakietkę dla podglądu wersji roboczej i nie zatrzymuje budowania. Sprawdza również strony kampanii (adres, słowa zakazane, bloki, zdjęcia). `buduj_pochodne.py` tworzy podglądy stron, mapę pól, JSON-LD, listę grafik, oba pliki dla AI i mapę strony.

Stan na 17.11.2026: zero błędów, 2 zaślepki (dane ekspertki na stronie O nas), 6 uwag (dwa rozdziały „Najczęstsze pytania” w tym samym tonie co rozdział wyżej, jeden tytuł o znak za długi, trzy rozdziały o tej samej nazwie na kilku stronach przy tym samym temacie).

## Zaślepki, które blokują publikację

| Gdzie | Czego brakuje | Kto decyduje |
|---|---|---|
| O nas · Nasza metoda | ekspertka: imię i nazwisko, specjalizacja, staż, jednostka naukowa, wspólne zdjęcie (Z1) | Ty |

## Decyzje otwarte

- Zamówienie („Umów mamie próbne arthurozmowy”, „Zamów online”) prowadzi do panelu klienta, którego jeszcze nie ma; przyciski są nieaktywne.
- Strony `/regulamin-strony`, `/regulamin-uslugi`, `/prywatnosc` i `/pliki-cookie` to na adresie tymczasowym strony „w przygotowaniu”. Strona Pliki cookie opisze narzędzia z okienka zgód (GA4, Google Ads, Meta) i czas przechowywania plików cookie.
- Okienka „Porozmawiaj z Arthurem” i „Napisz do nas” mają teksty, ale włączamy je dopiero po ocenie skutków dla ochrony danych (Z6), razem z polityką prywatności.
- Sposób płatności i bramka (FIRMA), opinia prawnika o rozliczeniu „Pożegnania” (Z9), zbieranie zgody mamy (Z5), numer, z którego Arthur dzwoni do mamy. Kanałem rozmów jest telefon (decyzja z 17.11.2026).
- Plausible czy Umami jako licznik bez cookies. Okienko zgód nie ma rejestru zgód (dowodu zgody); do oceny w Z6.
- Pisownia nazwy firmy „arthurozmowy Piotr Jaworski” do potwierdzenia z CEIDG.
