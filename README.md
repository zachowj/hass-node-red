# hass-node-red

[![License][license-shield]](LICENSE.md) [![BuyMeCoffee][buymecoffeebadge]][buymecoffee]

_Companion Component to [node-red-contrib-home-assistant-websocket](https://github.com/zachowj/node-red-contrib-home-assistant-websocket) to integrate Node-RED with Home Assistant._

## Installation

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


## Contributions are welcome!

If you want to contribute to this please read the [Contribution guidelines](CONTRIBUTING.md)

***

[buymecoffee]: https://www.buymeacoffee.com/zachowj
[buymecoffeebadge]: https://img.shields.io/badge/buy%20me%20a%20coffee-donate-yellow.svg?style=for-the-badge
[license-shield]: https://img.shields.io/github/license/zachowj/hass-node-red.svg?style=for-the-badge
