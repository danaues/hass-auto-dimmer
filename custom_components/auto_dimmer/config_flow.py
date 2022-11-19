"""Config flow for Auto Dimmer."""
from __future__ import annotations

import logging

import voluptuous as vol

from homeassistant.core import HomeAssistant, callback
from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME, ATTR_SUPPORTED_FEATURES
from homeassistant.components.light import ATTR_BRIGHTNESS

import homeassistant.helpers.config_validation as cv

from copy import deepcopy

from .const import (
    DOMAIN, 
    CONF_LIGHTS, 
    CONF_INTERVAL,
    STEP_IMPORT_FAILED,
    ABORT_REASON_IMPORT_FAILED,
    VALIDATION_TUPLES,
    NONE_STR,
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
    
    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            await self.async_set_unique_id(user_input[CONF_NAME])
            self._abort_if_unique_id_configured()
            return self.async_create_entry(title=user_input[CONF_NAME], data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required(CONF_NAME): str}),
            errors=errors,
        )

    async def async_step_import(self, user_input=None):
        """Import a new Auto Dimmer as a config entry.

        This flow is triggered by `async_setup`.
        """
        await self.async_set_unique_id(user_input[CONF_NAME])
        for entry in self._async_current_entries():
            if entry.unique_id == self.unique_id:
                _LOGGER.debug("update entry!!! %s", user_input)
                self.hass.config_entries.async_update_entry(entry, data=user_input)
                self._abort_if_unique_id_configured()
        return self.async_create_entry(title=user_input[CONF_NAME], data=user_input)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return OptionsFlowHandler(config_entry)

def validate_options(user_input, errors):
    """Validate the options in the OptionsFlow.

    This is an extra validation step because the validators
    in `EXTRA_VALIDATION` cannot be serialized to json.
    """
    #for key, (_validate, _) in EXTRA_VALIDATION.items():
    #    # these are unserializable validators
    #    value = user_input.get(key)
    #    try:
    #        if value is not None and value != NONE_STR:
    #            _validate(value)
    #    except vol.Invalid:
    #        _LOGGER.exception("Configuration option %s=%s is incorrect", key, value)
    #        errors["base"] = "option_error"


def validate(config_entry: ConfigEntry):
    """Get the options and data from the config_entry and add defaults."""
    defaults = {key: default for key, default, _ in VALIDATION_TUPLES}
    data = deepcopy(defaults)
    data.update(config_entry.options)  # come from options flow
    data.update(config_entry.data)  # all yaml settings come from data
    data = {key: replace_none_str(value) for key, value in data.items()}
    #for key, (validate_value, _) in EXTRA_VALIDATION.items():
    #    value = data.get(key)
    #    if value is not None:
    #        data[key] = validate_value(value)  # Fix the types of the inputs
    return data

def replace_none_str(value, replace_with=None):
    """Replace "None" -> replace_with."""
    return value if value != NONE_STR else replace_with

#def _supports_brightness(hass: HomeAssistant, light: str):
#    state = hass.states.get(light)
#    _LOGGER.debug("testing light support %s", state.attributes[ATTR_SUPPORTED_FEATURES])
#    return ATTR_BRIGHTNESS in state.attributes[ATTR_SUPPORTED_FEATURES]

class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle a option flow for Adaptive Lighting."""

    def __init__(self, config_entry: config_entries.ConfigEntry):
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Handle options flow."""
        conf = self.config_entry
        data = validate(conf)
        
        if conf.source == config_entries.SOURCE_IMPORT:
            return self.async_show_form(step_id="init", data_schema=None)
        errors = {}
        if user_input is not None:
            validate_options(user_input, errors)
            if not errors:
                return self.async_create_entry(title="", data=user_input)

        all_lights = [
            light
            for light in self.hass.states.async_entity_ids("light")
            #if _supports_brightness(self.hass, light)
        ]

        for configured_light in data[CONF_LIGHTS]:
            if configured_light not in all_lights:
                errors = {CONF_LIGHTS: "entity_missing"}
                _LOGGER.error(
                    "%s: light entity %s is configured, but was not found",
                    data[CONF_NAME],
                    configured_light,
                )
                all_lights.append(configured_light)
        to_replace = {CONF_LIGHTS: cv.multi_select(sorted(all_lights))}

        options_schema = {}
        for name, default, validation in VALIDATION_TUPLES:
            key = vol.Optional(name, default=conf.options.get(name, default))
            value = to_replace.get(name, validation)
            options_schema[key] = value

        return self.async_show_form(
            step_id="init", data_schema=vol.Schema(options_schema), errors=errors
        )