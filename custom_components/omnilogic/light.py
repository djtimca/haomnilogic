"""Platform for light integration."""
import time

from omnilogic import LightEffect, OmniLogicException
import voluptuous as vol

from homeassistant.components.light import ATTR_EFFECT, LightEntity, ColorMode
from homeassistant.components.light import LightEntityFeature
from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.helpers import config_validation as cv, entity_platform

from .common import OmniLogicEntity, OmniLogicUpdateCoordinator
from .const import COORDINATOR, DOMAIN

SERVICE_SET_V2EFFECT = "set_v2_lights"


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the light platform."""

    coordinator = hass.data[DOMAIN][entry.entry_id][COORDINATOR]
    entities = []

    for item_id, item in coordinator.data.items():
        id_len = len(item_id)
        item_kind = item_id[-2]
        entity_settings = LIGHT_TYPES.get((id_len, item_kind))

        if not entity_settings:
            continue

        for entity_setting in entity_settings:
            for state_key, entity_class in entity_setting["entity_classes"].items():
                if state_key not in item:
                    continue

                guard = False
                for guard_condition in entity_setting["guard_condition"]:
                    if guard_condition and all(
                        item.get(guard_key) == guard_value
                        for guard_key, guard_value in guard_condition.items()
                    ):
                        guard = True

                if guard:
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
        SERVICE_SET_V2EFFECT,
        {
            vol.Optional("brightness"): vol.All(
                vol.Coerce(int), vol.Range(min=0, max=4)
            ),
            vol.Optional("speed"): vol.All(vol.Coerce(int), vol.Range(min=0, max=8)),
        },
        "async_set_v2effect",
    )


class OmniLogicLightControl(OmniLogicEntity, LightEntity):
    """Define an Omnilogic Water Heater entity."""

    def __init__(
        self,
        coordinator: OmniLogicUpdateCoordinator,
        kind: str,
        name: str,
        icon: str,
        item_id: tuple,
        state_key: str,
    ):
        """Initialize Entities."""
        super().__init__(
            coordinator=coordinator,
            kind=kind,
            name=name,
            item_id=item_id,
            icon=icon,
        )

        self._state_key = state_key
        self._wait_for_state_change = False
        if coordinator.data[item_id].get("V2") == "yes" or coordinator.data[item_id].get("speed"):
            self._version = 2
            self._brightness = 4
            self._speed = 4
        else:
            self._version = 1

        self._last_action = 0
        self._state = None
        self._state_delay = 60
        self._effect = None
        self._attr_supported_color_modes = {ColorMode.ONOFF}

    @property
    def is_on(self):
        """Return if the light is on."""
        if self._last_action < (time.time() - self._state_delay):
            if self._version == 2:
                self._attrs["brightness"] = self.coordinator.data[self._item_id].get(
                    "brightness"
                )
                self._attrs["speed"] = self.coordinator.data[self._item_id].get("speed")

            self._state = int(self.coordinator.data[self._item_id][self._state_key])

        return self._state

    @property
    def effect(self):
        """Return the current light effect."""

        if self._last_action < (time.time() - self._state_delay):
            self._effect = LightEffect(
                self.coordinator.data[self._item_id]["currentShow"]
            ).name

        return self._effect

    @property
    def effect_list(self):
        """Return the supported light effects."""
        effect_list = list(LightEffect.__members__)[:17]
        if self._version == 2:
            effect_list = list(LightEffect.__members__)

        return effect_list

    @property
    def supported_features(self):
        """Return the list of supported features of the light."""
        return LightEntityFeature.EFFECT
        
    @property
    def color_mode(self):
        """Return the color mode of the light."""
        return ColorMode.ONOFF

    async def async_set_effect(self, effect):
        """Set the light show effect."""
        self._last_action = time.time()
        self._effect = LightEffect[effect].value
        self.async_schedule_update_ha_state()

        await self.coordinator.api.set_lightshow(
            int(self._item_id[1]),
            int(self._item_id[3]),
            int(self._item_id[-1]),
            int(LightEffect[effect].value),
        )

    async def async_turn_on(self, **kwargs):
        """Turn on the light."""
        self._last_action = time.time()
        self._state = True
        self.async_schedule_update_ha_state()

        if kwargs.get(ATTR_EFFECT):
            await self.async_set_effect(kwargs[ATTR_EFFECT])

        await self.coordinator.api.set_relay_valve(
            int(self._item_id[1]),
            int(self._item_id[3]),
            int(self._item_id[-1]),
            1,
        )

    async def async_turn_off(self, **kwargs):
        """Turn off the light."""
        self._last_action = time.time()
        self._state = False
        self.async_schedule_update_ha_state()

        await self.coordinator.api.set_relay_valve(
            int(self._item_id[1]),
            int(self._item_id[3]),
            int(self._item_id[-1]),
            0,
        )

    async def async_set_v2effect(self, **kwargs):
        """Set the light effect speed or brightness for V2 lights."""

        if self._version == 2:
            speed = kwargs.get("speed", self._speed)
            brightness = kwargs.get("brightness", self._brightness)
            if 0 <= speed <= 8 and 0 <= brightness <= 4:
                await self.coordinator.api.set_lightshowv2(
                    int(self._item_id[1]),
                    int(self._item_id[3]),
                    int(self._item_id[-1]),
                    int(self.coordinator.data[self._item_id]["currentShow"]),
                    speed,
                    brightness,
                )

            else:
                raise OmniLogicException("Speed must be 0-8 and brightness 0-4.")
        else:
            raise OmniLogicException(
                "Cannot set effect speed or brightness on version 1 lights."
            )


LIGHT_TYPES = {
    (6, "Lights"): [
        {
            "entity_classes": {"lightState": OmniLogicLightControl},
            "name": "",
            "kind": "lights",
            "icon": None,
            "guard_condition": [],
        },
    ],
}