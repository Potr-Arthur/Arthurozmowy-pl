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
    {"label": "t5 · cena", "value": "t5"},
]

def ton():
    return sel("ton", "Ton tła rozdziału", TONY, default="t1",
               hint="Sąsiednie rozdziały nie mają tego samego tonu.")

def kotwica():
    return s("kotwica", "Kotwica (adres rozdziału po #)",
             hint="Małe litery, bez polskich znaków, słowa łączone łącznikiem. Zmiana psuje linki do rozdziału.",
             pattern=["^[a-z0-9-]*$", "Tylko a–z, cyfry i łącznik"])

def etykieta():
    return s("etykieta", "Nazwa w spisie treści („Na tej stronie”)",
             hint="Krótko, 1–4 słowa. Puste pole = rozdział nie trafia do spisu treści.")

def zdjecie(label, hint):
    return obj("zdjecie", label, hint=hint + " Nazwa pliku: arthurozmowy-{strona}-{treść}-{format}.webp. Bez retuszu skóry.", fields=[
        b("widoczne", "Pokaż zdjęcie", True),
        img("plik", "Plik zdjęcia", "strony"),
        img("plik_telefon", "Kadr 4:3 na telefon (tylko wejście strony głównej)", "strony"),
        s("alt", "Tekst alternatywny (alt)", hint=(
            "Co naprawdę widać, słowami strony (mama, córka, opowiada, rozmowa). Jedno zdanie, 50–125 znaków. "
            "Nigdy „Arthur”, „arthurozmowy” ani „AI” przy zdjęciu człowieka. Bez dopowiadania emocji i skutków.")),
    ])

def lid(label="Lid (kursywa pod nagłówkiem)"):
    return md("lid", label, hint="Jeden akapit, który streszcza rozdział. " + ZAKAZANE)

def faq_rel(min_=None, max_=None, label="Pytania z bazy"):
    f = {"label": label, "name": "pytania", "widget": "relation", "required": False,
         "collection": "pytania", "file": "baza",
         "value_field": "pytania.*.id", "search_fields": ["pytania.*.pytanie"],
         "display_fields": ["pytania.*.pytanie"], "multiple": True}
    if min_: f["min"] = min_
    if max_: f["max"] = max_
    return f

# ---------------------------------------------------------------- bloki (jeden typ = jeden moduł makiety)

B_TEKST = obj("tekst", "Tekst akapitu", summary="Tekst: {{fields.tekst}}", fields=[
    md("tekst", "Tekst", hint=("Akapity oddzielaj pustą linią. Znaczniki: {firma} (dane firmy), {email}, {telefon}, {godziny}. "
                               + ZAKAZANE)),
])
B_GLOS = obj("glos", "Voice aside (karta w kolorze piasku, kursywa)", summary="Voice aside: {{fields.tekst}}", fields=[
    md("tekst", "Tekst", hint="Jedna myśl, 1–3 zdania. Znaczniki jak w tekście akapitu."),
])
B_LISTA = obj("lista", "Lista punktów", summary="Lista: {{fields.naglowek}}", fields=[
    s("naglowek", "Zdanie nad listą"),
    b("numerowana", "Lista numerowana", False),
    lst("punkty", "Punkty", field=t("punkt", "Punkt")),
])
B_ZASADY = obj("zasady", "Zasady (nagłówek H3, lid H3, tekst)", summary="Zasady", fields=[
    lst("zasady", "Zasady", summary="{{fields.naglowek}}", fields=[
        s("naglowek", "Zasada (nagłówek H3)", hint="Bez numeru, szablon go dopisuje."),
        t("lid", "Lid H3"),
        t("tekst", "Tekst akapitu"),
    ]),
])
B_CYTAT = obj("cytat", "Karta cytatu (żółta karta)", summary="Karta cytatu: {{fields.etykieta}}", hint=(
    "Przykładowy dialog mamy z Arthurem zawsze ma etykietę „Przykład rozmowy”, bo jest wymyślony. "
    "Nigdy fragment prawdziwej rozmowy z mamą."), fields=[
    b("widoczny", "Pokaż kartę", True),
    s("etykieta", "Etykieta nad kartą", hint="Np. „Przykład rozmowy”, „Przykład”. Może zostać pusta."),
    t("wstep", "Zdanie wstępu w karcie"),
    lst("repliki", "Kwestie", summary="{{fields.kto}}: {{fields.kwestia}}", fields=[
        s("kto", "Kto mówi", hint="Mama, Arthur albo Ty. Puste pole = sam cytat."),
        t("kwestia", "Kwestia", hint="Bez cudzysłowu, szablon go dodaje."),
    ]),
])
B_CENNIK = obj("cennik", "Karty ceny (pakiety z Ustawień)", summary="Karty ceny", fields=[
    {"label": "Pakiety", "name": "info", "widget": "hidden", "required": False},
])
B_LINK = obj("link", "Link wewnętrzny (przycisk w kolorze rdzy)", summary="Link: {{fields.tekst}} → {{fields.adres}}", fields=[
    s("tekst", "Tekst przycisku", required=True,
      hint="Nazwa strony albo rozdziału, do którego prowadzi (jeden temat, jedna nazwa)."),
    s("adres", "Adres", hint="Ścieżka wewnętrzna, np. /jak-dziala-arthur albo /jak-korzystac#rezygnacja."),
    b("aktywny", "Link aktywny", True, hint="Wyłącz, dopóki strona docelowa nie istnieje."),
])
B_WEZWANIE = obj("wezwanie", "Przycisk CTA (błękitny)", summary="Przycisk CTA: {{fields.rodzaj}}", fields=[
    sel("rodzaj", "Który przycisk", [
        {"label": "Porozmawiaj z Arthurem (okienko z formularzem rozmowy)", "value": "glowne"},
        {"label": "Umów mamie próbne arthurozmowy (zamówienie)", "value": "zakupowe"},
        {"label": "Napisz do nas (okienko z formularzem kontaktu)", "value": "napisz"},
    ], default="glowne", required=True, hint="Teksty przycisków zmieniasz w Ustawieniach."),
    b("objasnienie", "Pokaż objaśnienie pod przyciskiem (tylko „Porozmawiaj z Arthurem”)", False),
])
B_PYTANIA = obj("pytania", "Karty pytań (strona Pytania)", summary="Pytania z bazy", fields=[
    faq_rel(label="Pytania z bazy, w kolejności"),
])
B_FAQ = obj("faq", "Najczęstsze pytania (akordeon z 3 pytaniami)", summary="Najczęstsze pytania", hint=(
    "Pod akordeonem szablon dodaje przycisk „Wszystkie pytania” → /pytania."), fields=[
    faq_rel(3, 3, label="Trzy pytania z bazy"),
])

BLOKI = [B_TEKST, B_GLOS, B_LISTA, B_ZASADY, B_CYTAT, B_CENNIK, B_LINK, B_WEZWANIE, B_PYTANIA, B_FAQ]

def bloki():
    return {"label": "Bloki, w kolejności wyświetlania", "name": "bloki", "widget": "list", "required": False,
            "collapsed": True, "typeKey": "typ", "types": BLOKI,
            "hint": "Jeden blok = jeden moduł makiety. Przeciągnij, aby zmienić kolejność."}

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
         "hint": "Zmieniaj przy każdej zmianie treści. Autor i data trafiają do danych strukturalnych."},
    ])
    geo = obj("geo", "Streszczenie dla AI (GEO)", fields=[
        t("streszczenie", "Streszczenie strony",
          hint="2–5 zdań faktów z tej strony, w trzeciej osobie. Trafia do llms.txt."),
    ])
    hero = ("Wejście strony głównej: plik 21:9 i osobny kadr 4:3 na telefon." if szablon == "glowna"
            else "Wejście podstrony: kwadrat 1:1 (1200 × 1200).")
    wejscie_pola = [
        kotwica(), etykieta(),
        t("h1", "Nagłówek H1", required=True,
          hint="Jeden na stronę. Korzyść mamy w nagłówku (dominanta). Bez Entera. " + ZAKAZANE),
        zdjecie("Zdjęcie wejścia", hero),
        lid("Lid H1 (kursywa pod nagłówkiem)"),
    ]
    if szablon == "blad":
        wejscie_pola.append(obj("przycisk_powrotu", "Przycisk powrotu", fields=[s("tekst", "Tekst"), s("adres", "Adres")]))
    wejscie_pola.append(bloki())
    pola = [
        obj("strona", "Strona", fields=[
            s("nazwa", "Nazwa strony", required=True,
              hint="Ta sama nazwa stoi nad H1 (wielkimi literami), w menu, w stopce i w przyciskach „Link wewnętrzny”."),
            {"label": "Szablon", "name": "szablon", "widget": "hidden", "default": szablon},
        ]),
        seo, geo,
        obj("wejscie", "Wejście strony (H1, zdjęcie, lid, bloki)", collapsed=False, fields=wejscie_pola),
    ]
    if szablon != "blad":
        pola.append(lst("sekcje", "Rozdziały strony", summary="{{fields.etykieta}} · {{fields.h2}}",
                        hint="Kolejność rozdziałów = kolejność na stronie. Przeciągnij, aby zmienić.", fields=[
            kotwica(), etykieta(), ton(),
            t("h2", "Nagłówek H2",
              hint="Jedno pełne zdanie, które samo odpowiada na pytanie rozdziału (cytowalne przez AI). Bez Entera. " + ZAKAZANE),
            zdjecie("Zdjęcie rozdziału", "Zdjęcie w rozdziale: poziome 4:3 (1200 × 900)."),
            lid("Lid H2 (kursywa pod nagłówkiem)"),
            bloki(),
        ]))
    else:
        pola.append({"label": "Rozdziały", "name": "sekcje", "widget": "hidden", "default": []})
    return pola

STRONY = [
    ("strona-glowna", "Jej sprawy (strona główna)", "glowna"),
    ("o-nas", "O nas", "podstrona"),
    ("jak-dziala-arthur", "Jak działa Arthur", "podstrona"),
    ("jak-korzystac", "Jak korzystać", "podstrona"),
    ("jak-rozmawiac-z-mama", "Jak rozmawiać z mamą", "podstrona"),
    ("czego-nie-obiecujemy", "Czego nie obiecujemy", "podstrona"),
    ("bezpieczenstwo", "Bezpieczeństwo", "podstrona"),
    ("pytania", "Pytania", "podstrona"),
    ("kontakt", "Kontakt", "podstrona"),
    ("404", "Strona błędu (404)", "blad"),
]

# ---------------------------------------------------------------- baza pytań i ustawienia

POLA_BAZY = [lst("pytania", "Pytania i odpowiedzi", summary="{{fields.pytanie}}", collapsed=True, fields=[
    s("id", "Identyfikator", required=True,
      hint="Stały, małe litery i łącznik. Strony odwołują się do pytania po identyfikatorze.",
      pattern=["^[a-z0-9-]+$", "Tylko a–z, cyfry i łącznik"]),
    s("pytanie", "Pytanie", required=True, hint="Tak, jak zadałaby je córka."),
    md("odpowiedz", "Odpowiedź", required=True,
       hint="Pierwsze zdanie zawiera całą odpowiedź (GEO). " + ZAKAZANE),
    obj("link", "Link wewnętrzny pod odpowiedzią", fields=[s("tekst", "Tekst linku"), s("adres", "Adres")]),
])]

def okno_pola(kontakt=False):
    if kontakt:
        pola = [s("tytul", "Tytuł"), t("wstep", "Wstęp"), s("pole_imie", "Pole: imię"), s("pole_email", "Pole: e-mail"),
                s("pole_telefon", "Pole: telefon"), s("pole_wiadomosc", "Pole: wiadomość"), s("przycisk", "Przycisk")]
    else:
        pola = [s("tytul", "Tytuł"), t("wstep", "Wstęp"), s("pole_numer", "Pole: numer"),
                s("pytanie_kiedy", "Pytanie o porę"), s("opcja_teraz", "Opcja: teraz"), s("opcja_termin", "Opcja: termin"),
                s("pole_data", "Pole: data"), s("pole_godzina", "Pole: godzina"), s("przycisk", "Przycisk")]
    return pola + [t("potwierdzenie", "Potwierdzenie"), t("blad", "Komunikat błędu"), t("zgoda", "Zgoda i informacja RODO")]

def lista_linkow(name, label, summary="{{fields.tekst}} → {{fields.adres}}", hint=None):
    return lst(name, label, summary=summary, hint=hint, fields=[s("tekst", "Tekst"), s("adres", "Adres")])

WEZWANIA = [{"label": "Porozmawiaj z Arthurem", "value": "glowne"},
            {"label": "Umów mamie próbne arthurozmowy", "value": "zakupowe"},
            {"label": "Napisz do nas", "value": "napisz"}]

POLA_USTAWIEN = [
    obj("marka", "Marka", fields=[
        s("nazwa", "Nazwa usługi", hint="Zawsze jednym słowem, małą literą w tekście ciągłym."),
        s("domena", "Domena"), s("jezyk", "Język"),
        t("definicja", "Definicja arthurozmów",
          hint="Słowo w słowo to samo w odpowiedzi „Czym są arthurozmowy?”, w JSON-LD i w llms.txt."),
        obj("logo", "Logo", fields=[img("plik", "Plik SVG", "marka"), s("alt", "Alt")]),
    ]),
    obj("naglowek", "Belka górna i menu", hint=(
        "Od lewej: logo, przycisk Menu, linki, przycisk zamówienia i Panel klienta. Menu to jedna lista stron; "
        "rozdziały stoją pod stroną oglądaną albo wskazaną."), fields=[
        s("menu", "Napis na przycisku menu"),
        s("grupa_rozdzialy", "Napis nad rozdziałami strony", hint="Szablon dopisuje nazwę strony, np. „Na stronie Jak działa Arthur”."),
        s("grupa_strony", "Nazwa grupy stron"),
        lista_linkow("linki", "Linki w belce (np. Cena, Kontakt)"),
        s("zakup", "Napis na przycisku zamówienia w belce"),
        s("panel_klienta", "Napis linku do panelu klienta"),
        b("przycisk_staly", "Przycisk „Porozmawiaj z Arthurem” przyklejony do dołu ekranu na telefonie", True),
    ]),
    obj("nawigacja", "Lista stron (menu i stopka)", hint=(
        "Jeden temat, jedna nazwa: nazwa strony taka sama w menu, stopce, linkach wewnętrznych "
        "i spisie treści strony głównej."), fields=[
        lista_linkow("strony", "Strony"),
        s("wszystkie_pytania", "Napis przycisku pod akordeonem pytań"),
        s("wiecej", "Słowo przed linkiem wewnętrznym", hint="Np. „Więcej:”. Po nim stoi nazwa strony albo rozdziału."),
    ]),
    obj("wezwania", "Przyciski CTA", fields=[
        obj("glowne", "Porozmawiaj z Arthurem (otwiera okienko rozmowy)", fields=[
            s("przycisk", "Przycisk"), t("dopisek", "Objaśnienie pod przyciskiem")]),
        obj("zakupowe", "Zamówienie", fields=[s("przycisk", "Przycisk"), s("adres", "Adres")]),
        obj("napisz", "Napisz do nas (otwiera okienko kontaktu)", fields=[s("przycisk", "Przycisk")]),
    ]),
    obj("okno_rozmowy", "Okienko „Porozmawiaj z Arthurem”", hint=(
        "Włączamy po ocenie skutków dla ochrony danych (Z6) i z polityką prywatności."), fields=okno_pola()),
    obj("okno_kontaktu", "Okienko „Napisz do nas”", hint=(
        "Włączamy po ocenie skutków dla ochrony danych (Z6) i z polityką prywatności."), fields=okno_pola(True)),
    obj("pakiety", "Pakiety i ceny", fields=[
        s("waluta", "Waluta"), s("okres", "Dopisek przy cenie"),
        s("dlugosc", "Długość rozmów (zdanie na każdej karcie ceny)", hint="Długość jednej rozmowy, nigdy suma minut w miesiącu."),
        lst("lista", "Pakiety", summary="{{fields.cena}} zł · {{fields.opis}}", fields=[
            {"label": "Cena (zł brutto)", "name": "cena", "widget": "number", "value_type": "int", "required": True},
            {"label": "Rozmowy pełne", "name": "rozmowy_pelne", "widget": "number", "value_type": "int"},
            {"label": "Rozmowy podtrzymujące", "name": "rozmowy_podtrzymujace", "widget": "number", "value_type": "int"},
            s("opis", "Opis na karcie ceny", hint="Z odmianą, np. „6 rozmów pełnych i 8 rozmów podtrzymujących”."),
            s("rytm", "Rytm tygodnia na karcie ceny", hint="Np. „co tydzień 1–2 rozmowy pełne i 2 podtrzymujące”."),
            s("nazwa", "Nazwa pakietu", hint="Małą literą, np. „pakiet optymalny”."),
            b("polecany", "Pakiet proponowany na początek"),
        ]),
    ]),
    obj("firma", "Dane firmy", hint="Znaczniki w tekstach: {firma}, {email}, {telefon}, {godziny}.", fields=[
        s("nazwa", "Nazwa"), s("ulica", "Ulica i numer"), s("kod_pocztowy", "Kod pocztowy"),
        s("miejscowosc", "Miejscowość"), s("kraj", "Kraj (kod)"), s("nip", "NIP"),
        s("email", "E-mail"), s("telefon", "Telefon"),
        s("telefon_godziny", "Godziny odbierania telefonu"),
        s("panel_klienta", "Adres panelu klienta"),
    ]),
    obj("autor", "Autor", fields=[s("imie_nazwisko", "Imię i nazwisko"), s("adres_strony", "Strona autora")]),
    obj("stopka", "Stopka", fields=[
        sel("wezwania", "Przyciski CTA na górze stopki", WEZWANIA, multiple=True),
        s("prywatnosc", "Zdanie o statystykach"), s("prawa", "Linia praw autorskich i danych firmy"),
        lista_linkow("linki_prawne", "Linki prawne", summary="{{fields.tekst}}"),
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
         "description": "Teksty stron arthurozmowy.pl: wejście i rozdziały, w rozdziale bloki (moduły makiety).",
         "files": [{"name": n, "label": l, "file": f"src/content/strony/{n}.yml",
                    "format": "yml", "fields": pola_strony(sz)} for n, l, sz in STRONY]},
        {"name": "pytania", "label": "Pytania i odpowiedzi",
         "description": "Jedno źródło odpowiedzi dla strony Pytania i akordeonów na podstronach.",
         "files": [{"name": "baza", "label": "Baza pytań", "file": "src/content/pytania/baza.yml",
                    "format": "yml", "fields": POLA_BAZY}]},
        {"name": "ustawienia", "label": "Ustawienia",
         "description": "Belka, lista stron, przyciski CTA, okienka, pakiety, dane firmy i stopka: raz, dla wszystkich stron.",
         "files": [{"name": "witryna", "label": "Ustawienia witryny", "file": "src/content/ustawienia/witryna.yml",
                    "format": "yml", "fields": POLA_USTAWIEN}]},
    ],
}

class NoAlias(yaml.SafeDumper):
    def ignore_aliases(self, data):
        return True

HEADER = """# Sveltia CMS · arthurozmowy.pl · konfiguracja redakcji
# PLIK GENEROWANY: zmiany wprowadzaj w narzedzia/generuj_config.py i uruchom go ponownie.
# Bez kotwic YAML, bo Sveltia czyta YAML ściśle. Bloki odpowiadają modułom makiety V2 (README, „Model treści”).
# Logowanie do /admin osobistym tokenem GitHub; worker logowania (base_url) dodamy dla kolejnych redaktorów.
"""

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(HEADER + yaml.dump(config, Dumper=NoAlias, sort_keys=False, allow_unicode=True, width=110),
               encoding="utf-8")
print(f"Zapisano {OUT.relative_to(ROOT)}")
