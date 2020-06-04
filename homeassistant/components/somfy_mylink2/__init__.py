"""Component for the Somfy MyLink device supporting the Synergy API."""
import asyncio
import logging

from somfy_mylink_synergy import SomfyMyLinkSynergy
import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv

from .const import (
    CONF_DEFAULT_REVERSE,
    CONF_ENTITY_CONFIG,
    CONF_REVERSE,
    CONF_SYSTEM_ID,
    DATA_SOMFY_MYLINK,
    DEFAULT_PORT,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


def validate_entity_config(values):
    """Validate config entry for CONF_ENTITY."""
    entity_config_schema = vol.Schema({vol.Optional(CONF_REVERSE): cv.boolean})
    if not isinstance(values, dict):
        raise vol.Invalid("expected a dictionary")
    entities = {}
    for entity_id, config in values.items():
        entity = cv.entity_id(entity_id)
        config = entity_config_schema(config)
        entities[entity] = config
    return entities


CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_SYSTEM_ID): cv.string,
                vol.Required(CONF_HOST): cv.string,
                vol.Optional(CONF_PORT, default=DEFAULT_PORT): cv.port,
                vol.Optional(CONF_DEFAULT_REVERSE, default=False): cv.boolean,
                vol.Optional(CONF_ENTITY_CONFIG, default={}): validate_entity_config,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)


# TODO List the platforms that you want to support.
# For your initial PR, limit it to 1 platform.
PLATFORMS = ["cover"]


async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the somfy_mylink2 component."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up somfy_mylink2 from a config entry."""
    # TODO Store an API object for your platforms to access
    # hass.data[DOMAIN][entry.entry_id] = MyApi(...)

    system_id = entry.data[CONF_SYSTEM_ID]
    host = entry.data[CONF_HOST]
    port = entry.data[CONF_PORT]

    hass.data[DATA_SOMFY_MYLINK] = SomfyMyLinkSynergy(system_id, host, port)

    for component in PLATFORMS:
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(entry, component)
        )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    unload_ok = all(
        await asyncio.gather(
            *[
                hass.config_entries.async_forward_entry_unload(entry, component)
                for component in PLATFORMS
            ]
        )
    )
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
