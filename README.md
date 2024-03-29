# Node-RED Companion Integration

[![hacs][hacsbadge]][hacs] [![releasebadge]][release] [![Build Status][buildstatus-shield]][buildstatus-link] [![License][license-shield]](LICENSE.md)

[![BuyMeCoffee][buymecoffeebadge]][buymecoffee]

_Companion Component to [node-red-contrib-home-assistant-websocket](https://github.com/zachowj/node-red-contrib-home-assistant-websocket) to integrate Node-RED with Home Assistant._

## Features

- Create and update entities from Node-RED
  - binary sensor
  - button
  - number
  - select
  - sensor
  - switch
  - text
- Disable and enable Node-RED flows from Home Assistant UI
- Create Home Assistant webhooks and handle them in Node-RED
- Use Device triggers and action from Node-RED

## Minimum Requirements

- [node-red-contrib-home-assistant-websocket](https://github.com/zachowj/node-red-contrib-home-assistant-websocket) v0.57+
- [Home Assistant](https://github.com/home-assistant/core) 2023.7.0+

## Installation

### HACS

Install via [HACS](https://hacs.xyz) (Home Assistant Community Store)

1. Go to HACS -> Integrations -> "+ Explore & Download Repos"
1. Find "Node-RED Companion".
1. Open the search result and click "Download this Repository with HACS".
1. Refresh your browser window (bug in HA where it doesn't update the integration list after a reboot)
1. From "Settings" in the Home Assistant sidebar, select "Devices and Services", click the blue [+ Add integration] button (in bottom right of the page) and search for "Node-RED", and install it. [![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=nodered)

### Manual

1. Using your tool of choice open the directory (folder) for your HA configuration (where you find `configuration.yaml`).
1. If you do not have a `custom_components` directory (folder) there, you need to create it.
1. In the `custom_components` directory (folder) create a new folder called `nodered`.
1. Download _all_ the files from the `custom_components/nodered/` directory (folder) in this repository.
1. Place the files you downloaded in the new directory (folder) you created.
1. Restart Home Assistant
1. Refresh your browser window (bug in HA where it doesn't update the integration list after a reboot)
1. From "Settings" in the Home Assistant sidebar, select "Devices and Services", click the blue [+ Add integration] button (in bottom right of the page) and search for "Node-RED", and install it. [![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=nodered)

## Configuration

Once installed and added via Home-Assistant Integrations all configuration is done from within Node-RED.

## Contributions are welcome!

If you want to contribute please read the [Contribution guidelines](CONTRIBUTING.md)

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
