// Talk block: push-to-talk button, live level meter, status line and text order input.
// Hold the button (pointer or Space) to listen; release to send to the assistant.

export function createTalkBlock({ live, t, session, speaker }) {
  let unsubscribe = null;
  let unsubscribeLevel = null;
  const dbToPercent = (db) => {
    const value = Number(db);
    if (!Number.isFinite(value)) return 0;
    return Math.min(100, Math.max(0, ((value + 60) / 60) * 100));
  };

  const statusLabel = (key) => ({
    idle: t('statusIdle'),
    listening: t('statusListening'),
    thinking: t('statusThinking'),
    speaking: t('statusSpeaking'),
  }[key] ?? t('statusIdle'));

  function beginHold() {
    session?.startTalking?.();
  }

  function endHold() {
    session?.stopTalking?.();
  }

  function sendWrittenOrder(input, error) {
    const text = input.value.trim();
    if (!text) {
      error.textContent = t('emptyCommand');
      error.hidden = false;
      input.focus();
      return;
    }
    error.hidden = true;
    live.addMessage('user', text);
    session?.sendText?.(text);
    input.value = '';
  }

  return {
    id: 'talk',
    title: t('blockTalk'),
    icon: '🎙️',
    defaultVisible: true,
    defaultColumn: 'side',
    optionsSchema: [
      { key: 'showTextInput', label: t('optShowTextInput'), type: 'boolean', default: true },
      { key: 'volume', label: t('optVolume'), type: 'number', default: 80, min: 0, max: 100 },
    ],
    render(container, options) {
      speaker?.setVolume?.((Number(options.volume) || 0) / 100);

      const hold = document.createElement('button');
      hold.type = 'button';
      hold.className = 'talk-hold';
      hold.textContent = t('holdToTalk');
      hold.addEventListener('pointerdown', (event) => { event.preventDefault(); hold.focus({ preventScroll: true }); hold.setPointerCapture?.(event.pointerId); beginHold(); });
      for (const name of ['pointerup', 'pointercancel', 'lostpointercapture']) {
        hold.addEventListener(name, endHold);
      }
      hold.addEventListener('keydown', (event) => {
        if (event.code === 'Space' && !event.repeat) { event.preventDefault(); beginHold(); }
      });
      hold.addEventListener('keyup', (event) => {
        if (event.code === 'Space') { event.preventDefault(); endHold(); }
      });
      hold.addEventListener('contextmenu', (event) => event.preventDefault());

      const meter = document.createElement('div');
      meter.className = 'talk-meter';
      meter.setAttribute('role', 'meter');
      meter.setAttribute('aria-label', t('levelLabel'));
      meter.setAttribute('aria-valuemin', '0');
      meter.setAttribute('aria-valuemax', '100');
      const fill = document.createElement('div');
      fill.className = 'talk-meter-fill';
      meter.append(fill);

      const statusLine = document.createElement('p');
      statusLine.className = 'talk-status';
      statusLine.setAttribute('aria-live', 'polite');
      statusLine.textContent = statusLabel(live.status);

      const errorLine = document.createElement('p');
      errorLine.className = 'talk-error';
      errorLine.setAttribute('role', 'alert');
      errorLine.hidden = !live.error;
      errorLine.textContent = live.error ?? '';

      const brainLine = document.createElement('p');
      brainLine.className = 'talk-brain';
      const brainText = () => t('brainLine').replace('{label}', live.brain?.label ?? t('brainDefault'));
      brainLine.textContent = brainText();

      container.append(brainLine, hold, meter, statusLine, errorLine);

      if (options.showTextInput !== false) {
        const label = document.createElement('label');
        label.className = 'talk-input-label';
        label.textContent = t('writeCommand');
        const row = document.createElement('div');
        row.className = 'talk-input-row';
        const input = document.createElement('input');
        input.type = 'text';
        input.className = 'talk-input';
        input.placeholder = t('writeCommand');
        input.autocomplete = 'off';
        const send = document.createElement('button');
        send.type = 'button';
        send.className = 'blocks-button talk-send';
        send.textContent = t('send');
        const inputError = document.createElement('p');
        inputError.className = 'talk-error';
        inputError.setAttribute('role', 'alert');
        inputError.hidden = true;
        send.addEventListener('click', () => sendWrittenOrder(input, inputError));
        input.addEventListener('keydown', (event) => { if (event.key === 'Enter') sendWrittenOrder(input, inputError); });
        row.append(input, send);
        container.append(label, row, inputError);
      }

      unsubscribe?.();
      unsubscribeLevel?.();
      unsubscribe = live.subscribe(() => {
        statusLine.textContent = statusLabel(live.status);
        brainLine.textContent = brainText();
        errorLine.hidden = !live.error;
        errorLine.textContent = live.error ?? '';
      });
      unsubscribeLevel = live.subscribeLevel((db) => {
        const percent = dbToPercent(db);
        fill.style.width = `${percent}%`;
        meter.setAttribute('aria-valuenow', String(Math.round(percent)));
      });
    },
    destroy() {
      unsubscribe?.();
      unsubscribeLevel?.();
      unsubscribe = null;
      unsubscribeLevel = null;
    },
  };
}
