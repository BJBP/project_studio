// AudioWorkletProcessor that forwards every input block to the main thread unchanged.
// Loaded via audioWorklet.addModule(); posts Float32Array copies through this.port.
class StudioMicProcessor extends AudioWorkletProcessor {
  process(inputs) {
    const channel = inputs && inputs[0] && inputs[0][0];
    if (channel && channel.length) {
      this.port.postMessage(channel.slice(0));
    }
    return true;
  }
}

registerProcessor('studio-mic', StudioMicProcessor);
