# Dockge for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![GitHub release](https://img.shields.io/github/release/darthrater78/ha-dockge.svg)](https://github.com/darthrater78/ha-dockge/releases/latest)
[![Built with Claude Code](https://img.shields.io/badge/Built_with-Claude_Code-blueviolet)](https://claude.ai/claude-code)

Home Assistant integration for monitoring and controlling Docker stacks via the [Dockge](https://github.com/darthrater78/dockge) REST API.

See container status across all your stacks, start/stop/restart stacks, and run system prune — all from within Home Assistant.

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=darthrater78&repository=ha-dockge&category=integration)

---

## Built Entirely by Claude Code

**Every line of code in this project was written by [Claude Code](https://claude.ai/claude-code)**, Anthropic's AI coding agent. From the initial scaffold to the latest refactor — 49 commits, 9 source modules, config flow, coordinator, sensors, buttons, switches, services, device hierarchy, multi-agent support — all of it was generated through conversational AI-assisted development.

This isn't a project with "some AI help." There is no hand-written code. The entire integration was designed, implemented, debugged, refactored, and documented through iterative prompting sessions with Claude Code.

### How it was built

The project evolved through a series of Claude Code sessions, each building on the last:

1. **Scaffolding** — Claude generated the initial Home Assistant integration structure: config flow, coordinator, constants, and manifest
2. **Entity platforms** — Sensors, binary sensors, buttons, and switches were added one platform at a time, each in its own commit
3. **Device hierarchy** — Claude designed the agent-level and stack-level device tree so entities group naturally in the HA UI
4. **Multi-agent support** — Support for multiple Dockge agents (remote Docker hosts) was implemented and then debugged across several iterations
5. **Stack lifecycle controls** — Start, stop, restart, and down buttons per stack, with processing-state tracking and refresh bursts for near-real-time UI updates
6. **Scope pivot (v2.0.0)** — The entire update-monitoring subsystem (auto-update scheduler, image update checks, update history, version-gating) was stripped out in a single refactor, repositioning the integration from "container updates" to "container control"

### Why this is almost a new project

The original vision was a **container update monitor** — it tracked image versions, showed update-available badges, ran scheduled update checks, and could trigger auto-updates. That required a large surface area: scheduler sensors, update history sensors, auto-update switches, binary sensors for update availability, and multiple service calls for checking and applying updates.

In **v2.0.0**, all of that was removed. What remains is a focused **container control** integration: see what's running, start/stop/restart stacks, and clean up unused resources. The codebase is smaller, the API surface is narrower, and the purpose is clearer. If you were tracking this project before v2.0.0, what you see now is a fundamentally different tool.

---

## Companion Project: Dockge Fork

This integration is designed to work with **[darthrater78/dockge](https://github.com/darthrater78/dockge)** — a fork of the original Dockge that adds a REST API for programmatic stack control. The upstream Dockge uses only WebSocket communication; this fork adds the HTTP endpoints this integration depends on.

You need the forked Dockge, not the original. The REST API and API key authentication are what make this integration possible.

---

## Features

- **Container status** — sensors showing each container's state (running, exited, etc.) with image and health details
- **Multi-agent support** — works with multiple Dockge agents, each with their own device hierarchy
- **Stack control** — start, stop, restart, and down buttons per stack
- **System prune** — clean up unused Docker resources via service call
- **Server summary** — running container count with per-stack breakdown in attributes

## Prerequisites

This integration requires a Dockge instance with the REST API enabled. You will need:

- A running [Dockge](https://github.com/darthrater78/dockge) instance (fork with REST API)
- An API key configured in Dockge

## Installation

### HACS (Recommended)

1. Open HACS in your Home Assistant instance
2. Click the three dots in the top right and select **Custom repositories**
3. Add `https://github.com/darthrater78/ha-dockge` with category **Integration**
4. Click **Download** on the Dockge card
5. Restart Home Assistant

Or click the button above to add the repository directly.

### Manual

1. Copy the `custom_components/dockge/` directory to your Home Assistant `custom_components/` folder
2. Restart Home Assistant

## Configuration

1. Go to **Settings > Devices & Services > Add Integration**
2. Search for **Dockge**
3. Enter your Dockge URL (e.g., `http://192.168.1.100:5001`)
4. Enter your API key
5. Optionally adjust the scan interval (default: 300 seconds)

## Entities

### Agent-level (Dockge Server device)

| Type | Entity | Description |
|------|--------|-------------|
| Sensor | Server Summary | Running container count with per-stack breakdown in attributes |
| Sensor | Version | Dockge server version |
| Sensor | Global Summary | Aggregate across all agents (multi-agent only, on primary device) |

### Stack-level (per stack device)

| Type | Entity | Description |
|------|--------|-------------|
| Sensor | {container} | Container state with image and health attributes |
| Button | Start | Start the stack |
| Button | Stop | Stop the stack |
| Button | Restart | Restart the stack |
| Button | Down | Stop and remove containers (make stack inactive) |

## Services

All services are available under the `dockge` domain (e.g., `dockge.start_stack`). The optional `agent` field accepts an agent display name (e.g., "Gastly") for multi-agent setups; leave empty for the primary server.

| Service | Fields | Description |
|---------|--------|-------------|
| `start_stack` | `stack_name`, `agent`? | Start a Docker Compose stack |
| `stop_stack` | `stack_name`, `agent`? | Stop a Docker Compose stack |
| `restart_stack` | `stack_name`, `agent`? | Restart a Docker Compose stack |
| `system_prune` | `agent`? | Run Docker system prune to clean up unused images, containers, and networks |

## Dashboard Card

For a visual dashboard, check out the [Dockge Card](https://github.com/darthrater78/dockge-card) — a custom Lovelace card that auto-discovers your servers and stacks with real-time status, actions, and processing indicators.

## Version History

### 2.0.0 (2026-08-27)
- Removed all image update monitoring, auto-update scheduler, and update-related entities/services. The integration is now focused purely on stack control (start/stop/restart/down) and container status monitoring.
- Removed: `update_stack`, `check_updates`, `update_all`, `trigger_auto_updates` services
- Removed: Update Available binary sensors, Auto Update switches, scheduler sensors, update history sensors, image updates available sensor
- Removed: version-gating logic (no longer needed)
- Coordinator no longer fetches `/api/scheduler` or `/api/update-history` endpoints

### 1.8.1 (2026-08-27)
- Fixed integration setup crashing with `Attempt to decode JSON with unexpected mimetype: text/html` against Dockge 1.8.0+, which removed the `/api/scheduler` and `/api/update-history` endpoints.

## Community

- [Home Assistant Community Forum thread](https://community.home-assistant.io/t/hacs-dockge-monitor-and-manage-docker-stacks-from-home-assistant/992901)
- [GitHub Issues](https://github.com/darthrater78/ha-dockge/issues)

## License

MIT
