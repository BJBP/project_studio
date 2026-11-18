// Tiny DOM builder: h('button', { class: 'x', onclick }, 'text', child). Text is always set as text, never HTML.
export function h(tag, attrs = {}, ...children) {
  const node = document.createElement(tag);
  for (const [key, value] of Object.entries(attrs ?? {})) {
    if (value === undefined || value === null || value === false) continue;
    if (key.startsWith('on')) node.addEventListener(key.slice(2), value);
    else if (key === 'class') node.className = value;
    else if (key === 'dataset') Object.assign(node.dataset, value);
    else node.setAttribute(key, value === true ? '' : value);
  }
  for (const child of children.flat()) {
    if (child === null || child === undefined || child === false) continue;
    node.append(child instanceof Node ? child : document.createTextNode(String(child)));
  }
  return node;
}

// Replaces a node's content, skipping empty children (null, undefined, false) instead of printing "null".
export function fill(node, ...children) {
  node.replaceChildren(...children.flat().filter((child) => child !== null && child !== undefined && child !== false));
}
