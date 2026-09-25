# Dockge for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![GitHub release](https://img.shields.io/github/release/darthrater78/ha-dockge.svg)](https://github.com/darthrater78/ha-dockge/releases/latest)
[![Built with Claude Code](https://img.shields.io/badge/Built_with-Claude_Code-blueviolet)](https://claude.ai/claude-code)

Home Assistant integration for monitoring and controlling Docker stacks via the [Dockge](https://github.com/darthrater78/dockge) REST API.

**[GitHub repository](https://github.com/darthrater78/ha-dockge)** · **[Release notes for v2.1.0](https://github.com/darthrater78/ha-dockge/releases/tag/v2.1.0)**

See container status across all your stacks, start/stop/restart stacks, and run system prune — all from within Home Assistant.

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=darthrater78&repository=ha-dockge&category=integration)

---

## Built Entirely by Claude Code

**Every line of code in this project was written by [Claude Code](https://claude.ai/claude-code)**, Anthropic's AI coding agent. From the initial scaffold to the latest refactor — 7 source modules, a test suite, CI, config flow, coordinator, sensors, buttons, services, device hierarchy, multi-agent support — all of it was generated through conversational AI-assisted development.

This isn't a project with "some AI help." There is no hand-written code. The entire integration was designed, implemented, debugged, refactored, and documented through iterative prompting sessions with Claude Code.

### How it was built

The project evolved through a series of Claude Code sessions, each building on the last:

1. **Scaffolding** — Claude generated the initial Home Assistant integration structure: config flow, coordinator, constants, and manifest
2. **Entity platforms** — Sensors, binary sensors, buttons, and switches were added one platform at a time, each in its own commit
3. **Device hierarchy** — Claude designed the agent-level and stack-level device tree so entities group naturally in the HA UI
4. **Multi-agent support** — Support for multiple Dockge agents (remote Docker hosts) was implemented and then debugged across several iterations
5. **Stack lifecycle controls** — Start, stop, restart, and down buttons per stack, with processing-state tracking and refresh bursts for near-real-time UI updates
6. **Scope pivot (v2.0.0)** — The entire update-monitoring subsystem (auto-update scheduler, image update checks, update history, version-gating) was stripped out in a single refactor, repositioning the integration from "container updates" to "container control"
7. **Audit and hardening (v2.1.0)** — A security and CI audit led to input validation on service calls, correct behavior with multiple Dockge instances, a pytest suite, and hardened GitHub Actions with a gated release workflow

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

All services are available under the `dockge` domain (e.g., `dockge.start_stack`). The optional `agent` field accepts an agent display name (e.g., "Gastly") for multi-agent setups; leave empty for the primary server. If you have more than one Dockge instance configured, set `config_entry_id` to pick which one. Stack names must match Dockge's own rule: lowercase letters, digits, `-` and `_`.

| Service | Fields | Description |
|---------|--------|-------------|
| `start_stack` | `stack_name`, `agent`?, `config_entry_id`? | Start a Docker Compose stack |
| `stop_stack` | `stack_name`, `agent`?, `config_entry_id`? | Stop a Docker Compose stack |
| `restart_stack` | `stack_name`, `agent`?, `config_entry_id`? | Restart a Docker Compose stack |
| `system_prune` | `agent`?, `config_entry_id`? | Run Docker system prune to clean up unused images, containers, and networks |

## Dashboard Card

For a visual dashboard, check out the [Dockge Card](https://github.com/darthrater78/dockge-card) — a custom Lovelace card that auto-discovers your servers and stacks with real-time status, actions, and processing indicators.

## Security

- **API key in transit:** the key is sent in an `X-API-Key` header on every request. Use an `https://` URL where you can; over plain `http://` anyone on the network path can read it.
- **API key at rest:** Home Assistant stores it, like every integration's settings, unencrypted in `.storage/core.config_entries`. Home Assistant has no at-rest encryption for config entries, so protect the config directory and keep backups encrypted (Home Assistant's own backups are encrypted by default).
- **Who can use it:** any Home Assistant user who can call services can start, stop and prune through this integration with the stored key.

## Version History

See [CHANGELOG.md](CHANGELOG.md) and the [GitHub releases](https://github.com/darthrater78/ha-dockge/releases/latest).

## Community

- [Home Assistant Community Forum thread](https://community.home-assistant.io/t/hacs-dockge-monitor-and-manage-docker-stacks-from-home-assistant/992901)
- [GitHub Issues](https://github.com/darthrater78/ha-dockge/issues)

## License

MIT
