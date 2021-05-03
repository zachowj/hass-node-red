"""Constants for Node-RED."""
# Base component constants
DOMAIN = "nodered"
DOMAIN_DATA = f"{DOMAIN}_data"
VERSION = "0.5.2"

ISSUE_URL = "https://github.com/zachowj/hass-node-red/issues"

# Configuration
CONF_ATTRIBUTES = "attributes"
CONF_BINARY_SENSOR = "binary_sensor"
CONF_COMPONENT = "component"
CONF_CONFIG = "config"
CONF_CONNECTION = "connection"
CONF_DATA = "data"
CONF_DEVICE_INFO = "device_info"
CONF_DEVICE_TRIGGER = "device_trigger"
CONF_ENABLED = "enabled"
CONF_NAME = "name"
CONF_NODE_ID = "node_id"
CONF_OUTPUT_PATH = "output_path"
CONF_PAYLOAD = "payload"
CONF_REMOVE = "remove"
CONF_SENSOR = "sensor"
CONF_SERVER_ID = "server_id"
CONF_SKIP_CONDITION = "skip_condition"
CONF_SUB_TYPE = "sub_type"
CONF_SWITCH = "switch"
CONF_TRIGGER_ENTITY_ID = "trigger_entity_id"
CONF_VERSION = "version"

NODERED_DISCOVERY = "nodered_discovery"
NODERED_DISCOVERY_NEW = "nodered_discovery_new_{}"
NODERED_DISCOVERY_UPDATED = "nodered_discovery_updated_{}"
NODERED_ENTITY = "nodered_entity_{}_{}"

SERVICE_TRIGGER = "trigger"

# Defaults
NAME = DOMAIN
SWITCH_ICON = "mdi:electric-switch-closed"

STARTUP_MESSAGE = f"""
-------------------------------------------------------------------
{NAME}
Version: {VERSION}
This is a custom integration!
If you have any issues with this you need to open an issue here:
{ISSUE_URL}
-------------------------------------------------------------------
"""
