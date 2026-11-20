// Cable mode bridge (see serial_bridge.h): reads "@" lines from the logger's UART and answers on it.
#include "serial_bridge.h"
#include <driver/uart.h>
#include "esphome/core/application.h"
#include "esphome/components/logger/logger.h"
#include "esphome/components/wifi/wifi_component.h"

namespace esphome::serial_bridge {

static const size_t MAX_LINE = 4096;  // a voice line (@spk) carries ~2 KB of base64 audio
static const uint32_t WIFI_EVERY_MS = 5000;

static std::string clean(std::string text) {
  for (auto &c : text) {
    if (c == '\t' || c == '\n' || c == '\r') c = ' ';
  }
  return text;
}

static std::vector<std::string> split_tabs(const std::string &line) {
  std::vector<std::string> parts;
  size_t start = 0, tab;
  while ((tab = line.find('\t', start)) != std::string::npos) {
    parts.push_back(line.substr(start, tab - start));
    start = tab + 1;
  }
  parts.push_back(line.substr(start));
  return parts;
}

void SerialBridge::setup() {
  this->uart_num_ = logger::global_logger->get_uart_num();
  for (auto *sw : App.get_switches())
    sw->add_on_state_callback([this, sw](bool on) { this->send_state_("switch", sw->get_name().str(), on ? "on" : "off"); });
  for (auto *tx : App.get_texts())
    tx->add_on_state_callback([this, tx](const std::string &value) { this->send_state_("text", tx->get_name().str(), value); });
  for (auto *bt : App.get_buttons())
    bt->add_on_press_callback([this, bt]() { this->send_state_("button", bt->get_name().str(), "pressed"); });
  this->voice_setup_();
}

void SerialBridge::loop() {
  if (this->uart_num_ < 0) return;
  uint8_t chunk[256];  // read in blocks: voice audio arrives at ~60 KB/s
  int got;
  while ((got = uart_read_bytes((uart_port_t) this->uart_num_, chunk, sizeof(chunk), 0)) > 0) {
    for (int i = 0; i < got; i++) {
      uint8_t byte = chunk[i];
      if (byte == '\n') {
        if (!this->buffer_.empty() && this->buffer_[0] == '@') this->handle_line_(this->buffer_);
        this->buffer_.clear();
      } else if (byte != '\r' && this->buffer_.size() < MAX_LINE) {
        this->buffer_ += (char) byte;
      }
    }
  }
  if (millis() - this->last_wifi_ > WIFI_EVERY_MS) this->send_wifi_();
  this->voice_loop_();
}

void SerialBridge::handle_line_(const std::string &line) {
  auto parts = split_tabs(line);
  if (this->handle_voice_(parts)) return;
  if (parts[0] == "@get") return this->send_all_();
  if (parts[0] == "@wifi" && parts.size() == 3) {
    wifi::global_wifi_component->save_wifi_sta(parts[1], parts[2]);
    return this->send_wifi_();
  }
  if (parts[0] != "@set" || parts.size() != 3) return this->send_("@error\tunknown command");
  for (auto *sw : App.get_switches())
    if (sw->get_name() == parts[1]) return parts[2] == "on" ? sw->turn_on() : sw->turn_off();
  for (auto *tx : App.get_texts())
    if (tx->get_name() == parts[1]) return tx->make_call().set_value(parts[2]).perform();
  for (auto *bt : App.get_buttons())
    if (bt->get_name() == parts[1]) return bt->press();
  this->send_("@error\tno entity " + clean(parts[1]));
}

void SerialBridge::send_(const std::string &line) {
  if (this->uart_num_ < 0) return;
  std::string out = line + "\r\n";
  uart_write_bytes((uart_port_t) this->uart_num_, out.data(), out.size());
}

void SerialBridge::send_state_(const char *domain, const std::string &name, const std::string &value) {
  this->send_(std::string("@state\t") + domain + "\t" + clean(name) + "\t" + clean(value));
}

void SerialBridge::send_all_() {
  for (auto *sw : App.get_switches()) this->send_state_("switch", sw->get_name().str(), sw->state ? "on" : "off");
  for (auto *tx : App.get_texts()) this->send_state_("text", tx->get_name().str(), tx->state);
  this->send_wifi_();
}

void SerialBridge::send_wifi_() {
  this->last_wifi_ = millis();
  bool online = wifi::global_wifi_component->is_connected();
  std::string ip;
  if (online) {
    for (auto &address : wifi::global_wifi_component->get_ip_addresses()) {
      if (address.is_ip4() && address.is_set()) {
        char text[network::IP_ADDRESS_BUFFER_SIZE];
        address.str_to(text);
        ip = text;
        break;
      }
    }
  }
  this->send_(std::string("@wifi\t") + (online ? "1" : "0") + "\t" + ip);
}

}  // namespace esphome::serial_bridge
