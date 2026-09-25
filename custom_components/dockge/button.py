"""Button platform for the Dockge integration."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .coordinator import DockgeCoordinator
from .devices import agent_display_name, stack_device_info

# action -> (entity name, icon); order is the order buttons are created in.
BUTTONS: dict[str, tuple[str, str]] = {
    "start": ("Start", "mdi:play"),
    "stop": ("Stop", "mdi:stop"),
    "restart": ("Restart", "mdi:restart"),
    "down": ("Down", "mdi:power-off"),
}


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Dockge buttons."""
    coordinator: DockgeCoordinator = entry.runtime_data

    # Per-stack buttons (dynamically tracked)
    tracked: set[str] = set()

    @callback
    def _async_add_new_entities() -> None:
        stacks = coordinator.data.get("stacks") or []
        names = coordinator.data.get("agent_names", {})
        is_multi = coordinator.data.get("multi_agent", False)
        new_entities: list[ButtonEntity] = []
        for stack in stacks:
            ep = stack.get("endpoint", "")
            key = f"{ep}|{stack['name']}"
            if key in tracked:
                continue
            tracked.add(key)
            aname = agent_display_name(names, ep)
            new_entities.extend(
                DockgeStackButton(coordinator, entry, stack, aname, action, multi_agent=is_multi)
                for action in BUTTONS
            )
        if new_entities:
            async_add_entities(new_entities)

    _async_add_new_entities()
    entry.async_on_unload(coordinator.async_add_listener(_async_add_new_entities))


class DockgeStackButton(CoordinatorEntity, ButtonEntity):
    """Button that runs one action (start/stop/restart/down) on a stack."""

    _attr_has_entity_name = True

    def __init__(
        self, coordinator: DockgeCoordinator, entry: ConfigEntry,
        stack: dict, agent_name: str, action: str, *, multi_agent: bool = False,
    ) -> None:
        super().__init__(coordinator)
        self._action = action
        self._stack_name = stack["name"]
        self._endpoint = stack.get("endpoint", "")
        self._attr_unique_id = f"{entry.entry_id}_{action}_{self._endpoint}_{self._stack_name}"
        self._attr_name, self._attr_icon = BUTTONS[action]
        self._attr_device_info = stack_device_info(
            entry.entry_id, self._endpoint, self._stack_name, agent_name,
            multi_agent=multi_agent,
        )

    async def async_press(self) -> None:
        await self.coordinator.async_stack_action(self._endpoint, self._stack_name, self._action)
