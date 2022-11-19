
from homeassistant.components.light import VALID_TRANSITION
from homeassistant.helpers import selector
from homeassistant.helpers.selector import selector
import homeassistant.util.dt as dt_util
import homeassistant.helpers.config_validation as cv
import voluptuous as vol

DOMAIN = "auto_dimmer"

NONE_STR = "None"

DEFAULT_INTERVAL = 300
DEFAULT_TRANSITION = 60
DEFAULT_LIGHTS = []
DEFAULT_MAX_BRIGHTNESS = 255
DEFAULT_MIN_BRIGHTNESS = 25
DEFAULT_MORNING_START = dt_util.parse_time("09:00:00")
DEFAULT_MORNING_END = dt_util.parse_time("13:00:00")
DEFAULT_AFTERNOON_START = dt_util.parse_time("17:00:00")
DEFAULT_AFTERNOON_END = dt_util.parse_time("21:00:00")

CONF_LIGHTS = "light_entities"
CONF_INTERVAL = "interval"
CONF_TRANSITION = "transition"
CONF_MAX_BRIGHTNESS = "max_brightness"
CONF_MIN_BRIGHTNESS = "min_brightness"
CONF_MORNING_START = "morning_start"
CONF_MORNING_END = "morning_end"
CONF_AFTERNOON_START = "afternoon_start"
CONF_AFTERNOON_END = "afternoon_end"

STEP_IMPORT_FAILED = "import_failed"
ABORT_REASON_IMPORT_FAILED = "import_failed"

def int_between(min_int, max_int):
    """Return an integer between 'min_int' and 'max_int'."""
    return vol.All(vol.Coerce(int), vol.Range(min=min_int, max=max_int))

VALIDATION_TUPLES = [
    (CONF_LIGHTS, DEFAULT_LIGHTS, cv.entity_ids),
    (CONF_INTERVAL, DEFAULT_INTERVAL, cv.positive_int),
    (CONF_TRANSITION, DEFAULT_TRANSITION, VALID_TRANSITION),
    (CONF_MIN_BRIGHTNESS, DEFAULT_MIN_BRIGHTNESS, int_between(1, 255)),
    (CONF_MAX_BRIGHTNESS, DEFAULT_MAX_BRIGHTNESS, int_between(1, 255)),
    (CONF_MORNING_START, DEFAULT_MORNING_START, selector({"time": {}})),
    (CONF_MORNING_END, DEFAULT_MORNING_END, selector({"time": {}})),
    (CONF_AFTERNOON_START, DEFAULT_AFTERNOON_START, selector({"time": {}})),
    (CONF_AFTERNOON_END, DEFAULT_AFTERNOON_END, selector({"time": {}})),
]
