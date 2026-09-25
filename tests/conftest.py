"""Fixtures for Dockge tests."""

from __future__ import annotations

import pytest

from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.test_util.aiohttp import AiohttpClientMocker

from custom_components.dockge.const import CONF_API_KEY, CONF_SCAN_INTERVAL, CONF_URL, DOMAIN

URL = "http://dockge.local:5001"

AGENTS = {
    "agents": [
        {"endpoint": "", "name": "Primary", "version": "1.8.0"},
        {"endpoint": "gastly:5001", "name": "Gastly", "version": "1.8.0"},
    ]
}
STACKS = {
    "stacks": [
        {
            "name": "web",
            "endpoint": "",
            "services": {"nginx": {"state": "running", "image": "nginx:1.27", "containerName": "web-nginx-1"}},
        },
        {
            "name": "db",
            "endpoint": "gastly:5001",
            "services": {"postgres": {"state": "exited", "image": "postgres:17"}},
        },
    ]
}


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Load custom_components/ in every test."""
    return


def mock_dockge(aioclient_mock: AiohttpClientMocker, base: str = URL) -> None:
    """Register the Dockge API responses."""
    aioclient_mock.get(f"{base}/api/agents", json=AGENTS)
    aioclient_mock.get(f"{base}/api/stacks", json=STACKS)
    aioclient_mock.post(f"{base}/api/stacks/web/restart", json={"ok": True})
    aioclient_mock.post(f"{base}/api/stacks/db/stop", json={"ok": True})
    aioclient_mock.post(f"{base}/api/system/prune", json={"ok": True})


def make_entry(base: str = URL) -> MockConfigEntry:
    return MockConfigEntry(
        domain=DOMAIN,
        unique_id=base,
        title=f"Dockge ({base})",
        data={CONF_URL: base, CONF_API_KEY: "secret", CONF_SCAN_INTERVAL: 300},
    )
