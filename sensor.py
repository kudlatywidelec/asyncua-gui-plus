"""Platform for sensor integration."""
from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import Any, Union

import voluptuous as vol

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import ConfigEntryError
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.config_validation import PLATFORM_SCHEMA
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import (
    ConfigType,
    DiscoveryInfoType,
)
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
class AsyncuaSensorEntityDescription(SensorEntityDescription):
    """Class to describe an Asyncua sensor entity."""

    device_class: str | None = None
    state_class: str = "measurement"
    unit_of_measurement: str | None = None
    precision: int = 2


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensors from config entry."""
    # Get hub ID from config entry
    hub_id = config_entry.data.get(CONF_HUB_ID)
    
    if not hub_id:
        _LOGGER.warning(f"Hub ID not found in config entry")
        return
    
    # Get sensors from stored config entry data (OptionsFlow stores here)
    sensors_data = config_entry.data.get("sensors", [])
    
    if not sensors_data:
        # No sensors to add from config entry
        return
    
    if hub_id not in hass.data[DOMAIN]:
        _LOGGER.error(f"Asyncua hub {hub_id} not found")
        return
    
    coordinator = hass.data[DOMAIN][hub_id]
    asyncua_sensors: list = []
    
    # Add sensors to coordinator
    coordinator.add_sensors(sensors_data)
    
    # Create sensors from config entry
    for sensor in sensors_data:
        asyncua_sensors.append(
            AsyncuaSensor(
                coordinator=coordinator,
                name=sensor.get("name"),
                unique_id=sensor.get("unique_id") or f"{DOMAIN}.{hub_id}.{sensor.get('nodeid')}",
                hub=hub_id,
                node_id=sensor.get("nodeid"),
                device_class=sensor.get("device_class"),
                state_class=sensor.get("state_class", "measurement"),
                unit_of_measurement=sensor.get("unit"),
            )
        )
    
    if asyncua_sensors:
        async_add_entities(new_entities=asyncua_sensors)



async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up asyncua_sensor coordinator_nodes."""

    # {"hub": [node0, node1]}
    # where node0 equals {"name": "node0", "unique_id": "node0", ...}.

    coordinator_nodes: dict[str, list[dict[str, str]]] = {}
    coordinators: dict[str, AsyncuaCoordinator] = {}
    asyncua_sensors: list = []

    # Compile dictionary of {hub: [node0, node1, ...]}
    for _idx_node, val_node in enumerate(config[CONF_NODES]):
        if val_node[CONF_NODE_HUB] not in coordinator_nodes.keys():
            coordinator_nodes[val_node[CONF_NODE_HUB]] = []
        coordinator_nodes[val_node[CONF_NODE_HUB]].append(val_node)

    for key_coordinator, val_coordinator in coordinator_nodes.items():
        # Get the respective asyncua coordinator
        if key_coordinator not in hass.data[DOMAIN].keys():
            raise ConfigEntryError(
                f"Asyncua hub {key_coordinator} not found. Specify a valid asyncua hub in the configuration."
            )
        coordinators[key_coordinator] = hass.data[DOMAIN][key_coordinator]
        coordinators[key_coordinator].add_sensors(sensors=val_coordinator)

        # Create sensors with injecting respective asyncua coordinator
        for _idx_sensor, val_sensor in enumerate(val_coordinator):
            asyncua_sensors.append(
                AsyncuaSensor(
                    coordinator=coordinators[key_coordinator],
                    name=val_sensor[CONF_NODE_NAME],
                    unique_id=val_sensor.get(CONF_NODE_UNIQUE_ID),
                    hub=val_sensor[CONF_NODE_HUB],
                    node_id=val_sensor[CONF_NODE_ID],
                    device_class=val_sensor.get(CONF_NODE_DEVICE_CLASS),
                    unit_of_measurement=val_sensor.get(CONF_NODE_UNIT_OF_MEASUREMENT),
                )
            )
    async_add_entities(new_entities=asyncua_sensors)



class AsyncuaSensor(CoordinatorEntity[AsyncuaCoordinator], SensorEntity):
    """A sensor implementation for Asyncua OPCUA nodes."""

    _attr_has_entity_name = True
    entity_description: AsyncuaSensorEntityDescription

    def __init__(
        self,
        coordinator: AsyncuaCoordinator,
        name: str,
        hub: str,
        node_id: str,
        device_class: Any,
        unique_id: Union[str, None] = None,
        state_class: str = "measurement",
        precision: int = 2,
        unit_of_measurement: Union[str, None] = None,
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator=coordinator)
        
        # Create entity description from provided parameters
        self.entity_description = AsyncuaSensorEntityDescription(
            key=node_id,
            name=name,
            device_class=device_class,
            state_class=state_class,
            unit_of_measurement=unit_of_measurement,
            precision=precision,
        )
        
        self._hub = hub
        self._node_id = node_id
        self._attr_unique_id = (
            unique_id if unique_id is not None else f"{hub}_{node_id}"
        )
        self._attr_available = False
        self._attr_native_unit_of_measurement = unit_of_measurement
        self._attr_native_value = None
        self._attr_suggested_display_precision = precision
        self._sensor_data = self._parse_coordinator_data(
            coordinator_data=coordinator.data
        )

    @property
    def unique_id(self) -> str | None:
        """Return the unique_id of the sensor."""
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
    def device_class(self) -> str | None:
        """Return the device class from entity description."""
        return self.entity_description.device_class

    @property
    def state_class(self) -> str:
        """Return the state class from entity description."""
        return self.entity_description.state_class

    @property
    def native_unit_of_measurement(self) -> str | None:
        """Return the unit of measurement from entity description."""
        return self.entity_description.unit_of_measurement

    def _parse_coordinator_data(
        self,
        coordinator_data: dict[str, Any],
    ) -> Any:
        """Parse the value from the mapped coordinator."""
        entity_name = self.entity_description.name
        if entity_name is None:
            raise ConfigEntryError(
                f"Unable to find {entity_name} in coordinator {self.coordinator.name}"
            )
        return coordinator_data.get(entity_name)

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle update of the data."""
        self._attr_native_value = self._parse_coordinator_data(
            coordinator_data=self.coordinator.data,
        )
        self.async_write_ha_state()
