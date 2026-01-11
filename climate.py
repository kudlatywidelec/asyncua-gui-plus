"""Platform for climate integration."""
from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import Any

from homeassistant.components.climate import (
    ATTR_TEMPERATURE,
    ClimateEntity,
    ClimateEntityDescription,
    ClimateEntityFeature,
    HVACMode,
    HVACAction,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import ConfigEntryError
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.device_registry import DeviceInfo

from . import AsyncuaCoordinator
from .const import CONF_HUB_ID, DOMAIN

_LOGGER = logging.getLogger(__name__)

DEFAULT_MIN_TEMP = 5
DEFAULT_MAX_TEMP = 35
DEFAULT_TARGET_TEMPERATURE_STEP = 0.5


@dataclass
class AsyncuaClimateEntityDescription(ClimateEntityDescription):
    """Class to describe an Asyncua climate entity."""

    current_temperature_node_id: str | None = None
    target_temperature_node_id: str | None = None
    hvac_mode_node_id: str | None = None
    preset_mode_node_id: str | None = None


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up climate entities from config entry."""
    hub_id = config_entry.data.get(CONF_HUB_ID)

    if not hub_id:
        _LOGGER.warning("Hub ID not found in config entry")
        return

    climate_data = config_entry.data.get("climate", [])

    if not climate_data:
        return

    if hub_id not in hass.data[DOMAIN]:
        _LOGGER.error(f"Asyncua hub {hub_id} not found")
        return

    coordinator = hass.data[DOMAIN][hub_id]
    asyncua_climate: list = []

    for climate in climate_data:
        asyncua_climate.append(
            AsyncuaClimate(
                coordinator=coordinator,
                name=climate.get("name"),
                unique_id=climate.get("unique_id")
                or f"{hub_id}_{climate.get('current_temp_nodeid')}",
                hub=hub_id,
                current_temperature_node_id=climate.get("current_temp_nodeid"),
                target_temperature_node_id=climate.get("target_temp_nodeid"),
                hvac_mode_node_id=climate.get("hvac_mode_nodeid"),
                preset_mode_node_id=climate.get("preset_mode_nodeid"),
                min_temp=climate.get("min_temp", DEFAULT_MIN_TEMP),
                max_temp=climate.get("max_temp", DEFAULT_MAX_TEMP),
            )
        )

    if asyncua_climate:
        async_add_entities(new_entities=asyncua_climate)


class AsyncuaClimate(CoordinatorEntity[AsyncuaCoordinator], ClimateEntity):
    """A climate implementation for Asyncua OPCUA nodes."""

    _attr_has_entity_name = True
    _attr_hvac_modes = [HVACMode.HEAT, HVACMode.COOL, HVACMode.HEAT_COOL, HVACMode.OFF]
    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.TURN_OFF
        | ClimateEntityFeature.TURN_ON
    )
    _attr_target_temperature_step = DEFAULT_TARGET_TEMPERATURE_STEP
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    entity_description: AsyncuaClimateEntityDescription

    def __init__(
        self,
        coordinator: AsyncuaCoordinator,
        name: str,
        hub: str,
        unique_id: str,
        current_temperature_node_id: str | None = None,
        target_temperature_node_id: str | None = None,
        hvac_mode_node_id: str | None = None,
        preset_mode_node_id: str | None = None,
        min_temp: float = DEFAULT_MIN_TEMP,
        max_temp: float = DEFAULT_MAX_TEMP,
    ) -> None:
        """Initialize the climate entity."""
        super().__init__(coordinator=coordinator)

        # Create entity description
        self.entity_description = AsyncuaClimateEntityDescription(
            key=unique_id,
            name=name,
            current_temperature_node_id=current_temperature_node_id,
            target_temperature_node_id=target_temperature_node_id,
            hvac_mode_node_id=hvac_mode_node_id,
            preset_mode_node_id=preset_mode_node_id,
        )

        self._hub = hub
        self._attr_unique_id = unique_id
        self._attr_min_temp = min_temp
        self._attr_max_temp = max_temp
        self._attr_available = False
        self._attr_hvac_mode = HVACMode.OFF
        self._attr_current_temperature = None
        self._attr_target_temperature = None

    @property
    def unique_id(self) -> str | None:
        """Return the unique_id of the climate entity."""
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
    def name(self) -> str:
        """Return the name from entity description."""
        return self.entity_description.name or ""

    @property
    def current_temperature(self) -> float | None:
        """Return the current temperature."""
        if self.entity_description.current_temperature_node_id:
            return self.coordinator.data.get(
                self.entity_description.current_temperature_node_id
            )
        return None

    @property
    def target_temperature(self) -> float | None:
        """Return the temperature we try to reach."""
        if self.entity_description.target_temperature_node_id:
            return self.coordinator.data.get(
                self.entity_description.target_temperature_node_id
            )
        return None

    @property
    def hvac_mode(self) -> HVACMode | None:
        """Return current HVAC mode."""
        if self.entity_description.hvac_mode_node_id:
            mode_value = self.coordinator.data.get(
                self.entity_description.hvac_mode_node_id
            )
            if mode_value == 0:
                return HVACMode.OFF
            elif mode_value == 1:
                return HVACMode.HEAT
            elif mode_value == 2:
                return HVACMode.COOL
            elif mode_value == 3:
                return HVACMode.HEAT_COOL
        return HVACMode.OFF

    @property
    def hvac_action(self) -> HVACAction | None:
        """Return the current running HVAC action."""
        # For OPC-UA, we would need a specific node to report hvac_action
        # For now, return None to indicate unknown state
        return None

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set new HVAC mode."""
        if self.entity_description.hvac_mode_node_id:
            mode_value = 0
            if hvac_mode == HVACMode.OFF:
                mode_value = 0
            elif hvac_mode == HVACMode.HEAT:
                mode_value = 1
            elif hvac_mode == HVACMode.COOL:
                mode_value = 2
            elif hvac_mode == HVACMode.HEAT_COOL:
                mode_value = 3

            await self.coordinator.async_set_node_value(
                self.entity_description.hvac_mode_node_id, mode_value
            )
            self.async_write_ha_state()

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set new target temperature."""
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is not None and self.entity_description.target_temperature_node_id:
            await self.coordinator.async_set_node_value(
                self.entity_description.target_temperature_node_id, temperature
            )
            self.async_write_ha_state()

    async def async_turn_on(self) -> None:
        """Turn on the climate entity."""
        await self.async_set_hvac_mode(HVACMode.HEAT_COOL)

    async def async_turn_off(self) -> None:
        """Turn off the climate entity."""
        await self.async_set_hvac_mode(HVACMode.OFF)

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle update of the data."""
        self.async_write_ha_state()
