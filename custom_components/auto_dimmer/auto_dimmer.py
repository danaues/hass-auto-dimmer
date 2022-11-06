from __future__ import annotations

import asyncio
import logging

from .const import (
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

AUTO_DIMMER_UPDATE_TOPIC = f"{DOMAIN}_update"

# from homeassistant.helpers.discovery import async_load_platform
from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers.typing import ConfigType
from homeassistant.components.light import VALID_TRANSITION, is_on

class AutoDimmer():
    """Auto Dimmer brightness."""

    def __init__(
        self,
        hass: HomeAssistant,
        name: str,
        interval: int,
        light_entities: list[str]

    ):
        self._hass = hass
        self._name = name
        self._interval = interval
        self._light_entities = light_entities

        _LOGGER.debug("AutoDimmer __init__; light_entities: %s", self._light_entities)

    async def _async_init(self, interval):
        _LOGGER.debug("AutoDimmer _async_init; interval: %s", interval)

        async_track_time_interval(self._hass, self.async_update, interval)

    async def async_update(self, var1=None):
        """Update the brightness for each light"""
        _LOGGER.debug("AutoDimmer async_update; name: %s, time: %s", self._name, var1)
        
        for light_entity in self._light_entities:
            _LOGGER.debug("autodim update: light entity: %s is on: %s", light_entity, is_on(self._hass, light_entity))


        #async_dispatcher_send(self._hass, "auto_dimmer_KTEST")