"""Config flow tests for the Dockge integration."""

from __future__ import annotations

import pytest

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.dockge.const import CONF_API_KEY, CONF_URL, DOMAIN

from .conftest import URL


async def _start(hass: HomeAssistant, user_input: dict):
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    return await hass.config_entries.flow.async_configure(result["flow_id"], user_input)


async def test_create_entry_normalizes_url(hass: HomeAssistant, aioclient_mock) -> None:
    aioclient_mock.get(f"{URL}/api/agents", json={"agents": []})
    result = await _start(hass, {CONF_URL: f" {URL}/ ", CONF_API_KEY: "secret"})
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"][CONF_URL] == URL


@pytest.mark.parametrize("url", ["dockge.local:5001", "ftp://dockge.local", "http://", "not a url"])
async def test_invalid_url(hass: HomeAssistant, aioclient_mock, url: str) -> None:
    result = await _start(hass, {CONF_URL: url, CONF_API_KEY: "secret"})
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {CONF_URL: "invalid_url"}
    assert aioclient_mock.call_count == 0


async def test_invalid_auth(hass: HomeAssistant, aioclient_mock) -> None:
    aioclient_mock.get(f"{URL}/api/agents", status=401)
    result = await _start(hass, {CONF_URL: URL, CONF_API_KEY: "wrong"})
    assert result["errors"] == {"base": "invalid_auth"}


async def test_cannot_connect(hass: HomeAssistant, aioclient_mock) -> None:
    aioclient_mock.get(f"{URL}/api/agents", status=500)
    result = await _start(hass, {CONF_URL: URL, CONF_API_KEY: "secret"})
    assert result["errors"] == {"base": "cannot_connect"}
