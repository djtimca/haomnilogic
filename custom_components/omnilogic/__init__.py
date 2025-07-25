"""The Omnilogic integration."""
import logging

_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(logging.DEBUG)

from omnilogic import LoginException, OmniLogic, OmniLogicException

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import aiohttp_client

from .common import OmniLogicUpdateCoordinator
from .const import (
    CONF_SCAN_INTERVAL,
    COORDINATOR,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    OMNI_API,
)

PLATFORMS = [
    Platform.SENSOR,
    Platform.SWITCH,
    Platform.LIGHT,
    Platform.WATER_HEATER,
    Platform.BINARY_SENSOR,
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Omnilogic from a config entry."""

    conf = entry.data
    username = conf[CONF_USERNAME]
    password = conf[CONF_PASSWORD]

    polling_interval = conf.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)

    session = aiohttp_client.async_get_clientsession(hass)

    api = OmniLogic(username, password, session)

    try:
        await api.connect()
        await api.get_telemetry_data()
    except LoginException as error:
        _LOGGER.error("Login Failed: %s", error)
        _LOGGER.error("Authentication failed with email: %s. Check your credentials and ensure you're using the correct email address.", username)
        return False
    except OmniLogicException as error:
        _LOGGER.error("OmniLogic API error: %s", error)
        _LOGGER.debug("API error details: Connection attempt with email: %s", username)
        raise ConfigEntryNotReady from error

    coordinator = OmniLogicUpdateCoordinator(
        hass=hass,
        api=api,
        name="Omnilogic",
        config_entry=entry,
        polling_interval=polling_interval,
    )
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        COORDINATOR: coordinator,
        OMNI_API: api,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
