"""Sensor platform for the Dockge integration."""

from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import DockgeCoordinator
from .devices import agent_device_info, agent_display_name, stack_device_info


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Dockge sensors."""
    coordinator: DockgeCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[SensorEntity] = []
    agents = coordinator.data.get("agents") or []
    agent_names = coordinator.data.get("agent_names", {})
    multi_agent = coordinator.data.get("multi_agent", False)

    if not agents:
        agents = [{"endpoint": ""}]

    for agent in agents:
        endpoint = agent.get("endpoint", "")
        name = agent_display_name(agent_names, endpoint)
        entities.append(
            DockgeAgentSummarySensor(coordinator, entry, endpoint, name, multi_agent),
        )
        entities.append(
            DockgeVersionSensor(coordinator, entry, endpoint, name, multi_agent, version=agent.get("version")),
        )

    if multi_agent:
        entities.append(DockgeGlobalSummarySensor(coordinator, entry))

    # Per-container sensors (dynamically tracked)
    tracked_containers: set[str] = set()

    @callback
    def _async_add_new_container_sensors() -> None:
        stacks = coordinator.data.get("stacks") or []
        names = coordinator.data.get("agent_names", {})
        is_multi = coordinator.data.get("multi_agent", False)
        new_entities: list[SensorEntity] = []
        for stack in stacks:
            endpoint = stack.get("endpoint", "")
            aname = agent_display_name(names, endpoint)
            services = stack.get("services") or {}
            for svc_name, svc_data in services.items():
                key = f"{endpoint}|{stack['name']}|{svc_name}"
                if key not in tracked_containers:
                    tracked_containers.add(key)
                    new_entities.append(
                        DockgeContainerSensor(
                            coordinator, entry, stack["name"],
                            endpoint, aname, svc_name, svc_data,
                            multi_agent=is_multi,
                        )
                    )
        if new_entities:
            async_add_entities(new_entities)

    # Add initial containers
    stacks = coordinator.data.get("stacks") or []
    for stack in stacks:
        endpoint = stack.get("endpoint", "")
        aname = agent_display_name(agent_names, endpoint)
        services = stack.get("services") or {}
        for svc_name, svc_data in services.items():
            key = f"{endpoint}|{stack['name']}|{svc_name}"
            tracked_containers.add(key)
            entities.append(
                DockgeContainerSensor(
                    coordinator, entry, stack["name"],
                    endpoint, aname, svc_name, svc_data,
                    multi_agent=multi_agent,
                )
            )

    async_add_entities(entities)
    entry.async_on_unload(coordinator.async_add_listener(_async_add_new_container_sensors))


class DockgeContainerSensor(CoordinatorEntity, SensorEntity):
    """Sensor representing an individual container within a stack."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:docker"

    def __init__(
        self, coordinator: DockgeCoordinator, entry: ConfigEntry,
        stack_name: str, endpoint: str, agent_name: str,
        service_name: str, service_data: dict,
        *, multi_agent: bool = False,
    ) -> None:
        super().__init__(coordinator)
        self._stack_name = stack_name
        self._endpoint = endpoint
        self._agent_name = agent_name
        self._service_name = service_name
        self._attr_unique_id = f"{entry.entry_id}_container_{endpoint}_{stack_name}_{service_name}"
        self._attr_name = service_name
        self._attr_device_info = stack_device_info(
            entry.entry_id, endpoint, stack_name, agent_name,
            multi_agent=multi_agent,
        )

    def _get_service(self) -> dict | None:
        for s in self.coordinator.data.get("stacks") or []:
            if s["name"] == self._stack_name and s.get("endpoint", "") == self._endpoint:
                services = s.get("services") or {}
                return services.get(self._service_name)
        return None

    @property
    def native_value(self) -> str | None:
        svc = self._get_service()
        if not svc:
            return None
        return svc.get("state")

    @property
    def available(self) -> bool:
        return self.coordinator.last_update_success and self._get_service() is not None

    @staticmethod
    def _split_image(image: str) -> tuple[str, str]:
        """Split 'registry/name:tag' into (name, tag)."""
        if ":" in image and not image.endswith(":"):
            name, tag = image.rsplit(":", 1)
            if "/" in tag:
                return image, "latest"
            return name, tag
        return image, "latest"

    @property
    def extra_state_attributes(self) -> dict:
        svc = self._get_service()
        if not svc:
            return {}
        image = svc.get("image", "")
        image_name, image_tag = self._split_image(image)
        return {
            "container_name": svc.get("containerName"),
            "image": image,
            "image_name": image_name,
            "image_tag": image_tag,
            "status": svc.get("status"),
            "health": svc.get("health"),
            "stack_name": self._stack_name,
            "agent_name": self._agent_name,
        }


class DockgeAgentSummarySensor(CoordinatorEntity, SensorEntity):
    """Sensor summarising all stacks and containers on an agent."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:server"

    def __init__(
        self, coordinator: DockgeCoordinator, entry: ConfigEntry,
        endpoint: str, agent_name: str, multi_agent: bool = False,
    ) -> None:
        super().__init__(coordinator)
        self._endpoint = endpoint
        self._agent_name = agent_name
        self._attr_unique_id = f"{entry.entry_id}_agent_summary_{endpoint}"
        self._attr_name = "Server Summary"
        self._attr_device_info = agent_device_info(entry.entry_id, endpoint, agent_name, multi_agent=multi_agent)

    def _agent_stacks(self) -> list[dict]:
        stacks = self.coordinator.data.get("stacks") or []
        return [s for s in stacks if s.get("endpoint", "") == self._endpoint]

    @property
    def native_value(self) -> int:
        total = 0
        for stack in self._agent_stacks():
            for svc in (stack.get("services") or {}).values():
                if svc.get("state") == "running":
                    total += 1
        return total

    @property
    def extra_state_attributes(self) -> dict:
        agent_stacks = self._agent_stacks()
        stack_names = sorted(s["name"] for s in agent_stacks)
        total_containers = 0
        running_containers = 0
        for stack in agent_stacks:
            for svc in (stack.get("services") or {}).values():
                total_containers += 1
                if svc.get("state") == "running":
                    running_containers += 1
        return {
            "agent_name": self._agent_name,
            "stacks": stack_names,
            "total_stacks": len(stack_names),
            "total_containers": total_containers,
            "running_containers": running_containers,
        }


class DockgeVersionSensor(CoordinatorEntity, SensorEntity):
    """Sensor showing the Dockge version for an agent."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:tag"

    def __init__(
        self, coordinator: DockgeCoordinator, entry: ConfigEntry,
        endpoint: str, agent_name: str, multi_agent: bool = False,
        version: str | None = None,
    ) -> None:
        super().__init__(coordinator)
        self._endpoint = endpoint
        self._attr_unique_id = f"{entry.entry_id}_version_{endpoint}"
        self._attr_name = "Version"
        self._attr_device_info = agent_device_info(entry.entry_id, endpoint, agent_name, multi_agent=multi_agent, version=version)

    @property
    def native_value(self) -> str | None:
        agents = self.coordinator.data.get("agents") or []
        for agent in agents:
            if agent.get("endpoint", "") == self._endpoint:
                return agent.get("version")
        return None


class DockgeGlobalSummarySensor(CoordinatorEntity, SensorEntity):
    """Sensor summarising all stacks and containers across all agents."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:server-network"

    def __init__(
        self, coordinator: DockgeCoordinator, entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_global_summary"
        self._attr_name = "Global Summary"
        self._attr_device_info = agent_device_info(
            entry.entry_id, "", agent_display_name(
                coordinator.data.get("agent_names", {}), "",
            ), multi_agent=True,
        )

    @property
    def native_value(self) -> int:
        total = 0
        for stack in self.coordinator.data.get("stacks") or []:
            for svc in (stack.get("services") or {}).values():
                if svc.get("state") == "running":
                    total += 1
        return total

    @property
    def extra_state_attributes(self) -> dict:
        stacks = self.coordinator.data.get("stacks") or []
        agents = self.coordinator.data.get("agent_names") or {}
        total_containers = 0
        running_containers = 0
        per_agent: dict[str, dict] = {}
        for stack in stacks:
            ep = stack.get("endpoint", "")
            aname = agent_display_name(agents, ep)
            if aname not in per_agent:
                per_agent[aname] = {"stacks": [], "running": 0, "total": 0}
            per_agent[aname]["stacks"].append(stack["name"])
            for svc in (stack.get("services") or {}).values():
                total_containers += 1
                per_agent[aname]["total"] += 1
                if svc.get("state") == "running":
                    running_containers += 1
                    per_agent[aname]["running"] += 1
        return {
            "total_stacks": len(stacks),
            "total_containers": total_containers,
            "running_containers": running_containers,
            "agents": {name: {
                "stacks": sorted(data["stacks"]),
                "running_containers": data["running"],
                "total_containers": data["total"],
            } for name, data in per_agent.items()},
        }
