"""Config flow for somfy_mylink2 integration."""
import logging

from somfy_mylink_synergy import SomfyMyLinkSynergy
import voluptuous as vol

from homeassistant import config_entries, core, exceptions
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import callback

from .const import (  # pylint:disable=unused-import
    CONF_DEFAULT_REVERSE,
    CONF_SYSTEM_ID,
    DEFAULT_PORT,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_PORT, default=DEFAULT_PORT): int,
        vol.Required(CONF_SYSTEM_ID): str,
        vol.Optional(CONF_DEFAULT_REVERSE): bool,
    }
)


async def validate_input(hass: core.HomeAssistant, data):
    """Validate the user input allows us to connect.

    Data has the keys from DATA_SCHEMA with values provided by the user.
    """

    system_id = data[CONF_SYSTEM_ID]
    host = data[CONF_HOST]
    port = data[CONF_PORT]

    somfy_mylink = SomfyMyLinkSynergy(system_id, host, port)

    try:
        mylink_status = await somfy_mylink.status_info()
        if "error" in mylink_status:
            raise InvalidAuth
    except TimeoutError:
        raise CannotConnect

    # Return info that you want to store in the config entry.
    return {"title": system_id}


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for somfy_mylink2."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_ASSUMED

    async def async_step_import(self, user_input=None):
        """Handle configuration by yaml file."""
        self._is_import = True
        _LOGGER.info("MYLINK IMPORT %s" % user_input)
        return await self.async_step_user(user_input)

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}
        if user_input is not None:
            _LOGGER.info("MYLINK USER INPUT: %s" % user_input)
            try:
                info = await validate_input(self.hass, user_input)

                await self.async_set_unique_id(user_input[CONF_SYSTEM_ID])
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title=info["title"], data=user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user", data_schema=DATA_SCHEMA, errors=errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return OptionsFlowHandler()


class OptionsFlowHandler(config_entries.OptionsFlow):
    async def async_step_init(self, user_input=None):
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        "show_things",
                        default=self.config_entry.options.get("show_things"),
                    ): bool
                }
            ),
        )


class CannotConnect(exceptions.HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(exceptions.HomeAssistantError):
    """Error to indicate there is invalid auth."""
