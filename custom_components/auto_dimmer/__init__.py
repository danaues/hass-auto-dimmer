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
    DEFAULT_INTERVAL,
    CONF_TRANSITION,
    CONF_MAX_BRIGHTNESS,
    CONF_MIN_BRIGHTNESS,
    CONF_MORNING_START_TIME,
    CONF_MORNING_END_TIME,
    CONF_AFTERNOON_START_TIME,
    CONF_AFTERNOON_END_TIME,
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

    if CONF_LIGHTS not in options:
        # Options have not been configured, skip setup and wait for config/reload.
        return True

    name = data[CONF_NAME]
    interval = options[CONF_INTERVAL]
    interval_seconds = interval * 60
    interval_delta = timedelta(seconds=interval_seconds)

    hass.data[DOMAIN][entry_id] = myautodimmer = AutoDimmer(
        hass,
        name,
        interval,
        options,
    )

    await myautodimmer._async_init(interval=interval_delta)

    return True

async def update_listener(hass, config_entry: ConfigEntry):
    """Update options."""
    _LOGGER.debug("update and reload of options called")
    await hass.config_entries.async_reload(config_entry.entry_id)

async def async_unload_entry(hass, config_entry: ConfigEntry) -> bool:
    """Unload a config entry."""

    _LOGGER.debug("auto dimmer: async_unload_entry")

    if myautodimmer := hass.data[DOMAIN].get(config_entry.entry_id):
        _LOGGER.debug("auto dimmer: async_unload_entry: unsubscribing")
        return await myautodimmer.unsubscribe()

    return True