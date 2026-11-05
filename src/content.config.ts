// arthurozmowy.pl · kolekcje treści Astro 5 (content layer)
// Schemat odpowiada polom z public/admin/config.yml (generowanym przez narzedzia/generuj_config.py).
// Zmiana pola w CMS wymaga zmiany tutaj i w generatorze konfiguracji.
import { defineCollection, z } from 'astro:content';
import { glob } from 'astro/loaders';

const ton = z.enum(['t1', 't2', 't3', 't4', 't5']);

const wezwania = z
  .object({
    glowne: z.boolean().default(false),
    dopisek: z.boolean().default(false),
    jawnosc: z.boolean().default(false),
    zakupowe: z.boolean().default(false),
    nad_zakupowym: z.boolean().default(false),
  })
  .partial()
  .optional();

const zdjecie = z
  .object({
    widoczne: z.boolean().default(true),
    plik_desktop: z.string().optional(),
    plik_telefon: z.string().optional(),
    alt: z.string().optional(),
    kadr: z.string().optional(),
  })
  .optional();

const link = z.object({
  tekst: z.string(),
  adres: z.string().optional(),
  aktywny: z.boolean().default(true),
});
const linki = z.array(link).optional();

const wspolne = {
  kotwica: z.string().regex(/^[a-z0-9-]*$/).optional(),
  etykieta: z.string().optional().nullable(),
  ton,
};

const rozdzial = z.object({
  typ: z.literal('rozdzial'),
  ...wspolne,
  h2: z.string().optional(),
  tekst: z.string().optional(),
  definicje: z.array(z.object({ termin: z.string(), opis: z.string() })).optional(),
  lista: z.object({ wprowadzenie: z.string(), punkty: z.array(z.string()) }).optional(),
  cennik: z.object({ widoczny: z.boolean(), pokaz_nazwy: z.boolean().default(false) }).optional(),
  tekst_po: z.string().optional(),
  akapit_ukryty: z
    .object({ widoczny: z.boolean(), tekst: z.string(), warunek: z.string().optional() })
    .optional(),
  zdjecie,
  okno_glosu: z
    .object({
      widoczne: z.boolean(),
      wariant: z.enum(['cieple', 'glebia', 'jasne']),
      etykieta: z.string(),
      dialog: z.array(z.object({ kto: z.enum(['Mama', 'Arthur']), kwestia: z.string() })).optional(),
      zdanie: z.string().optional(),
      przypis: z.string().optional(),
      nagranie: z.object({ plik: z.string().optional(), transkrypcja: z.string().optional() }).optional(),
    })
    .optional(),
  cudze_zdanie: z
    .object({
      widoczne: z.boolean(),
      cytat: z.string().optional(),
      kto: z.string().optional(),
      zgoda: z.boolean(),
    })
    .optional(),
  linki,
  wezwania,
});

const zasady = z.object({
  typ: z.literal('zasady'),
  ...wspolne,
  h2: z.string(),
  tekst: z.string().optional(),
  zasady: z.array(z.object({ naglowek: z.string(), tekst: z.string(), dlaczego: z.string() })),
  linki,
  wezwania,
});

const krok = z.object({
  typ: z.literal('krok'),
  ...wspolne,
  numer: z.number().int().min(1),
  h2: z.string(),
  tekst: z.string(),
  przyklad: z.string().optional(),
  zdjecie,
  linki,
  wezwania,
});

const watpliwosci = z.object({
  typ: z.literal('watpliwosci'),
  ...wspolne,
  h2: z.string(),
  tekst: z.string().optional(),
  pary: z.array(z.object({ mama: z.string(), odpowiedz: z.string() })),
  zakonczenie: z.string().optional(),
  linki,
  wezwania,
});

const pytania = z.object({
  typ: z.literal('pytania'),
  ...wspolne,
  wstep: z.string().optional(),
  zdjecie,
  pytania: z.array(z.string()),
  wezwania,
});

const faq = z.object({
  typ: z.literal('faq'),
  ...wspolne,
  h2: z.string().default('Najczęstsze pytania'),
  pytania: z.array(z.string()).length(3),
  linki,
});

const kontakt = z.object({
  typ: z.literal('kontakt'),
  ...wspolne,
  h2: z.string(),
  tekst: z.string().optional(),
  pokaz: z
    .object({
      email: z.boolean(),
      telefon: z.boolean(),
      godziny_telefonu: z.boolean(),
      czas_odpowiedzi: z.boolean(),
    })
    .partial()
    .optional(),
  uwaga: z.string().optional(),
  zdjecie,
  linki,
  wezwania,
});

const koniec = z.object({ typ: z.literal('koniec'), ton, linki, wezwania });

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
      etykieta: z.string().optional(),
      h1: z.string(),
      h1_wyroznienie: z.string().optional(),
      lid: z.string(),
      zdjecie,
      przycisk_powrotu: z.object({ tekst: z.string(), adres: z.string() }).optional(),
      linki,
      wezwania,
      pokaz_autora_i_date: z.boolean().default(true),
    }),
    sekcje: z
      .array(
        z.discriminatedUnion('typ', [rozdzial, zasady, krok, watpliwosci, pytania, faq, kontakt, koniec]),
      )
      .default([]),
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

const strona = z.object({ tekst: z.string(), adres: z.string() });

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
      panel_klienta: z.string(),
      przycisk_staly: z.boolean().default(true),
    }),
    nawigacja: z.object({ strony: z.array(strona) }),
    wezwania: z.object({
      glowne: z.object({ przycisk: z.string(), dopisek: z.string() }),
      jawnosc: z.string(),
      zakupowe: z.object({ przycisk: z.string(), adres: z.string(), nad_przyciskiem: z.string() }),
    }),
    okno_rozmowy: z.object({
      tytul: z.string(),
      wstep: z.string(),
      pole_numer: z.string(),
      pytanie_kiedy: z.string(),
      opcja_teraz: z.string(),
      opcja_termin: z.string(),
      pole_data: z.string(),
      pole_godzina: z.string(),
      przycisk: z.string(),
      potwierdzenie: z.string(),
      blad: z.string(),
      zgoda: z.string(),
    }),
    pakiety: z.object({
      waluta: z.string(),
      okres: z.string(),
      lista: z.array(
        z.object({
          cena: z.number(),
          rozmowy_pelne: z.number(),
          rozmowy_podtrzymujace: z.number(),
          opis: z.string(),
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
      czas_odpowiedzi: z.string(),
      panel_klienta: z.string(),
    }),
    autor: z.object({ imie_nazwisko: z.string(), adres_strony: z.string() }),
    stopka: z.object({
      wezwanie_glowne: z.boolean().default(true),
      linki_prawne: z.array(strona),
      kontakt_etykieta: z.string(),
      jawnosc: z.string(),
      prywatnosc: z.string(),
      prawa: z.string(),
    }),
  }),
});

export const collections = { strony, pytania: pytaniaBaza, ustawienia };
