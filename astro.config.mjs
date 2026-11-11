// @ts-check
import { defineConfig } from 'astro/config';
import { readdirSync, readFileSync, rmSync } from 'node:fs';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';

// PUBLIKACJA=tak tylko na arthurozmowy.pl (zmienna środowiskowa na Netlify).
// Na adresie tymczasowym adres witryny bierzemy z Netlify (URL), żeby obrazy do udostępniania działały.
const publikacja = process.env.PUBLIKACJA === 'tak';
const site = publikacja ? 'https://arthurozmowy.pl' : (process.env.URL || 'https://arthurozmowy.pl');

// Publikujemy tylko zdjęcia stron, które stoją na którejś stronie. Zdjęcie ukryte (widoczne: false),
// np. robocze arthurozmowy-o-nas-eksperci-4x3.webp, zostaje w repozytorium, ale nie trafia na hosting.
const tylkoWidoczneZdjecia = {
  name: 'tylko-widoczne-zdjecia',
  hooks: {
    'astro:build:done': ({ dir, logger }) => {
      const dist = fileURLToPath(dir);
      const html = readdirSync(dist).filter((f) => f.endsWith('.html')).map((f) => readFileSync(join(dist, f), 'utf8')).join('\n');
      const katalog = join(dist, 'images', 'strony');
      let pliki = [];
      try { pliki = readdirSync(katalog); } catch { return; }
      for (const plik of pliki) {
        if (!html.includes(`/images/strony/${plik}`)) {
          rmSync(join(katalog, plik));
          logger.info(`pominięte (nie stoi na żadnej stronie): /images/strony/${plik}`);
        }
      }
    },
  },
};

export default defineConfig({
  site,
  trailingSlash: 'never',
  build: { format: 'file' },
  devToolbar: { enabled: false },
  integrations: [tylkoWidoczneZdjecia],
});
