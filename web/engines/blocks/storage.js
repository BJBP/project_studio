// localStorage-backed persistence for block layouts.
// Failures are reported through console.warn and never thrown.

export function createStorage(key) {
  return {
    load() {
      try {
        const store = globalThis.localStorage;
        if (!store) {
          console.warn(`blocks storage: localStorage is not available; "${key}" was not loaded`);
          return null;
        }
        const raw = store.getItem(key);
        return raw ? JSON.parse(raw) : null;
      } catch (error) {
        console.warn(`blocks storage: could not load "${key}": ${error?.message ?? error}`);
        return null;
      }
    },
    save(layout) {
      try {
        const store = globalThis.localStorage;
        if (!store) {
          console.warn(`blocks storage: localStorage is not available; "${key}" was not saved`);
          return false;
        }
        store.setItem(key, JSON.stringify(layout));
        return true;
      } catch (error) {
        console.warn(`blocks storage: could not save "${key}": ${error?.message ?? error}`);
        return false;
      }
    },
  };
}
