"""
Auto Dimmer integration for Home-Assistant.

This integration will automatically dim light entities based on the time of day.
"""
from __future__ import annotations

import asyncio
import logging

from homeassistant.const import CONF_HOST, CONF_NAME
from .const import (
    DOMAIN,
    CONF_INTERVAL,
    CONF_LIGHTS,
)

from .auto_dimmer import AutoDimmer

# from homeassistant.helpers.discovery import async_load_platform
from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers.typing import ConfigType

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
                    data={
                        CONF_NAME: config[CONF_NAME],
                        CONF_INTERVAL: config[CONF_INTERVAL],
                        CONF_LIGHTS: config[CONF_LIGHTS],
                    }
                )
            )

    return True

async def async_setup_entry(
    hass: HomeAssistant, config_entry: config_entries.ConfigEntry
) -> bool:

    _LOGGER.debug("auto-dimmer async_setup_entry: config_entry: %s", config_entry.data)

    entry_id = config_entry.entry_id
    data = config_entry.data

    interval = data[CONF_INTERVAL]
    light_entities = data[CONF_LIGHTS]
    name = data[CONF_NAME]
    
    test_interval = timedelta(seconds=interval)

    hass.data[DOMAIN][entry_id] = myautodimmer = AutoDimmer(
        hass,
        name,
        interval,
        light_entities,
    )

    _LOGGER.debug("auto-dimmer async_setup_entry: myautodimmer: %s", test_interval)
    
    await myautodimmer._async_init(interval=test_interval)

    #_LOGGER.debug("auto-dimmer async_setup_entry: light_entites: %s", data[CONF_LIGHTS])

    return True