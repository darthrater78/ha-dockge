"""Setup, entity, and service tests for the Dockge integration."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers import entity_registry as er

from custom_components.dockge.const import DOMAIN

from .conftest import URL, make_entry, mock_dockge


@pytest.fixture(autouse=True)
def no_burst():
    """Keep the 5-minute refresh burst out of the tests."""
    with patch("custom_components.dockge.coordinator.DockgeCoordinator.start_refresh_burst"):
        yield


async def _setup(hass: HomeAssistant, aioclient_mock, base: str = URL):
    mock_dockge(aioclient_mock, base)
    entry = make_entry(base)
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


def _posts(aioclient_mock) -> list[str]:
    return [str(url) for method, url, _data, _headers in aioclient_mock.mock_calls if method.upper() == "POST"]


async def test_setup_creates_entities(hass: HomeAssistant, aioclient_mock) -> None:
    entry = await _setup(hass, aioclient_mock)
    assert entry.state is ConfigEntryState.LOADED

    registry = er.async_get(hass)
    unique_ids = {e.unique_id for e in er.async_entries_for_config_entry(registry, entry.entry_id)}
    # Unique IDs from before the button refactor must be unchanged.
    for action in ("start", "stop", "restart", "down"):
        assert f"{entry.entry_id}_{action}__web" in unique_ids
        assert f"{entry.entry_id}_{action}_gastly:5001_db" in unique_ids
    assert f"{entry.entry_id}_container__web_nginx" in unique_ids

    for method, url, _data, headers in aioclient_mock.mock_calls:
        assert headers["X-API-Key"] == "secret", (method, url)


async def test_button_press_calls_api(hass: HomeAssistant, aioclient_mock) -> None:
    entry = await _setup(hass, aioclient_mock)
    registry = er.async_get(hass)
    entity_id = registry.async_get_entity_id("button", DOMAIN, f"{entry.entry_id}_restart__web")
    await hass.services.async_call("button", "press", {"entity_id": entity_id}, blocking=True)
    assert any(url.endswith("/api/stacks/web/restart") for url in _posts(aioclient_mock))


async def test_service_with_agent_uses_encoded_query(hass: HomeAssistant, aioclient_mock) -> None:
    await _setup(hass, aioclient_mock)
    await hass.services.async_call(
        DOMAIN, "stop_stack", {"stack_name": "db", "agent": "gastly"}, blocking=True
    )
    urls = _posts(aioclient_mock)
    assert f"{URL}/api/stacks/db/stop?endpoint=gastly:5001" in urls


@pytest.mark.parametrize(
    "stack_name",
    ["../system/prune", "web?x=1", "web/../../x", "Web", "web#frag", ""],
)
async def test_service_rejects_bad_stack_names(hass: HomeAssistant, aioclient_mock, stack_name) -> None:
    await _setup(hass, aioclient_mock)
    with pytest.raises(ServiceValidationError):
        await hass.services.async_call(
            DOMAIN, "start_stack", {"stack_name": stack_name}, blocking=True
        )
    assert _posts(aioclient_mock) == []


async def test_service_rejects_unknown_agent(hass: HomeAssistant, aioclient_mock) -> None:
    await _setup(hass, aioclient_mock)
    with pytest.raises(ServiceValidationError):
        await hass.services.async_call(
            DOMAIN, "system_prune", {"agent": "x&endpoint=evil"}, blocking=True
        )
    assert _posts(aioclient_mock) == []


async def test_services_with_two_entries(hass: HomeAssistant, aioclient_mock) -> None:
    other = "http://other.local:5001"
    first = await _setup(hass, aioclient_mock)
    second = await _setup(hass, aioclient_mock, other)

    # Ambiguous without config_entry_id.
    with pytest.raises(ServiceValidationError):
        await hass.services.async_call(DOMAIN, "system_prune", {}, blocking=True)

    await hass.services.async_call(
        DOMAIN, "system_prune", {"config_entry_id": first.entry_id}, blocking=True
    )
    assert _posts(aioclient_mock) == [f"{URL}/api/system/prune"]

    # Unloading one instance leaves services working for the other.
    assert await hass.config_entries.async_unload(first.entry_id)
    await hass.async_block_till_done()
    assert hass.services.has_service(DOMAIN, "restart_stack")
    await hass.services.async_call(
        DOMAIN, "restart_stack", {"stack_name": "web"}, blocking=True
    )
    assert f"{other}/api/stacks/web/restart" in _posts(aioclient_mock)
    assert second.state is ConfigEntryState.LOADED


async def test_api_error_raises_ha_error(hass: HomeAssistant, aioclient_mock) -> None:
    await _setup(hass, aioclient_mock)
    aioclient_mock.post(f"{URL}/api/stacks/web/start", status=500)
    with pytest.raises(HomeAssistantError):
        await hass.services.async_call(DOMAIN, "start_stack", {"stack_name": "web"}, blocking=True)
