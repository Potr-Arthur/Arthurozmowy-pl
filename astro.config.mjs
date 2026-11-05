// @ts-check
import { defineConfig } from 'astro/config';

// PUBLIKACJA=tak tylko na arthurozmowy.pl (zmienna środowiskowa na Netlify).
// Na adresie tymczasowym adres witryny bierzemy z Netlify (URL), żeby obrazy do udostępniania działały.
const publikacja = process.env.PUBLIKACJA === 'tak';
const site = publikacja ? 'https://arthurozmowy.pl' : (process.env.URL || 'https://arthurozmowy.pl');

export default defineConfig({
  site,
  trailingSlash: 'never',
  build: { format: 'file' },
  devToolbar: { enabled: false },
});
