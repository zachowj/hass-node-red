"""Constants for Node-RED."""
# Base component constants
DOMAIN = "nodered"
DOMAIN_DATA = f"{DOMAIN}_data"
VERSION = "0.0.1"
REQUIRED_FILES = [
    ".translations/en.json",
    "binary_sensor.py",
    "config_flow.py",
    "const.py",
    "discovery.py",
    "manifest.json",
    "sensor.py",
    "switch.py",
    "websocket.py",
]
ISSUE_URL = "https://github.com/zachowj/hass-node-red/issues"
ATTRIBUTION = "Data from this is provided by Node-RED."

# Configuration
CONF_ATTRIBUTES = "attributes"
CONF_BINARY_SENSOR = "binary_sensor"
CONF_COMPONENT = "component"
CONF_CONFIG = "config"
CONF_CONNECTION = "connection"
CONF_ENABLED = "enabled"
CONF_NAME = "name"
CONF_NODE_ID = "node_id"
CONF_REMOVE = "remove"
CONF_SENSOR = "sensor"
CONF_SERVER_ID = "server_id"
CONF_SWITCH = "switch"

NODERED_DISCOVERY = "nodered_discovery"
NODERED_DISCOVERY_NEW = "nodered_discovery_new_{}"
NODERED_DISCOVERY_UPDATED = "nodered_discovery_updated_{}"
NODERED_ENTITY = "nodered_entity_{}_{}"

# Defaults
DEFAULT_NAME = DOMAIN
SWITCH_ICON = "mdi:electric-switch-closed"
