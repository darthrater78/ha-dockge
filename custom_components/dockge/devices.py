"""Device info helpers for the Dockge integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.helpers.entity import DeviceInfo

from .const import DOMAIN


def agent_display_name(agent_names: dict[str, str], endpoint: str) -> str:
    """Get the display name for an agent endpoint."""
    return agent_names.get(endpoint, endpoint or "Primary")


def agent_device_info(
    entry_id: str, endpoint: str, agent_name: str, *, multi_agent: bool = False,
    version: str | None = None,
) -> DeviceInfo:
    """Return DeviceInfo for an agent (server-level) device."""
    if multi_agent:
        name = f"Dockge Server ({agent_name})"
    else:
        name = "Dockge Server"
    return DeviceInfo(
        identifiers={agent_identifier(entry_id, endpoint)},
        name=name,
        manufacturer="Dockge",
        model="Docker Compose Manager",
        entry_type=DeviceEntryType.SERVICE,
        sw_version=version,
    )


def stack_device_info(
    entry_id: str, endpoint: str, stack_name: str, agent_name: str,
    *, multi_agent: bool = False, via_device_id: str | None = None,
) -> DeviceInfo:
    """Return DeviceInfo for a stack device, child of its agent device.

    Pass the agent device's registry id (from agent_device_id) as via_device_id.
    Without it (Home Assistant before 2026.8) the link falls back to the agent's
    identifier through the old via_device parameter.
    """
    if multi_agent:
        name = f"{stack_name} ({agent_name})"
    else:
        name = stack_name
    link: dict[str, object] = (
        {"via_device_id": via_device_id}
        if via_device_id is not None
        else {"via_device": agent_identifier(entry_id, endpoint)}
    )
    return DeviceInfo(
        identifiers={(DOMAIN, f"{entry_id}_{endpoint}_{stack_name}")},
        name=name,
        manufacturer="Dockge",
        model="Docker Compose Stack",
        **link,
    )


def agent_device_id(
    hass: HomeAssistant, entry: ConfigEntry, endpoint: str, agent_name: str,
    *, multi_agent: bool = False,
) -> str | None:
    """Return the registry id of an agent's device, registering it if needed.

    Home Assistant 2026.8 deprecated linking a device to its parent by identifier
    (via_device, removed in 2027.8) in favour of the parent's device id. Stack devices
    can be set up by the button platform before the sensor platform has registered
    the agent device, so make sure it exists first. Returns None on Home Assistant
    versions without the per-entry lookup, where via_device is still the way.
    """
    dev_reg = dr.async_get(hass)
    if not hasattr(dev_reg, "async_get_device_by_identifier"):
        return None
    identifier = agent_identifier(entry.entry_id, endpoint)
    device = dev_reg.async_get_device_by_identifier(identifier, entry.entry_id)
    if device is None:
        device = dev_reg.async_get_or_create(
            config_entry_id=entry.entry_id,
            **agent_device_info(
                entry.entry_id, endpoint, agent_name, multi_agent=multi_agent
            ),
        )
    return device.id


def agent_identifier(entry_id: str, endpoint: str) -> tuple[str, str]:
    """Return the device identifier of an agent (server-level) device."""
    return (DOMAIN, f"{entry_id}_{endpoint}")
