// Lays out text for a 128x64 OLED with a 6x8 px font (21 chars per line,
// 6 lines max). Receives { header, body }, returns truncated header and lines.
const COLS = 21;
const MAX_LINES = 6;

export function oledLayout({ header, body }) {
  const outHeader = String(header ?? "").slice(0, COLS);
  const words = String(body ?? "").split(/\s+/).filter(Boolean);
  const chunks = [];
  for (const word of words) {
    for (let i = 0; i < word.length; i += COLS) {
      chunks.push(word.slice(i, i + COLS));
    }
  }
  const lines = [];
  let current = "";
  for (const chunk of chunks) {
    const candidate = current === "" ? chunk : `${current} ${chunk}`;
    if (candidate.length <= COLS) {
      current = candidate;
    } else {
      if (current !== "") lines.push(current);
      current = chunk;
    }
  }
  if (current !== "") lines.push(current);

  if (lines.length > MAX_LINES) {
    const kept = lines.slice(0, MAX_LINES);
    kept[MAX_LINES - 1] = `${kept[MAX_LINES - 1].slice(0, COLS - 1)}…`;
    return { header: outHeader, lines: kept };
  }
  return { header: outHeader, lines };
}
