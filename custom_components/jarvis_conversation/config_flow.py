"""Config flow for Jarvis AI Conversation Agent integration."""
import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant

from .const import CONF_URL, DEFAULT_URL, DOMAIN

_LOGGER = logging.getLogger(__name__)


class JarvisConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Jarvis AI."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Handle the initial step."""
        if user_input is not None:
            # Create the config entry
            return self.async_create_entry(
                title="Jarvis AI",
                data={CONF_URL: DEFAULT_URL},
            )

        # Show the configuration form
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({}),
            description_placeholders={
                "url": DEFAULT_URL,
            },
        )
