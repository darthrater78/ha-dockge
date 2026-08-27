# Dockge for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![GitHub release](https://img.shields.io/github/release/darthrater78/ha-dockge.svg)](https://github.com/darthrater78/ha-dockge/releases/latest)

Home Assistant integration for monitoring and controlling Docker stacks via the [Dockge](https://github.com/darthrater78/dockge) REST API.

See container status across all your stacks, start/stop/restart stacks, and run system prune — all from within Home Assistant.

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=darthrater78&repository=ha-dockge&category=integration)

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

## Vibecoded

This integration was built entirely through vibe coding with [Claude Code](https://claude.ai/claude-code).

## License

MIT
