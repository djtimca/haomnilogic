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
    
    # Always create a system-wide alarm sensor, regardless of current alarm state
    entity = OmniLogicSystemAlarmSensor(
        coordinator=coordinator,
        name="System Alarm",
        icon="mdi:alarm-light",
    )
    entities.append(entity)

    # Process equipment-specific alarms
    for item_id, item in coordinator.data.items():
        # Skip the top-level "Alarms" entry as it's handled separately
        if item_id == "Alarms":
            continue
            
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
        # Regular equipment alarm handling
        if self._state_key in self.coordinator.data[self._item_id]:
            alarms = len(self.coordinator.data[self._item_id][self._state_key]) > 0
            if alarms:
                self._attrs["alarm"] = self.coordinator.data[self._item_id][
                    self._state_key
                ][0]["Message"]
                self._attrs["alarm_comment"] = self.coordinator.data[self._item_id][
                    self._state_key
                ][0].get("Comment")
                self._attrs["alarm_severity"] = self.coordinator.data[self._item_id][
                    self._state_key
                ][0].get("Severity")
            else:
                self._attrs["alarm"] = "None"
                self._attrs["alarm_comment"] = ""
                self._attrs["alarm_severity"] = ""
            return alarms
        else:
            self._attrs["alarm"] = "None"
            self._attrs["alarm_comment"] = ""
            self._attrs["alarm_severity"] = ""
            return False


class OmniLogicSystemAlarmSensor(BinarySensorEntity):
    """Define an OmniLogic System-wide Alarm Sensor."""

    def __init__(
        self,
        coordinator: OmniLogicUpdateCoordinator,
        name: str,
        icon: str,
    ) -> None:
        """Initialize System Alarm Entity."""
        self.coordinator = coordinator
        self._icon = icon
        self._attrs = {}
        
        # Find the first backyard entry to get system ID and name
        backyard_id = None
        for item_id in coordinator.data:
            if isinstance(item_id, tuple) and len(item_id) >= 2:
                backyard_id = item_id[:2]
                break
        
        if backyard_id and backyard_id in coordinator.data:
            # Get MSP system ID and backyard name from the data
            self._msp_system_id = coordinator.data[backyard_id].get("systemId")
            self._backyard_name = coordinator.data[backyard_id].get("BackyardName", "Omnilogic")
            
            # Create a friendly name that includes the backyard name
            self._name = f"{self._backyard_name} {name}"
        else:
            # Fallback if we can't find the backyard data
            self._msp_system_id = coordinator.config_entry.entry_id
            self._backyard_name = "Omnilogic"
            self._name = name
        
        # Generate a unique ID for this entity
        self._attr_unique_id = f"{self._msp_system_id}_system_alarm"

    @property
    def name(self):
        """Return the name of the entity."""
        return self._name

    @property
    def icon(self):
        """Return the icon of the entity."""
        return self._icon
        
    @property
    def device_info(self):
        """Define the device as back yard/MSP System."""
        return {
            "identifiers": {(DOMAIN, self._msp_system_id)},
            "manufacturer": "Hayward",
            "model": "OmniLogic",
            "name": self._backyard_name,
        }

    @property
    def should_poll(self) -> bool:
        """No need to poll. Coordinator notifies entity of updates."""
        return False

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        self.async_on_remove(
            self.coordinator.async_add_listener(self.async_write_ha_state)
        )

    async def async_update(self) -> None:
        """Update the entity."""
        await self.coordinator.async_request_refresh()

    @property
    def is_on(self):
        """Return the state for the system alarm sensor."""
        # Check if the Alarms key exists and has entries
        if "Alarms" in self.coordinator.data and self.coordinator.data["Alarms"]:
            alarms = len(self.coordinator.data["Alarms"]) > 0
            if alarms:
                self._attrs["alarm"] = self.coordinator.data["Alarms"][0]["Message"]
                self._attrs["alarm_comment"] = self.coordinator.data["Alarms"][0].get("Comment")
                self._attrs["alarm_severity"] = self.coordinator.data["Alarms"][0].get("Severity")
            else:
                self._attrs["alarm"] = "None"
                self._attrs["alarm_comment"] = ""
                self._attrs["alarm_severity"] = ""
            return alarms
        else:
            # No alarms key or empty alarms
            self._attrs["alarm"] = "None"
            self._attrs["alarm_comment"] = ""
            self._attrs["alarm_severity"] = ""
            return False
            
    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        return self._attrs





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
