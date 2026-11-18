// Guided tour engine, shared by the Help tour and the self-running presentation.
// createTour({ t, speak(text) -> Promise<audio url|null>, runAction(action) -> Promise }) -> { play(scenes), stop() }.
// A scene: { route?, text, highlight? (CSS selector), action?, pause_ms? }. A failed action is announced and skipped.
const WAIT_FOR_ELEMENT_MS = 4000;
const MS_PER_CHAR = 55; // reading time when the voice is off

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

export function createTour({ t, speak, runAction }) {
  let bar = null, scenes = [], index = 0, paused = false, muted = false, speed = 1, run = 0, audio = null;

  function button(label, title, onClick) {
    const node = Object.assign(document.createElement('button'), { type: 'button', className: 'tour-button', textContent: label, title });
    node.setAttribute('aria-label', title);
    node.addEventListener('click', onClick);
    return node;
  }

  function buildBar() {
    bar = document.createElement('div');
    bar.className = 'tour-bar';
    bar.setAttribute('role', 'dialog');
    bar.setAttribute('aria-label', t('tourLabel'));
    const text = Object.assign(document.createElement('p'), { className: 'tour-text' });
    text.setAttribute('aria-live', 'polite');
    const step = Object.assign(document.createElement('span'), { className: 'tour-step' });
    const pauseButton = button('⏸', t('tourPause'), () => { paused = !paused; pauseButton.textContent = paused ? '▶' : '⏸'; if (paused) audio?.pause(); else audio?.play(); });
    const muteButton = button('🔊', t('tourMute'), () => { muted = !muted; muteButton.textContent = muted ? '🔇' : '🔊'; if (muted) audio?.pause(); });
    const speedSelect = document.createElement('select');
    speedSelect.className = 'tour-speed';
    speedSelect.setAttribute('aria-label', t('tourSpeed'));
    for (const value of [1, 1.5, 2]) speedSelect.append(new Option(`${value}x`, value));
    speedSelect.addEventListener('change', () => { speed = Number(speedSelect.value); });
    const controls = Object.assign(document.createElement('div'), { className: 'tour-controls' });
    controls.append(button('⏮', t('tourPrev'), () => go(index - 1)), pauseButton, button('⏭', t('tourNext'), () => go(index + 1)),
      step, muteButton, speedSelect, button('✕', t('tourClose'), stop));
    bar.append(text, controls);
    document.body.append(bar);
    document.addEventListener('keydown', onKey);
  }

  const onKey = (event) => { if (event.key === 'Escape') stop(); };

  function clearHighlight() {
    for (const node of document.querySelectorAll('.tour-highlight')) node.classList.remove('tour-highlight');
  }

  async function findElement(selector) {
    const deadline = Date.now() + WAIT_FOR_ELEMENT_MS;
    while (Date.now() < deadline) {
      const node = document.querySelector(selector);
      if (node) return node;
      await sleep(150);
    }
    return null;
  }

  async function waitWhilePaused(myRun) {
    while (paused && myRun === run) await sleep(200);
  }

  async function narrate(text, myRun) {
    const url = muted ? null : await speak(text).catch(() => null);
    if (myRun !== run) return;
    if (!url || muted) { await sleep((text.length * MS_PER_CHAR) / speed); return; }
    audio = new Audio(url);
    audio.playbackRate = speed;
    await new Promise((resolve) => {
      audio.addEventListener('ended', resolve, { once: true });
      audio.addEventListener('error', resolve, { once: true });
      audio.play().catch(resolve);
    });
    audio = null;
  }

  async function showScene(myRun) {
    const scene = scenes[index];
    bar.querySelector('.tour-step').textContent = t('tourStep', { n: index + 1, total: scenes.length });
    bar.querySelector('.tour-text').textContent = scene.text;
    clearHighlight();
    if (scene.route && location.hash !== scene.route) location.hash = scene.route;
    if (scene.highlight) {
      const node = await findElement(scene.highlight);
      node?.classList.add('tour-highlight');
      node?.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
    await narrate(scene.text, myRun);
    await waitWhilePaused(myRun);
    if (scene.action && myRun === run) {
      try {
        await runAction(scene.action);
      } catch (error) {
        bar?.querySelector('.tour-text')?.append(` ${t('tourActionFailed', { reason: error?.message ?? error })}`);
      }
    }
    await sleep((scene.pause_ms ?? 600) / speed);
  }

  async function go(target) {
    if (!bar || target < 0) return;
    if (target >= scenes.length) { stop(); return; }
    index = target;
    run += 1;
    const myRun = run;
    audio?.pause();
    audio = null;
    await showScene(myRun);
    if (myRun === run) go(index + 1);
  }

  function play(list) {
    stop();
    scenes = list;
    paused = false;
    buildBar();
    go(0);
  }

  function stop() {
    run += 1;
    audio?.pause();
    audio = null;
    clearHighlight();
    document.removeEventListener('keydown', onKey);
    bar?.remove();
    bar = null;
  }

  return { play, stop };
}
