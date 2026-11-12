"""Report missing, stale, or implausibly future-dated observations."""

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import PackstationConfigEntry, PackstationCoordinator
from .entity import PackstationEntity

PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant,
    entry: PackstationConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the freshness diagnostic."""
    async_add_entities([StaleDataSensor(entry.runtime_data)])


class StaleDataSensor(PackstationEntity, BinarySensorEntity):
    """A problem is reported when the source observation cannot be trusted."""

    _attr_device_class = BinarySensorDeviceClass.PROBLEM
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_translation_key = "stale_data"

    def __init__(self, coordinator: PackstationCoordinator) -> None:
        """Initialize the diagnostic entity."""
        super().__init__(coordinator, "stale_data")

    @property
    def is_on(self) -> bool:
        """Return true if the source timestamp is unusable or too old."""
        return not self.coordinator.data_is_fresh
