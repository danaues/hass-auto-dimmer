"""Config flow for Auto Dimmer."""
from __future__ import annotations

import logging

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_NAME

from .const import (
    DOMAIN, 
    CONF_LIGHTS, 
    CONF_INTERVAL,
    STEP_IMPORT_FAILED,
    ABORT_REASON_IMPORT_FAILED,
)

_LOGGER = logging.getLogger(__name__)

ENTRY_DEFAULT_TITLE = "Auto Dimmer"

DATA_SCHEMA = vol.Schema({vol.Required(CONF_LIGHTS): str})

class AutoDimmerFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle Auto Dimmer config flow."""

    VERSION = 1

    def __init__(self):
        """Initialize an Auto Dimmer flow."""
        self.data = {}
        _LOGGER.debug("auto dimmer: config flow init")
       
    async def async_step_import(self, import_info):
        """Import a new Auto Dimmer as a config entry.

        This flow is triggered by `async_setup`.
        """
        _LOGGER.debug("auto dimmer: config flow async_step_import: %s", import_info)

        name = import_info[CONF_NAME]
        lights = import_info[CONF_LIGHTS]
        interval = import_info[CONF_INTERVAL]
        # Store the imported config for other steps in this flow to access.
        self.data[CONF_NAME] = name
        self.data[CONF_LIGHTS] = lights
        self.data[CONF_INTERVAL] = interval

        # Abort if existing entry with matching host exists.
        self._async_abort_entries_match({CONF_NAME: self.data[CONF_NAME]})

        await self.async_set_unique_id(name, raise_on_progress=False)
        self._abort_if_unique_id_configured()
        return self.async_create_entry(title=name, data=self.data)

    async def async_step_import_failed(self, user_input=None):
        """Make failed import surfaced to user."""
        self.context["title_placeholders"] = {CONF_NAME: self.data[CONF_NAME]}

        if user_input is None:
            return self.async_show_form(
                step_id=STEP_IMPORT_FAILED,
                description_placeholders={"name": self.data[CONF_NAME]},
                errors={"base": ABORT_REASON_IMPORT_FAILED},
            )

        return self.async_abort(reason=ABORT_REASON_IMPORT_FAILED)
