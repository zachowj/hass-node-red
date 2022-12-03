This integration will give Node-RED the ability to create/update binary sensors, sensors and switches in Home Assistant. Event nodes in Node-RED can be exposed to Home Assistant as switches which will allow them to enable and disable flows from the Home Assistant UI or service calls.

_Must have [node-red-contrib-home-assistant-websocket](https://github.com/zachowj/node-red-contrib-home-assistant-websocket) installed in Node-RED. (minimum version 0.20)_

## Features

- Create and update binary sensors, sensors, and switches from Node-RED
- Disable and enable Node-RED flows from Home Assistant UI
- Create Home Assistant webhooks and handle them in Node-RED
- Use Device triggers and action from Node-RED

## Installation

1. Click install.
2. Restart Home Assistant
3. Refresh your browser window (bug in HA where it doesn't update the integration list after a reboot)
4. In the Home Assistant UI go to "Configuration" -> "Integrations" click "+" and search for "Node-RED"

## Configuration

Once installed and added via Integrations all configuration is done from Node-RED.

---

[![Buy me a coffee](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://buymeacoff.ee/zachowj)
