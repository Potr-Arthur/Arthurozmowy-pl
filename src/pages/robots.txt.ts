// robots.txt: na adresie tymczasowym blokuje wszystkie roboty.
// Docelowa wersja (wszystkie roboty wpuszczone, decyzja z 1.11.2026) jest w narzedzia/robots-docelowy.txt
// i włącza się sama, gdy na Netlify ustawisz zmienną PUBLIKACJA=tak.
import type { APIRoute } from 'astro';
import docelowy from '../../narzedzia/robots-docelowy.txt?raw';

const tymczasowy = `# arthurozmowy · adres tymczasowy: witryna przed startem, żadnych robotów.
User-agent: *
Disallow: /
`;

export const GET: APIRoute = () =>
  new Response(process.env.PUBLIKACJA === 'tak' ? docelowy : tymczasowy, {
    headers: { 'Content-Type': 'text/plain; charset=utf-8' },
  });
