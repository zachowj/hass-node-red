"""Sensor platform for nodered."""

from datetime import date, datetime, timezone
import logging
from typing import Any

from dateutil import parser
from propcache.api import cached_property

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.components.websocket_api.connection import ActiveConnection
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_STATE, CONF_UNIT_OF_MEASUREMENT, EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CONF_CONFIG,
    CONF_LAST_RESET,
    CONF_SENSOR,
    CONF_STATE_CLASS,
    NODERED_DISCOVERY_NEW,
)
from .entity import NodeRedEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensor platform."""

    async def async_discover(
        config: dict[str, Any], _connection: ActiveConnection
    ) -> None:
        await _async_setup_entity(hass, config, async_add_entities)

    config_entry.async_on_unload(
        async_dispatcher_connect(
            hass,
            NODERED_DISCOVERY_NEW.format(CONF_SENSOR),
            async_discover,
        )
    )


async def _async_setup_entity(
    hass: HomeAssistant,
    config: dict[str, Any],
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Node-RED sensor."""
    async_add_entities([NodeRedSensor(hass, config)])


class NodeRedSensor(NodeRedEntity, SensorEntity):
    """Node-RED Sensor class."""

    component = CONF_SENSOR

    def __init__(self, hass: HomeAssistant, config: dict[str, Any]) -> None:
        """Initialize the sensor."""
        super().__init__(hass, config)
        self._attr_unit_of_measurement = None
        # Only attempt conversion if a state was provided in discovery/config
        if CONF_STATE in config:
            self._attr_native_value = self.convert_state(config.get(CONF_STATE))
        else:
            self._attr_native_value = None
        self._attr_native_unit_of_measurement = self._config.get(
            CONF_UNIT_OF_MEASUREMENT
        )
        self._attr_state_class = self._config.get(CONF_STATE_CLASS)

    @cached_property
    def last_reset(self) -> datetime | None:
        """Return the cached parsed last reset time for this sensor."""
        return self.__dict__.get("last_reset")

    def convert_state(
        self, state: str | float | None
    ) -> datetime | date | float | int | str | bool | None:
        """Convert state if needed."""
        if state is None:
            return None

        if self.device_class in [
            SensorDeviceClass.TIMESTAMP,
            SensorDeviceClass.DATE,
        ]:
            # Accept numeric timestamps (seconds or milliseconds) as well as
            # ISO date strings. Numeric timestamps are often sent as integers
            # (ms since epoch) by Node-RED/JS environments.
            ts: float | None = None
            if isinstance(state, (int, float)):
                ts = float(state)
            elif isinstance(state, str):
                s = state.strip()
                # Accept numeric strings (ints or floats)
                if s.lstrip("-+").replace(".", "", 1).isdigit():
                    try:
                        ts = float(s)
                    except ValueError:
                        ts = None

            if ts is not None:
                # Heuristic: treat large numbers as milliseconds
                if ts > 1e11:
                    seconds = ts / 1000.0
                else:
                    seconds = ts
                try:
                    parsed = datetime.fromtimestamp(seconds, tz=timezone.utc)
                except (OverflowError, OSError, ValueError):
                    _LOGGER.exception(
                        "Invalid timestamp (%s): %s has a timestamp device class",
                        state,
                        self.entity_id,
                    )
                    return None
                else:
                    if self.device_class is SensorDeviceClass.DATE:
                        return parsed.date()
                    return parsed

            # Fallback to ISO parsing for string states
            if not isinstance(state, str):
                _LOGGER.exception(
                    "Invalid ISO date string (%s): %s has a timestamp device class",
                    state,
                    self.entity_id,
                )
                return None
            try:
                parsed = parser.parse(state)
            except (ValueError, TypeError):
                _LOGGER.exception(
                    "Invalid ISO date string (%s): %s has a timestamp device class",
                    state,
                    self.entity_id,
                )
                return None
            else:
                if self.device_class is SensorDeviceClass.DATE:
                    return parsed.date()
                return parsed

        return state

    def update_entity_state_attributes(self, msg: dict[str, Any]) -> None:
        """Update entity state attributes."""
        super().update_entity_state_attributes(msg)
        # Only update native value when a state key is present; this avoids
        # overwriting existing values when messages only include attributes.
        if CONF_STATE in msg:
            self._attr_native_value = self.convert_state(msg.get(CONF_STATE))

    def update_discovery_config(self, msg: dict[str, Any]) -> None:
        """Update entity config."""
        super().update_discovery_config(msg)
        config = msg[CONF_CONFIG]
        self._attr_native_unit_of_measurement = config.get(CONF_UNIT_OF_MEASUREMENT)
        self._attr_unit_of_measurement = None
        self._attr_state_class = config.get(CONF_STATE_CLASS)
        # Validate and cache last_reset from discovery config to surface invalid
        # values immediately and to ensure the cached property reflects updates.
        last = config.get(CONF_LAST_RESET)
        if last is not None:
            # Only cache last_reset when it makes sense for the sensor. Home
            # Assistant will raise if last_reset is present for sensors that do
            # not have a supported state_class (for example, None). Accept
            # last_reset when the sensor has a timestamp/date device class or
            # when the state_class indicates a total counter ("total" or
            # "total_increasing"). Otherwise ignore and warn.
            allowed_state_classes = {"total", "total_increasing"}
            if self.device_class in [
                SensorDeviceClass.TIMESTAMP,
                SensorDeviceClass.DATE,
            ] or (self.state_class in allowed_state_classes):
                self._validate_and_cache_last_reset(last)
            else:
                _LOGGER.warning(
                    "Sensor %s (node ID: %s) provided last_reset but state_class is %s; "
                    "ignoring last_reset",
                    self.name,
                    self._node_id,
                    self.state_class,
                )
                # Ensure no stale cached value remains
                if "last_reset" in self.__dict__:
                    del self.__dict__["last_reset"]

    def _validate_and_cache_last_reset(self, last: str) -> None:
        """Validate a last_reset ISO string and cache the parsed value.

        Keeps the same logging and cache-invalidation behaviour as before.
        """
        try:
            parsed = parser.parse(last)
        except (ValueError, TypeError):
            _LOGGER.exception(
                "Invalid ISO date string (%s): %s requires last_reset to be "
                "an iso date formatted string",
                last,
                self.entity_id,
            )
            # Remove any cached value so it will be recomputed on next access
            if "last_reset" in self.__dict__:
                del self.__dict__["last_reset"]
        else:
            if self.device_class is SensorDeviceClass.DATE:
                self.__dict__["last_reset"] = parsed.date()
            else:
                self.__dict__["last_reset"] = parsed

    def entity_category_mapper(self, category: str) -> None | EntityCategory:
        """Map Node-RED category to Home Assistant entity category."""
        if category == "config":
            _LOGGER.warning(
                "Sensor %s has category 'config' which is not supported",
                self.name,
            )
        if category == "diagnostic":
            return EntityCategory.DIAGNOSTIC
        return None
