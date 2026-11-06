#!/usr/bin/env python3
"""Generuje public/admin/config.yml dla Sveltia CMS z jednego opisu pól.

Uruchom z katalogu głównego repozytorium:  python3 narzedzia/generuj_config.py
Plik wynikowy nie używa kotwic YAML (Sveltia czyta YAML ściśle), więc pola powtarzają się jawnie.
Zmieniasz model treści tutaj, a nie w config.yml.
"""
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "public" / "admin" / "config.yml"

# ---------------------------------------------------------------- klocki pól

def s(name, label, hint=None, required=False, **kw):
    f = {"label": label, "name": name, "widget": "string", "required": required}
    if hint: f["hint"] = hint
    f.update(kw)
    return f

def t(name, label, hint=None, required=False, **kw):
    f = {"label": label, "name": name, "widget": "text", "required": required}
    if hint: f["hint"] = hint
    f.update(kw)
    return f

def md(name, label, hint=None, required=False):
    f = {"label": label, "name": name, "widget": "markdown", "required": required,
         "modes": ["rich_text", "raw"],
         "buttons": ["bold", "italic", "link", "bulleted-list", "numbered-list"],
         "editor_components": []}
    if hint: f["hint"] = hint
    return f

def b(name, label, default=False, hint=None):
    f = {"label": label, "name": name, "widget": "boolean", "default": default, "required": False}
    if hint: f["hint"] = hint
    return f

def obj(name, label, fields, collapsed=True, hint=None, summary=None, required=False):
    f = {"label": label, "name": name, "widget": "object", "collapsed": collapsed,
         "required": required, "fields": fields}
    if hint: f["hint"] = hint
    if summary: f["summary"] = summary
    return f

def lst(name, label, fields=None, field=None, summary=None, hint=None, collapsed=True, **kw):
    f = {"label": label, "name": name, "widget": "list", "required": False, "collapsed": collapsed}
    if fields is not None: f["fields"] = fields
    if field is not None: f["field"] = field
    if summary: f["summary"] = summary
    if hint: f["hint"] = hint
    f.update(kw)
    return f

def sel(name, label, options, default=None, hint=None, multiple=False, required=False):
    f = {"label": label, "name": name, "widget": "select", "options": options,
         "multiple": multiple, "required": required}
    if default is not None: f["default"] = default
    if hint: f["hint"] = hint
    return f

def img(name, label, folder, hint=None):
    f = {"label": label, "name": name, "widget": "image", "required": False,
         "media_folder": f"/public/images/{folder}", "public_folder": f"/images/{folder}"}
    if hint: f["hint"] = hint
    return f

ZAKAZANE = ("Słowa zakazane: senior, aktywny senior, podopieczny, złota jesień, srebrna gospodarka, "
            "aktywizacja, monitoring, kontrola, opiekun, nowoczesny.")

TONY = [
    {"label": "t1 · rozdział (na przemian z t2)", "value": "t1"},
    {"label": "t2 · rozdział (na przemian z t1)", "value": "t2"},
    {"label": "t3", "value": "t3"},
    {"label": "t4 · spokój, sprawy praktyczne", "value": "t4"},
    {"label": "t5 · cena i pas wezwań na końcu strony", "value": "t5"},
]

def ton():
    return sel("ton", "Ton tła sekcji", TONY, default="t1",
               hint="Matryca: przejścia gradientem między sekcjami; sąsiednie sekcje nie mają tego samego tonu.")

def kotwica():
    return s("kotwica", "Kotwica (adres sekcji po #)",
             hint="Małe litery, bez polskich znaków, słowa łączone łącznikiem. Zmiana psuje linki do sekcji.",
             pattern=["^[a-z0-9-]*$", "Tylko a–z, cyfry i łącznik"])

def etykieta():
    return s("etykieta", "Etykieta w spisie treści",
             hint="Krótko, 1–4 słowa. Puste pole = sekcja nie trafia do spisu treści.")

def h2():
    return t("h2", "Nagłówek H2",
             hint="Jedno pełne zdanie, które samo odpowiada na pytanie sekcji (cytowalne przez AI). Bez Entera. " + ZAKAZANE)

def tekst(label="Tekst", hint=None):
    return md("tekst", label, hint=hint or "Akapity oddzielaj pustą linią. Znacznik {firma} wstawia dane firmy z ustawień.")

def linki():
    return lst("linki", "Linki ze strzałką (blok 11)", summary="{{fields.tekst}} → {{fields.adres}}", fields=[
        s("tekst", "Tekst linku", required=True),
        s("adres", "Adres", hint="Ścieżka wewnętrzna, np. /jak-to-dziala albo /jak-skorzystac#rezygnacja."),
        b("aktywny", "Link aktywny", True, hint="Wyłącz, dopóki strona docelowa nie istnieje."),
    ])

def wezwania(label="Wezwania (blok 12)"):
    return obj("wezwania", label, hint="Teksty wezwań są w Ustawieniach, tu wybierasz tylko, które pokazać.", fields=[
        b("glowne", "Przycisk „Porozmawiaj z Arthurem” (otwiera okienko z formularzem)"),
        b("dopisek", "Dopisek pod przyciskiem (tylko wejście strony głównej)"),
        b("jawnosc", "Zdanie o jawności przy przycisku"),
        b("zakupowe", "Przycisk „Umów mamie pierwszą arthurozmowę”"),
        b("nad_zakupowym", "Pytanie „Mama się zgodziła?” nad przyciskiem zakupowym"),
    ])

def zdjecie(folder="strony", label="Zdjęcie (blok 13)"):
    return obj("zdjecie", label, hint=(
        "Nazwa pliku opisuje treść zdjęcia: arthurozmowy-{opis}.webp. Jeden plik na komputer i telefon. Bez retuszu skóry."), fields=[
        b("widoczne", "Pokaż zdjęcie", True),
        img("plik", "Plik", folder, hint=("Wejście podstrony: kwadrat 1:1 (1200 × 1200). Rozdział: 4:3 (1200 × 900). "
            "Wejście strony głównej: 21:9 (2880 × 1234 albo 2100 × 900). WebP.")),
        img("plik_telefon", "Plik na telefon (tylko wejście strony głównej)", folder,
            hint="Tylko strona główna: kadr 4:3 (1200 × 900) na telefon. W pozostałych miejscach zostaw puste."),
        s("alt", "Tekst alternatywny (alt)", hint=(
            "Co naprawdę widać, słowami strony (mama, córka, opowiada, rozmowa). Jedno zdanie, 50–125 znaków. "
            "Nigdy „Arthur”, „arthurozmowy” ani „AI” przy zdjęciu człowieka. Bez dopowiadania emocji i skutków.")),
        t("kadr", "Opis kadru dla redakcji (nie wyświetla się)"),
    ])

def okno_glosu():
    return obj("okno_glosu", "Okno głosu (blok 17)", hint=(
        "Najwyżej jedno w rozdziale i trzy na stronie. Przykład rozmowy zawsze z etykietą „Przykład rozmowy” "
        "i przypisem, że jest wymyślony. Nagranie tylko demonstracyjne, nigdy z prawdziwej rozmowy z mamą."), fields=[
        b("widoczne", "Pokaż okno głosu"),
        sel("wariant", "Wariant", [{"label": "ciepłe", "value": "cieple"},
                                    {"label": "głębia", "value": "glebia"},
                                    {"label": "jasne", "value": "jasne"}], default="cieple"),
        s("etykieta", "Etykieta", default="Przykład rozmowy"),
        lst("dialog", "Dialog", summary="{{fields.kto}}: {{fields.kwestia}}", fields=[
            sel("kto", "Kto mówi", ["Mama", "Arthur"], default="Mama"),
            t("kwestia", "Kwestia"),
        ]),
        t("zdanie", "Pojedyncze zdanie Arthura (zamiast dialogu)"),
        t("przypis", "Przypis pod oknem"),
        obj("nagranie", "Nagranie głosu (opcjonalnie)", fields=[
            {"label": "Plik audio", "name": "plik", "widget": "file", "required": False,
             "media_folder": "/public/audio", "public_folder": "/audio"},
            t("transkrypcja", "Transkrypcja (wymagana przy nagraniu)"),
        ]),
    ])

def cudze_zdanie():
    return obj("cudze_zdanie", "Cudze zdanie (blok 16)", hint=(
        "Tylko prawdziwe zdanie mamy i tylko za jej udokumentowaną zgodą. Do tego czasu ukryte."), fields=[
        b("widoczne", "Pokaż cytat"),
        t("cytat", "Cytat"),
        s("kto", "Podpis (np. imię i wiek, za zgodą)"),
        b("zgoda", "Mamy udokumentowaną zgodę na publikację"),
    ])

def faq_rel(min_=None, max_=None, label="Pytania z bazy"):
    f = {"label": label, "name": "pytania", "widget": "relation", "required": False,
         "collection": "pytania", "file": "baza",
         "value_field": "pytania.*.id", "search_fields": ["pytania.*.pytanie"],
         "display_fields": ["pytania.*.pytanie"], "multiple": True}
    if min_: f["min"] = min_
    if max_: f["max"] = max_
    return f

# ---------------------------------------------------------------- typy sekcji

T_ROZDZIAL = obj("rozdzial", "Rozdział (bloki 3, 4, 5, 7, 13, 16, 17)", collapsed=True,
                 summary="{{fields.etykieta}} · {{fields.ton}}", fields=[
    kotwica(), etykieta(), ton(), h2(), tekst(),
    lst("definicje", "Definicje (blok 4)", summary="{{fields.termin}}", fields=[
        s("termin", "Termin (pogrubiony)"),
        t("opis", "Dalszy ciąg zdania"),
    ]),
    obj("lista", "Lista (blok 5)", fields=[
        s("wprowadzenie", "Zdanie nad listą (pogrubione)"),
        lst("punkty", "Punkty", field=t("punkt", "Punkt")),
    ]),
    obj("cennik", "Cennik (blok 7, pakiety z Ustawień)", fields=[
        b("widoczny", "Pokaż cennik"),
        b("pokaz_nazwy", "Pokaż nazwy pakietów przy cenach"),
    ]),
    md("tekst_po", "Tekst pod listą lub cennikiem"),
    obj("akapit_ukryty", "Akapit czekający na warunek", fields=[
        b("widoczny", "Pokaż akapit"),
        t("tekst", "Tekst"),
        s("warunek", "Warunek publikacji (nie wyświetla się)"),
    ]),
    zdjecie(), okno_glosu(), cudze_zdanie(), linki(), wezwania(),
])

T_ZASADY = obj("zasady", "Lista zasad (blok 6)", summary="{{fields.etykieta}} · {{fields.ton}}", fields=[
    kotwica(), etykieta(), ton(), h2(), tekst(),
    lst("zasady", "Zasady", summary="{{fields.naglowek}}", fields=[
        s("naglowek", "Zasada (pogrubione zdanie)"),
        t("tekst", "Opis"),
        t("dlaczego", "Dlaczego", hint="Bez słowa „Dlaczego:”, szablon dopisuje je od nowej linii (R168)."),
    ]),
    linki(), wezwania(),
])

T_KROK = obj("krok", "Krok z przykładem (blok 9)", summary="{{fields.numer}}. {{fields.etykieta}}", fields=[
    {"label": "Numer kroku", "name": "numer", "widget": "number", "value_type": "int", "min": 1, "required": True},
    kotwica(), etykieta(), ton(), h2(), tekst(),
    t("przyklad", "Przykład (co może powiedzieć córka)", hint="Bez cudzysłowu, szablon go dodaje."),
    zdjecie(), linki(), wezwania(),
])

T_WATPLIWOSCI = obj("watpliwosci", "Wątpliwości (blok 10)", summary="{{fields.etykieta}}", fields=[
    kotwica(), etykieta(), ton(), h2(), tekst(),
    lst("pary", "Zdanie mamy i odpowiedź", summary="{{fields.mama}}", fields=[
        s("mama", "Co może powiedzieć mama"),
        t("odpowiedz", "Co możesz odpowiedzieć"),
    ]),
    t("zakonczenie", "Zdanie na końcu"),
    linki(), wezwania(),
])

T_PYTANIA = obj("pytania", "Rozdział pytań (blok 8)", summary="{{fields.etykieta}}", fields=[
    kotwica(), etykieta(), ton(),
    t("wstep", "Wstęp rozdziału (blok 15)"),
    zdjecie(),
    faq_rel(label="Pytania z bazy, w kolejności"),
    wezwania(),
])

T_FAQ = obj("faq", "Najczęstsze pytania, akordeon (blok 19)", summary="{{fields.h2}}", fields=[
    kotwica(), ton(),
    s("h2", "Nagłówek", default="Najczęstsze pytania"),
    faq_rel(3, 3, label="Trzy pytania z bazy"),
    linki(),
], hint="Bez etykiety, więc nie wchodzi do spisu treści. Kończy się linkiem „Wszystkie pytania” → /pytania.")

T_KONTAKT = obj("kontakt", "Kontakt i dane firmy (bloki 5, 14)", summary="{{fields.etykieta}}", fields=[
    kotwica(), etykieta(), ton(), h2(), tekst(),
    obj("pokaz", "Pokaż dane z Ustawień", fields=[
        b("email", "E-mail"), b("telefon", "Telefon"),
        b("godziny_telefonu", "Godziny, w których odbieramy telefon"),
        b("czas_odpowiedzi", "Zdanie o czasie odpowiedzi na e-mail"),
    ]),
    t("uwaga", "Uwaga pod listą"),
    zdjecie(), linki(), wezwania(),
])

T_KONIEC = obj("koniec", "Pas wezwań na koniec strony (blok 12)", summary="koniec · {{fields.ton}}", fields=[
    ton(), linki(), wezwania(),
])

TYPY = [T_ROZDZIAL, T_ZASADY, T_KROK, T_WATPLIWOSCI, T_PYTANIA, T_FAQ, T_KONTAKT, T_KONIEC]

SCHEMATY = ["Organization", "WebSite", "WebPage", "Service", "Offer", "FAQPage", "HowTo",
            "AboutPage", "ContactPage", "Person", "BreadcrumbList"]

# ---------------------------------------------------------------- pola strony

def pola_strony(szablon):
    seo = obj("seo", "Wyszukiwarki i udostępnianie (SEO)", collapsed=False, fields=[
        s("adres", "Adres strony", required=True,
          hint="Zmiana adresu wymaga przekierowania 301 w netlify.toml.",
          pattern=["^/[a-z0-9/-]*$", "Ścieżka od /, małe litery bez polskich znaków"]),
        s("tytul", "Tytuł strony (title)", required=True,
          hint="Najlepiej do 60 znaków, z nazwą arthurozmowy; Google pokazuje ok. 580 px.",
          pattern=["^.{10,70}$", "10–70 znaków"]),
        t("opis", "Opis w wynikach (meta description)",
          hint="120–155 znaków. Pierwsze zdanie samo odpowiada, o czym jest strona (Google i AI).",
          pattern=["^[^\\n]{0,160}$", "Do 160 znaków, bez Entera"]),
        obj("obraz_og", "Obraz do udostępniania (1200 × 630)", fields=[
            img("plik", "Plik JPG", "og"),
            s("alt", "Tekst alternatywny"),
        ]),
        sel("schemat", "Dane strukturalne (JSON-LD)", SCHEMATY, multiple=True,
            hint="FAQPage tylko na stronie Pytania. Szablon buduje JSON-LD z treści i Ustawień."),
        b("indeksuj", "Pokazuj w wyszukiwarkach", True),
        s("autor", "Autor strony", default="Piotr Jaworski"),
        {"label": "Data aktualizacji", "name": "zaktualizowano", "widget": "datetime", "required": True,
         "format": "YYYY-MM-DD", "date_format": "YYYY-MM-DD", "time_format": False,
         "hint": "Zmieniaj przy każdej zmianie treści (Księga, rozdz. 21.6)."},
    ])
    geo = obj("geo", "Streszczenie dla AI (GEO)", fields=[
        t("streszczenie", "Streszczenie strony",
          hint="2–3 zdania faktów z tej strony, w trzeciej osobie. Trafia do llms.txt i opisu w JSON-LD."),
    ])
    wejscie_pola = [
        kotwica(), etykieta(),
        t("h1", "Nagłówek H1", required=True,
          hint="Jeden na stronę. Korzyść mamy w nagłówku (dominanta). Bez Entera. " + ZAKAZANE),
        s("h1_wyroznienie", "Słowo wyróżnione w H1 (tylko strona główna)"),
        md("lid", "Wstęp (lid)", hint="1–3 akapity. Pierwsze zdanie streszcza stronę."),
        zdjecie(label="Zdjęcie wejścia (blok 1 lub 2, 13)"),
    ]
    if szablon == "blad":
        wejscie_pola += [
            obj("przycisk_powrotu", "Przycisk powrotu", fields=[s("tekst", "Tekst"), s("adres", "Adres")]),
            linki(),
        ]
    wejscie_pola += [wezwania(), b("pokaz_autora_i_date", "Pokaż autora i datę aktualizacji (blok 18)", True)]
    pola = [
        obj("strona", "Strona", fields=[
            s("nazwa", "Nazwa w CMS", required=True),
            {"label": "Szablon", "name": "szablon", "widget": "hidden", "default": szablon},
        ]),
        seo, geo,
        obj("wejscie", "Wejście strony (H1, wstęp, zdjęcie)", collapsed=False, fields=wejscie_pola),
    ]
    if szablon != "blad":
        pola.append({"label": "Sekcje strony", "name": "sekcje", "widget": "list", "required": False,
                     "collapsed": True, "typeKey": "typ", "types": TYPY,
                     "hint": "Kolejność sekcji = kolejność na stronie. Przeciągnij, aby zmienić."})
    else:
        pola.append({"label": "Sekcje", "name": "sekcje", "widget": "hidden", "default": []})
    return pola

STRONY = [
    ("strona-glowna", "Strona główna", "glowna"),
    ("jak-to-dziala", "Jak to działa", "podstrona"),
    ("czego-nie-obiecujemy", "Czego nie obiecujemy", "podstrona"),
    ("pytania", "Pytania", "podstrona"),
    ("jak-skorzystac", "Jak skorzystać", "podstrona"),
    ("jak-rozmawiac-z-mama", "Jak rozmawiać z mamą", "podstrona"),
    ("o-nas", "O nas", "podstrona"),
    ("kontakt", "Kontakt", "podstrona"),
    ("404", "Strona błędu (404)", "blad"),
]

# ---------------------------------------------------------------- baza pytań i ustawienia

POLA_BAZY = [lst("pytania", "Pytania i odpowiedzi", summary="{{fields.pytanie}}", collapsed=True, fields=[
    s("id", "Identyfikator", required=True,
      hint="Stały, małe litery i łącznik. Strony odwołują się do pytania po identyfikatorze.",
      pattern=["^[a-z0-9-]+$", "Tylko a–z, cyfry i łącznik"]),
    s("pytanie", "Pytanie", required=True, hint="Tak, jak zadałaby je córka. Na stronie Pytania to nagłówek H2."),
    md("odpowiedz", "Odpowiedź", required=True,
       hint="Pierwsze zdanie zawiera całą odpowiedź (GEO). " + ZAKAZANE),
    obj("link", "Link pod odpowiedzią", fields=[s("tekst", "Tekst linku"), s("adres", "Adres")]),
])]

POLA_USTAWIEN = [
    obj("marka", "Marka", fields=[
        s("nazwa", "Nazwa usługi", hint="Zawsze jednym słowem, małą literą w tekście ciągłym."),
        s("domena", "Domena"), s("jezyk", "Język"),
        t("definicja", "Definicja arthurozmów",
          hint="Słowo w słowo to samo w Pytaniach, w JSON-LD i w llms.txt (R167)."),
        obj("logo", "Logo", fields=[img("plik", "Plik SVG", "marka"), s("alt", "Alt")]),
    ]),
    obj("naglowek", "Nagłówek strony i menu", hint=(
        "Przycisk „Menu” otwiera panel z grupami: rozdziały oglądanej strony i lista stron, "
        "a pod nimi zakup i Panel klienta. Tak samo na telefonie i na komputerze."), fields=[
        s("menu", "Napis na przycisku menu"),
        s("grupa_rozdzialy", "Nazwa grupy rozdziałów (spis treści)"),
        s("grupa_strony", "Nazwa grupy stron"),
        s("panel_klienta", "Link do panelu klienta w nagłówku"),
        b("przycisk_staly", "Przycisk wezwania przyklejony do dołu ekranu na telefonie", True),
    ]),
    obj("nawigacja", "Lista stron (menu i stopka)", hint=(
        "Jeden temat, jedna nazwa: nazwa strony taka sama w menu, stopce, linkach i spisie treści strony głównej."), fields=[
        lst("strony", "Strony", summary="{{fields.tekst}} → {{fields.adres}}",
            fields=[s("tekst", "Nazwa strony"), s("adres", "Adres")]),
    ]),
    obj("wezwania", "Teksty wezwań", fields=[
        obj("glowne", "Wezwanie główne (otwiera okienko rozmowy)", fields=[
            s("przycisk", "Przycisk"), t("dopisek", "Dopisek pod przyciskiem")]),
        s("jawnosc", "Zdanie o jawności przy wezwaniu"),
        obj("zakupowe", "Wezwanie zakupowe", fields=[
            s("przycisk", "Przycisk"), s("adres", "Adres"), s("nad_przyciskiem", "Pytanie nad przyciskiem")]),
    ]),
    obj("okno_rozmowy", "Okienko „Porozmawiaj z Arthurem”", hint=(
        "Włączamy po ocenie skutków dla ochrony danych (Z6) i z polityką prywatności."), fields=[
        s("tytul", "Tytuł"), t("wstep", "Wstęp"), s("pole_numer", "Pole: numer"),
        s("pytanie_kiedy", "Pytanie o porę"), s("opcja_teraz", "Opcja: teraz"), s("opcja_termin", "Opcja: termin"),
        s("pole_data", "Pole: data"), s("pole_godzina", "Pole: godzina"), s("przycisk", "Przycisk"),
        t("potwierdzenie", "Potwierdzenie"), t("blad", "Komunikat błędu"), t("zgoda", "Zgoda i informacja RODO"),
    ]),
    obj("pakiety", "Pakiety i ceny", fields=[
        s("waluta", "Waluta"), s("okres", "Dopisek przy cenie"),
        lst("lista", "Pakiety", summary="{{fields.cena}} zł · {{fields.opis}}", fields=[
            {"label": "Cena (zł brutto)", "name": "cena", "widget": "number", "value_type": "int", "required": True},
            {"label": "Rozmowy pełne", "name": "rozmowy_pelne", "widget": "number", "value_type": "int"},
            {"label": "Rozmowy podtrzymujące", "name": "rozmowy_podtrzymujace", "widget": "number", "value_type": "int"},
            s("opis", "Opis pozycji cennika", hint="Z odmianą, np. „6 rozmów pełnych i 8 rozmów podtrzymujących”."),
            s("nazwa", "Nazwa pakietu", hint="Małą literą, np. „pakiet optymalny”."),
            b("polecany", "Pakiet proponowany na początek"),
        ]),
    ]),
    obj("firma", "Dane firmy", hint="Linia {firma} w tekstach: nazwa, ulica, kod i miejscowość, NIP.", fields=[
        s("nazwa", "Nazwa"), s("ulica", "Ulica i numer"), s("kod_pocztowy", "Kod pocztowy"),
        s("miejscowosc", "Miejscowość"), s("kraj", "Kraj (kod)"), s("nip", "NIP"),
        s("email", "E-mail"), s("telefon", "Telefon"),
        s("telefon_godziny", "Godziny odbierania telefonu"), t("czas_odpowiedzi", "Czas odpowiedzi na e-mail"),
        s("panel_klienta", "Adres panelu klienta"),
    ]),
    obj("autor", "Autor", fields=[s("imie_nazwisko", "Imię i nazwisko"), s("adres_strony", "Strona autora")]),
    obj("stopka", "Stopka", fields=[
        b("wezwanie_glowne", "Wezwanie główne w stopce", True),
        lst("linki_prawne", "Linki prawne (pod listą stron, zakupem i Panelem klienta)", summary="{{fields.tekst}}",
            fields=[s("tekst", "Tekst"), s("adres", "Adres")]),
        s("kontakt_etykieta", "Etykieta przy e-mailu"), s("jawnosc", "Zdanie o jawności"),
        s("prywatnosc", "Zdanie o statystykach"), s("prawa", "Linia praw autorskich i danych firmy"),
    ]),
]

# ---------------------------------------------------------------- config

config = {
    "backend": {
        "name": "github",
        "repo": "Potr-Arthur/arthurozmowy-pl",
        "branch": "main",
        # Logowanie: osobisty token GitHub (fine-grained, tylko to repozytorium, Contents: read and write).
        # Worker sveltia-cms-auth (base_url) dodamy, gdy do redakcji dojdzie druga osoba.
        "commit_messages": {
            "create": "Treść: dodano {{collection}} „{{slug}}”",
            "update": "Treść: zmieniono {{collection}} „{{slug}}”",
            "delete": "Treść: usunięto {{collection}} „{{slug}}”",
            "uploadMedia": "Media: dodano „{{path}}”",
            "deleteMedia": "Media: usunięto „{{path}}”",
        },
    },
    "site_url": "https://arthurozmowy.pl",
    "display_url": "https://arthurozmowy.pl",
    "media_folder": "public/images",
    "public_folder": "/images",
    "collections": [
        {"name": "strony", "label": "Strony", "label_singular": "Strona",
         "description": "Teksty stron arthurozmowy.pl, ułożone według bloków Matrycy.",
         "files": [{"name": n, "label": l, "file": f"src/content/strony/{n}.yml",
                    "format": "yml", "fields": pola_strony(sz)} for n, l, sz in STRONY]},
        {"name": "pytania", "label": "Pytania i odpowiedzi",
         "description": "Jedno źródło odpowiedzi dla strony Pytania i akordeonów na podstronach.",
         "files": [{"name": "baza", "label": "Baza pytań", "file": "src/content/pytania/baza.yml",
                    "format": "yml", "fields": POLA_BAZY}]},
        {"name": "ustawienia", "label": "Ustawienia",
         "description": "Wezwania, pakiety, dane firmy i stopka: raz, dla wszystkich stron.",
         "files": [{"name": "witryna", "label": "Ustawienia witryny", "file": "src/content/ustawienia/witryna.yml",
                    "format": "yml", "fields": POLA_USTAWIEN}]},
    ],
}

class NoAlias(yaml.SafeDumper):
    def ignore_aliases(self, data):
        return True

HEADER = """# Sveltia CMS · arthurozmowy.pl · konfiguracja redakcji
# PLIK GENEROWANY: zmiany wprowadzaj w narzedzia/generuj_config.py i uruchom go ponownie.
# Bez kotwic YAML, bo Sveltia czyta YAML ściśle. Pola i bloki odpowiadają Matrycy (claude/Matryca_WITRYNA_v1.md).
# Logowanie do /admin osobistym tokenem GitHub; worker logowania (base_url) dodamy dla kolejnych redaktorów.
"""

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(HEADER + yaml.dump(config, Dumper=NoAlias, sort_keys=False, allow_unicode=True, width=110),
               encoding="utf-8")
print(f"Zapisano {OUT.relative_to(ROOT)}")
