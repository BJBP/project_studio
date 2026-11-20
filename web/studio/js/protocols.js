// Protocols block rules, pure: which protocols Home Assistant has active, and the link that adds one.
// protocolRows(catalog, entries, bridges) -> [{ ...protocol, active }]; addLink(haUrl, domain) -> URL of HA's own form.

export function protocolRows(catalog, entries, bridges = {}) {
  const domains = new Set((entries ?? []).filter((e) => e.state !== 'not_loaded').map((e) => e.domain));
  return catalog.protocols.map((p) => ({
    ...p, active: p.bridge ? bridges[p.bridge] === 'running' : domains.has(p.domain),
  }));
}

export function addLink(haUrl, domain) {
  return `${haUrl.replace(/\/$/, '')}/_my_redirect/config_flow_start?domain=${encodeURIComponent(domain)}`;
}
