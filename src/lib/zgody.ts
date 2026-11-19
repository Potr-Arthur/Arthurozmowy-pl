// Okienko zgód na pliki cookie (19.11.2026): stałe wspólne dla skryptu w <head> i dla okienka (Zgody.astro).
// Consent Mode v2: do zgody wszystko, co zapisuje pliki cookie Google i Meta, jest wyłączone.
// Nowy cel albo nowa kategoria = nowa WERSJA: wtedy okienko pyta wszystkich jeszcze raz.
export const KLUCZ = 'arthurozmowy-zgody';
export const WERSJA = 1;
export const WAZNOSC_DNI = 365;

export type Wybor = { statystyki: boolean; reklamy: boolean };

/** Sygnały Consent Mode v2 dla wyboru z okienka: statystyki = GA4, reklamy = Google Ads i Meta. */
export function sygnaly(w: Wybor) {
  const s = (x: boolean) => (x ? 'granted' : 'denied');
  return { analytics_storage: s(w.statystyki), ad_storage: s(w.reklamy), ad_user_data: s(w.reklamy), ad_personalization: s(w.reklamy) };
}

/** Skrypt do <head>, przed wszystkim innym: domyślnie brak zgody, zapisany wybór z przeglądarki, potem kontener GTM. */
export function skryptGlowy(gtm?: string | null): string {
  const zapisany =
    `try{var z=JSON.parse(localStorage.getItem(${JSON.stringify(KLUCZ)}));` +
    `if(z&&z.wersja===${WERSJA}&&Date.now()-z.czas<${WAZNOSC_DNI * 864e5}){` +
    `var s=function(x){return x?'granted':'denied'};` +
    `gtag('consent','update',{analytics_storage:s(z.statystyki),ad_storage:s(z.reklamy),ad_user_data:s(z.reklamy),ad_personalization:s(z.reklamy)});}}catch(e){}`;
  const kontener = gtm
    ? `(function(w,d,s,l,i){w[l]=w[l]||[];w[l].push({'gtm.start':new Date().getTime(),event:'gtm.js'});` +
      `var f=d.getElementsByTagName(s)[0],j=d.createElement(s);j.async=true;` +
      `j.src='https://www.googletagmanager.com/gtm.js?id='+i;f.parentNode.insertBefore(j,f);})` +
      `(window,document,'script','dataLayer',${JSON.stringify(gtm)});`
    : '';
  return (
    `window.dataLayer=window.dataLayer||[];window.gtag=function(){dataLayer.push(arguments);};` +
    `gtag('consent','default',{ad_storage:'denied',ad_user_data:'denied',ad_personalization:'denied',` +
    `analytics_storage:'denied',functionality_storage:'granted',security_storage:'granted',wait_for_update:500});` +
    `gtag('set','ads_data_redaction',true);` +
    zapisany +
    kontener
  );
}
