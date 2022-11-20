"""Diagnostics support for Auto Dimmer."""
from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .auto_dimmer import AutoDimmer


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    auto_dimmer: AutoDimmer = hass.data[DOMAIN][entry.entry_id]
    
    return {
        "entry": {
            "title": entry.title,
            "data": dict(entry.data),
            "options": dict(entry.options),
        },
        "integration_data": {
            "Light Entities": auto_dimmer._light_entities,
            "Max Brightness": auto_dimmer._max_brightness,
            "Min Brightness": auto_dimmer._min_brightness,
            "Morning Start Time": auto_dimmer.morning_start_time,
            "Morning End Time": auto_dimmer.morning_end_time,
            "Afternoon Start Time": auto_dimmer.afternoon_start_time,
            "Afternoon End Time": auto_dimmer.afternoon_end_time,
        },
        "light data": {
            "lights": dict(auto_dimmer._light_data),
        }
    }
