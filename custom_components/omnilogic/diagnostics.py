"""Diagnostics support for Hayward OmniLogic."""
from __future__ import annotations

import copy
import json
from typing import Any, Dict

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant

from .const import COORDINATOR, DOMAIN, OMNI_API

TO_REDACT = {CONF_USERNAME, CONF_PASSWORD}
SYSTEM_ID_FIELDS = {"systemId", "System-Id"}


def make_serializable(obj):
    """Recursively convert an object to be JSON serializable."""
    if isinstance(obj, dict):
        # Convert dictionary with potential tuple keys
        result = {}
        for k, v in obj.items():
            # Convert tuple keys to string
            if isinstance(k, tuple):
                k = "_".join(str(item) for item in k)
            else:
                k = str(k)
            # Recursively process the value
            result[k] = make_serializable(v)
        return result
    elif isinstance(obj, list):
        # Process each item in the list
        return [make_serializable(item) for item in obj]
    elif isinstance(obj, tuple):
        # Convert tuples to lists
        return [make_serializable(item) for item in obj]
    elif isinstance(obj, (str, int, float, bool, type(None))):
        # These types are already JSON serializable
        return obj
    else:
        # Convert any other types to strings
        return str(obj)


def redact_system_ids(data):
    """Recursively redact system IDs in the data."""
    if isinstance(data, dict):
        result = {}
        for k, v in data.items():
            # Check if this key is a system ID field
            if k in SYSTEM_ID_FIELDS:
                result[k] = "**REDACTED**"
            else:
                # Check if the key contains a system ID (like "Backyard_49840")
                new_k = k
                if isinstance(k, str) and any(part.isdigit() and len(part) >= 4 for part in k.split("_")):
                    # Replace numeric parts that look like IDs with REDACTED
                    parts = k.split("_")
                    new_k = "_".join(["**REDACTED**" if part.isdigit() and len(part) >= 4 else part for part in parts])
                
                # Recursively process the value
                result[new_k] = redact_system_ids(v)
        return result
    elif isinstance(data, list):
        # Process each item in the list
        return [redact_system_ids(item) for item in data]
    else:
        # Return other types as is
        return data


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id][COORDINATOR]
    api = hass.data[DOMAIN][entry.entry_id][OMNI_API]

    # Get MSP config data using the correct method
    try:
        # Use get_msp_config_file as specified by the API author
        msp_config = await api.get_msp_config_file()
        # Ensure MSP config is serializable
        msp_config = make_serializable(msp_config)
    except Exception as e:
        msp_config = {"error": f"Failed to retrieve MSP config: {str(e)}"}
    
    # Convert telemetry data to be JSON serializable
    telemetry_data = make_serializable(coordinator.data)
    
    # Redact system IDs from telemetry data and MSP config
    telemetry_data = redact_system_ids(telemetry_data)
    msp_config = redact_system_ids(msp_config)
    
    # Create diagnostics data
    diagnostics_data = {
        "entry": async_redact_data(entry.as_dict(), TO_REDACT),
        "msp_config": msp_config,
        "telemetry_data": telemetry_data,
    }

    return diagnostics_data
