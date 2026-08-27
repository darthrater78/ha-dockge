"""The Dockge integration."""

import asyncio
import logging

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv

from .const import DOMAIN
from .coordinator import DockgeCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor", "button"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Dockge from a config entry."""
    _LOGGER.debug("Setting up Dockge entry %s with data: %s", entry.entry_id, {k: v for k, v in entry.data.items() if k != "api_key"})
    try:
        coordinator = DockgeCoordinator(hass, entry)
        await coordinator.async_config_entry_first_refresh()
    except Exception:
        _LOGGER.exception("Failed to set up Dockge coordinator")
        raise

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Register services
    def _resolve_endpoint(agent_name: str) -> str:
        """Resolve agent display name to endpoint. Empty string = primary."""
        if not agent_name:
            return ""
        agent_names_map = coordinator.data.get("agent_names", {})
        for ep, name in agent_names_map.items():
            if name.lower() == agent_name.lower():
                return ep
        return agent_name

    STACK_ACTION_SCHEMA = vol.Schema({
        vol.Required("stack_name"): cv.string,
        vol.Optional("agent", default=""): cv.string,
    })

    async def _handle_stack_action(call, action_path: str) -> None:
        stack_name = call.data["stack_name"]
        endpoint = _resolve_endpoint(call.data.get("agent", ""))
        endpoint_param = f"?endpoint={endpoint}" if endpoint else ""
        coordinator.mark_busy(endpoint, stack_name)
        await asyncio.sleep(0.1)
        try:
            await coordinator.api_call("POST", f"/api/stacks/{stack_name}/{action_path}{endpoint_param}", timeout=300)
        finally:
            coordinator.mark_done(endpoint, stack_name)
            await coordinator.async_request_refresh()
            coordinator.start_refresh_burst()

    def _make_stack_handler(action_path: str):
        async def handler(call) -> None:
            await _handle_stack_action(call, action_path)
        return handler

    for service_name, path in [
        ("start_stack", "start"),
        ("stop_stack", "stop"),
        ("restart_stack", "restart"),
    ]:
        hass.services.async_register(
            DOMAIN, service_name,
            _make_stack_handler(path),
            schema=STACK_ACTION_SCHEMA,
        )

    async def _handle_system_prune(call) -> None:
        endpoint = _resolve_endpoint(call.data.get("agent", ""))
        endpoint_param = f"?endpoint={endpoint}" if endpoint else ""
        await coordinator.api_call("POST", f"/api/system/prune{endpoint_param}")
        await coordinator.async_request_refresh()

    hass.services.async_register(
        DOMAIN, "system_prune", _handle_system_prune,
        schema=vol.Schema({vol.Optional("agent", default=""): cv.string}),
    )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    for svc in ["start_stack", "stop_stack", "restart_stack", "system_prune"]:
        if hass.services.has_service(DOMAIN, svc):
            hass.services.async_remove(DOMAIN, svc)

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
