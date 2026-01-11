"""Platform for cover integration with Asyncua OPCUA nodes."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.components.cover import (
    ATTR_CURRENT_POSITION,
    ATTR_POSITION,
    PLATFORM_SCHEMA,
    CoverEntity,
    CoverEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_UNAVAILABLE
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import ConfigEntryError
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.config_validation import PLATFORM_SCHEMA
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.device_registry import DeviceInfo
from datetime import timedelta

from . import AsyncuaCoordinator
from .const import (
    CONF_NODE_HUB,
    CONF_NODE_ID,
    CONF_NODE_NAME,
    CONF_NODE_UNIQUE_ID,
    CONF_NODES,
    DOMAIN,
    CONF_TRAVELLING_TIME_DOWN,
    CONF_TRAVELLING_TIME_UP,
    CONF_OPEN_NODEID,
    CONF_CLOSE_NODEID,
    CONF_STOP_NODEID,
    CONF_FULLY_OPEN_NODEID,
    CONF_FULLY_CLOSED_NODEID,
)
from .travelcalculator import TravelCalculator, TravelStatus

_LOGGER = logging.getLogger(__name__)

DEFAULT_TRAVEL_TIME = 25

NODE_SCHEMA = {
    CONF_NODES: [
        {
            vol.Required(CONF_NODE_HUB): cv.string,
            vol.Required(CONF_NODE_NAME): cv.string,
            vol.Required(CONF_NODE_ID): cv.string,
            vol.Required(CONF_TRAVELLING_TIME_DOWN, default=DEFAULT_TRAVEL_TIME): cv.positive_int,
            vol.Required(CONF_TRAVELLING_TIME_UP, default=DEFAULT_TRAVEL_TIME): cv.positive_int,
            vol.Required(CONF_OPEN_NODEID): cv.string,
            vol.Required(CONF_CLOSE_NODEID): cv.string,
            vol.Optional(CONF_STOP_NODEID): cv.string,
            vol.Optional(CONF_FULLY_OPEN_NODEID): cv.string,
            vol.Optional(CONF_FULLY_CLOSED_NODEID): cv.string,
            vol.Optional(CONF_NODE_UNIQUE_ID): cv.string,
        }
    ]
}

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    schema=NODE_SCHEMA,
    extra=vol.ALLOW_EXTRA,
)

SERVICE_SET_POSITION = "set_position"
SERVICE_RESET_FULLY_OPEN = "reset_fully_open"
SERVICE_RESET_FULLY_CLOSED = "reset_fully_closed"

SET_POSITION_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_POSITION): cv.positive_int,
    }
)

RESET_POSITION_SCHEMA = vol.Schema({})


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up covers from a config entry.

    If no covers are defined in entry data, exit gracefully."""
    hub_id = config_entry.data.get("name")
    if not hub_id or hub_id not in hass.data.get(DOMAIN, {}):
        return

    coordinator: AsyncuaCoordinator = hass.data[DOMAIN][hub_id]
    
    # Store async_add_entities callback for dynamic entity addition
    if not hasattr(coordinator, '_add_entities_callbacks'):
        coordinator._add_entities_callbacks = {}
    coordinator._add_entities_callbacks['cover'] = async_add_entities
    
    covers_cfg = config_entry.data.get("covers", [])
    if not covers_cfg:
        return

    coordinator.add_sensors(covers_cfg)
    entities: list[AsyncuaCover] = []
    for cv in covers_cfg:
        entities.append(
            AsyncuaCover(
                coordinator=coordinator,
                name=cv.get(CONF_NODE_NAME),
                hub=cv.get(CONF_NODE_HUB, hub_id),
                node_id=cv.get(CONF_NODE_ID),
                travel_time_down=cv.get(CONF_TRAVELLING_TIME_DOWN, DEFAULT_TRAVEL_TIME),
                travel_time_up=cv.get(CONF_TRAVELLING_TIME_UP, DEFAULT_TRAVEL_TIME),
                open_nodeid=cv.get(CONF_OPEN_NODEID),
                close_nodeid=cv.get(CONF_CLOSE_NODEID),
                stop_nodeid=cv.get(CONF_STOP_NODEID),
                fully_open_nodeid=cv.get(CONF_FULLY_OPEN_NODEID),
                fully_closed_nodeid=cv.get(CONF_FULLY_CLOSED_NODEID),
                unique_id=cv.get(CONF_NODE_UNIQUE_ID),
            )
        )

    if entities:
        async_add_entities(entities)


async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up asyncua_cover coordinator_nodes."""

    coordinator_nodes: dict[str, list[dict[str, str]]] = {}
    coordinators: dict[str, AsyncuaCoordinator] = {}
    asyncua_covers: list = []

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

        # Create covers with injecting respective asyncua coordinator
        for _idx_cover, val_cover in enumerate(val_coordinator):
            asyncua_covers.append(
                AsyncuaCover(
                    coordinator=coordinators[key_coordinator],
                    name=val_cover[CONF_NODE_NAME],
                    unique_id=val_cover.get(CONF_NODE_UNIQUE_ID),
                    hub=val_cover[CONF_NODE_HUB],
                    node_id=val_cover[CONF_NODE_ID],
                    travel_time_down=val_cover.get(CONF_TRAVELLING_TIME_DOWN, DEFAULT_TRAVEL_TIME),
                    travel_time_up=val_cover.get(CONF_TRAVELLING_TIME_UP, DEFAULT_TRAVEL_TIME),
                    open_nodeid=val_cover[CONF_OPEN_NODEID],
                    close_nodeid=val_cover[CONF_CLOSE_NODEID],
                    stop_nodeid=val_cover.get(CONF_STOP_NODEID),
                    fully_open_nodeid=val_cover.get(CONF_FULLY_OPEN_NODEID),
                    fully_closed_nodeid=val_cover.get(CONF_FULLY_CLOSED_NODEID),
                )
            )

    async_add_entities(new_entities=asyncua_covers)

    # Register cover services
    from homeassistant.helpers import entity_platform
    platform = entity_platform.current_platform.get()

    platform.async_register_entity_service(
        SERVICE_SET_POSITION,
        SET_POSITION_SCHEMA,
        "async_service_set_position",
    )

    platform.async_register_entity_service(
        SERVICE_RESET_FULLY_OPEN,
        RESET_POSITION_SCHEMA,
        "async_service_reset_fully_open",
    )

    platform.async_register_entity_service(
        SERVICE_RESET_FULLY_CLOSED,
        RESET_POSITION_SCHEMA,
        "async_service_reset_fully_closed",
    )


class AsyncuaCover(CoordinatorEntity[AsyncuaCoordinator], CoverEntity, RestoreEntity):
    """A cover implementation for Asyncua OPCUA nodes."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: AsyncuaCoordinator,
        name: str,
        hub: str,
        node_id: str,
        travel_time_down: int,
        travel_time_up: int,
        open_nodeid: str,
        close_nodeid: str,
        stop_nodeid: str | None = None,
        fully_open_nodeid: str | None = None,
        fully_closed_nodeid: str | None = None,
        unique_id: str | None = None,
    ) -> None:
        """Initialize the cover."""
        super().__init__(coordinator=coordinator)
        self._attr_name = name
        self._hub = hub
        self._node_id = node_id
        self._attr_unique_id = (
            unique_id if unique_id is not None else node_id
        )
        self._attr_available = False
        self._hub = hub
        self._node_id = node_id
        self._travel_time_down = travel_time_down
        self._travel_time_up = travel_time_up
        self._open_nodeid = open_nodeid
        self._close_nodeid = close_nodeid
        self._stop_nodeid = stop_nodeid
        self._fully_open_nodeid = fully_open_nodeid
        self._fully_closed_nodeid = fully_closed_nodeid
        self._target_position = 50
        self._unsubscribe_auto_updater = None
        
        # Track active command to keep signal high during travel
        self._active_command = None  # "open", "close", or None
        self._command_started = False

        # Travel calculator
        self.tc = TravelCalculator(self._travel_time_down, self._travel_time_up)

    async def async_added_to_hass(self):
        """Restore cover position from last state."""
        await super().async_added_to_hass()
        old_state = await self.async_get_last_state()
        _LOGGER.debug(
            "%s: async_added_to_hass - oldState %s",
            self._attr_name,
            old_state,
        )
        if (
            old_state is not None
            and self.tc is not None
            and old_state.attributes.get(ATTR_CURRENT_POSITION) is not None
        ):
            self.tc.set_position(int(old_state.attributes.get(ATTR_CURRENT_POSITION)))

    async def _check_limit_switches(self) -> None:
        """Check limit switches and update position if activated."""
        if self._fully_open_nodeid:
            try:
                fully_open_state = await self.coordinator.hub.get_value(
                    nodeid=self._fully_open_nodeid
                )
                if fully_open_state:
                    _LOGGER.debug(
                        "%s: Fully open sensor activated, setting position to 100",
                        self._attr_name,
                    )
                    self.tc.set_position(100)
                    self._handle_stop()
                    return
            except Exception as e:
                _LOGGER.debug(
                    "%s: Error reading fully_open sensor: %s",
                    self._attr_name,
                    e,
                )

        if self._fully_closed_nodeid:
            try:
                fully_closed_state = await self.coordinator.hub.get_value(
                    nodeid=self._fully_closed_nodeid
                )
                if fully_closed_state:
                    _LOGGER.debug(
                        "%s: Fully closed sensor activated, setting position to 0",
                        self._attr_name,
                    )
                    self.tc.set_position(0)
                    self._handle_stop()
                    return
            except Exception as e:
                _LOGGER.debug(
                    "%s: Error reading fully_closed sensor: %s",
                    self._attr_name,
                    e,
                )

    @property
    def unique_id(self) -> str | None:
        """Return the unique_id of the cover."""
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
    def supported_features(self) -> CoverEntityFeature:
        """Return the supported features of the cover."""
        return (
            CoverEntityFeature.OPEN
            | CoverEntityFeature.CLOSE
            | CoverEntityFeature.STOP
            | CoverEntityFeature.SET_POSITION
        )

    @property
    def current_cover_position(self) -> int:
        """Return the current position of the cover."""
        return self.tc.current_position()

    @property
    def is_opening(self) -> bool:
        """Return if the cover is opening or not."""
        return (
            self.tc.is_traveling()
            and self.tc.travel_direction == TravelStatus.DIRECTION_UP
        )

    @property
    def is_closing(self) -> bool:
        """Return if the cover is closing or not."""
        return (
            self.tc.is_traveling()
            and self.tc.travel_direction == TravelStatus.DIRECTION_DOWN
        )

    @property
    def is_closed(self) -> bool:
        """Return if the cover is closed."""
        return self.tc.is_closed()

    @property
    def assumed_state(self) -> bool:
        """Return True because we calculate position based on time."""
        return True

    async def async_open_cover(self, **kwargs: Any) -> None:
        """Open the cover."""
        _LOGGER.debug("%s: async_open_cover", self._attr_name)
        self.tc.start_travel_up()
        self._target_position = 100
        self._active_command = "open"
        self._command_started = False
        self.start_auto_updater()
        await self._send_command_start("open")

    async def async_close_cover(self, **kwargs: Any) -> None:
        """Close the cover."""
        _LOGGER.debug("%s: async_close_cover", self._attr_name)
        self.tc.start_travel_down()
        self._target_position = 0
        self._active_command = "close"
        self._command_started = False
        self.start_auto_updater()
        await self._send_command_start("close")

    async def async_stop_cover(self, **kwargs: Any) -> None:
        """Stop the cover."""
        _LOGGER.debug("%s: async_stop_cover", self._attr_name)
        self._handle_stop()
        await self._send_command_stop()

    async def async_set_cover_position(self, **kwargs: Any) -> None:
        """Move the cover to a specific position."""
        if ATTR_POSITION in kwargs:
            position = kwargs[ATTR_POSITION]
            _LOGGER.debug(
                "%s: async_set_cover_position - position: %d",
                self._attr_name,
                position,
            )
            await self.set_position(position)

    def _handle_stop(self) -> None:
        """Handle stop."""
        if self.tc.is_traveling():
            _LOGGER.debug("%s: _handle_stop - stopping cover", self._attr_name)
            self.tc.stop()
            self.stop_auto_updater()

    def start_auto_updater(self) -> None:
        """Start the autoupdater to update HA while cover is moving."""
        _LOGGER.debug("%s: start_auto_updater", self._attr_name)
        if self._unsubscribe_auto_updater is None:
            _LOGGER.debug("%s: Initializing auto updater", self._attr_name)
            interval = timedelta(milliseconds=100)
            self._unsubscribe_auto_updater = async_track_time_interval(
                self.hass, self.auto_updater_hook, interval
            )

    @callback
    def auto_updater_hook(self, now: Any) -> None:
        """Call for the autoupdater."""
        _LOGGER.debug(
            "%s: auto_updater_hook - position: %d, target: %d",
            self._attr_name,
            self.tc.current_position(),
            self.tc.travel_to_position,
        )
        
        # Keep command signal active during travel
        if self._active_command and not self._command_started:
            _LOGGER.debug(
                "%s: Starting command signal for %s",
                self._attr_name,
                self._active_command,
            )
            self._command_started = True
        
        # Check limit switches asynchronously
        self.hass.async_create_task(self._check_limit_switches())
        
        self.async_write_ha_state()
        
        if self.position_reached():
            _LOGGER.debug("%s: Position reached, stopping updater", self._attr_name)
            self.stop_auto_updater()

    def stop_auto_updater(self) -> None:
        """Stop the autoupdater and deactivate command signals."""
        _LOGGER.debug("%s: stop_auto_updater", self._attr_name)
        if self._unsubscribe_auto_updater is not None:
            self._unsubscribe_auto_updater()
            self._unsubscribe_auto_updater = None
        
        # Deactivate command signals
        if self._active_command:
            _LOGGER.debug(
                "%s: Deactivating command signal for %s",
                self._attr_name,
                self._active_command,
            )
            self.hass.async_create_task(self._send_command_stop())
            self._active_command = None
            self._command_started = False

    def position_reached(self) -> bool:
        """Return if cover has reached its final position."""
        return self.tc.position_reached()

    async def set_position(self, position: int) -> None:
        """Move cover to a designated position."""
        _LOGGER.debug(
            "%s: set_position - current: %d, target: %d",
            self._attr_name,
            self.tc.current_position(),
            position,
        )
        current_position = self.tc.current_position()

        if position < current_position:
            self.tc.start_travel(position)
            self._active_command = "close"
            self._command_started = False
            self.start_auto_updater()
            await self._send_command_start("close")
        elif position > current_position:
            self.tc.start_travel(position)
            self._active_command = "open"
            self._command_started = False
            self.start_auto_updater()
            await self._send_command_start("open")

    async def _send_command_start(self, command_type: str) -> None:
        """Send START command to OPCUA node (set to True)."""
        if command_type == "open":
            nodeid = self._open_nodeid
            cmd_name = "OPEN"
        elif command_type == "close":
            nodeid = self._close_nodeid
            cmd_name = "CLOSE"
        else:
            _LOGGER.error("%s: Unknown command type: %s", self._attr_name, command_type)
            return

        try:
            _LOGGER.debug(
                "%s: Starting command %s on node %s (value=True)",
                self._attr_name,
                cmd_name,
                nodeid,
            )
            await self.coordinator.hub.set_value(nodeid=nodeid, value=True)
        except Exception as e:
            _LOGGER.error(
                "%s: Error starting command %s: %s",
                self._attr_name,
                cmd_name,
                e,
            )

    async def _send_command_stop(self) -> None:
        """Send STOP command to OPCUA nodes (set to False)."""
        try:
            if self._active_command == "open":
                nodeid = self._open_nodeid
                cmd_name = "OPEN"
            elif self._active_command == "close":
                nodeid = self._close_nodeid
                cmd_name = "CLOSE"
            else:
                return

            _LOGGER.debug(
                "%s: Stopping command %s on node %s (value=False)",
                self._attr_name,
                cmd_name,
                nodeid,
            )
            await self.coordinator.hub.set_value(nodeid=nodeid, value=False)
            
            # Also send to STOP node if available
            if self._stop_nodeid:
                _LOGGER.debug(
                    "%s: Sending STOP signal to node %s (value=True)",
                    self._attr_name,
                    self._stop_nodeid,
                )
                await self.coordinator.hub.set_value(nodeid=self._stop_nodeid, value=True)
        except Exception as e:
            _LOGGER.error(
                "%s: Error stopping command: %s",
                self._attr_name,
                e,
            )

    async def async_service_set_position(self, **kwargs: Any) -> None:
        """Service call to set a specific position."""
        if ATTR_POSITION in kwargs:
            position = kwargs[ATTR_POSITION]
            _LOGGER.debug(
                "%s: Service set_position called with position: %d",
                self._attr_name,
                position,
            )
            await self.set_position(position)

    async def async_service_reset_fully_open(self, **kwargs: Any) -> None:
        """Service call to reset position to fully open (100%)."""
        _LOGGER.debug(
            "%s: Service reset_fully_open called",
            self._attr_name,
        )
        self.tc.set_position(100)
        self._handle_stop()
        self.async_write_ha_state()

    async def async_service_reset_fully_closed(self, **kwargs: Any) -> None:
        """Service call to reset position to fully closed (0%)."""
        _LOGGER.debug(
            "%s: Service reset_fully_closed called",
            self._attr_name,
        )
        self.tc.set_position(0)
        self._handle_stop()
        self.async_write_ha_state()
