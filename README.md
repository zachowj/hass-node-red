# hass-node-red

[![hacs][hacsbadge]][hacs] [![releasebadge]][release] ![buildbadge] [![License][license-shield]](LICENSE.md)

[![BuyMeCoffee][buymecoffeebadge]][buymecoffee]

_Companion Component to [node-red-contrib-home-assistant-websocket](https://github.com/zachowj/node-red-contrib-home-assistant-websocket) to integrate Node-RED with Home Assistant. (minimum version 0.17.1)_

## Installation

_This integration is available in [HACS](https://hacs.xyz) (Home Assistant Community Store)_

1. Using the tool of choice open the directory (folder) for your HA configuration (where you find `configuration.yaml`).
2. If you do not have a `custom_components` directory (folder) there, you need to create it.
3. In the `custom_components` directory (folder) create a new folder called `nodered`.
4. Download _all_ the files from the `custom_components/nodered/` directory (folder) in this repository.
5. Place the files you downloaded in the new directory (folder) you created.
6. Restart Home Assistant
7. In the HA UI go to "Configuration" -> "Integrations" click "+" and search for "Node-RED"

Using your HA configuration directory (folder) as a starting point you should now also have this:

```text
custom_components/nodered/.translations/en.json
custom_components/nodered/__init__.py
custom_components/nodered/binary_sensor.py
custom_components/nodered/config_flow.py
custom_components/nodered/const.py
custom_components/nodered/discovery.py
custom_components/nodered/manifest.json
custom_components/nodered/sensor.py
custom_components/nodered/switch.py
custom_components/nodered/websocket.py
```

## Configuration

Once installed and added via Integrations all configuration is done from Node-RED.

## Contributions are welcome!

If you want to contribute to this please read the [Contribution guidelines](CONTRIBUTING.md)

***

[buymecoffee]: https://www.buymeacoffee.com/zachowj
[buymecoffeebadge]: https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png
[license-shield]: https://img.shields.io/github/license/zachowj/hass-node-red.svg?style=for-the-badge
[hacs]: https://github.com/zachowj/hass-node-red
[hacsbadge]: https://img.shields.io/badge/HACS-Default-orange.svg?style=for-the-badge
[release]: https://github.com/zachowj/hass-node-red/releases
[releasebadge]: https://img.shields.io/github/v/release/zachowj/hass-node-red?style=for-the-badge
[buildbadge]: https://img.shields.io/github/workflow/status/zachowj/hass-node-red/pre-commit?style=for-the-badge
