// Cable mode: talks text lines over the logger's UART (the «COM» connector), next to the normal logs.
// PC -> board:  @get | @set<TAB>name<TAB>value (switch on/off, text, button press) | @wifi<TAB>ssid<TAB>password
//               voice: @voice<TAB>1|0 (wake word on the cable) | @listen (talk now) | @stop (end of speech)
//               | @play<TAB>rate
//               | @spk<TAB>base64 PCM 16-bit mono | @end (answer finished)
// board -> PC:  @state<TAB>domain<TAB>name<TAB>value (on every change and on @get)
//               @wifi<TAB>1|0<TAB>ip (every few seconds) | @error<TAB>what
//               voice: @listen (wake word heard) | @mic<TAB>base64 PCM 16 kHz 16-bit mono
#pragma once
#include <memory>
#include <string>
#include "esphome/core/component.h"
#include "esphome/core/defines.h"
#ifdef USE_SERIAL_BRIDGE_VOICE
#include "esphome/components/microphone/microphone_source.h"
#include "esphome/components/micro_wake_word/micro_wake_word.h"
#include "esphome/components/ring_buffer/ring_buffer.h"
#include "esphome/components/speaker/speaker.h"
#endif

namespace esphome::serial_bridge {

class SerialBridge : public Component {
 public:
  void setup() override;
  void loop() override;
  float get_setup_priority() const override { return setup_priority::AFTER_WIFI; }
#ifdef USE_SERIAL_BRIDGE_VOICE
  void set_voice(microphone::MicrophoneSource *mic, speaker::Speaker *spk, micro_wake_word::MicroWakeWord *wake) {
    this->mic_ = mic;
    this->speaker_ = spk;
    this->wake_ = wake;
  }
  /// Wake word heard with no Home Assistant connection: stream the microphone to the PC.
  void listen();
  bool voice_enabled() const { return this->voice_enabled_; }
#endif

 protected:
  void handle_line_(const std::string &line);
  bool handle_voice_(const std::vector<std::string> &parts);
  void send_(const std::string &line);
  void send_state_(const char *domain, const std::string &name, const std::string &value);
  void send_all_();
  void send_wifi_();
  void voice_setup_();
  void voice_loop_();
  std::string buffer_;
  uint32_t last_wifi_{0};
  int uart_num_{-1};
#ifdef USE_SERIAL_BRIDGE_VOICE
  void wake_again_();
  microphone::MicrophoneSource *mic_{nullptr};
  speaker::Speaker *speaker_{nullptr};
  micro_wake_word::MicroWakeWord *wake_{nullptr};
  std::unique_ptr<ring_buffer::RingBuffer> mic_ring_;
  bool voice_enabled_{false};
  bool listening_{false};
#endif
};

}  // namespace esphome::serial_bridge
