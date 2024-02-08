"""Common classes and elements for Omnilogic Integration."""

from datetime import timedelta
import logging

import async_timeout

from omnilogic import OmniLogic, OmniLogicException, LoginException

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import ALL_ITEM_KINDS, DOMAIN

_LOGGER = logging.getLogger(__name__)


class OmniLogicUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching update data from single endpoint."""

    def __init__(
        self,
        hass: HomeAssistant,
        api: OmniLogic,
        name: str,
        config_entry: ConfigEntry,
        polling_interval: int,
    ) -> None:
        """Initialize the global Omnilogic data updater."""
        self.api = api
        self.config_entry = config_entry
        self._last_data = None
        self._timeout_count = 0

        super().__init__(
            hass=hass,
            logger=_LOGGER,
            name=name,
            update_interval=timedelta(seconds=polling_interval),
        )

    async def _async_update_data(self):
        """Fetch data from OmniLogic."""
        try:
            async with async_timeout.timeout(30):
                data = await self.api.get_telemetry_data()

            self._timeout_count = 0

        except OmniLogicException as error:
            raise UpdateFailed(f"Error updating from OmniLogic: {error}") from error

        except LoginException as error:
            raise UpdateFailed(f"Login failed for Omnilogic: {error}") from error

        except TimeoutError as error:
            self._timeout_count += 1

            if self._timeout_count > 10 or not self._last_data:
                raise UpdateFailed(f"Timeout updating OmniLogic from cloud: {error}") from error
            else:
                data = self._last_data

        parsed_data = {}
        self._last_data = data

        def get_item_data(item, item_kind, current_id, data):
            """Get data per kind of Omnilogic API item."""
            if isinstance(item, list):
                for single_item in item:
                    data = get_item_data(single_item, item_kind, current_id, data)

            if "systemId" in item:
                system_id = item["systemId"]
                current_id = current_id + (item_kind, system_id)
                data[current_id] = item

            for kind in ALL_ITEM_KINDS:
                if kind in item:
                    data = get_item_data(item[kind], kind, current_id, data)

            return data

        parsed_data = get_item_data(data, "Backyard", (), parsed_data)

        return parsed_data


class OmniLogicEntity(CoordinatorEntity[OmniLogicUpdateCoordinator]):
    """Defines the base OmniLogic entity."""

    def __init__(
        self,
        coordinator: OmniLogicUpdateCoordinator,
        kind: str,
        name: str,
        item_id: tuple,
        icon: str,
    ) -> None:
        """Initialize the OmniLogic Entity."""
        super().__init__(coordinator)

        bow_id = None
        entity_data = coordinator.data[item_id]

        backyard_id = item_id[:2]
        if len(item_id) == 6:
            bow_id = item_id[:4]

        msp_system_id = coordinator.data[backyard_id]["systemId"]
        entity_friendly_name = f"{coordinator.data[backyard_id]['BackyardName']} "
        unique_id = f"{msp_system_id}"

        if bow_id is not None:
            unique_id = f"{unique_id}_{coordinator.data[bow_id]['systemId']}"

            if kind != "Heaters":
                entity_friendly_name = (
                    f"{entity_friendly_name}{coordinator.data[bow_id]['Name']} "
                )
            else:
                entity_friendly_name = f"{entity_friendly_name}{coordinator.data[bow_id]['Operation']['VirtualHeater']['Name']} "

        unique_id = f"{unique_id}_{coordinator.data[item_id]['systemId']}_{kind}"

        if entity_data.get("Name") is not None:
            entity_friendly_name = f"{entity_friendly_name} {entity_data['Name']}"

        entity_friendly_name = f"{entity_friendly_name} {name}"

        unique_id = unique_id.replace(" ", "_")

        self._kind = kind
        self._name = entity_friendly_name
        self._unique_id = unique_id
        self._item_id = item_id
        self._icon = icon
        self._attrs = {}
        self._msp_system_id = msp_system_id
        self._backyard_name = coordinator.data[backyard_id]["BackyardName"]

    @property
    def unique_id(self) -> str:
        """Return a unique, Home Assistant friendly identifier for this entity."""
        return self._unique_id

    @property
    def name(self) -> str:
        """Return the name of the entity."""
        return self._name

    @property
    def icon(self):
        """Return the icon for the entity."""
        return self._icon

    @property
    def extra_state_attributes(self):
        """Return the attributes."""
        return self._attrs

    @property
    def device_info(self) -> DeviceInfo:
        """Define the device as back yard/MSP System."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._msp_system_id)},
            manufacturer="Hayward",
            model="OmniLogic",
            name=self._backyard_name,
        )


def check_guard(state_key, item, entity_setting):
    """Validate that this entity passes the defined guard conditions defined at setup."""

    if state_key not in item:
        return True

    for guard_condition in entity_setting["guard_condition"]:
        if guard_condition and all(
            item.get(guard_key) == guard_value
            for guard_key, guard_value in guard_condition.items()
        ):
            return True

    return False
