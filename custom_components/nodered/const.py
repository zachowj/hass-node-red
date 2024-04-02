"""Constants for Node-RED."""
from .version import __version__ as VERSION

# Base component constants
DOMAIN = "nodered"
DOMAIN_DATA = f"{DOMAIN}_data"

ISSUE_URL = "https://github.com/zachowj/hass-node-red/issues"

# Configuration
CONF_ATTRIBUTES = "attributes"
CONF_BINARY_SENSOR = "binary_sensor"
CONF_BUTTON = "button"
CONF_COMPONENT = "component"
CONF_CONFIG = "config"
CONF_CONNECTION = "connection"
CONF_DATA = "data"
CONF_DEVICE_INFO = "device_info"
CONF_DEVICE_TRIGGER = "device_trigger"
CONF_ENABLED = "enabled"
CONF_ENTITY_PICTURE = "entity_picture"
CONF_LAST_RESET = "last_reset"
CONF_MESSAGE = "message"
CONF_NAME = "name"
CONF_NODE_ID = "node_id"
CONF_NUMBER = "number"
CONF_OPTIONS = "options"
CONF_OUTPUT_PATH = "output_path"
CONF_REMOVE = "remove"
CONF_SELECT = "select"
CONF_SENSOR = "sensor"
CONF_SERVER_ID = "server_id"
CONF_SKIP_CONDITION = "skip_condition"
CONF_STATE_CLASS = "state_class"
CONF_SUB_TYPE = "sub_type"
CONF_SWITCH = "switch"
CONF_TEXT = "text"
CONF_TIME = "time"
CONF_TRIGGER_ENTITY_ID = "trigger_entity_id"
CONF_VERSION = "version"

EVENT_VALUE_CHANGE = "value_change"

NODERED_DISCOVERY = "nodered_discovery"
NODERED_DISCOVERY_NEW = "nodered_discovery_new_{}"
NODERED_DISCOVERY_UPDATED = "nodered_discovery_updated_{}"
NODERED_ENTITY = "nodered_entity_{}_{}"
NODERED_CONFIG_UPDATE = "nodered_config_update_{}_{}"

SERVICE_TRIGGER = "trigger"

# Defaults
NAME = "Node-RED Companion"
NUMBER_ICON = "mdi:numeric"
SWITCH_ICON = "mdi:electric-switch-closed"
SELECT_ICON = "mdi:format-list-bulleted"
TEXT_ICON = "mdi:form-textbox"
TIME_ICON = "mdi:clock-time-three"

STARTUP_MESSAGE = f"""
-------------------------------------------------------------------
{NAME}
Version: {VERSION}
This is a custom integration!
If you have any issues with this you need to open an issue here:
{ISSUE_URL}
-------------------------------------------------------------------
"""
