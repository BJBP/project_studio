// Loads web/locales/es.json once and exposes t(key) plus the raw dict for the blocks engine.
// Missing keys fall back to the key itself so nothing renders blank.

const url = new URL('../../../../locales/es.json', import.meta.url);
let dict = {};

try {
  const response = await fetch(url);
  if (response.ok) dict = await response.json();
  else console.warn(`i18n: no se pudo cargar es.json (HTTP ${response.status})`);
} catch (error) {
  console.warn('i18n: no se pudo cargar es.json', error);
}

export function t(key) {
  return typeof dict[key] === 'string' && dict[key] ? dict[key] : key;
}

export const localeTable = dict;
