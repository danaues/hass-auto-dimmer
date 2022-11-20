
from homeassistant.components.light import VALID_TRANSITION
#from homeassistant.helpers import selector
from homeassistant.helpers.selector import selector
import homeassistant.util.dt as dt_util
import homeassistant.helpers.config_validation as cv
import voluptuous as vol

DOMAIN = "auto_dimmer"

DEFAULT_INTERVAL = 5
DEFAULT_LIGHTS = []
DEFAULT_MAX_BRIGHTNESS = 255
DEFAULT_MIN_BRIGHTNESS = 25

TIME_OPTION_SPECIFY = "specify a time"
TIME_OPTION_SUNRISE_OFFSET = "sunrise with offset"
TIME_OPTION_SUNSET_OFFSET = "sunset with offset"

DEFAULT_MORNING_START_TYPE = TIME_OPTION_SPECIFY
DEFAULT_MORNING_END_TYPE = TIME_OPTION_SPECIFY
DEFAULT_AFTERNOON_START_TYPE = TIME_OPTION_SPECIFY
DEFAULT_AFTERNOON_END_TYPE = TIME_OPTION_SPECIFY

DEFAULT_MORNING_START_TIME = dt_util.parse_time("07:00:00")
DEFAULT_MORNING_END_TIME = dt_util.parse_time("11:00:00")
DEFAULT_AFTERNOON_START_TIME = dt_util.parse_time("14:00:00")
DEFAULT_AFTERNOON_END_TIME = dt_util.parse_time("17:00:00")
DEFAULT_OFFSET = 0

CONF_LIGHTS = "light_entities"
CONF_INTERVAL = "interval"
CONF_TRANSITION = "transition"
CONF_MAX_BRIGHTNESS = "max_brightness"
CONF_MIN_BRIGHTNESS = "min_brightness"

CONF_MORNING_START_TYPE = "morning_start_type"
CONF_MORNING_END_TYPE = "morning_end_type"
CONF_AFTERNOON_START_TYPE = "afternoon_start_type"
CONF_AFTERNOON_END_TYPE = "afternoon_end_type"

CONF_MORNING_START_TIME = "morning_start_time"
CONF_MORNING_END_TIME = "morning_end_time"
CONF_AFTERNOON_START_TIME = "afternoon_start_time"
CONF_AFTERNOON_END_TIME = "afternoon_end_time"

CONF_MORNING_START_OFFSET = "morning_start_offset"
CONF_MORNING_END_OFFSET = "morning_end_offset"
CONF_AFTERNOON_START_OFFSET = "afternoon_start_offset"
CONF_AFTERNOON_END_OFFSET = "afternoon_end_offset"

STEP_IMPORT_FAILED = "import_failed"
ABORT_REASON_IMPORT_FAILED = "import_failed"

def int_between(min_int, max_int):
    """Return an integer between 'min_int' and 'max_int'."""
    return vol.All(vol.Coerce(int), vol.Range(min=min_int, max=max_int))

OPTION_INIT_FIELDS = [
    (CONF_LIGHTS, DEFAULT_LIGHTS, cv.entity_ids),
    (CONF_INTERVAL, DEFAULT_INTERVAL, cv.positive_int),
    (CONF_MIN_BRIGHTNESS, DEFAULT_MIN_BRIGHTNESS, int_between(1, 255)),
    (CONF_MAX_BRIGHTNESS, DEFAULT_MAX_BRIGHTNESS, int_between(1, 255)),
    (CONF_MORNING_START_TYPE, DEFAULT_MORNING_START_TYPE, selector({"select": {"mode": "dropdown", "options": [TIME_OPTION_SPECIFY, TIME_OPTION_SUNRISE_OFFSET]}})),
    (CONF_MORNING_END_TYPE, DEFAULT_MORNING_END_TYPE, selector({"select": {"mode": "dropdown", "options": [TIME_OPTION_SPECIFY, TIME_OPTION_SUNRISE_OFFSET]}})),
    (CONF_AFTERNOON_START_TYPE, DEFAULT_AFTERNOON_START_TYPE, selector({"select": {"mode": "dropdown", "options": [TIME_OPTION_SPECIFY, TIME_OPTION_SUNSET_OFFSET]}})),
    (CONF_AFTERNOON_END_TYPE, DEFAULT_AFTERNOON_END_TYPE, selector({"select": {"mode": "dropdown", "options": [TIME_OPTION_SPECIFY, TIME_OPTION_SUNSET_OFFSET]}})),
]

OPTION_MORNING_START_OFFSET = (CONF_MORNING_START_OFFSET, DEFAULT_OFFSET, int)
OPTION_MORNING_END_OFFSET = (CONF_MORNING_END_OFFSET, DEFAULT_OFFSET, int)
OPTION_AFTERNOON_START_OFFSET = (CONF_AFTERNOON_START_OFFSET, DEFAULT_OFFSET, int)
OPTION_AFTERNOON_END_OFFSET = (CONF_AFTERNOON_END_OFFSET, DEFAULT_OFFSET, int)

OPTION_MORNING_START_TIME = (CONF_MORNING_START_TIME, DEFAULT_MORNING_START_TIME, selector({"time": {}}))
OPTION_MORNING_END_TIME = (CONF_MORNING_END_TIME, DEFAULT_MORNING_END_TIME, selector({"time": {}}))
OPTION_AFTERNOON_START_TIME = (CONF_AFTERNOON_START_TIME, DEFAULT_AFTERNOON_START_TIME, selector({"time": {}}))
OPTION_AFTERNOON_END_TIME = (CONF_AFTERNOON_END_TIME, DEFAULT_AFTERNOON_END_TIME, selector({"time": {}}))