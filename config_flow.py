"""Config flow for Asyncua component."""
from __future__ import annotations

import logging
import re
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_NAME, CONF_URL
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError

import homeassistant.helpers.config_validation as cv

from .const import (
    DOMAIN,
    CONF_HUB_ID,
    CONF_HUB_URL,
    CONF_HUB_USERNAME,
    CONF_HUB_PASSWORD,
    CONF_HUB_MANUFACTURER,
    CONF_HUB_MODEL,
    CONF_HUB_SCAN_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)

# OPC-UA node ID pattern: ns=X;s=... or ns=X;i=...
OPC_UA_NODE_ID_PATTERN = re.compile(r'^ns=\d+;[si]=[a-zA-Z0-9_\-\.:/]+$')


def _validate_opc_ua_node_id(node_id: str) -> bool:
    """Validate OPC-UA node ID format."""
    return bool(OPC_UA_NODE_ID_PATTERN.match(node_id))


class AsyncuaConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Asyncua."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step - configure OPC-UA hub."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Check if hub already exists
            await self.async_set_unique_id(user_input[CONF_HUB_ID])
            self._abort_if_unique_id_configured()

            # Validate the input
            try:
                await self._async_validate_input(user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except Exception as err:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected error: %s", err)
                errors["base"] = "unknown"

            if not errors:
                # Create the config entry directly
                return self.async_create_entry(
                    title=user_input[CONF_HUB_ID],
                    data=user_input,
                )

        data_schema = vol.Schema(
            {
                vol.Required(CONF_HUB_ID, default="plc_15"): cv.string,
                vol.Required(CONF_HUB_URL, default="opc.tcp://192.168.2.15:4840"): cv.string,
                vol.Optional(CONF_HUB_MANUFACTURER, default=""): cv.string,
                vol.Optional(CONF_HUB_MODEL, default=""): cv.string,
                vol.Optional(CONF_HUB_USERNAME): cv.string,
                vol.Optional(CONF_HUB_PASSWORD): cv.string,
                vol.Optional(CONF_HUB_SCAN_INTERVAL, default=30): cv.positive_int,
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
            description_placeholders={
                "url_example": "opc.tcp://192.168.1.100:4840"
            },
        )

    async def _async_validate_input(self, user_input: dict[str, Any]) -> None:
        """Validate the user input allows us to connect."""
        # Basic validation - just check if URL looks valid
        url = user_input[CONF_HUB_URL]
        if not url.startswith("opc.tcp://"):
            raise CannotConnect("Invalid OPC-UA URL format")

        # Verify URL has host and port
        try:
            url_parts = url.replace("opc.tcp://", "").split(":")
            if len(url_parts) < 2:
                raise ValueError("URL must contain host and port")
            
            # Validate port is a number
            try:
                port = int(url_parts[1])
                if port < 1 or port > 65535:
                    raise ValueError(f"Invalid port number: {port}")
            except ValueError as e:
                if "invalid literal" in str(e):
                    raise ValueError("Port must be a valid number") from e
                raise
        except Exception as err:
            raise CannotConnect(f"Invalid URL format: {err}") from err

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Get the options flow for this integration."""
        return AsyncuaOptionsFlow(config_entry)


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""

class AsyncuaOptionsFlow(config_entries.OptionsFlow):
    """Handle options for Asyncua."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        # In HA Core, OptionsFlow exposes read-only property `config_entry`
        # backed by `_config_entry`. Assign to the private attr to avoid
        # AttributeError: property 'config_entry' has no setter.
        self._config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_menu(
            step_id="init",
            menu_options=[
                "add_sensor",
                "add_binary_sensor",
                "add_switch",
                "add_cover",
                "add_light",
                "add_climate",
                "manage_entities"
            ],
        )

    async def async_step_add_sensor(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Add a sensor."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Validate node ID format
            if not _validate_opc_ua_node_id(user_input.get("nodeid", "")):
                errors["nodeid"] = "invalid_node_id"
            
            if not errors:
                # Add sensor to entry data
                sensors = self._config_entry.data.get("sensors", [])
                sensors.append({
                    "name": user_input.get("sensor_name"),
                    "nodeid": user_input.get("nodeid"),
                    "device_class": user_input.get("device_class", ""),
                    "state_class": user_input.get("state_class", "measurement"),
                    "unit": user_input.get("unit", ""),
                })
                
                # Update config entry
                self.hass.config_entries.async_update_entry(
                    self._config_entry,
                    data={**self._config_entry.data, "sensors": sensors}
                )
                
                # Reload entry
                await self.hass.config_entries.async_reload(self._config_entry.entry_id)
                
                return self.async_abort(reason="reconfigure_successful")

        data_schema = vol.Schema(
            {
                vol.Required("sensor_name"): cv.string,
                vol.Required("nodeid"): cv.string,
                vol.Optional("device_class"): cv.string,
                vol.Optional("state_class", default="measurement"): cv.string,
                vol.Optional("unit"): cv.string,
            }
        )

        return self.async_show_form(
            step_id="add_sensor",
            data_schema=data_schema,
            description_placeholders={
                "nodeid_example": "ns=2;s=zmienna"
            },
            errors=errors,
        )

    async def async_step_add_binary_sensor(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Add a binary sensor."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Validate node ID format
            if not _validate_opc_ua_node_id(user_input.get("nodeid", "")):
                errors["nodeid"] = "invalid_node_id"
            
            if not errors:
                sensors = self._config_entry.data.get("binary_sensors", [])
                sensors.append({
                    "name": user_input.get("name"),
                    "nodeid": user_input.get("nodeid"),
                    "device_class": user_input.get("device_class", ""),
                    "hub": self._config_entry.data.get("name"),
                })
                self.hass.config_entries.async_update_entry(
                    self._config_entry,
                    data={**self._config_entry.data, "binary_sensors": sensors}
                )
                await self.hass.config_entries.async_reload(self._config_entry.entry_id)
                return self.async_abort(reason="reconfigure_successful")

        data_schema = vol.Schema(
            {
                vol.Required("name"): cv.string,
                vol.Required("nodeid"): cv.string,
                vol.Optional("device_class"): cv.string,
            }
        )
        return self.async_show_form(
            step_id="add_binary_sensor",
            data_schema=data_schema,
            description_placeholders={
                "nodeid_example": "ns=2;s=wejscie_binary"
            },
            errors=errors,
        )

    async def async_step_add_switch(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Add a switch."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Validate node ID formats
            if not _validate_opc_ua_node_id(user_input.get("nodeid", "")):
                errors["nodeid"] = "invalid_node_id"
            if user_input.get("nodeid_switch_di") and not _validate_opc_ua_node_id(user_input.get("nodeid_switch_di")):
                errors["nodeid_switch_di"] = "invalid_node_id"
            
            if not errors:
                switches = self._config_entry.data.get("switches", [])
                switches.append({
                    "name": user_input.get("name"),
                    "nodeid": user_input.get("nodeid"),
                    "nodeid_switch_di": user_input.get("nodeid_switch_di", ""),
                    "hub": self._config_entry.data.get("name"),
                })
                self.hass.config_entries.async_update_entry(
                    self._config_entry,
                    data={**self._config_entry.data, "switches": switches}
                )
                await self.hass.config_entries.async_reload(self._config_entry.entry_id)
                return self.async_abort(reason="reconfigure_successful")

        data_schema = vol.Schema(
            {
                vol.Required("name"): cv.string,
                vol.Required("nodeid"): cv.string,
                vol.Optional("nodeid_switch_di"): cv.string,
            }
        )
        return self.async_show_form(
            step_id="add_switch",
            data_schema=data_schema,
            description_placeholders={
                "nodeid_example": "ns=2;s=sterowanie_wyjscie"
            },
            errors=errors,
        )

    async def async_step_add_cover(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Add a cover."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Validate all node ID formats
            node_id_fields = ["nodeid", "open_nodeid", "close_nodeid", "stop_nodeid", "fully_open_nodeid", "fully_closed_nodeid"]
            for field in node_id_fields:
                if user_input.get(field) and not _validate_opc_ua_node_id(user_input.get(field)):
                    errors[field] = "invalid_node_id"
            
            if not errors:
                covers = self._config_entry.data.get("covers", [])
                covers.append({
                    "name": user_input.get("name"),
                    "hub": self._config_entry.data.get("name"),
                    "nodeid": user_input.get("nodeid"),
                    "travelling_time_down": user_input.get("travelling_time_down", 25),
                    "travelling_time_up": user_input.get("travelling_time_up", 25),
                    "open_nodeid": user_input.get("open_nodeid"),
                    "close_nodeid": user_input.get("close_nodeid"),
                    "stop_nodeid": user_input.get("stop_nodeid"),
                    "fully_open_nodeid": user_input.get("fully_open_nodeid"),
                    "fully_closed_nodeid": user_input.get("fully_closed_nodeid"),
                })
                self.hass.config_entries.async_update_entry(
                    self._config_entry,
                    data={**self._config_entry.data, "covers": covers}
                )
                await self.hass.config_entries.async_reload(self._config_entry.entry_id)
                return self.async_abort(reason="reconfigure_successful")

        data_schema = vol.Schema(
            {
                vol.Required("name"): cv.string,
                vol.Required("nodeid"): cv.string,
                vol.Required("open_nodeid"): cv.string,
                vol.Required("close_nodeid"): cv.string,
                vol.Optional("stop_nodeid"): cv.string,
                vol.Optional("fully_open_nodeid"): cv.string,
                vol.Optional("fully_closed_nodeid"): cv.string,
                vol.Optional("travelling_time_down", default=25): cv.positive_int,
                vol.Optional("travelling_time_up", default=25): cv.positive_int,
            }
        )
        return self.async_show_form(
            step_id="add_cover",
            data_schema=data_schema,
            description_placeholders={
                "nodeid_example": "ns=2;s=pozycja_roleta"
            },
            errors=errors,
        )

    async def async_step_add_light(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Add a light."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Validate node ID format
            if not _validate_opc_ua_node_id(user_input.get("nodeid", "")):
                errors["nodeid"] = "invalid_node_id"
            if user_input.get("brightness_nodeid") and not _validate_opc_ua_node_id(user_input.get("brightness_nodeid")):
                errors["brightness_nodeid"] = "invalid_node_id"
            
            if not errors:
                lights = self._config_entry.data.get("lights", [])
                lights.append({
                    "name": user_input.get("name"),
                    "hub": self._config_entry.data.get("name"),
                    "nodeid": user_input.get("nodeid"),
                    "brightness_nodeid": user_input.get("brightness_nodeid"),
                })
                self.hass.config_entries.async_update_entry(
                    self._config_entry,
                    data={**self._config_entry.data, "lights": lights}
                )
                await self.hass.config_entries.async_reload(self._config_entry.entry_id)
                return self.async_abort(reason="reconfigure_successful")

        data_schema = vol.Schema(
            {
                vol.Required("name"): cv.string,
                vol.Required("nodeid"): cv.string,
                vol.Optional("brightness_nodeid"): cv.string,
            }
        )
        return self.async_show_form(
            step_id="add_light",
            data_schema=data_schema,
            description_placeholders={
                "nodeid_example": "ns=2;s=swiatlo",
                "brightness_example": "ns=2;s=jasnosc"
            },
            errors=errors,
        )

    async def async_step_add_climate(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Add a climate/thermostat."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Validate node ID formats
            node_id_fields = ["current_temp_nodeid", "target_temp_nodeid", "hvac_mode_nodeid", "preset_mode_nodeid"]
            for field in node_id_fields:
                if user_input.get(field) and not _validate_opc_ua_node_id(user_input.get(field)):
                    errors[field] = "invalid_node_id"
            
            if not errors:
                climate = self._config_entry.data.get("climate", [])
                climate.append({
                    "name": user_input.get("name"),
                    "hub": self._config_entry.data.get("name"),
                    "current_temp_nodeid": user_input.get("current_temp_nodeid"),
                    "target_temp_nodeid": user_input.get("target_temp_nodeid"),
                    "hvac_mode_nodeid": user_input.get("hvac_mode_nodeid"),
                    "preset_mode_nodeid": user_input.get("preset_mode_nodeid"),
                    "min_temp": user_input.get("min_temp", 5),
                    "max_temp": user_input.get("max_temp", 35),
                })
                self.hass.config_entries.async_update_entry(
                    self._config_entry,
                    data={**self._config_entry.data, "climate": climate}
                )
                await self.hass.config_entries.async_reload(self._config_entry.entry_id)
                return self.async_abort(reason="reconfigure_successful")

        data_schema = vol.Schema(
            {
                vol.Required("name"): cv.string,
                vol.Optional("current_temp_nodeid"): cv.string,
                vol.Optional("target_temp_nodeid"): cv.string,
                vol.Optional("hvac_mode_nodeid"): cv.string,
                vol.Optional("preset_mode_nodeid"): cv.string,
                vol.Optional("min_temp", default=5): cv.positive_int,
                vol.Optional("max_temp", default=35): cv.positive_int,
            }
        )
        return self.async_show_form(
            step_id="add_climate",
            data_schema=data_schema,
            description_placeholders={
                "current_temp_example": "ns=2;s=temperatura_aktualna",
                "target_temp_example": "ns=2;s=temperatura_ustawiana"
            },
            errors=errors,
        )

    async def async_step_manage_entities(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage (edit/delete) existing entities."""
        if user_input is not None:
            action = user_input.get("action")
            entity_type = user_input.get("entity_type")
            entity_index = user_input.get("entity_index", -1)
            
            if action == "delete" and entity_index >= 0:
                # Delete entity
                key = f"{entity_type}s"  # sensors, binary_sensors, switches, covers
                entities = self._config_entry.data.get(key, [])
                if 0 <= entity_index < len(entities):
                    entities.pop(entity_index)
                    self.hass.config_entries.async_update_entry(
                        self._config_entry,
                        data={**self._config_entry.data, key: entities}
                    )
                    await self.hass.config_entries.async_reload(self._config_entry.entry_id)
                    return self.async_abort(reason="reconfigure_successful")
            
            return self.async_abort(reason="user_aborted")

        # Build list of entities for user to choose from
        all_entities = []
        
        for entity_type, key in [("sensor", "sensors"), ("binary_sensor", "binary_sensors"), ("switch", "switches"), ("cover", "covers"), ("light", "lights"), ("climate", "climate")]:
            entities = self._config_entry.data.get(key, [])
            for idx, entity in enumerate(entities):
                label = f"{entity_type}: {entity.get('name', f'Entity {idx}')}"
                all_entities.append((f"{entity_type}_{idx}", label))
        
        if not all_entities:
            return self.async_abort(reason="no_entities")
        
        data_schema = vol.Schema(
            {
                vol.Required("action"): vol.In(["delete"]),
                vol.Required("entity"): vol.In(dict(all_entities)),
            }
        )
        
        return self.async_show_form(
            step_id="manage_entities",
            data_schema=data_schema,
            description_placeholders={
                "info": "Select an entity and action to perform"
            },
        )