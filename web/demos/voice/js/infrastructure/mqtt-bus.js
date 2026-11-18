// MQTT over WebSocket pub/sub bus on top of the global `mqtt` (web/vendor/mqtt.min.js).
// createMqttBus({ url, clientId, will }) -> { connect, publish, subscribe, close }.
// Failures are reported as { code: 'E_...', message } objects with Spanish, actionable text.

const CONNECT_TIMEOUT_MS = 5000;

export function createMqttBus({ url, clientId, will } = {}) {
  let client = null;
  let subscriptions = [];
  let pendingSubscriptions = [];

  function connect() {
    return new Promise((resolve, reject) => {
      const mqttLib = globalThis.mqtt;
      if (!mqttLib || typeof mqttLib.connect !== 'function') {
        reject({ code: 'E_MQTT_DOWN', message: 'La librería MQTT no está cargada. Recarga la página.' });
        return;
      }
      const options = { clientId, reconnectPeriod: 0 };
      if (will && will.topic) options.will = normalizeWill(will);
      const instance = mqttLib.connect(url, options);
      client = instance;
      const timer = setTimeout(() => down(instance, reject, url), CONNECT_TIMEOUT_MS);
      instance.on('connect', () => {
        clearTimeout(timer);
        flushPendingSubscriptions();
        resolve();
      });
      instance.on('error', () => {
        clearTimeout(timer);
        instance.end(true);
        reject(downError(url));
      });
      instance.on('message', (topic, payloadBuffer) => deliverMessage(topic, payloadBuffer));
    });
  }

  function publish(topic, payload, { retain } = {}) {
    if (!client) {
      throw { code: 'E_MQTT_DOWN', message: 'MQTT no está conectado. Llama a connect() primero.' };
    }
    const data = typeof payload === 'string' ? payload : JSON.stringify(payload);
    client.publish(topic, data, { retain: Boolean(retain) });
  }

  function subscribe(topicFilter, handler) {
    if (typeof handler !== 'function') {
      throw new TypeError('subscribe: handler must be a function');
    }
    if (client) {
      subscriptions.push({ filter: topicFilter, handler });
      client.subscribe(topicFilter);
    } else {
      pendingSubscriptions.push({ filter: topicFilter, handler });
    }
  }

  function close() {
    subscriptions = [];
    pendingSubscriptions = [];
    if (client) {
      try {
        client.end();
      } catch (err) {
        console.warn('mqtt-bus: error al cerrar el cliente', err);
      }
      client = null;
    }
  }

  function flushPendingSubscriptions() {
    const pending = pendingSubscriptions;
    pendingSubscriptions = [];
    for (const { filter, handler } of pending) subscribe(filter, handler);
  }

  function deliverMessage(topic, payloadBuffer) {
    const payloadString = payloadBuffer == null ? '' : payloadBuffer.toString();
    for (const { filter, handler } of subscriptions) {
      if (topicMatches(filter, topic)) handler(topic, payloadString);
    }
  }

  return { connect, publish, subscribe, close };
}

function normalizeWill(will) {
  const normalized = { ...will };
  if (normalized.payload && typeof normalized.payload === 'object') {
    normalized.payload = JSON.stringify(normalized.payload);
  }
  return normalized;
}

function down(instance, reject, url) {
  try {
    instance.end(true);
  } catch (err) {
    console.warn('mqtt-bus: error al abortar la conexión', err);
  }
  reject(downError(url));
}

function downError(url) {
  return { code: 'E_MQTT_DOWN', message: `No conecta con MQTT en ${url}. ¿Está arrancado el stack?` };
}

export function topicMatches(filter, topic) {
  const filterParts = filter.split('/');
  const topicParts = topic.split('/');
  for (let i = 0; i < filterParts.length; i += 1) {
    const part = filterParts[i];
    if (part === '#') return true;
    if (topicParts[i] === undefined) return false;
    if (part !== '+' && part !== topicParts[i]) return false;
  }
  return filterParts.length === topicParts.length;
}
