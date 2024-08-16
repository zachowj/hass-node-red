# Node-RED Companion Integration

[![hacs][hacsbadge]][hacs] [![releasebadge]][release] [![Build Status][buildstatus-shield]][buildstatus-link] [![License][license-shield]](LICENSE.md)

[![BuyMeCoffee][buymecoffeebadge]][buymecoffee]

_Companion Component to [node-red-contrib-home-assistant-websocket](https://github.com/zachowj/node-red-contrib-home-assistant-websocket) for seamless integration of Node-RED with Home Assistant._

## Overview

The Node-RED Companion Integration bridges Node-RED and Home Assistant, allowing you to manage Home Assistant entities and automations directly from Node-RED. This integration enhances your smart home automation setup by enabling dynamic interaction between these two powerful tools.

## Key Features

- **Entity Management:**
  - Create and update Home Assistant entities from Node-RED, including:
    - Binary Sensors
    - Buttons
    - Numbers
    - Selects
    - Sensors
    - Switches
    - Text fields
- **Flow Control:**
  - Enable or disable Node-RED flows directly from the Home Assistant UI.
- **Webhooks:**
  - Create and manage Home Assistant webhooks, with handling in Node-RED.
- **Device Automation:**
  - Utilize device triggers and actions within Node-RED for advanced automation capabilities.

## Minimum Requirements

- [node-red-contrib-home-assistant-websocket](https://github.com/zachowj/node-red-contrib-home-assistant-websocket) v0.57+
- [Home Assistant](https://github.com/home-assistant/core) 2024.5+

## Installation

### Option 1: HACS (Home Assistant Community Store)

To install via HACS:

1. Navigate to HACS -> Integrations -> "+ Explore & Download Repos".
2. Search for "Node-RED Companion".
3. Click on the result and select "Download this Repository with HACS".
4. Refresh your browser (due to a known HA bug that may not update the integration list immediately).
5. Go to "Settings" in the Home Assistant sidebar, then select "Devices and Services".
6. Click the blue [+ Add Integration] button at the bottom right, search for "Node-RED", and install it.  
   [![Set up a new integration in Home Assistant](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=nodered)

### Option 2: Manual Installation

For manual installation:

1. Access your Home Assistant configuration directory (`configuration.yaml` location).
2. If it doesn’t already exist, create a `custom_components` directory.
3. Within `custom_components`, create a new folder named `nodered`.
4. Download all files from the `custom_components/nodered/` directory in this repository.
5. Place these files in the newly created `nodered` directory.
6. Restart Home Assistant.
7. Refresh your browser window.
8. From "Settings" in the Home Assistant sidebar, select "Devices and Services", click the blue [+ Add Integration] button, search for "Node-RED", and install it.  
   [![Set up a new integration in Home Assistant](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=nodered)

## Configuration

Once the Node-RED Companion Integration is installed and added via Home Assistant Integrations, all further configuration is managed from within Node-RED.

## Contributing

Contributions are welcome! If you're interested in contributing, please review our [Contribution Guidelines](CONTRIBUTING.md) before submitting a pull request or issue.

## Support

If you find this project helpful and want to support its development, consider buying me a coffee!  
[![Buy Me a Coffee][buymecoffeebadge]][buymecoffee]

---

[buymecoffee]: https://www.buymeacoffee.com/zachowj
[buymecoffeebadge]: https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png
[license-shield]: https://img.shields.io/github/license/zachowj/hass-node-red.svg?style=for-the-badge
[hacs]: https://github.com/zachowj/hass-node-red
[hacsbadge]: https://img.shields.io/badge/HACS-Default-orange.svg?style=for-the-badge
[release]: https://github.com/zachowj/hass-node-red/releases
[releasebadge]: https://img.shields.io/github/v/release/zachowj/hass-node-red?style=for-the-badge
[buildstatus-shield]: https://img.shields.io/github/actions/workflow/status/zachowj/hass-node-red/push.yml?branch=main&style=for-the-badge
[buildstatus-link]: https://github.com/zachowj/hass-node-red/actions
