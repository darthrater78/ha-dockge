"""The Dockge integration."""

from __future__ import annotations

import logging

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigEntryState
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN
from .coordinator import DockgeCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor", "button"]

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

ATTR_CONFIG_ENTRY_ID = "config_entry_id"

_BASE_SCHEMA = {
    vol.Optional("agent", default=""): cv.string,
    vol.Optional(ATTR_CONFIG_ENTRY_ID): cv.string,
}
STACK_ACTION_SCHEMA = vol.Schema({vol.Required("stack_name"): cv.string, **_BASE_SCHEMA})
SYSTEM_PRUNE_SCHEMA = vol.Schema(_BASE_SCHEMA)

STACK_SERVICES = {
    "start_stack": "start",
    "stop_stack": "stop",
    "restart_stack": "restart",
}


def _get_coordinator(hass: HomeAssistant, call: ServiceCall) -> DockgeCoordinator:
    """Pick the Dockge instance a service call targets."""
    loaded = {
        entry.entry_id: entry.runtime_data
        for entry in hass.config_entries.async_entries(DOMAIN)
        if entry.state is ConfigEntryState.LOADED
    }
    entry_id = call.data.get(ATTR_CONFIG_ENTRY_ID)
    if entry_id:
        if entry_id not in loaded:
            raise ServiceValidationError(f"Dockge config entry {entry_id!r} is not loaded")
        return loaded[entry_id]
    if len(loaded) == 1:
        return next(iter(loaded.values()))
    if not loaded:
        raise ServiceValidationError("No Dockge instance is loaded")
    raise ServiceValidationError(
        "Several Dockge instances are configured; set config_entry_id to choose one"
    )


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Register Dockge services once, shared by every config entry."""

    async def _handle_stack_action(call: ServiceCall) -> None:
        coordinator = _get_coordinator(hass, call)
        endpoint = coordinator.resolve_endpoint(call.data["agent"])
        await coordinator.async_stack_action(
            endpoint, call.data["stack_name"], STACK_SERVICES[call.service]
        )

    async def _handle_system_prune(call: ServiceCall) -> None:
        coordinator = _get_coordinator(hass, call)
        await coordinator.async_system_prune(coordinator.resolve_endpoint(call.data["agent"]))

    for service_name in STACK_SERVICES:
        hass.services.async_register(
            DOMAIN, service_name, _handle_stack_action, schema=STACK_ACTION_SCHEMA
        )
    hass.services.async_register(
        DOMAIN, "system_prune", _handle_system_prune, schema=SYSTEM_PRUNE_SCHEMA
    )
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Dockge from a config entry."""
    _LOGGER.debug("Setting up Dockge entry %s with data: %s", entry.entry_id, {k: v for k, v in entry.data.items() if k != "api_key"})
    coordinator = DockgeCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator
    entry.async_on_unload(coordinator.cancel_refresh_burst)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
