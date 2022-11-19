from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, date
import pytz

from typing import Any

_LOGGER = logging.getLogger(__name__)

from homeassistant.core import HomeAssistant
from homeassistant.components.light import DOMAIN as LIGHT_DOMAIN
from homeassistant.components.light import ATTR_BRIGHTNESS, ATTR_TRANSITION
from homeassistant.helpers.event import async_track_time_interval, async_track_state_change
from homeassistant.helpers.sun import get_astral_event_next
import homeassistant.util.dt as dt_util

from homeassistant.const import (
    ATTR_ENTITY_ID,
    SERVICE_TURN_ON,
    SUN_EVENT_SUNRISE,
    SUN_EVENT_SUNSET,
)


def _is_time_between(check_time, start_time, end_time) -> bool:
    """Check if check_time is between start_time and end_time."""
    if start_time <= end_time:
        return start_time <= check_time < end_time
    else:
        return start_time <= check_time or check_time < end_time

class AutoDimmer():
    """Auto Dimmer brightness."""

    def __init__(
        self,
        hass: HomeAssistant,
        name: str,
        interval: int,
        light_entities: list[str],
        transition: int,
        max_brightness: int,
        min_brightness: int,
        morning_start: dt_util.time,
        morning_end: dt_util.time,
        afternoon_start: dt_util.time,
        afternoon_end: dt_util.time,
    ):
        self._hass = hass
        self._name = name
        self._interval = interval
        self._light_entities = light_entities
        self._light_data: dict[str, dict[str,Any]] = {}
        self._max_brightness: int = max_brightness
        self._min_brightness: int = min_brightness
        self._morning_start: dt_util.time = dt_util.parse_time(morning_start)
        self._morning_end: dt_util.time = dt_util.parse_time(morning_end)
        self._afternoon_start: dt_util.time = dt_util.parse_time(afternoon_start)
        self._afternoon_end: dt_util.time = dt_util.parse_time(afternoon_end)

        for light in self._light_entities:
            self._light_data.setdefault(
                light, {
                    "entity_name": light,
                    "enabled": True,
                    "last_brightness": None,
                    "last_update": None,
                }
            )

        _LOGGER.debug("AutoDimmer __init__; light_entities: %s", self._light_entities)


    async def _async_init(self, interval):
        _LOGGER.debug("AutoDimmer _async_init; interval: %s", interval)

        self._track_state_change = async_track_state_change(
            self._hass, self._light_entities, self._state_changed, to_state="on"
        )

        self._track_time_interval = async_track_time_interval(self._hass, self.async_update, interval)

        self._hass.loop.create_task(self.async_update())


    async def unsubscribe(self) -> bool:
        """Unsubscribe to tracks for unload."""
        self._track_time_interval()
        self._track_state_change()
        return True


    async def _set_brightness(self, light: str, brightness: int):
        """Set the brightness of a light entity."""
        await self._hass.services.async_call(
            LIGHT_DOMAIN,
            SERVICE_TURN_ON,
            {ATTR_ENTITY_ID: light, ATTR_BRIGHTNESS: brightness},
            blocking=True,
        )
        await self._hass.async_block_till_done()
        #await self._async_update()
        _LOGGER.debug("Auto Dim: Adjust light %s, to %s", light, brightness)


    async def _calculate_brightness(self):
        """Calculate the light brightness based on time of day."""

        mininum_brightness = self._min_brightness
        maximum_brightness = self._max_brightness

        today = dt_util.start_of_local_day(dt_util.now())
        current_time = dt_util.now()

        sunrise_time = get_astral_event_next(self._hass, SUN_EVENT_SUNRISE, today)
        sunset_time = get_astral_event_next(self._hass, SUN_EVENT_SUNSET, today)

        morning_start = dt_util.as_local(datetime.combine(today, self._morning_start))
        morning_end = dt_util.as_local(datetime.combine(today, self._morning_end))
        afternoon_start = dt_util.as_local(datetime.combine(today,self._afternoon_start))
        afternoon_end = dt_util.as_local(datetime.combine(today, self._afternoon_end))

        _LOGGER.debug("calc bright; current time: %s", current_time)
        _LOGGER.debug("calc bright; sunrise time: %s", sunrise_time)
        _LOGGER.debug("calc bright; sunset time: %s", sunset_time)
        _LOGGER.debug("calc bright; morning start: %s", morning_start)
        _LOGGER.debug("calc bright; morning end: %s", morning_end)
        _LOGGER.debug("calc bright; afternoon start: %s", afternoon_start)
        _LOGGER.debug("calc bright; afternoon end: %s", afternoon_end)

        brightness_delta = maximum_brightness - mininum_brightness
        morning_time_delta = (morning_end - morning_start).total_seconds()
        afternoon_time_delta = (afternoon_end - afternoon_start).total_seconds()

        if _is_time_between(current_time, morning_end, afternoon_start):
            # During Mid Afternoon
            _LOGGER.debug("calc bright; mid afternoon")
            return maximum_brightness
        elif _is_time_between(current_time, morning_start, morning_end):
            # During Morning Transition
            _LOGGER.debug("calc bright; morning transition")
            current_delta = (current_time - morning_start).total_seconds()
            return round((current_delta/morning_time_delta)*brightness_delta)+mininum_brightness
        elif _is_time_between(current_time, afternoon_start, afternoon_end):
            # During Afternoon Transition
            _LOGGER.debug("calc bright; afternoon transition")
            current_delta = (current_time - afternoon_start).total_seconds()
            return maximum_brightness-round((current_delta/afternoon_time_delta)*brightness_delta)
        
        # Sleep Time, minumim brighness
        _LOGGER.debug("calc bright; morning/evening minimum brightness")
        return mininum_brightness


    async def async_update(self, var1=None):
        """Update the brightness for each light"""

        new_brightness = await self._calculate_brightness()

        #async_dispatcher_send(self._hass, "auto_dimmer_KTEST")
        for light_entity in self._light_entities:
            
            current_state = self._hass.states.get(light_entity)

            if current_state and current_state.state == "on":
                current_brightness = current_state.attributes[ATTR_BRIGHTNESS]
                last_brightness = self._light_data[light_entity]["last_brightness"]

                _LOGGER.debug("autodim update: light entity: %s current brightness: %s", light_entity, current_brightness)
                light_data = self._light_data[light_entity]
                if light_data["enabled"]:
                    # Light is enabled, adjust brightness if required
                    if current_brightness != new_brightness:
                        # Test to see if the current brightness matches our last setting, if not, disable control
                        if last_brightness is None or (current_brightness <= (last_brightness+2) and current_brightness >= (last_brightness-2)):
                            # brightness adjustment required, current brightness doesn't match new brightness
                            _LOGGER.debug("autodim update: light entity: %s adjusted brightness to: %s", light_entity, new_brightness)
                            await self._set_brightness(light_entity, new_brightness)
                            self._light_data[light_entity]["last_brightness"] = new_brightness
                        else:
                            # Light was manually adjusted, disable and ignore future updates
                            _LOGGER.debug("autodim update: light entity: %s was manually adjusted.  Disabling", light_entity)
                            self._light_data[light_entity]["enabled"] = False
                    else:
                        _LOGGER.debug("autodim update: light %s brightness is the same, no adjustment", light_entity)        
                else:
                    _LOGGER.debug("autodim update: light entity: %s is disabled, no adjustment", light_entity)
            else:
                _LOGGER.debug("autodim update: light entity: %s state is off, no adjustment", light_entity)
            
    
    async def _state_changed(self, entity_id, from_state, to_state):
        if from_state:
            _LOGGER.debug("light state change: %s from: %s brightness %s, to: %s brightness %s", entity_id, from_state.state, from_state.attributes[ATTR_BRIGHTNESS], to_state.state, to_state.attributes[ATTR_BRIGHTNESS])
        
        if to_state:
            _LOGGER.debug("light state change: %s from: None, to: %s brightness %s", entity_id, to_state.state, to_state.attributes[ATTR_BRIGHTNESS])
        
        if from_state is None and to_state is None:
            # Entity is not ready yet, ignore:
            return
        elif from_state is None:
            # Initial Startup, do nothing
            self._hass.loop.create_task(self.async_update())
        elif to_state.state != "on":
            # this light entity was turned off, disable updates
            self._light_data[entity_id]["enabled"] = False
        elif from_state.state == "off":
            # this light entity was just turned from off to on, enable and update
            self._light_data[entity_id]["enabled"] = True
            self._light_data[entity_id]["last_brightness"] = None
            self._hass.loop.create_task(self.async_update())
