// Conversation block: scrollable list of user / assistant messages from live.messages.

export function createConversationBlock({ live, t }) {
  let unsubscribe = null;

  function renderList(list, options) {
    list.textContent = '';
    const max = Math.max(1, Number(options.maxMessages) || 20);
    const visible = live.messages.slice(-max);
    if (!visible.length) {
      const empty = document.createElement('p');
      empty.className = 'conversation-empty';
      empty.textContent = t('conversationEmpty');
      list.append(empty);
      return;
    }
    for (const message of visible) {
      const item = document.createElement('div');
      item.className = `conversation-msg conversation-msg-${message.role}`;
      const who = document.createElement('span');
      who.className = 'conversation-who';
      who.textContent = message.role === 'user' ? t('you') : t('assistant');
      const text = document.createElement('p');
      text.className = 'conversation-text';
      text.textContent = message.text;
      item.append(who, text);
      list.append(item);
    }
    list.scrollTop = list.scrollHeight;
  }

  return {
    id: 'conversation',
    title: t('blockConversation'),
    icon: '💬',
    defaultVisible: false,
    defaultColumn: 'side',
    optionsSchema: [
      { key: 'maxMessages', label: t('optMaxMessages'), type: 'number', default: 20, min: 1, max: 100 },
    ],
    render(container, options) {
      const list = document.createElement('div');
      list.className = 'conversation-list';
      container.append(list);
      renderList(list, options);
      unsubscribe?.();
      unsubscribe = live.subscribe(() => renderList(list, options));
    },
    destroy() {
      unsubscribe?.();
      unsubscribe = null;
    },
  };
}
