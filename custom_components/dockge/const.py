"""Constants for the Dockge integration."""

import re

DOMAIN = "dockge"

CONF_URL = "url"
CONF_API_KEY = "api_key"
CONF_SCAN_INTERVAL = "scan_interval"

DEFAULT_SCAN_INTERVAL = 300

# Dockge only allows lowercase letters, digits, "-" and "_" in stack names.
STACK_NAME_RE = re.compile(r"^[a-z0-9_-]+$")

STACK_ACTIONS = ("start", "stop", "restart", "down")
STACK_ACTION_TIMEOUT = 300
