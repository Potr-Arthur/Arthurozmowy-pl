// arthurozmowy.pl · kolekcje treści Astro 5 (content layer)
// Schemat odpowiada polom z public/admin/config.yml (generowanym przez narzedzia/generuj_config.py).
// Zmiana pola w CMS wymaga zmiany tutaj i w generatorze konfiguracji.
//
// Model treści od makiety V2 (11.11.2026): strona = wejście + rozdziały. Wejście i każdy rozdział mają nagłówek,
// zdjęcie, lid i listę bloków w kolejności wyświetlania. Jeden typ bloku = jeden moduł makiety:
//   tekst     Tekst akapitu                         lista    lista punktów (numerowana albo nie)
//   glos      Voice aside                           zasady   zasady z nagłówkiem H3, lidem H3 i tekstem
//   cytat     Karta cytatu                          cennik   Karty ceny (pakiety z Ustawień)
//   link      Link wewnętrzny                       wezwanie Przycisk CTA (tekst z Ustawień)
//   pytania   karty pytań w rozdziale strony Pytania
//   faq       akordeon „Najczęstsze pytania” (3 pytania z bazy i przycisk „Wszystkie pytania”)
import { defineCollection, z } from 'astro:content';
import { glob } from 'astro/loaders';

const ton = z.enum(['t1', 't2', 't3', 't4', 't5']);

const zdjecie = z
  .object({
    widoczne: z.boolean().default(true),
    // jeden plik na zdjęcie: wejście podstrony 1:1 (1200 × 1200), rozdział 4:3 (1200 × 900);
    // wyjątek: wejście strony głównej ma plik 21:9 (komputer) i plik_telefon 4:3
    plik: z.string().optional(),
    plik_telefon: z.string().optional(),
    alt: z.string().optional(),
  })
  .optional();

const blokTekst = z.object({ typ: z.literal('tekst'), tekst: z.string() });
const blokGlos = z.object({ typ: z.literal('glos'), tekst: z.string() });
const blokLista = z.object({
  typ: z.literal('lista'),
  naglowek: z.string().optional(),
  numerowana: z.boolean().default(false),
  punkty: z.array(z.string()),
});
const blokZasady = z.object({
  typ: z.literal('zasady'),
  zasady: z.array(z.object({ naglowek: z.string(), lid: z.string().optional(), tekst: z.string().optional() })),
});
const blokCytat = z.object({
  typ: z.literal('cytat'),
  widoczny: z.boolean().default(true),
  etykieta: z.string().optional(),
  wstep: z.string().optional(),
  repliki: z.array(z.object({ kto: z.string().optional(), kwestia: z.string() })).default([]),
});
const blokCennik = z.object({ typ: z.literal('cennik') });
const blokLink = z.object({
  typ: z.literal('link'),
  tekst: z.string(),
  adres: z.string().optional(),
  aktywny: z.boolean().default(true),
});
const blokWezwanie = z.object({
  typ: z.literal('wezwanie'),
  rodzaj: z.enum(['glowne', 'zakupowe', 'napisz']),
  objasnienie: z.boolean().default(false),
});
const blokPytania = z.object({ typ: z.literal('pytania'), pytania: z.array(z.string()) });
const blokFaq = z.object({ typ: z.literal('faq'), pytania: z.array(z.string()).length(3) });

const bloki = z
  .array(
    z.discriminatedUnion('typ', [
      blokTekst, blokGlos, blokLista, blokZasady, blokCytat, blokCennik, blokLink, blokWezwanie, blokPytania, blokFaq,
    ]),
  )
  .default([]);

const sekcja = z.object({
  kotwica: z.string().regex(/^[a-z0-9-]*$/).optional(),
  etykieta: z.string().optional().nullable(),
  ton,
  h2: z.string().optional(),
  zdjecie,
  lid: z.string().optional(),
  bloki,
});

const strony = defineCollection({
  loader: glob({ pattern: '*.yml', base: './src/content/strony' }),
  schema: z.object({
    strona: z.object({ nazwa: z.string(), szablon: z.enum(['glowna', 'podstrona', 'blad']) }),
    seo: z.object({
      adres: z.string().startsWith('/'),
      tytul: z.string().max(70),
      opis: z.string().max(160),
      obraz_og: z.object({ plik: z.string(), alt: z.string() }),
      schemat: z.array(z.string()),
      indeksuj: z.boolean(),
      autor: z.string(),
      zaktualizowano: z.coerce.date(),
    }),
    geo: z.object({ streszczenie: z.string() }),
    wejscie: z.object({
      kotwica: z.string().optional(),
      etykieta: z.string().optional().nullable(),
      h1: z.string(),
      zdjecie,
      lid: z.string().optional(),
      przycisk_powrotu: z.object({ tekst: z.string(), adres: z.string() }).optional(),
      bloki,
    }),
    sekcje: z.array(sekcja).default([]),
  }),
});

const pytaniaBaza = defineCollection({
  loader: glob({ pattern: '*.yml', base: './src/content/pytania' }),
  schema: z.object({
    pytania: z.array(
      z.object({
        id: z.string().regex(/^[a-z0-9-]+$/),
        pytanie: z.string(),
        odpowiedz: z.string(),
        link: z.object({ tekst: z.string(), adres: z.string() }).optional(),
      }),
    ),
  }),
});

const linkNazwany = z.object({ tekst: z.string(), adres: z.string() });
const okno = z.record(z.string());

const ustawienia = defineCollection({
  loader: glob({ pattern: '*.yml', base: './src/content/ustawienia' }),
  schema: z.object({
    marka: z.object({
      nazwa: z.string(),
      domena: z.string().url(),
      jezyk: z.string(),
      definicja: z.string(),
      logo: z.object({ plik: z.string(), alt: z.string() }),
    }),
    naglowek: z.object({
      menu: z.string(),
      grupa_rozdzialy: z.string(),
      grupa_strony: z.string(),
      linki: z.array(linkNazwany).default([]),
      zakup: z.string(),
      panel_klienta: z.string(),
      przycisk_staly: z.boolean().default(true),
    }),
    nawigacja: z.object({ strony: z.array(linkNazwany), wszystkie_pytania: z.string(), wiecej: z.string() }),
    wezwania: z.object({
      glowne: z.object({ przycisk: z.string(), dopisek: z.string().optional() }),
      zakupowe: z.object({ przycisk: z.string(), adres: z.string() }),
      napisz: z.object({ przycisk: z.string() }),
    }),
    okno_rozmowy: okno,
    okno_kontaktu: okno,
    pakiety: z.object({
      waluta: z.string(),
      okres: z.string(),
      dlugosc: z.string(),
      lista: z.array(
        z.object({
          cena: z.number(),
          rozmowy_pelne: z.number(),
          rozmowy_podtrzymujace: z.number(),
          opis: z.string(),
          rytm: z.string(),
          nazwa: z.string().optional(),
          polecany: z.boolean().optional(),
        }),
      ),
    }),
    firma: z.object({
      nazwa: z.string(),
      ulica: z.string(),
      kod_pocztowy: z.string(),
      miejscowosc: z.string(),
      kraj: z.string(),
      nip: z.string(),
      email: z.string(),
      telefon: z.string(),
      telefon_godziny: z.string(),
      panel_klienta: z.string(),
    }),
    autor: z.object({ imie_nazwisko: z.string(), adres_strony: z.string() }),
    stopka: z.object({
      wezwania: z.array(z.enum(['glowne', 'zakupowe', 'napisz'])).default([]),
      prywatnosc: z.string(),
      prawa: z.string(),
      linki_prawne: z.array(linkNazwany),
    }),
  }),
});

export const collections = { strony, pytania: pytaniaBaza, ustawienia };
