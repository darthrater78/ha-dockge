"""Config flow for Dockge integration."""

from __future__ import annotations

import logging

import aiohttp
import voluptuous as vol
from yarl import URL

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import CONF_API_KEY, CONF_SCAN_INTERVAL, CONF_URL, DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_URL): str,
        vol.Required(CONF_API_KEY): str,
        vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): vol.All(
            int, vol.Range(min=30)
        ),
    }
)


def _is_valid_url(url: str) -> bool:
    """Accept only http(s) URLs with a host."""
    try:
        parsed = URL(url)
    except ValueError:
        return False
    return parsed.scheme in ("http", "https") and bool(parsed.host)


class DockgeConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Dockge."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            url = user_input[CONF_URL].strip().rstrip("/")
            api_key = user_input[CONF_API_KEY]

            if not _is_valid_url(url):
                errors[CONF_URL] = "invalid_url"
            else:
                errors.update(await self._async_check_connection(url, api_key))

            if not errors:
                await self.async_set_unique_id(url)
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=f"Dockge ({url})",
                    data={**user_input, CONF_URL: url},
                )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

    async def _async_check_connection(self, url: str, api_key: str) -> dict[str, str]:
        """Call /api/agents (authenticated) to check both the URL and the API key."""
        session = async_get_clientsession(self.hass)
        try:
            async with session.get(
                f"{url}/api/agents",
                headers={"X-API-Key": api_key},
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                if resp.status == 401:
                    return {"base": "invalid_auth"}
                resp.raise_for_status()
        except (aiohttp.ClientError, TimeoutError):
            return {"base": "cannot_connect"}
        except Exception:  # noqa: BLE001 - config flow must not crash on unexpected errors
            _LOGGER.exception("Unexpected error validating Dockge connection")
            return {"base": "unknown"}
        return {}
