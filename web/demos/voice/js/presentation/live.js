// Shared mutable UI state for the voice demo blocks.
// createLiveStore(initialState) -> { state, answer, status, error, level, messages, subscribe, subscribeLevel, ... }.

export function createLiveStore(initialState) {
  const store = {
    state: initialState,
    answer: '',
    status: 'idle',
    error: null,
    level: null,
    lastEvent: null,
    messages: [],
    listeners: new Set(),
    levelListeners: new Set(),
  };

  store.subscribe = (fn) => {
    store.listeners.add(fn);
    return () => store.listeners.delete(fn);
  };
  store.subscribeLevel = (fn) => {
    store.levelListeners.add(fn);
    return () => store.levelListeners.delete(fn);
  };
  store.emit = () => {
    for (const fn of [...store.listeners]) fn();
  };
  store.emitLevel = () => {
    for (const fn of [...store.levelListeners]) fn(store.level);
  };
  store.addMessage = (role, text) => {
    const clean = String(text ?? '').trim();
    if (!clean) return;
    store.messages.push({ role, text: clean });
    if (store.messages.length > 100) store.messages.shift();
    store.emit();
  };
  return store;
}
