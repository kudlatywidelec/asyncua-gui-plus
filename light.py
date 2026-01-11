"""Platform for light integration."""
from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import Any, Union

import voluptuous as vol

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ColorMode,
    LightEntity,
    LightEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import ConfigEntryError
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.config_validation import PLATFORM_SCHEMA
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.device_registry import DeviceInfo

from . import AsyncuaCoordinator
from .const import (
    CONF_HUB_ID,
    CONF_NODE_DEVICE_CLASS,
    CONF_NODE_HUB,
    CONF_NODE_ID,
    CONF_NODE_NAME,
    CONF_NODE_STATE_CLASS,
    CONF_NODE_UNIQUE_ID,
    CONF_NODE_UNIT_OF_MEASUREMENT,
    CONF_NODES,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

NODE_SCHEMA = {
    CONF_NODES: [
        {
            vol.Optional(CONF_NODE_DEVICE_CLASS): cv.string,
            vol.Optional(CONF_NODE_STATE_CLASS, default="measurement"): cv.string,
            vol.Optional(CONF_NODE_UNIT_OF_MEASUREMENT): cv.string,
            vol.Optional(CONF_NODE_UNIQUE_ID): cv.string,
            vol.Required(CONF_NODE_ID): cv.string,
            vol.Required(CONF_NODE_NAME): cv.string,
            vol.Required(CONF_NODE_HUB): cv.string,
        }
    ]
}

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    schema=NODE_SCHEMA,
    extra=vol.ALLOW_EXTRA,
)


@dataclass
class AsyncuaLightEntityDescription(LightEntityDescription):
    """Class to describe an Asyncua light entity."""

    brightness_node_id: str | None = None
    color_mode: ColorMode = ColorMode.BRIGHTNESS


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up lights from config entry."""
    hub_id = config_entry.data.get(CONF_HUB_ID)

    if not hub_id:
        _LOGGER.warning("Hub ID not found in config entry")
        return

    lights_data = config_entry.data.get("lights", [])

    if not lights_data:
        return

    if hub_id not in hass.data[DOMAIN]:
        _LOGGER.error(f"Asyncua hub {hub_id} not found")
        return

    coordinator = hass.data[DOMAIN][hub_id]
    asyncua_lights: list = []

    for light in lights_data:
        asyncua_lights.append(
            AsyncuaLight(
                coordinator=coordinator,
                name=light.get("name"),
                unique_id=light.get("unique_id")
                or f"{hub_id}_{light.get('nodeid')}",
                hub=hub_id,
                node_id=light.get("nodeid"),
                brightness_node_id=light.get("brightness_nodeid"),
            )
        )

    if asyncua_lights:
        async_add_entities(new_entities=asyncua_lights)


async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up asyncua light coordinator_nodes."""
    coordinator_nodes: dict[str, list[dict[str, str]]] = {}
    coordinators: dict[str, AsyncuaCoordinator] = {}
    asyncua_lights: list = []

    for _idx_node, val_node in enumerate(config[CONF_NODES]):
        if val_node[CONF_NODE_HUB] not in coordinator_nodes.keys():
            coordinator_nodes[val_node[CONF_NODE_HUB]] = []
        coordinator_nodes[val_node[CONF_NODE_HUB]].append(val_node)

    for key_coordinator, val_coordinator in coordinator_nodes.items():
        if key_coordinator not in hass.data[DOMAIN].keys():
            raise ConfigEntryError(
                f"Asyncua hub {key_coordinator} not found. Specify a valid asyncua hub in the configuration."
            )
        coordinators[key_coordinator] = hass.data[DOMAIN][key_coordinator]

        for _idx_light, val_light in enumerate(val_coordinator):
            asyncua_lights.append(
                AsyncuaLight(
                    coordinator=coordinators[key_coordinator],
                    name=val_light[CONF_NODE_NAME],
                    unique_id=val_light.get(CONF_NODE_UNIQUE_ID),
                    hub=val_light[CONF_NODE_HUB],
                    node_id=val_light[CONF_NODE_ID],
                    brightness_node_id=val_light.get("brightness_nodeid"),
                )
            )
    async_add_entities(new_entities=asyncua_lights)


class AsyncuaLight(CoordinatorEntity[AsyncuaCoordinator], LightEntity):
    """A light implementation for Asyncua OPCUA nodes."""

    _attr_has_entity_name = True
    _attr_color_mode = ColorMode.BRIGHTNESS
    _attr_supported_color_modes = {ColorMode.BRIGHTNESS, ColorMode.ONOFF}
    entity_description: AsyncuaLightEntityDescription

    def __init__(
        self,
        coordinator: AsyncuaCoordinator,
        name: str,
        hub: str,
        node_id: str,
        unique_id: Union[str, None] = None,
        brightness_node_id: Union[str, None] = None,
    ) -> None:
        """Initialize the light entity."""
        super().__init__(coordinator=coordinator)

        # Create entity description
        self.entity_description = AsyncuaLightEntityDescription(
            key=node_id,
            name=name,
            brightness_node_id=brightness_node_id,
            color_mode=ColorMode.BRIGHTNESS if brightness_node_id else ColorMode.ONOFF,
        )

        self._hub = hub
        self._node_id = node_id
        self._brightness_node_id = brightness_node_id
        self._attr_unique_id = (
            unique_id if unique_id is not None else node_id
        )
        self._attr_available = False
        self._attr_is_on = False
        self._attr_brightness = None

        if brightness_node_id:
            self._attr_supported_color_modes = {ColorMode.BRIGHTNESS}
            self._attr_color_mode = ColorMode.BRIGHTNESS
        else:
            self._attr_supported_color_modes = {ColorMode.ONOFF}
            self._attr_color_mode = ColorMode.ONOFF

    @property
    def unique_id(self) -> str | None:
        """Return the unique_id of the light."""
        return self._attr_unique_id

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information about this entity."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._hub)},
            name=self._hub,
            manufacturer=self.coordinator.hub.device_info.get("manufacturer", "OPC-UA"),
            model=self.coordinator.hub.device_info.get("model", "Server"),
        )

    @property
    def node_id(self) -> str:
        """Return the node address provided by the OPCUA server."""
        return self._node_id

    @property
    def name(self) -> str:
        """Return the name from entity description."""
        return self.entity_description.name or ""

    @property
    def is_on(self) -> bool:
        """Return True if light is on."""
        return self.coordinator.data.get(self._node_id, False)

    @property
    def brightness(self) -> int | None:
        """Return the brightness of this light between 0..255."""
        if self._brightness_node_id:
            brightness_value = self.coordinator.data.get(self._brightness_node_id)
            if brightness_value is not None:
                # Assuming brightness is in 0-100 range from OPC-UA
                return int((brightness_value / 100) * 255)
        return None

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the light on."""
        brightness = kwargs.get(ATTR_BRIGHTNESS)
        if brightness is not None and self._brightness_node_id:
            # Convert from 0-255 to 0-100 range
            normalized_brightness = int((brightness / 255) * 100)
            await self.coordinator.async_set_node_value(
                self._brightness_node_id, normalized_brightness
            )
        else:
            await self.coordinator.async_set_node_value(self._node_id, True)
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the light off."""
        await self.coordinator.async_set_node_value(self._node_id, False)
        self.async_write_ha_state()

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle update of the data."""
        self.async_write_ha_state()
