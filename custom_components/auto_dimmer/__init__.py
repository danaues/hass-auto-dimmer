"""
Auto Dimmer integration for Home-Assistant.

This integration will automatically dim light entities based on the time of day.
"""
from __future__ import annotations

from typing import Any
import asyncio
import logging

from homeassistant.const import CONF_NAME
from .const import (
    DOMAIN,
    CONF_INTERVAL,
    CONF_LIGHTS,
    CONF_TRANSITION,
    CONF_MAX_BRIGHTNESS,
    CONF_MIN_BRIGHTNESS,
)

from .auto_dimmer import AutoDimmer

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType
from homeassistant.config_entries import ConfigEntry

from datetime import datetime, timedelta

_LOGGER = logging.getLogger(__name__)

async def async_setup(hass: HomeAssistant, base_config: ConfigType) -> bool:
    """Set up the auto dimmer component."""
    hass.data.setdefault(DOMAIN, {})

    _LOGGER.debug("auto-dimmer async_setup: base_config: %s", DOMAIN)

    if DOMAIN in base_config:
        dimmer_configs = base_config[DOMAIN]
        for config in dimmer_configs:
            _LOGGER.debug("auto-dimmer async_setup loop, interval: %s, light_entities: %s", config[CONF_INTERVAL], config[CONF_LIGHTS])
            hass.async_create_task(
                hass.config_entries.flow.async_init(
                    DOMAIN,
                    context={"source": config_entries.SOURCE_IMPORT},
                    data = config,
                )
            )

    return True

async def async_setup_entry(
    hass: HomeAssistant, config_entry: config_entries.ConfigEntry
) -> bool:

    _LOGGER.debug("auto dimmer: async_setup_entry")
    config_entry.async_on_unload(config_entry.add_update_listener(update_listener))

    entry_id = config_entry.entry_id
    data = config_entry.data
    options = config_entry.options

    name = data[CONF_NAME]
    transition = options[CONF_TRANSITION]
    interval = options[CONF_INTERVAL]
    light_entities = options[CONF_LIGHTS]
    max_brightness = options[CONF_MAX_BRIGHTNESS]
    min_brightness = options[CONF_MIN_BRIGHTNESS]

    interval_delta = timedelta(seconds=interval)

    hass.data[DOMAIN][entry_id] = myautodimmer = AutoDimmer(
        hass,
        name,
        interval,
        light_entities,
        transition,
        max_brightness,
        min_brightness
    )

    await myautodimmer._async_init(interval=interval_delta)

    return True

async def update_listener(hass, config_entry: ConfigEntry):
    """Update options."""
    _LOGGER.debug("update and reload of options called")
    await hass.config_entries.async_reload(config_entry.entry_id)

async def async_unload_entry(hass, config_entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    
    myautodimmer = hass.data[DOMAIN][config_entry.entry_id]
    unload_ok = await myautodimmer.unsubscribe()

    return unload_ok