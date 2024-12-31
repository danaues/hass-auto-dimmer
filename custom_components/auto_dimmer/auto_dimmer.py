from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, date

from typing import Any

_LOGGER = logging.getLogger(__name__)

from homeassistant.core import HomeAssistant, Event, EventStateChangedData
from homeassistant.components.light import DOMAIN as LIGHT_DOMAIN
from homeassistant.components.light import ATTR_BRIGHTNESS, ATTR_TRANSITION
from homeassistant.helpers.event import async_track_time_interval, async_track_state_change_event
from homeassistant.helpers.sun import get_astral_event_next
import homeassistant.util.dt as dt_util

from homeassistant.const import (
    ATTR_ENTITY_ID,
    SERVICE_TURN_ON,
    SUN_EVENT_SUNRISE,
    SUN_EVENT_SUNSET,
)

from .const import (
    CONF_LIGHTS,
    CONF_MAX_BRIGHTNESS,
    CONF_MIN_BRIGHTNESS,
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
    DEFAULT_MORNING_START_TIME,
    DEFAULT_MORNING_END_TIME,
    DEFAULT_AFTERNOON_START_TIME,
    DEFAULT_AFTERNOON_END_TIME,
    DEFAULT_OFFSET,
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
        config_options: dict,
    ):

        self._hass = hass
        self._name = name
        self._interval = interval
        self._light_entities = config_options[CONF_LIGHTS]
        self._light_data: dict[str, dict[str,Any]] = {}
        self._max_brightness: int = config_options[CONF_MAX_BRIGHTNESS]
        self._min_brightness: int = config_options[CONF_MIN_BRIGHTNESS]
        
        self._conf_morning_start_type = config_options[CONF_MORNING_START_TYPE]
        self._conf_morning_end_type = config_options[CONF_MORNING_END_TYPE]
        self._conf_afternoon_start_type = config_options[CONF_AFTERNOON_START_TYPE]
        self._conf_afternoon_end_type = config_options[CONF_AFTERNOON_END_TYPE]
        
        self._conf_morning_start_time = config_options.get(CONF_MORNING_START_TIME, DEFAULT_MORNING_START_TIME)
        self._conf_morning_end_time =  config_options.get(CONF_MORNING_END_TIME, DEFAULT_MORNING_END_TIME)
        self._conf_afternoon_start_time =  config_options.get(CONF_AFTERNOON_START_TIME, DEFAULT_AFTERNOON_START_TIME)
        self._conf_afternoon_end_time =  config_options.get(CONF_AFTERNOON_END_TIME, DEFAULT_AFTERNOON_END_TIME)
        
        self._conf_morning_start_offset =  config_options.get(CONF_MORNING_START_OFFSET, DEFAULT_OFFSET)
        self._conf_morning_end_offset =  config_options.get(CONF_MORNING_END_OFFSET, DEFAULT_OFFSET)
        self._conf_afternoon_start_offset =  config_options.get(CONF_AFTERNOON_START_OFFSET, DEFAULT_OFFSET)
        self._conf_afternoon_end_offset =  config_options.get(CONF_AFTERNOON_END_OFFSET, DEFAULT_OFFSET)

        self._today: datetime = dt_util.start_of_local_day(dt_util.now())

        _LOGGER.debug("Auto dimmer init; Dimmer Name: %s", self._name)

        self.morning_start_time = None
        self.morning_end_time = None
        self.afternoon_start_time = None
        self.afternoon_end_time = None

        self._calculate_schedule()
 
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

    def _calculate_schedule(self):
        """calculate sunrise and sunset times for current day"""
   
        self._sunrise_time = dt_util.as_local(get_astral_event_next(self._hass, SUN_EVENT_SUNRISE, self._today))
        self._sunset_time = dt_util.as_local(get_astral_event_next(self._hass, SUN_EVENT_SUNSET, self._today))
        
        _LOGGER.debug("schedule; sunrise time: %s", self._sunrise_time)
        _LOGGER.debug("schedule; sunset time: %s",  self._sunset_time)
        
        #Morning Start Time:
        if self._conf_morning_start_type == TIME_OPTION_SPECIFY:
            self.morning_start_time = dt_util.as_local(datetime.combine(self._today, dt_util.parse_time(self._conf_morning_start_time)))
        else:
            self.morning_start_time = self._sunrise_time + timedelta(minutes=self._conf_morning_start_offset)
        
        #Morning Finish Time:
        if self._conf_morning_end_type == TIME_OPTION_SPECIFY:
            self.morning_end_time = dt_util.as_local(datetime.combine(self._today, dt_util.parse_time(self._conf_morning_end_time)))
        else:
            self.morning_end_time = self._sunrise_time + timedelta(minutes=self._conf_morning_end_offset)
        
        #Afternoon Start Time:
        if self._conf_afternoon_start_type == TIME_OPTION_SPECIFY:
            self.afternoon_start_time = dt_util.as_local(datetime.combine(self._today, dt_util.parse_time(self._conf_afternoon_start_time)))
        else:
            self.afternoon_start_time = self._sunset_time + timedelta(minutes=self._conf_afternoon_start_offset)
        
        #Afternoon Finish Time:
        if self._conf_afternoon_end_type == TIME_OPTION_SPECIFY:
            self.afternoon_end_time = dt_util.as_local(datetime.combine(self._today, dt_util.parse_time(self._conf_afternoon_end_time)))
        else:
            self.afternoon_end_time = self._sunset_time + timedelta(minutes=self._conf_afternoon_end_offset)
        
        _LOGGER.debug("schedule; morning start time: %s", self.morning_start_time)
        _LOGGER.debug("schedule; morning end time: %s", self.morning_end_time)
        _LOGGER.debug("schedule; afternoon start time: %s", self.afternoon_start_time)
        _LOGGER.debug("schedule; afternoon end time: %s", self.afternoon_end_time)

    async def _async_init(self, interval):
        _LOGGER.debug("AutoDimmer _async_init; interval: %s", interval)

        self._track_state_change_event = async_track_state_change_event(
            self._hass, self._light_entities, self._state_changed
        )

        self._track_time_interval = async_track_time_interval(self._hass, self.async_update, interval)

        self._hass.loop.create_task(self.async_update())


    async def unsubscribe(self) -> bool:
        """Unsubscribe to tracks for unload."""
        self._track_time_interval()
        self._track_state_change_event()
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

        current_time = dt_util.now()
        
        _LOGGER.debug("calc bright; Dimmer Name: %s", self._name)
        _LOGGER.debug("calc bright; current time: %s", current_time)

        brightness_delta = maximum_brightness - mininum_brightness
        morning_time_delta = (self.morning_end_time - self.morning_start_time).total_seconds()
        afternoon_time_delta = (self.afternoon_end_time - self.afternoon_start_time).total_seconds()

        if _is_time_between(current_time, self.morning_end_time, self.afternoon_start_time):
            # During Mid Day
            _LOGGER.debug("calc bright; mid day")
            return maximum_brightness
        elif _is_time_between(current_time, self.morning_start_time, self.morning_end_time):
            # During Morning Transition
            _LOGGER.debug("calc bright; morning transition")
            current_delta = (current_time - self.morning_start_time).total_seconds()
            return round((current_delta/morning_time_delta)*brightness_delta)+mininum_brightness
        elif _is_time_between(current_time, self.afternoon_start_time, self.afternoon_end_time):
            # During Afternoon Transition
            _LOGGER.debug("calc bright; afternoon transition")
            current_delta = (current_time - self.afternoon_start_time).total_seconds()
            return maximum_brightness-round((current_delta/afternoon_time_delta)*brightness_delta)
        
        # Sleep Time, minumim brighness
        _LOGGER.debug("calc bright; morning/evening minimum brightness")
        return mininum_brightness


    async def async_update(self, var1=None):
        """Update the brightness for each light"""

        _LOGGER.debug("async_update")

        if (dt_util.start_of_local_day(dt_util.now()) - self._today).days > 0:
            # A new day has ticked by since last update, recalculate schedule times
            self._today = dt_util.start_of_local_day(dt_util.now())
            self._calculate_schedule()

        new_brightness = await self._calculate_brightness()

        for light_entity in self._light_entities:
            
            current_state = self._hass.states.get(light_entity)

            if current_state and current_state.state == "on":
                current_brightness = current_state.attributes[ATTR_BRIGHTNESS]
                last_brightness = self._light_data[light_entity]["last_brightness"]

                _LOGGER.debug("auto dimmer update: light entity: %s current brightness: %s", light_entity, current_brightness)
                light_data = self._light_data[light_entity]
                if light_data["enabled"]:
                    # Light is enabled, adjust brightness if required
                    if current_brightness != new_brightness:
                        # Test to see if the current brightness matches our last setting, if not, disable control
                        if last_brightness is None or (current_brightness <= (last_brightness+2) and current_brightness >= (last_brightness-2)):
                            # brightness adjustment required, current brightness doesn't match new brightness
                            _LOGGER.debug("auto dimmer update: light entity: %s adjusted brightness to: %s", light_entity, new_brightness)
                            await self._set_brightness(light_entity, new_brightness)
                            self._light_data[light_entity]["last_brightness"] = new_brightness
                        else:
                            # Light was manually adjusted, disable and ignore future updates
                            _LOGGER.debug("auto dimmer update: light entity: %s was manually adjusted.  Disabling", light_entity)
                            self._light_data[light_entity]["enabled"] = False
                    else:
                        _LOGGER.debug("auto dimmer update: light %s brightness is the same, no adjustment", light_entity)        
                else:
                    _LOGGER.debug("auto dimmer update: light entity: %s is disabled, no adjustment", light_entity)
            else:
                _LOGGER.debug("auto dimmer update: light entity: %s state is off, no adjustment", light_entity)
            
    
    async def _state_changed(self, event):
        """state of a tracked light entity has changed, process based on new state"""

        from_state = event.data["old_state"]
        to_state = event.data["new_state"]
        entity_id = event.data["entity_id"]

        if from_state is None and to_state is None:
            # Entity is not ready yet, ignore:
            _LOGGER.debug("_state_changed - no ready: %s ",entity_id)
            return
        elif from_state is None:
            # Initial Startup, do nothing
            _LOGGER.debug("_state_changed - Initial Startup: %s ",entity_id)
            self._hass.loop.create_task(self.async_update())
        elif to_state.state != "on":
            # this light entity was turned off, disable updates
            _LOGGER.debug("_state_changed - Turned Off - Disable: %s ",entity_id)
            self._light_data[entity_id]["enabled"] = False
        elif from_state.state == "off":
            # this light entity was just turned from off to on, enable and update
            _LOGGER.debug("_state_changed - Off to On - Enable and Update: %s ",entity_id)
            self._light_data[entity_id]["enabled"] = True
            self._light_data[entity_id]["last_brightness"] = None
            self._hass.loop.create_task(self.async_update())
