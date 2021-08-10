"""."""
import logging

from apcaccess import status as apc
from apcaccess.status import ALL_UNITS
import socket

import voluptuous as vol

from homeassistant.components.sensor import PLATFORM_SCHEMA, SensorEntity

from homeassistant.const import (
    CONF_NAME,
    CONF_HOST,
    CONF_PORT,
    CONF_TIMEOUT,
    TIME_MINUTES,
    TIME_SECONDS,
    POWER_WATT,
    PERCENTAGE,
    DEVICE_CLASS_POWER,
    DEVICE_CLASS_VOLTAGE,
    DEVICE_CLASS_CURRENT
)


# Constants changed for energy dashboard
# https://github.com/home-assistant/core/commit/074d762664976d3414b8a33535e9b850d80a42fa#diff-07e20eb7c6560330f9774eb23343f5dd3002106bb8b6523ccb18d95857990d77

try:
    from homeassistant.const import (
        VOLT,
        ELECTRICAL_CURRENT_AMPERE,
    )
except ImportError:
    from homeassistant.const import ELECTRIC_POTENTIAL_VOLT as VOLT
    from homeassistant.const import ELECTRIC_CURRENT_AMPERE as ELECTRICAL_CURRENT_AMPERE



import homeassistant.helpers.config_validation as cv

_LOGGER = logging.getLogger(__name__)

DEFAULT_PREFIX = 'APC'
DEFAULT_HOST = '127.0.0.1'
DEFAULT_PORT = 3551
DEFAULT_TIMEOUT = 30
DEFAULT_SENSOR_TIMEOUT = 5

CONF_SENSORS = 'sensors'
CONF_POWER_CALC = 'power_calc'
CONF_SENSOR_TIMEOUT = 'sensor_timeout'

POWER_CALC_NAME = 'Power'

DEVICE_CLASS = {
    'Watts': DEVICE_CLASS_POWER,
    'Volts': DEVICE_CLASS_VOLTAGE,
    'Amps': DEVICE_CLASS_CURRENT
}

MEASUREMENTS = {
    'Volts': VOLT,
    'Watts': POWER_WATT,
    'Amps': ELECTRICAL_CURRENT_AMPERE,
    'Percent': PERCENTAGE,
    'Minutes': TIME_MINUTES,
    'Seconds': TIME_SECONDS
}

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Optional(CONF_HOST): cv.string,
        vol.Optional(CONF_PORT): cv.positive_int,
        vol.Optional(CONF_NAME): cv.string,
        vol.Optional(CONF_TIMEOUT): cv.positive_int,
        vol.Optional(CONF_SENSOR_TIMEOUT): cv.positive_int,
        vol.Optional(CONF_POWER_CALC): cv.boolean
    }
)


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the HTTP request sensor platform."""
    name = config.get(CONF_NAME, DEFAULT_PREFIX)
    host = config.get(CONF_HOST, DEFAULT_HOST)
    port = config.get(CONF_PORT, DEFAULT_PORT)
    timeout = config.get(CONF_TIMEOUT, DEFAULT_TIMEOUT)
    sensor_timeout = config.get(CONF_SENSOR_TIMEOUT, DEFAULT_SENSOR_TIMEOUT)
    power_calc = config.get(CONF_POWER_CALC, True)

    try:
        output = apc.parse(apc.get(host=host, port=port, timeout=timeout), strip_units=False)
    except (TimeoutError, socket.timeout):
        _LOGGER.error(f"Platform not setup! Unable to reach apcussd at: {host}:{port}")
        return

    add_entities([APCAccessSensor(host, port, name, sensor, sensor_timeout, output[sensor]) for sensor in output], True)
    if power_calc:
        add_entities([PowerUsage(host, port, name, sensor_timeout)], True)


class APCAccessSensor(SensorEntity):
    """Representation of APCAccess sensor."""

    def __init__(self, host, port, name, sensor, timeout, sensor_data):
        """Initialize the sensor."""
        self._host = host
        self._port = port
        self._sensor = sensor
        self._timeout = timeout
        self._state = None
        self._available = True
        self._measurement = None
        self._device_class = None
        self._name = f'{name} {sensor.capitalize()}'
        self._id = f'{host}_{port}_{sensor}'
        _unit = None
        for unit in ALL_UNITS:
            if sensor_data.endswith(" %s" % unit):
                _unit = unit
        self._measurement = MEASUREMENTS.get(_unit, None)
        self._device_class = DEVICE_CLASS.get(_unit, None)

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement of the sensor."""
        return self._measurement

    @property
    def device_class(self):
        """Return the device class of the sensor."""
        return self._device_class

    @property
    def available(self):
        """Return the availability of the sensor."""
        return self._available

    # @property
    # def extra_state_attributes(self):
    #     """Return the state attributes."""

    #     attr = dict(self._details)
    #     if self._state == STATE_OFFLINE:
    #         attr.update(self._error_details)
    #     return attr

    @property
    def unique_id(self):
        """Return unique ID for this sensor."""
        return self._id

    # @property
    # def icon(self):
    #     """Icon to use in the frontend, if any."""
    #     return ICON

    def update(self):
        """Update device state."""
        try:
            output = apc.parse(apc.get(host=self._host, port=self._port, timeout=self._timeout), strip_units=True)
            sensor = output[self._sensor]

        except (TimeoutError, socket.timeout, OSError):
            self._available = False
            return
        else:
            self._available = True
            self._state = sensor


class PowerUsage(SensorEntity):
    """Representation APC Power usage sensor."""

    def __init__(self, host, port, name, timeout):
        """Initialize the sensor."""
        self._host = host
        self._port = port
        self._state = None
        self._timeout = timeout
        self._available = None
        self._measurement = MEASUREMENTS['Watts']
        self._device_class = DEVICE_CLASS['Watts']
        self._name = f'{name} {POWER_CALC_NAME}'
        self._id = f'{host}_{port}_{POWER_CALC_NAME}'

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement of the sensor."""
        return self._measurement

    @property
    def device_class(self):
        """Return the device class of the sensor."""
        return self._device_class

    @property
    def available(self):
        """Return the availability of the sensor."""
        return self._available

    def update(self):
        """Update device state."""
        try:
            output = apc.parse(apc.get(host=self._host, port=self._port, timeout=self._timeout), strip_units=True)
            load = float(output['LOADPCT'])
            max_watt = float(output['NOMPOWER'])
        except (TimeoutError, socket.timeout, OSError):
            self._available = False
        except KeyError:
            self._LOGGER.warning('Insufficent sensors for power usage!')
            self._available = False
        else:
            self._available = True
            self._state = load * (max_watt / 100)
