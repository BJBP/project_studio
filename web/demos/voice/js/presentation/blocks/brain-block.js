// Brain block: lists the AIs the assistant can think with (local or cloud), shows which one is in use,
// switches between them and adds a cloud AI key. Reads/acts through brainChoice; texts come from t().

const KEY_ERRORS = { E_FLOW_INVALID: 'keyRejected', E_KEY_FORMAT: 'keyFormat', E_STUDIO_DOWN: 'studioDown' };

export function createBrainBlock({ live, t, brainChoice }) {
  let unsubscribe = null;
  let openKeyFor = null; // provider id whose key form is open; survives re-renders
  let busy = false;

  const el = (tag, className, text) => {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = text;
    return node;
  };

  function keyForm(brain, rerender) {
    const form = el('form', 'brain-key-form');
    const label = el('label', 'brain-key-label', t('keyLabel').replace('{label}', brain.label));
    const input = el('input', 'talk-input');
    input.type = 'password';
    input.autocomplete = 'off';
    input.required = true;
    label.append(input);
    const save = el('button', 'blocks-button', busy ? t('keySaving') : t('keySave'));
    save.type = 'submit';
    save.disabled = busy;
    const message = el('p', 'brain-key-message');
    message.setAttribute('role', 'status');
    form.append(label, save, message);
    if (brain.keyUrl) {
      const help = el('a', 'brain-key-help', t('keyHelp'));
      help.href = brain.keyUrl;
      help.target = '_blank';
      help.rel = 'noopener noreferrer';
      form.append(help);
    }
    form.addEventListener('submit', async (event) => {
      event.preventDefault();
      busy = true;
      save.disabled = true;
      save.textContent = t('keySaving');
      message.textContent = t('keySavingHint');
      const result = await brainChoice.addKey(brain.id, input.value);
      busy = false;
      input.value = '';
      if (result.ok) { openKeyFor = null; rerender(); return; }
      save.disabled = false;
      save.textContent = t('keySave');
      message.textContent = KEY_ERRORS[result.code] ? t(KEY_ERRORS[result.code]) : `${result.code}: ${result.message}`;
      message.dataset.state = 'error';
    });
    queueMicrotask(() => input.focus());
    return form;
  }

  function row(brain, rerender) {
    const inUse = brainChoice.current?.id === brain.id;
    const item = el('li', 'brain-row');
    item.dataset.state = inUse ? 'current' : brain.status;
    const text = el('div', 'brain-text');
    text.append(el('strong', 'brain-name', brain.label),
      el('span', 'brain-note', brain.cloud ? t('brainCloudNote') : t('brainLocalNote')));
    item.append(text);
    if (inUse) {
      item.append(el('span', 'brain-badge', t('brainInUse')));
    } else if (brain.status === 'ready') {
      const use = el('button', 'blocks-button', t('brainUse'));
      use.type = 'button';
      use.addEventListener('click', () => brainChoice.select(brain.id));
      item.append(use);
    } else if (brain.status === 'needs_key') {
      const add = el('button', 'blocks-button', t('keyAdd'));
      add.type = 'button';
      add.setAttribute('aria-expanded', String(openKeyFor === brain.id));
      add.addEventListener('click', () => { openKeyFor = openKeyFor === brain.id ? null : brain.id; rerender(); });
      item.append(add);
    } else {
      item.append(el('span', 'brain-note', t('brainNotReady')));
    }
    if (openKeyFor === brain.id && brain.status === 'needs_key') item.append(keyForm(brain, rerender));
    return item;
  }

  function render(container) {
    container.textContent = '';
    const brains = brainChoice.brains;
    if (!brains.length) { container.append(el('p', 'brain-note', t('brainNone'))); return; }
    const list = el('ul', 'brain-list');
    for (const brain of brains) list.append(row(brain, () => render(container)));
    container.append(list);
  }

  return {
    id: 'brain',
    title: t('blockBrain'),
    icon: '🧠',
    defaultVisible: true,
    defaultColumn: 'side',
    optionsSchema: [],
    render(container) {
      render(container);
      unsubscribe?.();
      // Re-render on changes, but never under someone typing a key.
      unsubscribe = live.subscribe(() => { if (!busy && !document.activeElement?.closest?.('.brain-key-form')) render(container); });
    },
    destroy() {
      unsubscribe?.();
      unsubscribe = null;
    },
  };
}
