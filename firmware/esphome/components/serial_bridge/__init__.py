# serial_bridge: the board's entities and Wi-Fi over the USB cable (the logger's UART), for the Studio's cable mode.
# Lines that start with "@" are the bridge's; everything else stays as normal log text. Protocol in serial_bridge.h.
import esphome.codegen as cg
import esphome.config_validation as cv
from esphome.const import CONF_ID

DEPENDENCIES = ["logger", "wifi"]
CODEOWNERS = []

serial_bridge_ns = cg.esphome_ns.namespace("serial_bridge")
SerialBridge = serial_bridge_ns.class_("SerialBridge", cg.Component)

CONFIG_SCHEMA = cv.Schema({cv.GenerateID(): cv.declare_id(SerialBridge)}).extend(cv.COMPONENT_SCHEMA)


async def to_code(config):
    var = cg.new_Pvariable(config[CONF_ID])
    await cg.register_component(var, config)
