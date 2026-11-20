# serial_bridge: the board's entities, Wi-Fi and (optionally) voice over the USB cable (the logger's UART), for the
# Studio's cable mode. Lines that start with "@" are the bridge's; everything else stays as normal log text.
# Protocol in serial_bridge.h. With microphone + speaker + micro_wake_word, "Okay Nabu" works over the cable too.
import esphome.codegen as cg
from esphome.components import microphone, speaker
import esphome.config_validation as cv
from esphome.const import CONF_ID, CONF_MICROPHONE, CONF_SPEAKER

DEPENDENCIES = ["logger", "wifi"]
AUTO_LOAD = ["ring_buffer"]
CODEOWNERS = []
CONF_MICRO_WAKE_WORD = "micro_wake_word"

serial_bridge_ns = cg.esphome_ns.namespace("serial_bridge")
SerialBridge = serial_bridge_ns.class_("SerialBridge", cg.Component)
MicroWakeWord = cg.esphome_ns.namespace("micro_wake_word").class_("MicroWakeWord", cg.Component)

CONFIG_SCHEMA = cv.All(
    cv.Schema({
        cv.GenerateID(): cv.declare_id(SerialBridge),
        cv.Optional(CONF_MICROPHONE): microphone.microphone_source_schema(min_bits_per_sample=16, max_bits_per_sample=16),
        cv.Optional(CONF_SPEAKER): cv.use_id(speaker.Speaker),
        cv.Optional(CONF_MICRO_WAKE_WORD): cv.use_id(MicroWakeWord),
    }).extend(cv.COMPONENT_SCHEMA),
    cv.has_none_or_all_keys(CONF_MICROPHONE, CONF_SPEAKER, CONF_MICRO_WAKE_WORD),
)

FINAL_VALIDATE_SCHEMA = cv.Schema(
    {cv.Optional(CONF_MICROPHONE): microphone.final_validate_microphone_source_schema("serial_bridge", sample_rate=16000)},
    extra=cv.ALLOW_EXTRA,
)


async def to_code(config):
    var = cg.new_Pvariable(config[CONF_ID])
    await cg.register_component(var, config)
    if CONF_MICROPHONE in config:
        cg.add_define("USE_SERIAL_BRIDGE_VOICE")
        cg.add(var.set_voice(await microphone.microphone_source_to_code(config[CONF_MICROPHONE]),
                             await cg.get_variable(config[CONF_SPEAKER]),
                             await cg.get_variable(config[CONF_MICRO_WAKE_WORD])))
