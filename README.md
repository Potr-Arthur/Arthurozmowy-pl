# arthurozmowy.pl · treści pod Astro, Netlify i Sveltia CMS

## Budowa witryny (WITRYNA)

- **Astro 5**: strony buduje `src/components/Strona.astro` z plików w `src/content/`; typy sekcji renderuje `Sekcja.astro`, wygląd jest w `src/styles/witryna.css` (prototyp „Matryca arthurozmowy”).
- **Netlify** buduje poleceniem z `netlify.toml`: sprawdzenie treści (błąd zatrzymuje publikację), pliki pochodne (JSON-LD, `llms.txt`), Astro.
- **Adres tymczasowy:** każda strona ma `noindex`, nagłówek `X-Robots-Tag` i `robots.txt` blokujący roboty. Przy starcie na arthurozmowy.pl: zmienna `PUBLIKACJA=tak` na Netlify (włącza docelowy `narzedzia/robots-docelowy.txt` i indeksowanie) i usunięcie bloku `X-Robots-Tag` z `netlify.toml`.
- **Formularze** są nieaktywne do oceny skutków dla ochrony danych (Z6). `/regulamin` i `/prywatnosc` to strony „w przygotowaniu”.
- **Redakcja `/admin`** (Sveltia CMS): logowanie osobistym tokenem GitHub (fine-grained, tylko to repozytorium, uprawnienie Contents: read and write).
- **Budowanie kontrolne** na GitHubie (`.github/workflows/podglad.yml`) odkłada log i zbudowaną stronę na gałąź `podglad-wynik`.

Ta paczka to baza dla pod-projektu WITRYNA. Zawiera wszystkie teksty witryny w stanie z 4.11.2026, rozpisane na pliki stron i przypisane do pól, które redaktor zmienia w Sveltia CMS. Każde pole odpowiada blokowi z Matrycy (`claude/Matryca_WITRYNA_v1.md`). Strony, ich rozdziały i nazwy pokazuje dokument projektu `claude/Mapa_witryny_v1.md`.

## Co jest w paczce

```
src/content/
  strony/                 9 plików, po jednym na stronę (treść, SEO, GEO, zdjęcia, wezwania)
    strona-glowna.yml  jak-to-dziala.yml  czego-nie-obiecujemy.yml  pytania.yml
    jak-skorzystac.yml  jak-rozmawiac-z-mama.yml  o-nas.yml  kontakt.yml  404.yml
  pytania/baza.yml        21 pytań i odpowiedzi, jedno źródło dla strony Pytania i akordeonów
  ustawienia/witryna.yml  menu i lista stron, wezwania, okienko rozmowy, pakiety, dane firmy, stopka
src/content.config.ts     schemat kolekcji Astro 5 (szkic, do uruchomienia w WITRYNA)
public/images/strony/     18 zdjęć stron: wejście podstrony 1:1, rozdział 4:3, wejście strony głównej 21:9 + 4:3 na telefon
public/images/og/         3 obrazy do udostępniania (JPG 1200 × 630)
public/images/marka/      logo (SVG i PNG) i ikony 192 i 512 px do manifestu
public/favicon.ico        ikona strony (16, 32 i 48 px); obok apple-touch-icon.png (180 px)
public/admin/index.html   panel redakcji Sveltia CMS (adres /admin)
public/admin/config.yml   konfiguracja Sveltia, generowana skryptem
public/llms.txt           streszczenie witryny dla modeli AI (generowane)
public/llms-full.txt      pełne teksty widocznych stron bez zaślepek (generowane)
public/robots.txt         docelowy dostęp dla wyszukiwarek i robotów AI, bez /admin/
narzedzia/                trzy skrypty: konfiguracja CMS, sprawdzenie treści, pliki pochodne
docs/podglad/             tekst każdej strony do czytania, z nazwą pola CMS przy każdym elemencie
docs/mapa-pol.md          mapa: strona → sekcja → blok Matrycy → pola w CMS
docs/lista-grafik.md      pliki graficzne: nazwa, alt, format, miejsce, treść zdjęcia, stan
docs/jsonld/              wzory danych strukturalnych dla każdej strony
```

Najprościej zacząć od `docs/podglad/`: tam widać każdą stronę tak, jak ją przeczyta córka, a przy każdym zdaniu stoi ścieżka pola, np. `sekcje[3].h2`.

## Nawigacja i nazwy (decyzje z 4.11.2026)

- **Jeden temat, jedna nazwa, jedno miejsce.** Nazwa strony brzmi tak samo w menu, w stopce, w linkach „więcej” i w spisie treści strony głównej. Rozdział nazwany jak strona stoi tylko na stronie głównej i prowadzi do tej strony. Skrypt sprawdzający pilnuje tej zasady.
- **Dwie warstwy.** Strona główna prowadzi do decyzji. Podstrona służy do sprawdzenia (Jak to działa, Czego nie obiecujemy, Pytania, O nas) albo do działania (Jak skorzystać, Jak rozmawiać z mamą, Kontakt).
- **Nagłówek:** logo, mały link „Panel klienta”, przycisk „Porozmawiaj z Arthurem” i przycisk „Menu”. Menu otwiera panel z grupami „Na tej stronie” (rozdziały oglądanej strony) i „Strony” (`nawigacja.strony`), a pod nimi „Umów mamie pierwszą arthurozmowę” i „Panel klienta”. Tak samo na telefonie i na komputerze; na telefonie przycisk wezwania jest przyklejony do dołu ekranu.
- **Stopka:** te same strony, zakup, Panel klienta i linki prawne.
- **„Porozmawiaj z Arthurem”** otwiera okienko z formularzem: numer telefonu oraz wybór „teraz” albo dzień i godzina. Na przyciskach nie ma numeru Arthura ani osobnego wezwania „Nie możesz teraz rozmawiać?”. Formularz włączamy po ocenie skutków dla ochrony danych (Z6), z polityką prywatności i decyzją, dokąd trafia numer i czy próbna rozmowa jest nagrywana.
- **Pytania na podstronach:** blok „Najczęstsze pytania” nie wchodzi do spisu treści i kończy się linkiem „Wszystkie pytania” → /pytania.

## Jak redaktor pracuje w CMS

| Grupa w CMS | Plik | Co redaktor zmienia |
|---|---|---|
| Strony | `src/content/strony/*.yml` | SEO, streszczenie dla AI, H1, wstęp, zdjęcie wejścia, sekcje strony w kolejności wyświetlania |
| Pytania i odpowiedzi | `src/content/pytania/baza.yml` | treść pytań, odpowiedzi i linków pod nimi |
| Ustawienia | `src/content/ustawienia/witryna.yml` | napisy menu, lista stron, teksty wezwań, okienko rozmowy, pakiety i ceny, dane firmy, stopka |

Wezwania, lista stron, ceny i dane firmy stoją w Ustawieniach tylko raz, a strona wybiera przełącznikami, które wezwanie pokazać. Dzięki temu przycisk „Porozmawiaj z Arthurem” i nazwy stron brzmią wszędzie tak samo, a zmiana ceny w jednym miejscu zmienia cennik na stronie głównej, na stronie Jak skorzystać, w danych strukturalnych i w `llms.txt`. Znacznik `{firma}` w tekście sekcji wstawia linię „arthurozmowy Piotr Jaworski, Kaliska 155G, 07-130 Łochów, NIP 113 135 29 41”.

Sekcje strony to lista z typami. Redaktor może zmienić kolejność sekcji, ukryć zdjęcie albo okno głosu i wybrać pytania do akordeonu, ale nie dopisze nowego typu bloku, bo typy odpowiadają komponentom Astro.

## Typy sekcji a bloki Matrycy

| Typ w CMS | Bloki Matrycy | Pola | Gdzie występuje |
|---|---|---|---|
| wejście (stałe pole strony) | 1 wejście strony głównej, 2 Hero2, 13 zdjęcie, 18 autor i data | `h1`, `h1_wyroznienie`, `lid`, `zdjecie`, `wezwania`, `pokaz_autora_i_date` | każda strona |
| `rozdzial` | 3 rozdział, 4 definicje, 5 lista, 7 cennik, 13 zdjęcie, 16 cudze zdanie, 17 okno głosu, 11 link, 12 wezwania | `h2`, `tekst`, `definicje`, `lista`, `cennik`, `tekst_po`, `akapit_ukryty`, `zdjecie`, `okno_glosu`, `cudze_zdanie`, `linki`, `wezwania` | większość rozdziałów |
| `zasady` | 6 lista zasad | `h2`, `zasady` (zdanie, opis, „Dlaczego:” od nowej linii, R168) | Jak to działa |
| `krok` | 9 krok z przykładem | `numer`, `h2`, `tekst`, `przyklad`, `zdjecie`, `linki`, `wezwania` | Jak rozmawiać z mamą |
| `watpliwosci` | 10 wątpliwości | `h2`, `tekst`, `pary` (zdanie mamy i odpowiedź), `zakonczenie` | Jak rozmawiać z mamą |
| `pytania` | 8 pytanie i odpowiedź, 15 wstęp rozdziału | `wstep`, `zdjecie`, `pytania` (identyfikatory z bazy), `wezwania` | Pytania |
| `faq` | 19 FAQ w akordeonie | `h2`, `pytania` (dokładnie 3 z bazy), `linki` („Wszystkie pytania”) | podstrony poza Pytaniami |
| `kontakt` | 5 lista, 14 dane firmy | `h2`, `tekst`, `pokaz` (e-mail, telefon, godziny, czas odpowiedzi), `uwaga`, `linki` | O nas, Kontakt |
| `koniec` | 12 pas wezwań na koniec strony | `ton`, `linki`, `wezwania` | podstrony |

Każda sekcja ma też `kotwica` (adres po #), `etykieta` (spis treści, puste pole = poza spisem) i `ton` (t1–t5). Pełną mapę dla każdej strony, z numerami bloków i nazwami pól, zawiera `docs/mapa-pol.md`.

## SEO

- **Adres** (`seo.adres`): małe litery bez polskich znaków. Zmiana adresu wymaga przekierowania 301 w `netlify.toml`.
- **Tytuł** (`seo.tytul`): najlepiej do 60 znaków, twarda granica 70. Trzy tytuły mają 62–63 znaki (strona główna, Jak to działa, Pytania); zostały, bo Google mierzy szerokość w pikselach, nie w znakach.
- **Opis** (`seo.opis`): 110–155 znaków, pierwsze zdanie samo mówi, o czym jest strona.
- **Nagłówki:** jeden H1 na stronę (`wejscie.h1`), H2 jako pełne zdanie w każdym rozdziale. Na stronie Pytania nagłówkami H2 są same pytania, a nazwy rozdziałów stoją tylko w spisie treści. Pierwszy rozdział strony O nas nie ma H2 ani wpisu w spisie treści, bo jest ciągiem dalszym H1.
- **Kotwice:** każda sekcja ze spisu treści ma stałą kotwicę zgodną z nazwą rozdziału. Linki w bazie pytań prowadzą do konkretnych sekcji, np. `/jak-skorzystac#rezygnacja`.
- **Dane strukturalne** (`seo.schemat`): szablon buduje JSON-LD z treści i Ustawień według wzorów w `docs/jsonld/`. FAQPage stoi tylko na stronie Pytania, bo Google prosi o oznaczenie każdego pytania w jednym miejscu witryny. HowTo stoi na stronie Jak rozmawiać z mamą, AboutPage i Person na O nas, ContactPage na Kontakcie, a Organization, WebSite i Service z trzema ofertami na stronie głównej. Google nie pokazuje już wyników rozszerzonych dla FAQ i HowTo na zwykłych stronach, ale oznaczenia nadal pomagają modelom AI zrozumieć treść.
- **Autor i data:** `seo.autor` i `seo.zaktualizowano` trafiają do bloku 18 i do `dateModified` (Księga, rozdz. 21.6). Datę zmieniasz przy każdej zmianie treści.
- **Strona 404:** `indeksuj: false`, bez opisu i bez danych strukturalnych.
- **Mapa witryny:** w WITRYNA dodać `@astrojs/sitemap`; `robots.txt` już na nią wskazuje.

## GEO, czyli widoczność w odpowiedziach modeli AI

- Definicja arthurozmów stoi słowo w słowo tak samo w Ustawieniach, w odpowiedzi „Czym są arthurozmowy?”, w JSON-LD i w `llms.txt` (R167). Skrypt sprawdzający pilnuje tej zgodności.
- Pierwsze zdanie każdej odpowiedzi w bazie pytań samo odpowiada na pytanie, a każdy H2 da się zacytować bez kontekstu.
- `geo.streszczenie` to 2–3 zdania faktów z danej strony w trzeciej osobie. Trafia do `llms.txt` i może zasilić `description` w JSON-LD. Streszczenia napisałem ze zdań, które są już na stronach, i są do Twojej akceptacji.
- `llms.txt` i `llms-full.txt` generuje skrypt. Strona z zaślepkami (dziś O nas) nie trafia do `llms-full.txt`.
- `robots.txt` wpuszcza wszystkie roboty, także wyszukujące i uczące roboty modeli AI (decyzja Piotra z 1.11.2026).

## Zdjęcia

Jedyna lista zdjęć to `docs/lista-grafik.md` (generowana z plików stron) i jej odpowiednik w Notion („Zdjęcia witryny arthurozmowy.pl (18) i grafiki”).

- **Zasada (5.11.2026):** strona główna ma 4 zdjęcia (wejście i 3 w rozdziałach), każda podstrona 2 (wejście i 1 w rozdziale), strona 404 żadnego. Razem 18 zdjęć. Skrypt sprawdzający zgłasza błąd przy innej liczbie i przy tym samym pliku w dwóch miejscach.
- **Nazwy plików:** `arthurozmowy-{strona}-{treść}.webp` w `public/images/strony/`, jeden plik na komputer i telefon (wyjątek: wejście strony głównej `-desk.webp` i `-tel.webp`); obrazy do udostępniania `arthurozmowy-og-{strona}.jpg` (1200 × 630) w `public/images/og/`. Nowa treść zdjęcia dostaje nową nazwę; nazwa nigdy nie wraca do innej treści.
- **Kadry (6.11.2026):** wejście strony głównej 21:9 (najlepiej 2880 × 1234) i 4:3 na telefonie (1200 × 900); wejście podstrony kwadrat 1:1 (1200 × 1200); zdjęcie w rozdziale 4:3 (1200 × 900).
- **Alt:** zaczyna się od tego, co naprawdę widać, i mówi słowami strony („mama”, „córka”, „opowiada”, „rozmowa”). Jedno zdanie, 50–125 znaków, bez słów zakazanych. Nigdy „Arthur”, „arthurozmowy” ani „AI” przy zdjęciu człowieka. Pod zdjęciami nie ma podpisów w stylu opinii.
- **Zero retuszu skóry** na zdjęciach osób starszych (zasada nienegocjowalna).
- **Stan (5.11.2026):** wszystkie 18 zdjęć, 3 obrazy do udostępniania, logo i ikony są w `public/`. Stan w `docs/lista-grafik.md` wynika z plików: zdjęcie jest „gotowe”, gdy plik jest na miejscu (wejście strony głównej: oba kadry). Skrypt sprawdzający zgłasza błąd, gdy widoczne zdjęcie nie ma pliku.
- **Jedyne ukryte zdjęcie** to wspólne zdjęcie ekspertki z Piotrem na O nas (`widoczne: false`). To wersja robocza z modelką i nie może się pokazać nawet na adresie tymczasowym; zastąpi je prawdziwe zdjęcie razem z danymi ekspertki (Z1).
- **Logo i ikony:** w nagłówku `/images/marka/arthur-logo.svg` (alt „Arthur”). W `<head>` każdej strony: `<link rel="icon" href="/favicon.ico" sizes="any">` i `<link rel="apple-touch-icon" href="/apple-touch-icon.png">`; ikony 192 i 512 px są do pliku manifestu, jeśli WITRYNA go doda.

## Okno głosu i cudze zdanie

- Okno głosu (blok 17): najwyżej jedno w rozdziale i trzy na stronie; przykład rozmowy zawsze z etykietą „Przykład rozmowy” i przypisem, że jest wymyślony. Dziś widoczne dwa: na stronie głównej (rozdział Jak to działa) i na stronie Jak to działa (Ciągłość rozmów). Pole `nagranie` przyjmie tylko nagranie demonstracyjne z transkrypcją, nigdy fragment prawdziwej rozmowy z mamą.
- Cudze zdanie (blok 16) w rozdziale „Czemu służą arthurozmowy?” jest zarezerwowane i ukryte. Pokaże się tylko prawdziwe zdanie mamy z udokumentowaną zgodą.

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

`generuj_config.py` tworzy `public/admin/config.yml` bez kotwic YAML, bo Sveltia czyta YAML ściśle; model treści zmieniasz w skrypcie, nie w pliku wynikowym. `sprawdz_tresci.py` sprawdza, czy każde pole treści ma pole w CMS, długości tytułów i opisów, H1 i H2, kotwice i linki, akordeony, słowa zakazane (z wyjątkiem „seniora” w cudzysłowie na O nas, R141), pisownię „Arthur” i „arthurozmowy”, zasady okna głosu i cudzego zdania, zgodność definicji i cen, zasadę „jeden temat, jedna nazwa”, a na końcu wypisuje zaślepki. `buduj_pochodne.py` tworzy podglądy stron, mapę pól, wzory JSON-LD i oba pliki dla AI. W WITRYNA warto podpiąć sprawdzenie do budowania na Netlify, żeby strona z błędem nie wyszła.

Stan na 5.11.2026: zero błędów, 10 zaślepek, 13 uwag (brak stron regulaminu i polityki prywatności, trzy tytuły powyżej 60 znaków i jeden opis powyżej 155, ukryte zdjęcie na O nas, rozdziały o tej samej nazwie na dwóch stronach przy tym samym temacie).

## Wdrożenie Sveltia (do zrobienia w WITRYNA)

1. W `public/admin/config.yml` wpisać repozytorium (`backend.repo`) i adres workera logowania (`backend.base_url`). Sveltia loguje przez GitHub; na Netlify najprostszy jest worker `sveltia-cms-auth` na Cloudflare Workers, bo Sveltia nie obsługuje Netlify Identity ani Git Gateway.
2. Przypiąć wersję skryptu w `public/admin/index.html` (dziś `@sveltia/cms` bez numeru wersji).
3. Sprawdzić w działającym panelu: pole `relation` do listy pytań w bazie (`pytania.*.id`), `media_folder` ustawiony na poziomie pól zdjęć, format daty. Konfiguracji nie dało się uruchomić w tej sesji, bo serwer nie miał dostępu do npm ani unpkg.
4. Uruchomić `npm run build` ze szkicem `src/content.config.ts` i poprawić schemat, jeśli Astro zgłosi rozbieżności.

## Zaślepki, które blokują publikację

| Gdzie | Czego brakuje | Kto decyduje |
|---|---|---|
| Ustawienia · okienko rozmowy | potwierdzenie, komunikat błędu, zgoda i informacja RODO (po ocenie skutków, Z6) | Ty, prawnik |
| Ustawienia · dane firmy | godziny odbierania telefonu i zdanie o czasie odpowiedzi na e-mail | Ty |
| O nas · Nasza metoda | ekspertka: imię i nazwisko, specjalizacja, staż, miejsce pracy, historia, wspólne zdjęcie (Z1) | Ty |

## Decyzje otwarte

- Trzy pytania w akordeonie na każdej podstronie: wybrane wstępnie, zmienisz je w CMS (pole `pytania` w sekcji „Najczęstsze pytania”).
- Strony `/regulamin`, `/prywatnosc` i `/umow` jeszcze nie istnieją; na adresie tymczasowym `/regulamin` i `/prywatnosc` to strony „w przygotowaniu”. Link „Zobacz przykładowy raport” jest nieaktywny, dopóki nie powstanie wzór raportu.
- Sposób płatności i bramka (FIRMA), opinia prawnika o rozliczeniu „Pożegnania” (Z9), zbieranie zgody mamy (Z5), docelowy kanał rozmów po pilotażu (Z14), liczba ponownych prób, gdy mama nie odbierze (AGENT), numer, z którego Arthur dzwoni do mamy.
- Plausible czy Umami (zdanie w stopce mówi tylko o statystykach bez plików cookies).
- Pisownia nazwy firmy „arthurozmowy Piotr Jaworski” do potwierdzenia z CEIDG.
