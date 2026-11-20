// Cable voice (see serial_bridge.h): "Okay Nabu" on the board, the microphone to the PC as @mic lines, and the PC's
// spoken answer to the speaker as @spk lines. The PC runs the Home Assistant pipeline; the board only moves audio.
#include "serial_bridge.h"
#include <driver/uart.h>
#include "esphome/core/alloc_helpers.h"
#include "esphome/core/helpers.h"
#include "esphome/core/log.h"

namespace esphome::serial_bridge {

#ifdef USE_SERIAL_BRIDGE_VOICE
static const char *const TAG = "serial_bridge.voice";
static const size_t RX_BUFFER = 16384;    // ~270 ms of answer audio: the main loop reads it every few ms
static const size_t TX_BUFFER = 8192;     // microphone lines go out while logs keep flowing
static const size_t MIC_RING = 32000;     // 1 s of 16 kHz 16-bit audio between the mic task and the loop
static const size_t MIC_CHUNK = 1536;     // per @mic line (2 KB of base64)

void SerialBridge::voice_setup_() {
  if (this->uart_num_ < 0 || this->mic_ == nullptr) return;
  // The logger installs its UART with a 129-byte receive buffer; audio from the PC needs room.
  uart_driver_delete((uart_port_t) this->uart_num_);
  uart_driver_install((uart_port_t) this->uart_num_, RX_BUFFER, TX_BUFFER, 0, nullptr, 0);
  this->mic_ring_ = ring_buffer::RingBuffer::create(MIC_RING);
  this->mic_->add_data_callback([this](const microphone::AudioCapture &capture) {
    if (this->listening_ && this->mic_ring_) this->mic_ring_->write(capture.data.data(), capture.data.size());
  });
}

void SerialBridge::listen() {
  if (!this->voice_enabled_ || this->listening_) return;
  this->wake_->stop();
  this->mic_ring_->reset();
  this->listening_ = true;
  this->mic_->start();
  this->send_("@listen");
}

void SerialBridge::wake_again_() {
  if (this->voice_enabled_ && !this->wake_->is_running()) this->wake_->start();
}

void SerialBridge::voice_loop_() {
  if (!this->listening_ || !this->mic_ring_) return;
  uint8_t data[MIC_CHUNK];
  size_t got;
  while ((got = this->mic_ring_->read(data, sizeof(data), 0)) > 0) this->send_("@mic\t" + base64_encode(data, got));
}

bool SerialBridge::handle_voice_(const std::vector<std::string> &parts) {
  if (this->mic_ == nullptr) return false;
  const std::string &cmd = parts[0];
  if (cmd == "@spk" && parts.size() == 2) {
    std::vector<uint8_t> pcm(parts[1].size() * 3 / 4 + 4);
    size_t length = base64_decode(parts[1], pcm.data(), pcm.size());
    if (this->speaker_->play(pcm.data(), length, 0) < length) ESP_LOGW(TAG, "speaker full: audio dropped");
  } else if (cmd == "@voice" && parts.size() == 2) {
    this->voice_enabled_ = parts[1] == "1";
    if (this->voice_enabled_) this->wake_again_(); else this->wake_->stop();
  } else if (cmd == "@listen") {  // "talk now" from the Studio, without the wake word
    this->listen();
  } else if (cmd == "@stop") {
    this->listening_ = false;
    this->mic_->stop();
  } else if (cmd == "@play" && parts.size() == 2) {
    this->speaker_->set_audio_stream_info(audio::AudioStreamInfo(16, 1, (uint32_t) atoi(parts[1].c_str())));
    this->speaker_->start();
  } else if (cmd == "@end") {
    this->listening_ = false;
    this->mic_->stop();
    this->speaker_->finish();
    this->wake_again_();
  } else {
    return false;
  }
  return true;
}
#else
void SerialBridge::voice_setup_() {}
void SerialBridge::voice_loop_() {}
bool SerialBridge::handle_voice_(const std::vector<std::string> &parts) { return false; }
#endif

}  // namespace esphome::serial_bridge
