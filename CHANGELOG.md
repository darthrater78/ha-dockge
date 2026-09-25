# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project uses
[Semantic Versioning](https://semver.org/).

## [Unreleased]

## [2.1.0] - 2026-09-25

### Added
- Optional `config_entry_id` field on every service, to choose the Dockge instance when more than one is configured.
- A pytest suite (`scripts/test.sh`) and a local validation script (`scripts/validate.sh`); CI runs both.

### Security
- Stack names are checked against Dockge's own naming rule before any API call, and the agent endpoint is sent as a properly encoded query parameter. Before, a crafted stack or agent name in a service call could change which Dockge API URL was called.
- Service calls with an unknown agent name are rejected instead of being passed through to Dockge as a raw endpoint.
- The config flow only accepts `http://` or `https://` URLs with a host, and warns that plain `http://` sends the API key unencrypted.

### Fixed
- With more than one Dockge instance configured, services went to whichever instance was set up last, and removing any one instance removed the services for all of them. Services are now registered once; use the new `config_entry_id` field to pick an instance when you have several.
- Start/Stop/Restart/Down buttons gave up after 30 seconds, while the same actions as services waited 300. Both now wait up to 300 seconds, and buttons also trigger the 5-minute fast refresh the services already used.
- Failed actions now show a proper Home Assistant error instead of a coordinator update failure.
- A timeout while polling Dockge is now reported as a failed update instead of an unhandled error.
- The fast-refresh loop stops when the integration is unloaded.
- The `system_prune` description claimed an empty agent prunes all agents; it prunes the primary server, like the other services.

### Changed
- Uses Home Assistant's shared HTTP session instead of opening a new one for every request.
- The four button classes are now one; entity IDs and unique IDs are unchanged.
- Removed the unused `binary_sensor` and `switch` platform files.
- Version history moved from the README to this file.

### CI
- Validation now runs `scripts/validate.sh`, the same script you run locally, with hassfest pinned by image digest.
- Workflow hardening: SHA-pinned `actions/checkout` (v7.0.1), `persist-credentials: false`, timeouts, concurrency groups, and `push` limited to `main`.
- New release workflow: publishes a GitHub release from a `v*` tag only if the tag is on `main`, CI passed on that commit, and the tag matches `manifest.json`.
- Dependabot keeps the pinned actions current.

## [2.0.0] - 2026-08-27

### Removed
- All image update monitoring, the auto-update scheduler, and update-related entities and services. The integration now focuses on stack control (start/stop/restart/down) and container status monitoring.
- The `update_stack`, `check_updates`, `update_all` and `trigger_auto_updates` services.
- Update Available binary sensors, Auto Update switches, scheduler sensors, update history sensors, and the image updates available sensor.
- The version-gating logic, which was no longer needed.
- Polling of the `/api/scheduler` and `/api/update-history` endpoints.

## 1.8.1 - 2026-08-27

Never tagged or published as a release; its fix shipped in 2.0.0.

### Fixed
- Setup crashed with `Attempt to decode JSON with unexpected mimetype: text/html` against Dockge 1.8.0+, which removed the `/api/scheduler` and `/api/update-history` endpoints.

## [1.8.0] - 2026-08-27

### Added
- Start, Stop, Restart and Down buttons on every stack, for full stack lifecycle control. Down requires Dockge v1.6.2+.

### Changed
- Codeowner and repository URLs now point to darthrater78/ha-dockge.

[Unreleased]: https://github.com/darthrater78/ha-dockge/compare/v2.1.0...HEAD
[2.1.0]: https://github.com/darthrater78/ha-dockge/compare/v2.0.0...v2.1.0
[2.0.0]: https://github.com/darthrater78/ha-dockge/compare/v1.8.0...v2.0.0
[1.8.0]: https://github.com/darthrater78/ha-dockge/releases/tag/v1.8.0
