// Talks to the Studio API (serve.py → studio/presentation/api.py). api(path) reads, api(path, body) writes.
// Errors come back as { code, message } and are thrown so callers show them.
export async function api(path, body) {
  const options = body === undefined ? {} : {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body),
  };
  let response;
  try {
    response = await fetch(`/api/studio/${path}`, options);
  } catch (error) {
    throw { code: 'E_STUDIO_DOWN', message: 'No responde el Estudio. ¿Sigue abierto iniciar_estudio.bat?' };
  }
  const data = await response.json().catch(() => null);
  if (!response.ok || data === null) throw data ?? { code: 'E_STUDIO', message: `HTTP ${response.status}` };
  return data;
}

// Saves a text as a file in the browser's downloads (delivery documents, CSV).
export function download(name, text, type = 'text/plain') {
  const url = URL.createObjectURL(new Blob([text], { type: `${type};charset=utf-8` }));
  const link = Object.assign(document.createElement('a'), { href: url, download: name });
  document.body.append(link);
  link.click();
  link.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
