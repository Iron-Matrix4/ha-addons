"""Conversation platform for Jarvis AI."""
import logging

import aiohttp
from homeassistant.components import conversation
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import intent
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import API_CONVERSATION, CONF_URL, DEFAULT_URL, DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Jarvis conversation agent."""
    url = entry.data.get(CONF_URL, DEFAULT_URL)
    async_add_entities([JarvisConversationAgent(hass, entry, url)])


class JarvisConversationAgent(conversation.ConversationEntity):
    """Jarvis conversation agent."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, url: str) -> None:
        """Initialize the agent."""
        self.hass = hass
        self.entry = entry
        self._url = url
        self._attr_name = "Jarvis AI"
        self._attr_unique_id = entry.entry_id

    @property
    def supported_languages(self) -> list[str]:
        """Return list of supported languages."""
        return ["en"]

    async def async_process(
        self, user_input: conversation.ConversationInput
    ) -> conversation.ConversationResult:
        """Process a sentence."""
        _LOGGER.info(f"=== JARVIS PROCESSING ===")
        _LOGGER.info(f"Input: {user_input.text}")
        _LOGGER.info(f"URL: {self._url}{API_CONVERSATION}")

        try:
            # Call Jarvis HTTP API
            async with aiohttp.ClientSession() as session:
                _LOGGER.info(f"Attempting connection to {self._url}{API_CONVERSATION}")
                async with session.post(
                    f"{self._url}{API_CONVERSATION}",
                    json={"text": user_input.text},
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as resp:
                    _LOGGER.info(f"Response status: {resp.status}")
                    if resp.status != 200:
                        error_text = await resp.text()
                        _LOGGER.error(f"HTTP error {resp.status}: {error_text}")
                        response_text = "I encountered an error, Sir."
                    else:
                        data = await resp.json()
                        response_text = data.get("response", "No response received.")
                        _LOGGER.info(f"Got response: {response_text[:50]}...")

        except aiohttp.ClientError as err:
            _LOGGER.error(f"Connection error: {err}", exc_info=True)
            response_text = "I'm unable to connect to my system, Sir."
        except Exception as err:
            _LOGGER.error(f"Unexpected error: {err}", exc_info=True)
            response_text = "I encountered an unexpected error, Sir."

        _LOGGER.info(f"Final response: {response_text}")

        # Return conversation result
        response = intent.IntentResponse(language=user_input.language)
        response.async_set_speech(response_text)
        
        return conversation.ConversationResult(
            response=response,
            conversation_id=user_input.conversation_id,
        )
