"""Config flow for Auto Dimmer."""
from __future__ import annotations

import logging

import voluptuous as vol

from homeassistant.core import HomeAssistant, callback
from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME, ATTR_SUPPORTED_FEATURES
from homeassistant.components.light import ATTR_BRIGHTNESS
from homeassistant.helpers.selector import selector
from homeassistant.helpers.sun import get_astral_event_next

import homeassistant.util.dt as dt_util
from datetime import datetime, timedelta

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
    OPTION_MORNING_START_OFFSET,    
    OPTION_MORNING_END_OFFSET,
    OPTION_AFTERNOON_START_OFFSET,
    OPTION_AFTERNOON_END_OFFSET,
    OPTION_MORNING_START_TIME,
    OPTION_MORNING_END_TIME,
    OPTION_AFTERNOON_START_TIME,
    OPTION_AFTERNOON_END_TIME,
    CONF_MORNING_START_TYPE,
    CONF_MORNING_END_TYPE,
    CONF_AFTERNOON_START_TYPE,
    CONF_AFTERNOON_END_TYPE,
    CONF_MORNING_START_TIME,
    CONF_MORNING_END_TIME,
    CONF_AFTERNOON_START_TIME,
    CONF_AFTERNOON_END_TIME,
    CONF_MORNING_START_OFFSET,
    CONF_MORNING_END_OFFSET,
    CONF_AFTERNOON_START_OFFSET,
    CONF_AFTERNOON_END_OFFSET,
    TIME_OPTION_SPECIFY,
    TIME_OPTION_SUNRISE_OFFSET,
    TIME_OPTION_SUNSET_OFFSET,
    DEFAULT_MORNING_START_TIME,
    DEFAULT_AFTERNOON_END_TIME,
)

_LOGGER = logging.getLogger(__name__)

ENTRY_DEFAULT_TITLE = "Auto Dimmer"

DATA_SCHEMA = vol.Schema({vol.Required(CONF_LIGHTS): str})

def int_between(min_int, max_int):
    """Return an integer between 'min_int' and 'max_int'."""
    return vol.All(vol.Coerce(int), vol.Range(min=min_int, max=max_int))

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

def validate_init_options(user_input, errors):
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


def validate_schedule_options(options, user_input, errors):
    """Validate the options in the OptionsFlow.

    This is an extra validation step because the validators
    in `EXTRA_VALIDATION` cannot be serialized to json.
    """

    today = dt_util.start_of_local_day(dt_util.now())
    sunrise_time = dt_util.as_local(datetime.combine(today, dt_util.parse_time(DEFAULT_MORNING_START_TIME)))
    sunset_time = dt_util.as_local(datetime.combine(today, dt_util.parse_time(DEFAULT_AFTERNOON_END_TIME)))

    #Morning Start Time:
    if options[CONF_MORNING_START_TYPE] == TIME_OPTION_SPECIFY:
        morning_start_time = dt_util.as_local(datetime.combine(today, dt_util.parse_time(user_input[CONF_MORNING_START_TIME])))
    else:
        morning_start_time = sunrise_time + timedelta(minutes=user_input[CONF_MORNING_START_OFFSET])
    
    #Morning Finish Time:
    if options[CONF_MORNING_END_TYPE] == TIME_OPTION_SPECIFY:
        morning_end_time = dt_util.as_local(datetime.combine(today, dt_util.parse_time(user_input[CONF_MORNING_END_TIME])))
    else:
        morning_end_time = sunrise_time + timedelta(minutes=user_input[CONF_MORNING_END_OFFSET])
    
    #Afternoon Start Time:
    if options[CONF_AFTERNOON_START_TYPE] == TIME_OPTION_SPECIFY:
        afternoon_start_time = dt_util.as_local(datetime.combine(today, dt_util.parse_time(user_input[CONF_AFTERNOON_START_TIME])))
    else:
        afternoon_start_time = sunset_time + timedelta(minutes=user_input[CONF_AFTERNOON_START_OFFSET])
    
    #Afternoon Finish Time:
    if options[CONF_AFTERNOON_START_TYPE] == TIME_OPTION_SPECIFY:
        afternoon_end_time = dt_util.as_local(datetime.combine(today, dt_util.parse_time(user_input[CONF_AFTERNOON_END_TIME])))
    else:
        afternoon_end_time = sunset_time + timedelta(minutes=user_input[CONF_AFTERNOON_START_OFFSET])


    if morning_end_time < morning_start_time:
        errors["base"] = "morning_schedule"

    if afternoon_start_time < morning_end_time:
        errors["base"] = "midday_schedule"

    if afternoon_end_time < morning_start_time:
        errors["base"] = "afternoon_schedule"


def replace_none_str(value, replace_with=None):
    """Replace "None" -> replace_with."""
    return value if value != NONE_STR else replace_with

def build_schema(fields, options, to_replace):
    """Build the data_schema for the form"""
    options_schema = {}
    for name, default, validation in fields:
        key = vol.Optional(name, default=options.get(name, default))
        value = to_replace.get(name, validation)
        options_schema[key] = value
    return options_schema

def build_schedule_schema(options):
    """Build the data_schema for the form"""

    fields = []
    if options[CONF_MORNING_START_TYPE] == TIME_OPTION_SUNRISE_OFFSET:
        fields.append(OPTION_MORNING_START_OFFSET)
    else:
        fields.append(OPTION_MORNING_START_TIME)

    if options[CONF_MORNING_END_TYPE] == TIME_OPTION_SUNRISE_OFFSET:
        fields.append(OPTION_MORNING_END_OFFSET)
    else:
        fields.append(OPTION_MORNING_END_TIME)

    if options[CONF_AFTERNOON_START_TYPE] == TIME_OPTION_SUNSET_OFFSET:
        fields.append(OPTION_AFTERNOON_START_OFFSET)
    else:
        fields.append(OPTION_AFTERNOON_START_TIME)

    if options[CONF_AFTERNOON_END_TYPE] == TIME_OPTION_SUNSET_OFFSET:
        fields.append(OPTION_AFTERNOON_END_OFFSET)
    else:
        fields.append(OPTION_AFTERNOON_END_TIME)

    options_schema = {}
    for name, default, validation in fields:
        key = vol.Optional(name, default=options.get(name, default))
        value = validation
        options_schema[key] = value
    return options_schema

#def _supports_brightness(hass: HomeAssistant, light: str):
#    state = hass.states.get(light)
#    _LOGGER.debug("testing light support %s", state.attributes[ATTR_SUPPORTED_FEATURES])
#    return ATTR_BRIGHTNESS in state.attributes[ATTR_SUPPORTED_FEATURES]

class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle a option flow for Adaptive Lighting."""

    def __init__(self, config_entry: config_entries.ConfigEntry):
        """Initialize options flow."""
        self.config_entry = config_entry
        self._options = dict(config_entry.options)

    async def async_step_init(self, user_input=None):
        """Handle options flow."""
        conf = self.config_entry
        options = conf.options
        
        if conf.source == config_entries.SOURCE_IMPORT:
            return self.async_show_form(step_id="init", data_schema=None)
        errors = {}
        if user_input is not None:
            validate_init_options(user_input, errors)
            if not errors:
                _LOGGER.debug("show the schedule form: %s", user_input)
                self._options.update(user_input)

                options_schema = build_schedule_schema(self._options)
                return self.async_show_form(
                    step_id="schedule", data_schema=vol.Schema(options_schema), errors=errors
                )
                

        all_lights = [
            light
            for light in self.hass.states.async_entity_ids("light")
            #if _supports_brightness(self.hass, light)
        ]

        for configured_light in options.get(CONF_LIGHTS, []):
            if configured_light not in all_lights:
                errors = {CONF_LIGHTS: "entity_missing"}
                _LOGGER.error(
                    "%s: light entity %s is configured, but was not found",
                    options[CONF_NAME],
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

    async def async_step_schedule(self, user_input=None):
        """Handle options flow - Timer Settings."""

        errors = {}
        if user_input is not None:
            validate_schedule_options(self._options, user_input, errors)
            if not errors:
                self._options.update(user_input)
                _LOGGER.debug("step timers: user_input: %s", user_input)
                return self.async_create_entry(title="", data=self._options)
        
        self._options.update(user_input)
        options_schema = build_schedule_schema(self._options)
        return self.async_show_form(
            step_id="schedule", data_schema=vol.Schema(options_schema), errors=errors
        )

