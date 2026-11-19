#!/usr/bin/env python3
"""Generuje public/admin/config.yml dla Sveltia CMS z jednego opisu pól.

Uruchom z katalogu głównego repozytorium:  python3 narzedzia/generuj_config.py
Plik wynikowy nie używa kotwic YAML (Sveltia czyta YAML ściśle), więc pola powtarzają się jawnie.
Zmieniasz model treści tutaj, a nie w config.yml.

Układ panelu (claude/CMS_panele_redakcji_v1.md, decyzje z 19.11.2026):
  lewa kolumna: Strony (kolejność menu) · Strony kampanii · Pytania i odpowiedzi · Elementy wspólne
  na stronie: Nazwa strony · Wejście · Rozdziały · Wyszukiwarki (SEO) · Streszczenie dla AI (GEO)
  układ rozdziałów i bloków zablokowany na stronach z menu (D2), wolny na stronach kampanii
  zapis = wersja robocza z podglądem na Netlify, „Opublikuj” wysyła na witrynę (D1, publish_mode: preview)
Listy adresów (Link wewnętrzny, link pod odpowiedzią) skrypt buduje z plików treści, więc po dodaniu
rozdziału albo zmianie jego nazwy trzeba go uruchomić ponownie.
"""
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "public" / "admin" / "config.yml"
C = ROOT / "src" / "content"

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

def b(name, label, default=False, hint=None, **kw):
    f = {"label": label, "name": name, "widget": "boolean", "default": default, "required": False}
    if hint: f["hint"] = hint
    f.update(kw)
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

def sel(name, label, options, default=None, hint=None, multiple=False, required=False, **kw):
    f = {"label": label, "name": name, "widget": "select", "options": options,
         "multiple": multiple, "required": required}
    if default is not None: f["default"] = default
    if hint: f["hint"] = hint
    f.update(kw)
    return f

def img(name, label, folder, hint=None):
    f = {"label": label, "name": name, "widget": "image", "required": False,
         "media_folder": f"/public/images/{folder}", "public_folder": f"/images/{folder}"}
    if hint: f["hint"] = hint
    return f

# Układ zablokowany (D2): rozdziałów i bloków nie da się dodać, usunąć ani przestawić.
ZABLOKOWANY = {"allow_add": False, "allow_remove": False, "allow_reorder": False}

ZAKAZANE = ("Słowa zakazane: senior, aktywny senior, podopieczny, osoba w wieku senioralnym, złota jesień, "
            "jesień życia, srebrna gospodarka, aktywizacja, monitoring, kontrola, nadzór, opiekun, kompleksowy, "
            "dedykowany, innowacyjny, nowoczesny, rewolucyjny.")

TONY = [
    {"label": "t1 · rozdział (na przemian z t2)", "value": "t1"},
    {"label": "t2 · rozdział (na przemian z t1)", "value": "t2"},
    {"label": "t3", "value": "t3"},
    {"label": "t4 · spokój, sprawy praktyczne", "value": "t4"},
    {"label": "t5 · cena", "value": "t5"},
]

# ---------------------------------------------------------------- listy wyboru z plików treści

def wczytaj(p):
    return yaml.safe_load(p.read_text(encoding="utf-8"))

UST = wczytaj(C / "ustawienia" / "witryna.yml")
STRONY_TRESC = {p.stem: wczytaj(p) for p in sorted((C / "strony").glob("*.yml"))}
PO_ADRESIE = {d["seo"]["adres"]: d for d in STRONY_TRESC.values()}

def skrot(tx, n=48):
    tx = " ".join((tx or "").split())
    return tx if len(tx) <= n else tx[:n - 1].rstrip() + "…"

def adresy_do_wyboru():
    """Strony w kolejności menu, a pod każdą jej rozdziały z kotwicą; na końcu strony prawne."""
    opcje = []
    for l in UST["nawigacja"]["strony"]:
        d = PO_ADRESIE.get(l["adres"])
        opcje.append({"label": l["tekst"], "value": l["adres"]})
        if not d:
            continue
        baza_adresu = "/" if l["adres"] == "/" else l["adres"]
        czesci = ([d["wejscie"]] if d["wejscie"].get("kotwica") else []) + list(d.get("sekcje") or [])
        for r in czesci:
            if not r.get("kotwica"):
                continue
            nazwa = r.get("etykieta") or skrot(r.get("h2") or r.get("h1"))
            opcje.append({"label": f"{l['tekst']} › {nazwa}", "value": f"{baza_adresu}#{r['kotwica']}"})
    for l in UST["stopka"]["linki_prawne"]:
        opcje.append({"label": l["tekst"], "value": l["adres"]})
    return opcje

ADRESY = adresy_do_wyboru()

def adres_z_listy(name="adres", label="Dokąd prowadzi", hint=None):
    return sel(name, label, ADRESY, hint=hint or "Strona albo rozdział. Nowy rozdział pojawi się na liście po przebudowie konfiguracji panelu.")

# ---------------------------------------------------------------- wspólne pola stron

def kotwica(readonly=True):
    f = s("kotwica", "Kotwica (adres rozdziału po #)",
          hint="Małe litery, bez polskich znaków, słowa łączone łącznikiem.",
          pattern=["^[a-z0-9-]*$", "Tylko a–z, cyfry i łącznik"])
    if readonly:
        f["readonly"] = True
    return f

def etykieta():
    return s("etykieta", "Nazwa rozdziału w menu („Na stronie …”)",
             hint="Krótko, 1–4 słowa. Puste pole = rozdziału nie ma w menu.")

def ton():
    return sel("ton", "Ton tła rozdziału", TONY, default="t1",
               hint="Sąsiednie rozdziały nie mają tego samego tonu.")

def alt():
    return s("alt", "Tekst alternatywny (alt)", maxlength=125, hint=(
        "Co naprawdę widać, słowami strony (mama, córka, opowiada, rozmowa). Jedno zdanie, 50–125 znaków. "
        "Nigdy „Arthur”, „arthurozmowy” ani „AI” przy zdjęciu człowieka."))

def zdjecie(label, hint, telefon=False):
    pola = [img("plik", "Plik zdjęcia", "strony")]
    if telefon:
        pola.append(img("plik_telefon", "Kadr 4:3 na telefon", "strony",
                        hint="Na telefonie zamiast zdjęcia 21:9 stoi ten kadr (1200 × 900)."))
    pola += [alt(), b("widoczne", "Pokaż zdjęcie", True)]
    return obj("zdjecie", label, fields=pola, hint=(
        hint + " Nazwa pliku: arthurozmowy-{strona}-{treść}-{format}.webp. "
        "Obróbka promptem „Xiaomi – Huawei Style” (Księga, rozdz. 17), bez odmładzania."))

def lid(label="Lid (kursywa pod nagłówkiem)"):
    return md("lid", label, hint="Jeden akapit, który streszcza rozdział. " + ZAKAZANE)

def faq_rel(min_=None, max_=None, label="Pytania z listy"):
    f = {"label": label, "name": "pytania", "widget": "relation", "required": False,
         "collection": "_singletons", "file": "pytania",
         "value_field": "pytania.*.id", "search_fields": ["pytania.*.pytanie"],
         "display_fields": ["pytania.*.pytanie"], "multiple": True}
    if min_: f["min"] = min_
    if max_: f["max"] = max_
    return f

# ---------------------------------------------------------------- bloki (jeden typ = jeden moduł makiety)

B_TEKST = obj("tekst", "Tekst akapitu", summary="Tekst akapitu: {{fields.tekst}}", fields=[
    md("tekst", "Tekst", hint=("Akapity oddzielaj pustą linią. Znaczniki: {firma} (dane firmy), {email}, {telefon}, {godziny}. "
                               + ZAKAZANE)),
])
B_GLOS = obj("glos", "Voice aside", summary="Voice aside: {{fields.tekst}}", fields=[
    md("tekst", "Tekst", hint="Jedna myśl, 1–3 zdania. Kursywa w kolorze rdzy na piasku. Znaczniki jak w tekście akapitu."),
])
B_LISTA = obj("lista", "Lista", summary="Lista: {{fields.naglowek}}", fields=[
    s("naglowek", "Zdanie nad listą"),
    lst("punkty", "Punkty", field=t("punkt", "Punkt"), label_singular="Punkt", collapsed=False),
    b("numerowana", "Lista numerowana", False),
])
B_ZASADY = obj("zasady", "Zasady (nagłówek H3, lid H3, tekst)", summary="Zasady", fields=[
    lst("zasady", "Zasady", summary="{{fields.naglowek}}", label_singular="Zasada", fields=[
        s("naglowek", "Zasada (nagłówek H3)", hint="Bez numeru, szablon go dopisuje."),
        t("lid", "Lid H3"),
        t("tekst", "Tekst akapitu"),
    ]),
])
B_CYTAT = obj("cytat", "Karta cytatu", summary="Karta cytatu: {{fields.etykieta}}", hint=(
    "Przykładowy dialog mamy z Arthurem zawsze ma etykietę „Przykład rozmowy”, bo jest wymyślony. "
    "Nigdy fragment prawdziwej rozmowy z mamą. Etykieta „Przykład raportu” zmienia wygląd karty na raport: "
    "wstęp jest wtedy tematem raportu, a „Kto mówi” nagłówkiem części raportu."), fields=[
    s("etykieta", "Etykieta nad kartą", hint="Np. „Przykład rozmowy”, „Przykład”, „Przykład raportu”. Może zostać pusta."),
    t("wstep", "Zdanie wstępu w karcie"),
    lst("repliki", "Kwestie", summary="{{fields.kto}}: {{fields.kwestia}}", label_singular="Kwestia", fields=[
        s("kto", "Kto mówi", hint="Mama, Arthur albo Ty. Puste pole = sam cytat."),
        t("kwestia", "Kwestia", hint="Bez cudzysłowu, szablon go dodaje."),
    ]),
    b("widoczny", "Pokaż kartę", True),
])
B_CENNIK = obj("cennik", "Karty ceny", summary="Karty ceny (ceny w Elementach wspólnych)", fields=[
    {"label": "Pakiety", "name": "info", "widget": "hidden", "required": False},
])
B_LINK = obj("link", "Link wewnętrzny", summary="Link wewnętrzny: {{fields.tekst}}", fields=[
    s("tekst", "Tekst linku", required=True,
      hint="Nazwa strony albo rozdziału, do którego prowadzi (jeden temat, jedna nazwa). Przed nim stoi „Więcej:”."),
    adres_z_listy(),
    b("aktywny", "Link aktywny", True, hint="Wyłącz, dopóki strona docelowa nie istnieje."),
])
B_WEZWANIE = obj("wezwanie", "Przycisk CTA", summary="Przycisk CTA: {{fields.rodzaj}}", fields=[
    sel("rodzaj", "Który przycisk", [
        {"label": "Porozmawiaj z Arthurem (okienko z formularzem rozmowy)", "value": "glowne"},
        {"label": "Umów mamie próbne arthurozmowy (zamówienie)", "value": "zakupowe"},
        {"label": "Napisz do nas (okienko z formularzem kontaktu)", "value": "napisz"},
    ], default="glowne", required=True, hint="Teksty przycisków są w Elementach wspólnych."),
    b("objasnienie", "Pokaż objaśnienie pod przyciskiem (tylko „Porozmawiaj z Arthurem”)", False),
])
B_PYTANIA = obj("pytania", "Karty pytań (strona Pytania)", summary="Karty pytań", fields=[
    faq_rel(label="Pytania z listy, w kolejności"),
])
B_FAQ = obj("faq", "Najczęstsze pytania (akordeon z 3 pytaniami)", summary="Najczęstsze pytania", hint=(
    "Pod akordeonem szablon dodaje link „Wszystkie pytania” do strony Pytania."), fields=[
    faq_rel(3, 3, label="Trzy pytania z listy"),
])

BLOKI = [B_TEKST, B_GLOS, B_LISTA, B_ZASADY, B_CYTAT, B_CENNIK, B_LINK, B_WEZWANIE, B_PYTANIA, B_FAQ]
BLOKI_KAMPANII = [x for x in BLOKI if x["name"] != "pytania"]

def bloki(wolny=False, typy=None):
    f = {"label": "Bloki, w kolejności wyświetlania", "name": "bloki", "widget": "list", "required": False,
         "collapsed": True, "typeKey": "typ", "types": typy or BLOKI, "label_singular": "Blok",
         "hint": "Jeden blok = jeden moduł makiety." + (" Przeciągnij, aby zmienić kolejność." if wolny else "")}
    if not wolny:
        f.update(ZABLOKOWANY)
    return f

SCHEMATY = ["Organization", "WebSite", "WebPage", "Service", "Offer", "FAQPage", "HowTo",
            "AboutPage", "ContactPage", "Person", "BreadcrumbList"]

def tytul():
    return s("tytul", "Tytuł strony (title)", required=True, maxlength=70,
             hint="Najlepiej do 60 znaków, twarda granica 70. Google pokazuje około 580 px.",
             pattern=["^.{10,70}$", "10–70 znaków"])

def opis():
    return t("opis", "Opis w wynikach (meta description)", maxlength=160,
             hint="110–155 znaków. Pierwsze zdanie samo mówi, o czym jest strona (Google i AI). Bez Entera.",
             pattern=["^[^\\n]{0,160}$", "Do 160 znaków, bez Entera"])

def obraz_og():
    return obj("obraz_og", "Obraz do udostępniania (1200 × 630)", fields=[
        img("plik", "Plik JPG", "og"),
        s("alt", "Tekst alternatywny", maxlength=125),
    ])

def data_aktualizacji(required=True):
    return {"label": "Data aktualizacji", "name": "zaktualizowano", "widget": "datetime", "required": required,
            "format": "YYYY-MM-DD", "date_format": "YYYY-MM-DD", "time_format": False,
            "hint": "Zmieniaj przy każdej zmianie treści. Autor i data trafiają do danych strukturalnych."}

def wejscie_pola(szablon, wolny=False):
    if szablon == "glowna":
        hero = zdjecie("Zdjęcie wejścia", "Wejście strony głównej: plik 21:9 i osobny kadr 4:3 na telefon.", telefon=True)
    else:
        hero = zdjecie("Zdjęcie wejścia", "Wejście podstrony: kwadrat 1:1 (1200 × 1200).")
    pola = [
        t("h1", "Nagłówek H1", required=True,
          hint="Jeden na stronę. Korzyść mamy w nagłówku (dominanta). Bez Entera. " + ZAKAZANE),
        hero,
        lid("Lid H1 (kursywa pod nagłówkiem)"),
    ]
    if szablon == "blad":
        pola.append(obj("przycisk_powrotu", "Przycisk powrotu", fields=[s("tekst", "Tekst"), adres_z_listy()]))
    pola += [bloki(wolny, BLOKI_KAMPANII if wolny else None), etykieta(), kotwica(readonly=not wolny)]
    return pola

def sekcje_pola(wolny=False):
    pola = [
        t("h2", "Nagłówek H2",
          hint="Jedno pełne zdanie, które samo odpowiada na pytanie rozdziału (cytowalne przez AI). Bez Entera. " + ZAKAZANE),
        zdjecie("Zdjęcie rozdziału", "Zdjęcie w rozdziale: poziome 4:3 (1200 × 900)."),
        lid("Lid H2 (kursywa pod nagłówkiem)"),
        bloki(wolny, BLOKI_KAMPANII if wolny else None),
        etykieta(), ton(), kotwica(readonly=not wolny),
    ]
    f = lst("sekcje", "Rozdziały strony", summary="{{fields.etykieta}} · {{fields.h2}}", fields=pola,
            label_singular="Rozdział", thumbnail="zdjecie.plik",
            hint=("Kolejność rozdziałów = kolejność na stronie. Przeciągnij, aby zmienić." if wolny
                  else "Układ rozdziałów zmienia paczka z WITRYNY; tu zmieniasz ich treść."))
    if not wolny:
        f.update(ZABLOKOWANY)
    return f

# ---------------------------------------------------------------- strony z menu

def pola_strony(szablon):
    blad = szablon == "blad"
    seo = obj("seo", "Wyszukiwarki (SEO)", fields=[
        tytul(), opis(), obraz_og(), data_aktualizacji(),
        s("autor", "Autor strony", default="Piotr Jaworski"),
        s("adres", "Adres strony", required=True, readonly=True,
          pattern=["^/[a-z0-9/-]*$", "Ścieżka od /, małe litery bez polskich znaków"]),
        sel("schemat", "Dane strukturalne (JSON-LD)", SCHEMATY, multiple=True, readonly=True),
        b("indeksuj", "Pokazuj w wyszukiwarkach", True, readonly=True),
    ])
    geo = obj("geo", "Streszczenie dla AI (GEO)", fields=[
        t("streszczenie", "Streszczenie strony",
          hint="2–5 zdań faktów z tej strony, w trzeciej osobie. Trafia do llms.txt."),
    ])
    pola = [
        obj("strona", "Nazwa strony", collapsed=False, fields=[
            s("nazwa", "Nazwa strony", required=True,
              hint="Ta sama nazwa stoi nad H1 (wielkimi literami), w menu, w stopce i w linkach wewnętrznych. "
                   "Zmieniasz ją też w Elementach wspólnych › Lista stron."),
            {"label": "Szablon", "name": "szablon", "widget": "hidden", "default": szablon},
        ]),
        obj("wejscie", "Wejście (H1, zdjęcie, lid, bloki)", collapsed=False, fields=wejscie_pola(szablon)),
    ]
    if blad:
        pola.append({"label": "Rozdziały", "name": "sekcje", "widget": "hidden", "default": []})
    else:
        pola.append(sekcje_pola())
    pola += [seo, geo]
    return pola

STRONY = [
    ("strona-glowna", "Jej sprawy (strona główna)", "glowna", "/"),
    ("o-nas", "O nas", "podstrona", "/o-nas"),
    ("jak-dziala-arthur", "Jak działa Arthur", "podstrona", "/jak-dziala-arthur"),
    ("jak-korzystac", "Jak korzystać", "podstrona", "/jak-korzystac"),
    ("jak-rozmawiac-z-mama", "Jak rozmawiać z mamą", "podstrona", "/jak-rozmawiac-z-mama"),
    ("czego-nie-obiecujemy", "Czego nie obiecujemy", "podstrona", "/czego-nie-obiecujemy"),
    ("bezpieczenstwo", "Bezpieczeństwo", "podstrona", "/bezpieczenstwo"),
    ("pytania", "Pytania", "podstrona", "/pytania"),
    ("kontakt", "Kontakt", "podstrona", "/kontakt"),
    ("404", "Strona błędu (404)", "blad", "/404"),
]

# ---------------------------------------------------------------- strony kampanii

POLA_KAMPANII = [
    s("nazwa_robocza", "Nazwa robocza", required=True,
      hint="Widać ją tylko w panelu, np. „Google Ads · listopad · rozmowy o książkach”."),
    s("adres", "Adres strony", required=True,
      hint="Część adresu po arthurozmowy.pl/, np. mama-ma-swoje-sprawy. Po starcie kampanii go nie zmieniaj, "
           "bo prowadzą na niego reklamy. Nie może powtarzać adresu innej strony.",
      pattern=["^[a-z0-9]+(-[a-z0-9]+)*$", "Małe litery bez polskich znaków, cyfry i łącznik"]),
    obj("strona", "Nazwa strony i układ wejścia", collapsed=False, fields=[
        s("nazwa", "Nazwa nad H1", hint="Wielkimi literami nad nagłówkiem. Puste pole = bez nazwy."),
        sel("szablon", "Układ wejścia", [
            {"label": "Zdjęcie 1:1 obok nagłówka (jak podstrony)", "value": "podstrona"},
            {"label": "Zdjęcie 21:9 od krawędzi do krawędzi (jak strona główna)", "value": "glowna"},
        ], default="podstrona", required=True),
    ]),
    obj("wejscie", "Wejście (H1, zdjęcie, lid, bloki)", collapsed=False, fields=[
        t("h1", "Nagłówek H1", required=True,
          hint="Jeden na stronę. Korzyść mamy w nagłówku (dominanta). Bez Entera. " + ZAKAZANE),
        zdjecie("Zdjęcie wejścia", "Układ „jak podstrony”: kwadrat 1:1 (1200 × 1200). Układ „jak strona główna”: plik 21:9 i kadr 4:3 na telefon.",
                telefon=True),
        lid("Lid H1 (kursywa pod nagłówkiem)"),
        bloki(True, BLOKI_KAMPANII),
    ]),
    sekcje_pola(wolny=True),
    obj("seo", "Wyszukiwarki i udostępnianie", fields=[
        tytul(), opis(), obraz_og(), data_aktualizacji(required=False),
        s("autor", "Autor strony", default="Piotr Jaworski"),
        b("indeksuj", "Pokazuj w wyszukiwarkach", False,
          hint="Zwykle wyłączone: strona kampanii jest dla osób z reklamy. Strony kampanii nie trafiają do mapy strony ani do llms.txt."),
    ]),
]

# ---------------------------------------------------------------- baza pytań

POLA_BAZY = [lst("pytania", "Pytania i odpowiedzi", summary="{{fields.pytanie}}", collapsed=True,
                 label_singular="Pytanie", fields=[
    s("pytanie", "Pytanie", required=True, hint="Tak, jak zadałaby je córka."),
    md("odpowiedz", "Odpowiedź", required=True,
       hint="Pierwsze zdanie zawiera całą odpowiedź (GEO). " + ZAKAZANE),
    obj("link", "Link pod odpowiedzią", fields=[
        s("tekst", "Tekst linku", hint="Nazwa strony albo rozdziału, do którego prowadzi."),
        adres_z_listy(),
    ]),
    s("id", "Identyfikator", required=True,
      hint="Nadajesz go raz, przy nowym pytaniu: małe litery i łącznik. Potem go nie zmieniaj, bo po nim strony wybierają pytania.",
      pattern=["^[a-z0-9-]+$", "Tylko a–z, cyfry i łącznik"]),
])]

# ---------------------------------------------------------------- elementy wspólne

def okno_pola(kontakt=False):
    if kontakt:
        pola = [s("tytul", "Tytuł"), t("wstep", "Wstęp"), s("pole_imie", "Pole: imię"), s("pole_email", "Pole: e-mail"),
                s("pole_telefon", "Pole: telefon"), s("pole_wiadomosc", "Pole: wiadomość"), s("przycisk", "Przycisk")]
    else:
        pola = [s("tytul", "Tytuł"), t("wstep", "Wstęp"), s("pole_numer", "Pole: numer"),
                s("pytanie_kiedy", "Pytanie o porę"), s("opcja_teraz", "Opcja: teraz"), s("opcja_termin", "Opcja: termin"),
                s("pole_data", "Pole: data"), s("pole_godzina", "Pole: godzina"), s("przycisk", "Przycisk")]
    return pola + [t("potwierdzenie", "Potwierdzenie"), t("blad", "Komunikat błędu"),
                   t("zgoda", "Zgoda i informacja RODO", hint="Zmieniamy tylko razem z polityką prywatności.")]

def lista_linkow(name, label, summary="{{fields.tekst}} → {{fields.adres}}", hint=None, adres_readonly=False, **kw):
    adres = s("adres", "Adres", readonly=True) if adres_readonly else s("adres", "Adres")
    return lst(name, label, summary=summary, hint=hint, fields=[s("tekst", "Tekst"), adres], **kw)

WEZWANIA = [{"label": "Porozmawiaj z Arthurem", "value": "glowne"},
            {"label": "Umów mamie próbne arthurozmowy", "value": "zakupowe"},
            {"label": "Napisz do nas", "value": "napisz"}]

POLA_WSPOLNE = [
    obj("pakiety", "Pakiety i ceny", hint=(
        "Jedno źródło cen: karty ceny na stronie głównej i na Jak korzystać, dane dla Google i llms.txt. "
        "Trzy pakiety, każdy z jedną ceną."), fields=[
        lst("lista", "Pakiety", summary="{{fields.cena}} zł · {{fields.rytm}}", label_singular="Pakiet",
            min=3, max=3, allow_add=False, allow_remove=False, fields=[
            s("nazwa", "Nazwa pakietu", hint="Małą literą, np. „pakiet optymalny”."),
            {"label": "Cena (zł z VAT, miesięcznie)", "name": "cena", "widget": "number", "value_type": "int", "required": True},
            s("rytm", "Rytm tygodnia (największy po cenie)",
              hint="Np. „co tydzień 1 rozmowa pełna i 1 podtrzymująca”. Liczby muszą się zgadzać z polami niżej."),
            s("opis", "Liczby w miesiącu (pod rytmem)",
              hint="Z odmianą, np. „4–5 rozmów pełnych i 4–5 rozmów podtrzymujących w miesiącu”."),
            {"label": "Rozmowy pełne w tygodniu", "name": "rozmowy_pelne", "widget": "number", "value_type": "int"},
            {"label": "Rozmowy podtrzymujące w tygodniu", "name": "rozmowy_podtrzymujace", "widget": "number", "value_type": "int"},
            b("polecany", "Pakiet proponowany na początek (ramka w rdzy)"),
        ]),
        s("okres", "Dopisek przy cenie"),
        s("dlugosc", "Długość rozmów (zdanie na każdej karcie ceny)", hint="Długość jednej rozmowy, nigdy suma minut."),
        s("waluta", "Waluta", readonly=True),
    ]),
    obj("wezwania", "Przyciski CTA", hint="Trzy przyciski witryny. Strony wybierają, który pokazać.", fields=[
        obj("glowne", "Porozmawiaj z Arthurem (otwiera okienko rozmowy)", fields=[
            s("przycisk", "Napis na przycisku"), t("dopisek", "Objaśnienie pod przyciskiem")]),
        obj("zakupowe", "Zamówienie", fields=[
            s("przycisk", "Napis na przycisku"),
            s("adres", "Adres zamówienia", hint="Dopóki zamówienia nie ma, przycisk jest nieaktywny.")]),
        obj("napisz", "Napisz do nas (otwiera okienko kontaktu)", fields=[s("przycisk", "Napis na przycisku")]),
    ]),
    obj("okno_rozmowy", "Okienko „Porozmawiaj z Arthurem”", hint=(
        "Okienko jest nieaktywne do oceny skutków dla ochrony danych (Z6) i polityki prywatności."), fields=okno_pola()),
    obj("okno_kontaktu", "Okienko „Napisz do nas”", hint=(
        "Okienko jest nieaktywne do oceny skutków dla ochrony danych (Z6) i polityki prywatności."), fields=okno_pola(True)),
    obj("naglowek", "Belka i menu", hint=(
        "Od lewej: logo, przycisk Menu, linki, przycisk zamówienia i Panel klienta. Menu to jedna lista stron; "
        "rozdziały stoją pod stroną oglądaną albo wskazaną."), fields=[
        s("menu", "Napis na przycisku menu"),
        s("grupa_strony", "Napis nad listą stron"),
        s("grupa_rozdzialy", "Napis nad rozdziałami strony", hint="Szablon dopisuje nazwę strony, np. „Na stronie Jak działa Arthur”."),
        lista_linkow("linki", "Linki w belce (np. Cena, Kontakt)", allow_add=False, allow_remove=False),
        s("zakup", "Napis na przycisku zamówienia w belce"),
        s("panel_klienta", "Napis linku do panelu klienta"),
        b("przycisk_staly", "Przycisk „Porozmawiaj z Arthurem” przyklejony do dołu ekranu na telefonie", True),
    ]),
    obj("nawigacja", "Lista stron (menu i stopka)", hint=(
        "Jeden temat, jedna nazwa: nazwa strony taka sama w menu, stopce, linkach wewnętrznych "
        "i rozdziałach strony głównej. Zmieniasz ją też w polu „Nazwa strony” na tej stronie."), fields=[
        lista_linkow("strony", "Strony, w kolejności menu", adres_readonly=True, allow_add=False, allow_remove=False),
        s("wszystkie_pytania", "Napis linku pod akordeonem pytań"),
        s("wiecej", "Słowo przed linkiem wewnętrznym", hint="Np. „Więcej:”. Po nim stoi nazwa strony albo rozdziału."),
    ]),
    obj("firma", "Dane firmy", hint="Znaczniki w tekstach: {firma}, {email}, {telefon}, {godziny}. Stąd biorą też stopka i dane dla Google.", fields=[
        s("nazwa", "Nazwa"), s("ulica", "Ulica i numer"), s("kod_pocztowy", "Kod pocztowy"),
        s("miejscowosc", "Miejscowość"), s("kraj", "Kraj (kod)"), s("nip", "NIP"),
        s("email", "E-mail"), s("telefon", "Telefon"),
        s("telefon_godziny", "Godziny odbierania telefonu"),
        s("panel_klienta", "Adres panelu klienta"),
    ]),
    obj("stopka", "Stopka", fields=[
        sel("wezwania", "Przyciski CTA na górze stopki", WEZWANIA, multiple=True),
        s("prywatnosc", "Zdanie o statystykach"), s("prawa", "Linia praw autorskich i danych firmy"),
        lista_linkow("linki_prawne", "Linki prawne", summary="{{fields.tekst}}", adres_readonly=True,
                     allow_add=False, allow_remove=False),
    ]),
    obj("pomiar", "Pomiar i reklama", hint=(
        "Pola zaczną działać po podłączeniu pomiaru przed startem; do tego czasu zostają puste. "
        "Piksele Google Ads i Meta oraz GA4 ustawia się w GTM, a teksty banera w panelu usługi banera."), fields=[
        s("gtm", "Kontener GTM", hint="Np. GTM-ABC1234.", pattern=["^(GTM-[A-Z0-9]+)?$", "Np. GTM-ABC1234"]),
        sel("baner_usluga", "Usługa banera zgód", [
            {"label": "Cookiebot", "value": "cookiebot"}, {"label": "CookieYes", "value": "cookieyes"}]),
        s("baner_id", "Identyfikator banera zgód"),
        s("licznik_skrypt", "Adres skryptu licznika bez cookies", hint="Adres z panelu Plausible albo Umami."),
        s("licznik_id", "Identyfikator witryny w liczniku", hint="Tylko Umami; przy Plausible zostaje puste."),
    ]),
    obj("marka", "Marka", fields=[
        t("definicja", "Definicja arthurozmów",
          hint="Słowo w słowo to samo w odpowiedzi „Czym są arthurozmowy?”, w danych dla Google i w llms.txt."),
        obj("logo", "Logo", fields=[img("plik", "Plik SVG", "marka"), s("alt", "Alt")]),
        s("nazwa", "Nazwa usługi", readonly=True),
        s("domena", "Domena", readonly=True), s("jezyk", "Język", readonly=True),
    ]),
    obj("autor", "Autor stron", fields=[s("imie_nazwisko", "Imię i nazwisko"), s("adres_strony", "Strona autora")]),
]

# ---------------------------------------------------------------- config

OPIS_STRON = ("Dziewięć stron z menu i strona błędu. Zmieniasz tu teksty, zdjęcia i wybór pytań; układ rozdziałów "
              "i bloków jest zablokowany. Zapis tworzy wersję roboczą z podglądem, a „Opublikuj” wysyła ją na witrynę.")
OPIS_KAMPANII = ("Strony pod konkretne reklamy, poza menu i mapą strony. Tu możesz dodawać, usuwać i przestawiać "
                 "rozdziały i bloki. Strona kampanii mówi o rozmowach, a nie o zdrowiu (ograniczenia reklam Google i Meta).")

config = {
    "backend": {
        "name": "github",
        "repo": "Potr-Arthur/arthurozmowy-pl",
        "branch": "main",
        # Link do podglądu wersji roboczej: status Netlify „netlify/arthurozmowy/deploy-preview”.
        "preview_context": "deploy-preview",
        # Logowanie: osobisty token GitHub (fine-grained, tylko to repozytorium; Contents i Pull requests:
        # read and write, Commit statuses: read). Worker logowania dodamy, gdy do redakcji dojdzie druga osoba.
        "commit_messages": {
            "create": "Treść: dodano {{collection}} „{{slug}}”",
            "update": "Treść: zmieniono {{collection}} „{{slug}}”",
            "delete": "Treść: usunięto {{collection}} „{{slug}}”",
            "uploadMedia": "Media: dodano „{{path}}”",
            "deleteMedia": "Media: usunięto „{{path}}”",
        },
    },
    # D1: zapis = wersja robocza (pull request z podglądem Netlify), „Opublikuj” scala ją z gałęzią main.
    "publish_mode": "preview",
    "app_title": "Redakcja arthurozmowy",
    "logo": {"src": "/images/marka/arthur-ikona-192.png"},
    # Adres witryny = adres, pod którym stoi panel (dziś adres tymczasowy, po starcie arthurozmowy.pl).
    "media_folder": "public/images",
    "public_folder": "/images",
    # Wbudowany podgląd pokazuje surowe pola, a nie wygląd strony; podglądem jest wersja zbudowana przez Netlify.
    "editor": {"preview": False},
    "slug": {"encoding": "ascii", "clean_accents": True},
    "collections": [
        {"name": "strony", "label": "Strony", "label_singular": "Strona", "icon": "article",
         "description": OPIS_STRON,
         "files": [{"name": n, "label": l, "file": f"src/content/strony/{n}.yml", "format": "yml",
                    "preview_path": adres, "fields": pola_strony(sz)} for n, l, sz, adres in STRONY]},
        {"name": "kampanie", "label": "Strony kampanii", "label_singular": "Strona kampanii", "icon": "campaign",
         "description": OPIS_KAMPANII,
         "folder": "src/content/kampanie", "extension": "yml", "format": "yml",
         "create": True, "delete": True,
         "identifier_field": "nazwa_robocza", "slug": "{{fields.adres}}",
         "summary": "{{fields.nazwa_robocza}} · /{{fields.adres}}",
         "preview_path": "/{{fields.adres}}",
         "fields": POLA_KAMPANII},
    ],
    "singletons": [
        {"name": "pytania", "label": "Pytania i odpowiedzi", "icon": "quiz",
         "file": "src/content/pytania/baza.yml", "format": "yml", "preview_path": "/pytania", "fields": POLA_BAZY},
        {"name": "wspolne", "label": "Elementy wspólne", "icon": "tune",
         "file": "src/content/ustawienia/witryna.yml", "format": "yml", "fields": POLA_WSPOLNE},
    ],
}

class NoAlias(yaml.SafeDumper):
    def ignore_aliases(self, data):
        return True

HEADER = """# Sveltia CMS · arthurozmowy.pl · konfiguracja redakcji
# PLIK GENEROWANY: zmiany wprowadzaj w narzedzia/generuj_config.py i uruchom go ponownie.
# Bez kotwic YAML, bo Sveltia czyta YAML ściśle. Bloki odpowiadają modułom makiety V2 (README, „Model treści”).
# Układ panelu: claude/CMS_panele_redakcji_v1.md. Listy adresów są zbudowane z plików treści.
"""

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(HEADER + yaml.dump(config, Dumper=NoAlias, sort_keys=False, allow_unicode=True, width=110),
               encoding="utf-8")
print(f"Zapisano {OUT.relative_to(ROOT)}")
