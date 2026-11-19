// Cable mode: talks text lines over the logger's UART (the «COM» connector), next to the normal logs.
// PC -> board:  @get | @set<TAB>name<TAB>value (switch on/off, text, button press) | @wifi<TAB>ssid<TAB>password
// board -> PC:  @state<TAB>domain<TAB>name<TAB>value (on every change and on @get)
//               @wifi<TAB>1|0<TAB>ip (every few seconds) | @error<TAB>what
#pragma once
#include <string>
#include "esphome/core/component.h"

namespace esphome::serial_bridge {

class SerialBridge : public Component {
 public:
  void setup() override;
  void loop() override;
  float get_setup_priority() const override { return setup_priority::AFTER_WIFI; }

 protected:
  void handle_line_(const std::string &line);
  void send_(const std::string &line);
  void send_state_(const char *domain, const std::string &name, const std::string &value);
  void send_all_();
  void send_wifi_();
  std::string buffer_;
  uint32_t last_wifi_{0};
  int uart_num_{-1};
};

}  // namespace esphome::serial_bridge
