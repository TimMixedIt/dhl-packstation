"""Constants for DHL Packstation."""

from datetime import timedelta

DOMAIN = "dhl_packstation"
CONF_POSTAL_CODE = "postal_code"
CONF_STATION_NUMBER = "station_number"
CONF_PRIMARY_KEY = "primary_key"
CONF_MAX_AGE = "max_age_minutes"
DEFAULT_MAX_AGE = 60
UPDATE_INTERVAL = timedelta(minutes=15)
API_BASE = "https://www.dhl.de/int-postfinder/webservice/rest/v1"
COMPARTMENTS = {
    "s": "freeCompartmentsS",
    "m": "freeCompartmentsM",
    "l": "freeCompartmentsL",
    "xl": "freeCompartmentsXl",
}
