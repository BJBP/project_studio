// Mounts declared blocks into columns: drag & drop, keyboard moves,
// options forms and persistence. Visible texts come from the `t` object.
// Data is never injected as HTML; DOM is built with createElement/textContent.

import {
  defaultLayout,
  hideBlock,
  mergeWithDefaults,
  moveBlock,
  setOption,
  showBlock,
} from './layout.js';

const ICONS = { drag: '⠿', options: '⚙', hide: '✕' };

export function mountBlocks(root, { blocks, columns, storage, t }) {
  const text = (key, fallback) =>
    (t && typeof t[key] === 'string' && t[key]) || fallback;
  const abort = new AbortController();
  const { signal } = abort;
  const blockById = new Map(blocks.map((block) => [block.id, block]));
  /** @type {Map<string, { element: HTMLElement, body: HTMLElement }>} */
  const mounted = new Map();
  let layout = loadInitialLayout();

  root.textContent = '';
  root.classList.add('blocks-root');

  const toolbar = buildToolbar();
  const board = document.createElement('div');
  board.className = 'blocks-board';
  root.append(toolbar, board);

  const indicator = document.createElement('div');
  indicator.className = 'blocks-drop-indicator';
  indicator.hidden = true;
  board.append(indicator);

  const columnLists = new Map();
  for (const column of columns) {
    const section = document.createElement('section');
    section.className = 'blocks-column';
    section.dataset.columnId = column.id;
    if (column.title) {
      const heading = document.createElement('h2');
      heading.className = 'blocks-column-title';
      heading.textContent = column.title;
      section.append(heading);
    }
    const list = document.createElement('div');
    list.className = 'blocks-column-list';
    list.dataset.columnId = column.id;
    const empty = document.createElement('p');
    empty.className = 'blocks-column-empty';
    empty.textContent = text('emptyColumn', 'Arrastra un bloque aquí');
    list.append(empty);
    wireColumnDrop(list);
    section.append(list);
    board.append(section);
    columnLists.set(column.id, list);
  }

  remountAll();

  return {
    destroy() {
      abort.abort();
      for (const [blockId, entry] of mounted) {
        blockById.get(blockId)?.destroy?.();
        entry.element.remove();
      }
      mounted.clear();
      root.textContent = '';
      root.classList.remove('blocks-root');
    },
  };

  // --- layout state ---------------------------------------------------------

  function loadInitialLayout() {
    const saved = storage?.load?.() ?? null;
    return mergeWithDefaults(saved, blocks, columns);
  }

  function persist() {
    storage?.save?.(layout);
  }

  function applyLayout(next) {
    layout = next;
    persist();
    syncToolbar();
  }

  // --- mounting -------------------------------------------------------------

  function remountAll() {
    for (const [blockId, entry] of mounted) {
      blockById.get(blockId)?.destroy?.();
      entry.element.remove();
    }
    mounted.clear();
    for (const list of columnLists.values()) {
      for (const element of [...list.querySelectorAll('.blocks-block')]) element.remove();
    }
    for (const column of layout.columns) {
      for (const blockId of column.blocks) mountBlock(blockId);
    }
    syncColumnEmptyHints();
  }

  function mountBlock(blockId) {
    const block = blockById.get(blockId);
    if (!block) return;
    const element = buildBlockElement(block);
    const body = element.querySelector('.blocks-block-body');
    mounted.set(blockId, { element, body });
    renderBlock(blockId);
    const columnId = layout.columns.find((column) => column.blocks.includes(blockId))?.id
      ?? columns[0]?.id;
    columnLists.get(columnId)?.append(element);
    syncColumnEmptyHints();
  }

  function renderBlock(blockId) {
    const block = blockById.get(blockId);
    const entry = mounted.get(blockId);
    if (!block || !entry) return;
    block.destroy?.();
    entry.body.textContent = '';
    block.render(entry.body, { ...(layout.options?.[blockId] ?? {}) });
  }

  function unmountBlock(blockId) {
    const entry = mounted.get(blockId);
    if (!entry) return;
    blockById.get(blockId)?.destroy?.();
    entry.element.remove();
    mounted.delete(blockId);
    syncColumnEmptyHints();
  }

  function placeBlockElement(blockId, toColumnId, toIndex) {
    const entry = mounted.get(blockId);
    const list = columnLists.get(toColumnId);
    if (!entry || !list) return;
    const siblings = [...list.querySelectorAll('.blocks-block')].filter(
      (element) => element !== entry.element,
    );
    const reference = siblings[toIndex] ?? null;
    list.insertBefore(entry.element, reference);
    syncColumnEmptyHints();
  }

  function syncColumnEmptyHints() {
    for (const list of columnLists.values()) {
      const hasBlock = list.querySelector('.blocks-block') !== null;
      const empty = list.querySelector('.blocks-column-empty');
      if (empty) empty.hidden = hasBlock;
    }
  }

  // --- block element ----------------------------------------------------------

  function buildBlockElement(block) {
    const element = document.createElement('article');
    element.className = 'blocks-block';
    element.dataset.blockId = block.id;

    const header = document.createElement('header');
    header.className = 'blocks-block-header';

    const handle = document.createElement('button');
    handle.type = 'button';
    handle.className = 'blocks-drag-handle';
    handle.textContent = ICONS.drag;
    handle.draggable = true;
    handle.setAttribute('aria-label', text('dragHandle', 'Arrastrar bloque'));
    handle.title = text('dragHandle', 'Arrastrar bloque');
    wireHandle(handle, block.id);

    const icon = document.createElement('span');
    icon.className = 'blocks-block-icon';
    icon.textContent = block.icon ?? '';
    icon.setAttribute('aria-hidden', 'true');

    const title = document.createElement('h3');
    title.className = 'blocks-block-title';
    title.textContent = block.title ?? block.id;

    const optionsButton = document.createElement('button');
    optionsButton.type = 'button';
    optionsButton.className = 'blocks-icon-button';
    optionsButton.textContent = ICONS.options;
    optionsButton.setAttribute('aria-label', text('showOptions', 'Opciones del bloque'));
    optionsButton.setAttribute('aria-expanded', 'false');

    const hideButton = document.createElement('button');
    hideButton.type = 'button';
    hideButton.className = 'blocks-icon-button';
    hideButton.textContent = ICONS.hide;
    hideButton.setAttribute('aria-label', text('hideBlock', 'Ocultar bloque'));

    header.append(handle, icon, title, optionsButton, hideButton);

    const optionsPanel = document.createElement('div');
    optionsPanel.className = 'blocks-options';
    optionsPanel.hidden = true;
    buildOptionsForm(optionsPanel, block);
    optionsButton.addEventListener('click', () => {
      optionsPanel.hidden = !optionsPanel.hidden;
      optionsButton.setAttribute('aria-expanded', String(!optionsPanel.hidden));
    }, { signal });

    hideButton.addEventListener('click', () => {
      applyLayout(hideBlock(layout, block.id));
      unmountBlock(block.id);
    }, { signal });

    const body = document.createElement('div');
    body.className = 'blocks-block-body';

    element.append(header, optionsPanel, body);
    return element;
  }

  function buildOptionsForm(panel, block) {
    const schema = block.optionsSchema ?? [];
    if (!schema.length) {
      const empty = document.createElement('p');
      empty.className = 'blocks-options-empty';
      empty.textContent = text('noOptions', 'Este bloque no tiene opciones.');
      panel.append(empty);
      return;
    }
    const form = document.createElement('div');
    form.className = 'blocks-options-form';
    for (const field of schema) {
      form.append(buildField(block, field));
    }
    const error = document.createElement('p');
    error.className = 'blocks-options-error';
    error.hidden = true;
    panel.append(form, error);
  }

  function buildField(block, field) {
    const row = document.createElement('label');
    row.className = 'blocks-option-row blocks-option-row-' + field.type;
    const caption = document.createElement('span');
    caption.className = 'blocks-option-label';
    caption.textContent = field.label ?? field.key;
    const input = buildFieldInput(block, field);
    input.className = 'blocks-option-input';
    if (field.type === 'boolean') {
      row.append(input, caption);
    } else {
      row.append(caption, input);
    }
    return row;
  }

  function buildFieldInput(block, field) {
    const current = layout.options?.[block.id]?.[field.key] ?? field.default;
    let input;
    if (field.type === 'boolean') {
      input = document.createElement('input');
      input.type = 'checkbox';
      input.checked = Boolean(current);
      input.addEventListener('change', () => applyOption(block, field, input.checked, input), { signal });
    } else if (field.type === 'number') {
      input = document.createElement('input');
      input.type = 'number';
      if (field.min !== undefined) input.min = String(field.min);
      if (field.max !== undefined) input.max = String(field.max);
      input.value = String(current ?? '');
      input.addEventListener('change', () => {
        const value = input.valueAsNumber;
        applyOption(block, field, Number.isNaN(value) ? undefined : value, input);
      }, { signal });
    } else if (field.type === 'select') {
      input = document.createElement('select');
      for (const choice of field.choices ?? []) {
        const option = document.createElement('option');
        if (choice !== null && typeof choice === 'object') {
          option.value = String(choice.value);
          option.textContent = String(choice.label ?? choice.value);
        } else {
          option.value = String(choice);
          option.textContent = String(choice);
        }
        input.append(option);
      }
      input.value = String(current ?? '');
      input.addEventListener('change', () => applyOption(block, field, input.value, input), { signal });
    } else {
      input = document.createElement('input');
      input.type = 'text';
      input.value = String(current ?? '');
      input.addEventListener('change', () => applyOption(block, field, input.value, input), { signal });
    }
    return input;
  }

  function applyOption(block, field, value, input) {
    const result = setOption(layout, block.optionsSchema, block.id, field.key, value);
    const panel = input.closest('.blocks-options');
    const error = panel?.querySelector('.blocks-options-error');
    if (result?.error === 'E_OPTION_INVALID') {
      if (error) {
        error.textContent = text('optionInvalid', 'Valor no válido.');
        error.hidden = false;
      }
      return;
    }
    if (error) error.hidden = true;
    applyLayout(result);
    renderBlock(block.id);
  }

  // --- toolbar -----------------------------------------------------------------

  function buildToolbar() {
    const bar = document.createElement('div');
    bar.className = 'blocks-toolbar';

    const addWrapper = document.createElement('div');
    addWrapper.className = 'blocks-add-wrapper';
    const addButton = document.createElement('button');
    addButton.type = 'button';
    addButton.className = 'blocks-button';
    addButton.textContent = text('addBlock', '+ Añadir bloque');
    addButton.setAttribute('aria-expanded', 'false');
    addButton.setAttribute('aria-haspopup', 'true');
    const menu = document.createElement('div');
    menu.className = 'blocks-add-menu';
    menu.hidden = true;
    menu.setAttribute('role', 'menu');
    addButton.addEventListener('click', () => {
      menu.hidden = !menu.hidden;
      addButton.setAttribute('aria-expanded', String(!menu.hidden));
      if (!menu.hidden) renderAddMenu(menu);
    }, { signal });
    document.addEventListener('click', (event) => {
      if (!menu.hidden && !addWrapper.contains(event.target)) {
        menu.hidden = true;
        addButton.setAttribute('aria-expanded', 'false');
      }
    }, { signal });
    addWrapper.append(addButton, menu);

    const resetButton = document.createElement('button');
    resetButton.type = 'button';
    resetButton.className = 'blocks-button blocks-button-secondary';
    resetButton.textContent = text('reset', '⟲ Restablecer');
    resetButton.addEventListener('click', () => {
      const message = text('resetConfirm', '¿Restablecer la disposición por defecto?');
      if (!globalThis.confirm?.(message)) return;
      applyLayout(defaultLayout(blocks, columns));
      remountAll();
    }, { signal });

    bar.append(addWrapper, resetButton);
    return bar;
  }

  function renderAddMenu(menu) {
    menu.textContent = '';
    const hiddenBlocks = layout.hidden
      .map((blockId) => blockById.get(blockId))
      .filter(Boolean);
    if (!hiddenBlocks.length) {
      const empty = document.createElement('p');
      empty.className = 'blocks-add-empty';
      empty.textContent = text('noHiddenBlocks', 'No hay bloques ocultos');
      menu.append(empty);
      return;
    }
    for (const block of hiddenBlocks) {
      const item = document.createElement('button');
      item.type = 'button';
      item.className = 'blocks-add-item';
      item.setAttribute('role', 'menuitem');
      const icon = document.createElement('span');
      icon.textContent = block.icon ?? '';
      icon.setAttribute('aria-hidden', 'true');
      const label = document.createElement('span');
      label.textContent = block.title ?? block.id;
      item.append(icon, label);
      item.addEventListener('click', () => {
        const columnId = columns.some((column) => column.id === block.defaultColumn)
          ? block.defaultColumn
          : columns[0]?.id;
        applyLayout(showBlock(layout, block.id, columnId));
        menu.hidden = true;
        mountBlock(block.id);
      }, { signal });
      menu.append(item);
    }
  }

  function syncToolbar() {
    const menu = root.querySelector('.blocks-add-menu');
    if (menu && !menu.hidden) renderAddMenu(menu);
  }

  // --- drag & drop + keyboard ---------------------------------------------------

  function wireHandle(handle, blockId) {
    handle.addEventListener('dragstart', (event) => {
      event.dataTransfer.setData('text/plain', blockId);
      event.dataTransfer.effectAllowed = 'move';
      handle.closest('.blocks-block')?.classList.add('is-dragging');
    }, { signal });
    handle.addEventListener('dragend', () => {
      handle.closest('.blocks-block')?.classList.remove('is-dragging');
      hideIndicator();
      for (const list of columnLists.values()) list.classList.remove('is-drop-target');
    }, { signal });
    handle.addEventListener('keydown', (event) => onHandleKeydown(event, blockId), { signal });
  }

  function wireColumnDrop(list) {
    const columnId = list.dataset.columnId;
    list.addEventListener('dragover', (event) => {
      if (![...(event.dataTransfer?.types ?? [])].includes('text/plain')) return;
      event.preventDefault();
      event.dataTransfer.dropEffect = 'move';
      list.classList.add('is-drop-target');
      showIndicator(list, dropIndex(list, event.clientY));
    }, { signal });
    list.addEventListener('dragleave', (event) => {
      if (event.relatedTarget && list.contains(event.relatedTarget)) return;
      list.classList.remove('is-drop-target');
      hideIndicator();
    }, { signal });
    list.addEventListener('drop', (event) => {
      event.preventDefault();
      const blockId = event.dataTransfer.getData('text/plain');
      const index = dropIndex(list, event.clientY);
      list.classList.remove('is-drop-target');
      hideIndicator();
      if (!blockId || !blockById.has(blockId)) return;
      applyLayout(moveBlock(layout, blockId, columnId, index));
      placeBlockElement(blockId, columnId, index);
    }, { signal });
  }

  function dropIndex(list, clientY) {
    const elements = [...list.querySelectorAll('.blocks-block:not(.is-dragging)')];
    for (let index = 0; index < elements.length; index += 1) {
      const box = elements[index].getBoundingClientRect();
      if (clientY < box.top + box.height / 2) return index;
    }
    return elements.length;
  }

  function showIndicator(list, index) {
    const elements = [...list.querySelectorAll('.blocks-block:not(.is-dragging)')];
    const reference = elements[index] ?? null;
    indicator.hidden = false;
    list.insertBefore(indicator, reference);
  }

  function hideIndicator() {
    indicator.hidden = true;
    indicator.remove();
  }

  function onHandleKeydown(event, blockId) {
    const keys = ['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'];
    if (!keys.includes(event.key)) return;
    const currentColumnId = layout.columns.find((column) => column.blocks.includes(blockId))?.id;
    if (!currentColumnId) return;
    const column = layout.columns.find((entry) => entry.id === currentColumnId);
    const index = column.blocks.indexOf(blockId);
    let targetColumnId = currentColumnId;
    let targetIndex = index;

    if (event.key === 'ArrowUp') targetIndex = index - 1;
    if (event.key === 'ArrowDown') targetIndex = index + 1;
    if (event.key === 'ArrowLeft' || event.key === 'ArrowRight') {
      const columnIds = layout.columns.map((entry) => entry.id);
      const position = columnIds.indexOf(currentColumnId);
      const offset = event.key === 'ArrowLeft' ? -1 : 1;
      const neighbour = layout.columns[position + offset];
      if (!neighbour) return;
      targetColumnId = neighbour.id;
      targetIndex = Math.min(index, neighbour.blocks.length);
    }

    if (targetColumnId === currentColumnId
      && (targetIndex < 0 || targetIndex >= column.blocks.length)) return;

    event.preventDefault();
    applyLayout(moveBlock(layout, blockId, targetColumnId, targetIndex));
    placeBlockElement(blockId, targetColumnId, targetIndex);
    mounted.get(blockId)?.element.querySelector('.blocks-drag-handle')?.focus();
  }
}
