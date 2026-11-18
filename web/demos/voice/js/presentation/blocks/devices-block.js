// Devices block: lists every entity of every device with its current state and actions.
// Switches toggle via virtualDevice.command; buttons send a PRESS command; locks open/close; simulated
// sensors get a «Simular» button (simulator.pulse) that acts like the real thing for a few seconds.

export function createDevicesBlock({ live, t, catalog, virtualDevice, simulator }) {
  let unsubscribe = null;

  const displayState = (entity, value) => {
    if (entity.component === 'switch') return String(value).toUpperCase() === 'ON' ? t('switchOn') : t('switchOff');
    if (entity.component === 'binary_sensor') return t(`binary.${entity.device_class ?? 'default'}.${value === 'ON' ? 'on' : 'off'}`);
    if (entity.component === 'lock') return value === 'LOCKED' ? t('lockLocked') : t('lockUnlocked');
    if (value === null || value === undefined || value === '') return t('noReading');
    return entity.unit ? `${value} ${entity.unit}` : String(value);
  };

  function buildRow(device, entity) {
    const state = live.state?.[device.id] ?? {};
    const value = state[entity.key];

    const row = document.createElement('div');
    row.className = 'device-entity';
    row.dataset.key = entity.key;

    const name = document.createElement('span');
    name.className = 'device-entity-name';
    name.textContent = entity.name ?? entity.key;

    const valueLabel = document.createElement('span');
    valueLabel.className = 'device-entity-value';
    valueLabel.textContent = entity.component === 'button' ? '' : displayState(entity, value);

    row.append(name, valueLabel);

    const action = (label, onClick) => Object.assign(document.createElement('button'), {
      type: 'button', className: 'blocks-button device-entity-action', textContent: label, onclick: onClick,
    });
    if (entity.component === 'lock') {
      const locked = value === 'LOCKED';
      row.append(action(locked ? t('lockOpen') : t('lockClose'), () => virtualDevice?.command(device.id, entity.key, locked ? 'UNLOCK' : 'LOCK')));
    } else if ((entity.sim && entity.sim.type !== 'drift') || entity.sim?.test !== undefined) {
      row.append(action(t('simulate'), () => simulator?.pulse(device.id, entity.key)));
    }
    if (entity.component === 'switch' || entity.component === 'button') {
      const action = document.createElement('button');
      action.type = 'button';
      action.className = 'blocks-button device-entity-action';
      if (entity.component === 'switch') {
        const isOn = String(value).toUpperCase() === 'ON';
        action.textContent = isOn ? t('turnOff') : t('turnOn');
        action.addEventListener('click', () => virtualDevice?.command(device.id, entity.key, isOn ? 'OFF' : 'ON'));
      } else {
        action.textContent = t('testButton');
        action.addEventListener('click', () => virtualDevice?.command(device.id, entity.key, 'PRESS'));
      }
      row.append(action);
    }
    return row;
  }

  function renderCatalog(container) {
    container.textContent = '';
    for (const device of catalog?.devices ?? []) {
      const section = document.createElement('section');
      section.className = 'devices-device';
      const heading = document.createElement('h4');
      heading.className = 'devices-device-name';
      heading.textContent = [device.name, device.area].filter(Boolean).join(' · ');
      section.append(heading);
      for (const entity of device.entities ?? []) section.append(buildRow(device, entity));
      container.append(section);
    }
  }

  return {
    id: 'devices',
    title: t('blockDevices'),
    icon: '🎛️',
    defaultVisible: false,
    defaultColumn: 'main',
    optionsSchema: [],
    render(container) {
      renderCatalog(container);
      unsubscribe?.();
      unsubscribe = live.subscribe(() => renderCatalog(container));
    },
    destroy() {
      unsubscribe?.();
      unsubscribe = null;
    },
  };
}
