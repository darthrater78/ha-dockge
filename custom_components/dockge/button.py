"""Button platform for the Dockge integration."""

from __future__ import annotations

import asyncio

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import DockgeCoordinator
from .devices import agent_display_name, stack_device_info


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Dockge buttons."""
    coordinator: DockgeCoordinator = hass.data[DOMAIN][entry.entry_id]

    # Global buttons per agent
    entities: list[ButtonEntity] = []
    agents = coordinator.data.get("agents") or []
    agent_names = coordinator.data.get("agent_names", {})
    multi_agent = coordinator.data.get("multi_agent", False)
    update_feature_supported = coordinator.data.get("update_feature_supported", True)

    if not agents:
        agents = [{"endpoint": ""}]

    # Per-stack buttons (dynamically tracked)
    tracked: set[str] = set()

    @callback
    def _async_add_new_entities() -> None:
        stacks = coordinator.data.get("stacks") or []
        names = coordinator.data.get("agent_names", {})
        is_multi = coordinator.data.get("multi_agent", False)
        supported = coordinator.data.get("update_feature_supported", True)
        new_entities = []
        for stack in stacks:
            key = f"{stack.get('endpoint', '')}|{stack['name']}"
            if key not in tracked:
                tracked.add(key)
                ep = stack.get("endpoint", "")
                aname = agent_display_name(names, ep)
                if supported:
                    new_entities.append(
                        DockgeUpdateStackButton(coordinator, entry, stack, aname, multi_agent=is_multi)
                    )
                    new_entities.append(
                        DockgeCheckUpdatesButton(coordinator, entry, stack, aname, multi_agent=is_multi)
                    )
                new_entities.append(
                    DockgeStartStackButton(coordinator, entry, stack, aname, multi_agent=is_multi)
                )
                new_entities.append(
                    DockgeStopStackButton(coordinator, entry, stack, aname, multi_agent=is_multi)
                )
                new_entities.append(
                    DockgeRestartStackButton(coordinator, entry, stack, aname, multi_agent=is_multi)
                )
                new_entities.append(
                    DockgeDownStackButton(coordinator, entry, stack, aname, multi_agent=is_multi)
                )
        if new_entities:
            async_add_entities(new_entities)

    # Add initial per-stack buttons
    stacks = coordinator.data.get("stacks") or []
    for stack in stacks:
        key = f"{stack.get('endpoint', '')}|{stack['name']}"
        tracked.add(key)
        ep = stack.get("endpoint", "")
        aname = agent_display_name(agent_names, ep)
        if update_feature_supported:
            entities.append(DockgeUpdateStackButton(coordinator, entry, stack, aname, multi_agent=multi_agent))
            entities.append(DockgeCheckUpdatesButton(coordinator, entry, stack, aname, multi_agent=multi_agent))
        entities.append(DockgeStartStackButton(coordinator, entry, stack, aname, multi_agent=multi_agent))
        entities.append(DockgeStopStackButton(coordinator, entry, stack, aname, multi_agent=multi_agent))
        entities.append(DockgeRestartStackButton(coordinator, entry, stack, aname, multi_agent=multi_agent))
        entities.append(DockgeDownStackButton(coordinator, entry, stack, aname, multi_agent=multi_agent))

    async_add_entities(entities)
    entry.async_on_unload(coordinator.async_add_listener(_async_add_new_entities))


class DockgeUpdateStackButton(CoordinatorEntity, ButtonEntity):
    """Button to trigger update for a single stack."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:package-up"

    def __init__(
        self, coordinator: DockgeCoordinator, entry: ConfigEntry,
        stack: dict, agent_name: str, *, multi_agent: bool = False,
    ) -> None:
        super().__init__(coordinator)
        self._stack_name = stack["name"]
        self._endpoint = stack.get("endpoint", "")
        self._attr_unique_id = f"{entry.entry_id}_update_{self._endpoint}_{self._stack_name}"
        self._attr_name = "Update"
        self._attr_device_info = stack_device_info(
            entry.entry_id, self._endpoint, self._stack_name, agent_name,
            multi_agent=multi_agent,
        )

    async def async_press(self) -> None:
        endpoint_param = f"?endpoint={self._endpoint}" if self._endpoint else ""
        self.coordinator.mark_busy(self._endpoint, self._stack_name)
        await asyncio.sleep(0.1)  # Let event loop propagate busy state to frontend
        try:
            await self.coordinator.api_call(
                "POST", f"/api/stacks/{self._stack_name}/update{endpoint_param}"
            )
        finally:
            self.coordinator.mark_done(self._endpoint, self._stack_name)
            await self.coordinator.async_request_refresh()


class DockgeCheckUpdatesButton(CoordinatorEntity, ButtonEntity):
    """Button to force check for image updates on a single stack."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:magnify"

    def __init__(
        self, coordinator: DockgeCoordinator, entry: ConfigEntry,
        stack: dict, agent_name: str, *, multi_agent: bool = False,
    ) -> None:
        super().__init__(coordinator)
        self._stack_name = stack["name"]
        self._endpoint = stack.get("endpoint", "")
        self._attr_unique_id = f"{entry.entry_id}_check_updates_{self._endpoint}_{self._stack_name}"
        self._attr_name = "Check Updates"
        self._attr_device_info = stack_device_info(
            entry.entry_id, self._endpoint, self._stack_name, agent_name,
            multi_agent=multi_agent,
        )

    async def async_press(self) -> None:
        endpoint_param = f"?endpoint={self._endpoint}" if self._endpoint else ""
        self.coordinator.mark_busy(self._endpoint, self._stack_name)
        await asyncio.sleep(0.1)  # Let event loop propagate busy state to frontend
        try:
            await self.coordinator.api_call(
                "POST", f"/api/stacks/{self._stack_name}/check-updates{endpoint_param}"
            )
        finally:
            self.coordinator.mark_done(self._endpoint, self._stack_name)
            await self.coordinator.async_request_refresh()


class DockgeStartStackButton(CoordinatorEntity, ButtonEntity):
    """Button to start a stack."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:play"

    def __init__(
        self, coordinator: DockgeCoordinator, entry: ConfigEntry,
        stack: dict, agent_name: str, *, multi_agent: bool = False,
    ) -> None:
        super().__init__(coordinator)
        self._stack_name = stack["name"]
        self._endpoint = stack.get("endpoint", "")
        self._attr_unique_id = f"{entry.entry_id}_start_{self._endpoint}_{self._stack_name}"
        self._attr_name = "Start"
        self._attr_device_info = stack_device_info(
            entry.entry_id, self._endpoint, self._stack_name, agent_name,
            multi_agent=multi_agent,
        )

    async def async_press(self) -> None:
        endpoint_param = f"?endpoint={self._endpoint}" if self._endpoint else ""
        self.coordinator.mark_busy(self._endpoint, self._stack_name)
        await asyncio.sleep(0.1)
        try:
            await self.coordinator.api_call(
                "POST", f"/api/stacks/{self._stack_name}/start{endpoint_param}"
            )
        finally:
            self.coordinator.mark_done(self._endpoint, self._stack_name)
            await self.coordinator.async_request_refresh()


class DockgeStopStackButton(CoordinatorEntity, ButtonEntity):
    """Button to stop a stack."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:stop"

    def __init__(
        self, coordinator: DockgeCoordinator, entry: ConfigEntry,
        stack: dict, agent_name: str, *, multi_agent: bool = False,
    ) -> None:
        super().__init__(coordinator)
        self._stack_name = stack["name"]
        self._endpoint = stack.get("endpoint", "")
        self._attr_unique_id = f"{entry.entry_id}_stop_{self._endpoint}_{self._stack_name}"
        self._attr_name = "Stop"
        self._attr_device_info = stack_device_info(
            entry.entry_id, self._endpoint, self._stack_name, agent_name,
            multi_agent=multi_agent,
        )

    async def async_press(self) -> None:
        endpoint_param = f"?endpoint={self._endpoint}" if self._endpoint else ""
        self.coordinator.mark_busy(self._endpoint, self._stack_name)
        await asyncio.sleep(0.1)
        try:
            await self.coordinator.api_call(
                "POST", f"/api/stacks/{self._stack_name}/stop{endpoint_param}"
            )
        finally:
            self.coordinator.mark_done(self._endpoint, self._stack_name)
            await self.coordinator.async_request_refresh()


class DockgeRestartStackButton(CoordinatorEntity, ButtonEntity):
    """Button to restart a stack."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:restart"

    def __init__(
        self, coordinator: DockgeCoordinator, entry: ConfigEntry,
        stack: dict, agent_name: str, *, multi_agent: bool = False,
    ) -> None:
        super().__init__(coordinator)
        self._stack_name = stack["name"]
        self._endpoint = stack.get("endpoint", "")
        self._attr_unique_id = f"{entry.entry_id}_restart_{self._endpoint}_{self._stack_name}"
        self._attr_name = "Restart"
        self._attr_device_info = stack_device_info(
            entry.entry_id, self._endpoint, self._stack_name, agent_name,
            multi_agent=multi_agent,
        )

    async def async_press(self) -> None:
        endpoint_param = f"?endpoint={self._endpoint}" if self._endpoint else ""
        self.coordinator.mark_busy(self._endpoint, self._stack_name)
        await asyncio.sleep(0.1)
        try:
            await self.coordinator.api_call(
                "POST", f"/api/stacks/{self._stack_name}/restart{endpoint_param}"
            )
        finally:
            self.coordinator.mark_done(self._endpoint, self._stack_name)
            await self.coordinator.async_request_refresh()


class DockgeDownStackButton(CoordinatorEntity, ButtonEntity):
    """Button to stop and remove containers (make stack inactive)."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:power-off"

    def __init__(
        self, coordinator: DockgeCoordinator, entry: ConfigEntry,
        stack: dict, agent_name: str, *, multi_agent: bool = False,
    ) -> None:
        super().__init__(coordinator)
        self._stack_name = stack["name"]
        self._endpoint = stack.get("endpoint", "")
        self._attr_unique_id = f"{entry.entry_id}_down_{self._endpoint}_{self._stack_name}"
        self._attr_name = "Down"
        self._attr_device_info = stack_device_info(
            entry.entry_id, self._endpoint, self._stack_name, agent_name,
            multi_agent=multi_agent,
        )

    async def async_press(self) -> None:
        endpoint_param = f"?endpoint={self._endpoint}" if self._endpoint else ""
        self.coordinator.mark_busy(self._endpoint, self._stack_name)
        await asyncio.sleep(0.1)
        try:
            await self.coordinator.api_call(
                "POST", f"/api/stacks/{self._stack_name}/down{endpoint_param}"
            )
        finally:
            self.coordinator.mark_done(self._endpoint, self._stack_name)
            await self.coordinator.async_request_refresh()
