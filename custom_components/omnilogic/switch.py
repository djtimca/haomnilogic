"""Platform for Omnilogic switch integration."""
import time

import voluptuous as vol

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv, entity_platform
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.exceptions import IntegrationError

from .common import OmniLogicEntity, OmniLogicUpdateCoordinator, check_guard
from .const import COORDINATOR, DOMAIN, PUMP_TYPES

SERVICE_SET_SPEED = "set_pump_speed"
SERVICE_SET_CHLOR_TIMED_PERCENT = "set_chlor_timed_percent"
OMNILOGIC_SWITCH_OFF = 7


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the light platform."""

    coordinator = hass.data[DOMAIN][entry.entry_id][COORDINATOR]
    entities = []

    for item_id, item in coordinator.data.items():
        id_len = len(item_id)
        item_kind = item_id[-2]
        entity_settings = SWITCH_TYPES.get((id_len, item_kind))

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
                    icon=entity_setting["icon"],
                )

                entities.append(entity)

    async_add_entities(entities)

    # register service
    platform = entity_platform.async_get_current_platform()

    platform.async_register_entity_service(
        SERVICE_SET_SPEED,
        {
            vol.Required("speed"): cv.positive_int
        },
        "async_set_speed",
    )

    platform.async_register_entity_service(
        SERVICE_SET_CHLOR_TIMED_PERCENT,
        {
            vol.Required("timed_percent"): vol.All(cv.positive_int, vol.Range(min=0, max=100))
        },
        "async_set_chlor_timed_percent",
    )


class OmniLogicSwitch(OmniLogicEntity, SwitchEntity):
    """Define an Omnilogic Base Switch entity to be extended."""

    def __init__(
        self,
        coordinator: OmniLogicUpdateCoordinator,
        kind: str,
        name: str,
        icon: str,
        item_id: tuple,
        state_key: str,
    ) -> None:

        switch_type = coordinator.data[item_id].get("Type", "")

        if switch_type == "RLY_VALVE_ACTUATOR":
            icon = "mdi:valve"

        """Initialize Entities."""
        super().__init__(
            coordinator=coordinator,
            kind=kind,
            name=name,
            item_id=item_id,
            icon=icon,
        )

        self._state_key = state_key
        self._state = None
        self._last_action = 0
        self._state_delay = 30

    @property
    def is_on(self):
        """Return the on/off state of the switch."""
        state_int = 0

        # The Omnilogic API has a significant delay in state reporting after calling for a
        # change. This state delay will ensure that HA keeps an optimistic value of state
        # during this period to improve the user experience and avoid confusion.
        if self._last_action < (time.time() - self._state_delay):
            state_int = int(self.coordinator.data[self._item_id][self._state_key])

            if self._state == OMNILOGIC_SWITCH_OFF:
                state_int = 0

        self._state = state_int != 0

        return self._state


class OmniLogicRelayControl(OmniLogicSwitch):
    """Define the OmniLogic Relay entity."""

    async def async_turn_on(self, **kwargs):
        """Turn on the relay."""
        self._state = True
        self._last_action = time.time()
        self.async_write_ha_state()

        """ Patch: determine case where the switch/relay is not associated with a bow """
        bow_id = int(self._item_id[3])
        if len(self._item_id) == 4:
            bow_id = 0

        await self.coordinator.api.set_relay_valve(
            int(self._item_id[1]),
            bow_id,
            int(self._item_id[-1]),
            1,
        )

    async def async_turn_off(self, **kwargs):
        """Turn off the relay."""
        self._state = False
        self._last_action = time.time()
        self.async_write_ha_state()

        """ Patch: determine case where the switch/relay is not associated with a bow """
        bow_id = int(self._item_id[3])
        if len(self._item_id) == 4:
            bow_id = 0

        await self.coordinator.api.set_relay_valve(
            int(self._item_id[1]),
            bow_id,
            int(self._item_id[-1]),
            0,
        )


class OmniLogicPumpControl(OmniLogicSwitch):
    """Define the OmniLogic Pump Switch Entity."""

    def __init__(
        self,
        coordinator: OmniLogicUpdateCoordinator,
        kind: str,
        name: str,
        icon: str,
        item_id: tuple,
        state_key: str,
    ) -> None:
        """Initialize entities."""
        super().__init__(
            coordinator=coordinator,
            kind=kind,
            name=name,
            icon=icon,
            item_id=item_id,
            state_key=state_key,
        )

        self._max_speed = int(coordinator.data[item_id].get("Max-Pump-Speed", 100))
        self._min_speed = int(coordinator.data[item_id].get("Min-Pump-Speed", 0))

        if "Filter-Type" in coordinator.data[item_id]:
            self._pump_type = PUMP_TYPES[coordinator.data[item_id]["Filter-Type"]]
        else:
            self._pump_type = PUMP_TYPES[coordinator.data[item_id]["Type"]]

        self._last_speed = None

    async def async_turn_on(self, **kwargs):
        """Turn on the pump."""
        self._state = True
        self._last_action = time.time()
        self.async_write_ha_state()

        on_value = 100

        if self._pump_type != "SINGLE" and self._last_speed:
            on_value = self._last_speed

        await self.coordinator.api.set_relay_valve(
            int(self._item_id[1]),
            int(self._item_id[3]),
            int(self._item_id[-1]),
            on_value,
        )

    async def async_turn_off(self, **kwargs):
        """Turn off the pump."""
        self._state = False
        self._last_action = time.time()
        self.async_write_ha_state()

        if self._pump_type != "SINGLE":
            if "filterSpeed" in self.coordinator.data[self._item_id]:
                self._last_speed = self.coordinator.data[self._item_id]["filterSpeed"]
            else:
                self._last_speed = self.coordinator.data[self._item_id]["pumpSpeed"]

        await self.coordinator.api.set_relay_valve(
            int(self._item_id[1]),
            int(self._item_id[3]),
            int(self._item_id[-1]),
            0,
        )

    async def async_set_speed(self, speed):
        """Set the switch speed."""

        if self._pump_type != "SINGLE":
            if self._min_speed <= speed <= self._max_speed:
                success = await self.coordinator.api.set_relay_valve(
                    int(self._item_id[1]),
                    int(self._item_id[3]),
                    int(self._item_id[-1]),
                    speed,
                )

                if success:
                    self.async_write_ha_state()

            else:
                raise IntegrationError(
                    "Cannot set speed. Speed is outside pump range."
                )

        else:
            raise IntegrationError("Cannot set speed on a non-variable speed pump.")


class OmniLogicChlorinatorSwitch(OmniLogicSwitch):
    """Define an OmniLogic Chlorinator Switch."""

    def __init__(self, coordinator, state_key, name, kind, item_id, icon):
        """Initialize the chlorinator switch."""
        super().__init__(coordinator, kind, name, icon, item_id, state_key)
        self._equipment_id = self.coordinator.data[self._item_id]["systemId"]



    async def async_turn_on(self):
        """Turn the chlorinator on."""
        success, _ = await self.coordinator.api.set_chlor_params(
            int(self._item_id[3]),  # PoolID
            int(self._equipment_id),  # ChlorID (from Operation System-Id)
            3  # cfgState: Enable/On
        )
        
        if success:
            await self.coordinator.async_request_refresh()

    async def async_turn_off(self):
        """Turn the chlorinator off."""
        success, _ = await self.coordinator.api.set_chlor_params(
            int(self._item_id[3]),  # PoolID
            int(self._equipment_id),  # ChlorID (from Operation System-Id)
            2  # cfgState: Disable/Off
        )
        
        if success:
            await self.coordinator.async_request_refresh()

    async def async_set_chlor_timed_percent(self, timed_percent):
        """Set the chlorinator timed percentage."""
        success, _ = await self.coordinator.api.set_chlor_params(
            int(self._item_id[3]),  # PoolID
            int(self._equipment_id),  # ChlorID (from Operation System-Id)
            None,  # cfgState (not changing state)
            None,  # opMode (not changing)
            None,  # bowType (not changing)
            int(timed_percent)  # timedPercent
        )
        
        if success:
            await self.coordinator.async_request_refresh()


class OmniLogicSuperchlorinateSwitch(OmniLogicSwitch):
    """Define an OmniLogic Superchlorinate Switch."""

    def __init__(self, coordinator, state_key, name, kind, item_id, icon):
        """Initialize the superchlorinate switch."""
        super().__init__(coordinator, kind, name, icon, item_id, state_key)
        self._equipment_id = self.coordinator.data[self._item_id]["Operation"][0]["System-Id"]

    @property
    def available(self):
        """Return if the superchlorinate switch is available."""
        # Only available if parent chlorinator is on
        return (
            super().available and 
            self.coordinator.data[self._item_id]["operatingMode"] != "0"
        )



    async def async_turn_on(self):
        """Turn superchlorination on."""
        # Ensure parent chlorinator is on first
        if self.coordinator.data[self._item_id]["operatingMode"] == "0":
            # Turn on chlorinator first
            await self.coordinator.api.set_equipment(
                int(self._item_id[3]),  # PoolID
                int(self._equipment_id),  # EquipmentID
                1  # IsOn
            )
        
        # Then enable superchlorination
        success = await self.coordinator.api.set_superchlorination(
            int(self._item_id[1]),  # MspSystemID
            int(self._item_id[3]),  # PoolID
            int(self._equipment_id),  # ChlorID
            1  # IsOn
        )
        
        if success:
            self.async_schedule_update_ha_state()

    async def async_turn_off(self):
        """Turn superchlorination off."""
        success = await self.coordinator.api.set_superchlorination(
            int(self._item_id[1]),  # MspSystemID
            int(self._item_id[3]),  # PoolID
            int(self._equipment_id),  # ChlorID
            0  # IsOn
        )
        
        if success:
            self.async_schedule_update_ha_state()


SWITCH_TYPES = {
    (4, "Relays"): [
        {
            "entity_classes": {"relayState": OmniLogicRelayControl},
            "name": "",
            "kind": "relay",
            "icon": "mdi:electric-switch",
            "guard_condition": [],
        },
    ],
    (6, "Relays"): [
        {
            "entity_classes": {"relayState": OmniLogicRelayControl},
            "name": "",
            "kind": "relay",
            "icon": "mdi:electric-switch",
            "guard_condition": [],
        }
    ],
    (6, "Pumps"): [
        {
            "entity_classes": {"pumpState": OmniLogicPumpControl},
            "name": "",
            "kind": "pump",
            "icon": "mdi:pump",
            "guard_condition": [],
        }
    ],
    (6, "Filter"): [
        {
            "entity_classes": {"filterState": OmniLogicPumpControl},
            "name": "",
            "kind": "pump",
            "icon": "mdi:pump",
            "guard_condition": [],
        }
    ],
    (6, "Chlorinator"): [
        {
            "entity_classes": {"enable": OmniLogicChlorinatorSwitch},
            "name": "",
            "kind": "chlorinator",
            "icon": "mdi:pool",
            "guard_condition": [],
        },
        {
            "entity_classes": {"scMode": OmniLogicSuperchlorinateSwitch},
            "name": "Superchlorinate",
            "kind": "superchlorinate",
            "icon": "mdi:pool-thermometer",
            "guard_condition": [],
        },
    ],
}
