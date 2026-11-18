// USB or built-in camera through the browser. createCamera({ onFrame(gray), width, height, fps }) -> { start(video), stop }.
// Each frame is shrunk to width×height grayscale; the image never leaves the browser.
export function createCamera({ onFrame, width = 64, height = 48, fps = 4 }) {
  let stream = null, timer = null;
  const canvas = Object.assign(document.createElement('canvas'), { width, height });
  const context = canvas.getContext('2d', { willReadFrequently: true });

  async function start(video) {
    if (!navigator.mediaDevices?.getUserMedia) {
      throw { code: 'E_CAMERA_UNSUPPORTED', message: 'Este navegador no da acceso a la cámara. Usa Chrome o Edge.' };
    }
    try {
      stream = await navigator.mediaDevices.getUserMedia({ video: { width: 320, height: 240 }, audio: false });
    } catch (error) {
      throw { code: 'E_CAMERA_DENIED', message: 'No hay permiso para la cámara o está en uso. Revisa el permiso del navegador.' };
    }
    video.srcObject = stream;
    await video.play().catch(() => {});
    timer = setInterval(() => {
      context.drawImage(video, 0, 0, width, height);
      const rgba = context.getImageData(0, 0, width, height).data;
      const gray = new Uint8Array(width * height);
      for (let i = 0; i < gray.length; i += 1) gray[i] = (rgba[i * 4] + rgba[i * 4 + 1] + rgba[i * 4 + 2]) / 3;
      onFrame(gray);
    }, 1000 / fps);
  }

  function stop() {
    clearInterval(timer);
    timer = null;
    for (const track of stream?.getTracks() ?? []) track.stop();
    stream = null;
  }

  return { start, stop };
}
