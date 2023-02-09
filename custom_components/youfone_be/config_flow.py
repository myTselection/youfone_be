"""Adds config flow for component."""
import logging
from collections import OrderedDict

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.const import (
    CONF_NAME,
    CONF_PASSWORD,
    CONF_RESOURCES,
    CONF_SCAN_INTERVAL,
    CONF_USERNAME
)

from . import DOMAIN, NAME
from .utils import (check_settings)

_LOGGER = logging.getLogger(__name__)


def create_schema(entry, option=False):
    """Create a default schema based on if a option or if settings
    is already filled out.
    """

    if option:
        # We use .get here incase some of the texts gets changed.
        default_username = entry.data.get(CONF_USERNAME, "")
        default_password = entry.data.get(CONF_PASSWORD, "")
    else:
        default_username = ""
        default_password = ""

    data_schema = OrderedDict()
    data_schema[
        vol.Required(CONF_USERNAME, description="username")
    ] = str
    data_schema[
        vol.Required(CONF_PASSWORD, description="password")
    ] = str

    return data_schema


class Mixin:
    async def test_setup(self, user_input):
        client = async_get_clientsession(self.hass)

        try:
            check_settings(user_input, self.hass)
        except ValueError:
            self._errors["base"] = "no_valid_settings"
            return False

        # This is what we really need.
        username = None

        if user_input.get("username"):
            username = user_input.get(CONF_USERNAME)
        else:
            self._errors["base"] = "missing username"
            
            
        password = None

        if user_input.get("password"):
            password = user_input.get(CONF_PASSWORD)
        else:
            self._errors["base"] = "missing password"
            


class ComponentFlowHandler(Mixin, config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for component."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    def __init__(self):
        """Initialize."""
        self._errors = {}

    async def async_step_user(self, user_input=None):  # pylint: disable=dangerous-default-value
        """Handle a flow initialized by the user."""

        if user_input is not None:
            await self.test_setup(user_input)
            return self.async_create_entry(title=NAME, data=user_input)

        return await self._show_config_form(user_input)

    async def _show_config_form(self, user_input):
        """Show the configuration form to edit location data."""
        data_schema = create_schema(user_input)
        return self.async_show_form(
            step_id="user", data_schema=vol.Schema(data_schema), errors=self._errors
        )

    async def async_step_import(self, user_input):  # pylint: disable=unused-argument
        """Import a config entry.
        Special type of import, we're not actually going to store any data.
        Instead, we're going to rely on the values that are in config file.
        """
        return self.async_create_entry(title="configuration.yaml", data={})

    # @staticmethod
    # @callback
    # def async_get_options_flow(config_entry):  # TODO
    #     """Get the options flow for this handler."""
    #     return ComponentOptionsHandler(config_entry)


class ComponentOptionsHandler(config_entries.OptionsFlow, Mixin):
    """Now this class isnt like any normal option handlers.. as ha devs option seems think options is
    #  supposed to be EXTRA options, i disagree, a user should be able to edit anything.."""

    def __init__(self, config_entry):
        self.config_entry = config_entry
        self.options = dict(config_entry.options)
        self._errors = {}

    async def async_step_init(self, user_input=None):

        return self.async_show_form(
            step_id="edit",
            data_schema=vol.Schema(create_schema(self.config_entry, option=True)),
            errors=self._errors,
        )

    async def async_step_edit(self, user_input):
        # edit does not work.
        if user_input is not None:
            await self.test_setup(user_input)
            if ok:
                self.hass.config_entries.async_update_entry(
                    self.config_entry, data=user_input
                )
                return self.async_create_entry(title="", data={})
            else:
                self._errors["base"] = "missing data options handler"
                # not suere this should be config_entry or user_input.
                return self.async_show_form(
                    step_id="edit",
                    data_schema=vol.Schema(
                        create_schema(self.config_entry, option=True)
                    ),
                    errors=self._errors,
                )