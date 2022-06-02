"""Definition and setup of the Omnilogic Binary Sensors for Home Assistant."""

import logging

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.config_entries import ConfigEntry

from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .common import OmniLogicEntity, OmniLogicUpdateCoordinator, check_guard
from .const import COORDINATOR, DOMAIN

async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the binary sensor platform."""

    coordinator = hass.data[DOMAIN][entry.entry_id][COORDINATOR]
    entities = []

    for item_id, item in coordinator.data.items():
        id_len = len(item_id)
        item_kind = item_id[-2]
        entity_settings = BINARY_SENSOR_TYPES.get((id_len, item_kind))
        
        if not entity_settings:
            continue

        for entity_setting in entity_settings:
            for state_key, entity_class in entity_setting["entity_classes"].items():
                if check_guard(state_key, item, entity_setting):
                    continue

                entity = entity_class(
                    coordinator=coordinator,
                    state_key=state_key,
                    name=entity_setting["name"],
                    kind=entity_setting["kind"],
                    item_id=item_id,
                    device_class=entity_setting["device_class"],
                    icon=entity_setting["icon"],
                )

                entities.append(entity)

    async_add_entities(entities)


class OmnilogicSensor(OmniLogicEntity, BinarySensorEntity):
    """Defines an Omnilogic sensor entity."""

    def __init__(
        self,
        coordinator: OmniLogicUpdateCoordinator,
        kind: str,
        name: str,
        device_class: str,
        icon: str,
        item_id: tuple,
        state_key: str,
    ) -> None:
        """Initialize Entities."""
        super().__init__(
            coordinator=coordinator,
            kind=kind,
            name=name,
            item_id=item_id,
            icon=icon,
        )

        self._device_class = device_class
        self._state_key = state_key

    @property
    def device_class(self):
        """Return the device class of the entity."""
        return self._device_class


class OmniLogicAlarmSensor(OmnilogicSensor, BinarySensorEntity):
    """Define an OmniLogic Alarm Sensor."""

    @property
    def is_on(self):
        """Return the state for the alarm sensor."""
        alarms = len(self.coordinator.data[self._item_id][self._state_key]) > 0

        if alarms:
            self._attrs["alarm"] = self.coordinator.data[self._item_id][
                self._state_key
            ][0]["Message"]
            self._attrs["alarm_comment"] = self.coordinator.data[self._item_id][
                self._state_key
            ][0].get("Comment")
        else:
            self._attrs["alarm"] = "None"
            self._attrs["alarm_comment"] = ""

        return alarms


BINARY_SENSOR_TYPES = {
    (6, "Filter"): [
        {
            "entity_classes": {"Alarms": OmniLogicAlarmSensor},
            "name": "Alarm",
            "kind": "alarm",
            "device_class": None,
            "icon": "mdi:alarm-light",
            "guard_condition": [],
        },
    ],
    (6, "Pumps"): [
        {
            "entity_classes": {"Alarms": OmniLogicAlarmSensor},
            "name": "Pump Alarm",
            "kind": "alarm",
            "device_class": None,
            "icon": "mdi:alarm-light",
            "guard_condition": [],
        },
    ],
    (6, "Chlorinator"): [
        {
            "entity_classes": {"Alarms": OmniLogicAlarmSensor},
            "name": "Alarm",
            "kind": "alarm",
            "device_class": None,
            "icon": "mdi:alarm-light",
            "guard_condition": [
                {
                    "Shared-Type": "BOW_SHARED_EQUIPMENT",
                    "status": "0",
                },
                {
                    "operatingMode": "2",
                },
            ],
        },
    ],
    (6, "CSAD"): [
        {
            "entity_classes": {"Alarms": OmniLogicAlarmSensor},
            "name": "CSAD Alarm",
            "kind": "alarm",
            "device_class": None,
            "icon": "mdi:alarm-light",
            "guard_condition": [
                {"ph": "", "orp": ""},
            ],
        },
    ],
    (6, "Heaters"): [
        {
            "entity_classes": {"Alarms": OmniLogicAlarmSensor},
            "name": "Heater Alarm",
            "kind": "alarm",
            "device_class": None,
            "icon": "mdi:alarm-light",
            "guard_condition": [],
        },
    ],
    (6, "Lights"): [
        {
            "entity_classes": {"Alarms": OmniLogicAlarmSensor},
            "name": "Alarm",
            "kind": "alarm",
            "device_class": None,
            "icon": "mdi:alarm-light",
            "guard_condition": [],
        },
    ],
    (6, "Relays"): [
        {
            "entity_classes": {"Alarms": OmniLogicAlarmSensor},
            "name": "Alarm",
            "kind": "alarm",
            "device_class": None,
            "icon": "mdi:alarm-light",
            "guard_condition": [],
        },
    ],
    (4, "Relays"): [
        {
            "entity_classes": {"Alarms": OmniLogicAlarmSensor},
            "name": "Alarm",
            "kind": "alarm",
            "device_class": None,
            "icon": "mdi:alarm-light",
            "guard_condition": [],
        },
    ],
}
