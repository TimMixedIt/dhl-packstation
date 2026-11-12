"""Free compartments and the DHL observation timestamp."""

from datetime import datetime

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import COMPARTMENTS
from .coordinator import PackstationConfigEntry, PackstationCoordinator
from .entity import PackstationEntity

PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant,
    entry: PackstationConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Add entities sharing a single coordinator."""
    async_add_entities(
        [
            *(CompartmentSensor(entry.runtime_data, size) for size in COMPARTMENTS),
            SourceTimestampSensor(entry.runtime_data),
        ]
    )


class CompartmentSensor(PackstationEntity, SensorEntity):
    """The exact number of free compartments for one size."""

    _attr_icon = "mdi:package-variant"

    def __init__(self, coordinator: PackstationCoordinator, size: str) -> None:
        """Initialize one compartment size."""
        super().__init__(coordinator, f"free_{size}")
        self._size = size
        self._attr_translation_key = f"free_{size}"

    @property
    def available(self) -> bool:
        """Do not present old, missing, or invalid counts as current data."""
        return (
            super().available
            and self.coordinator.data_is_fresh
            and self.native_value is not None
        )

    @property
    def native_value(self) -> int | None:
        """Return the count; zero is a valid observation."""
        return self.coordinator.data.compartments[self._size]


class SourceTimestampSensor(PackstationEntity, SensorEntity):
    """Keep the original timestamp visible even when counts expire."""

    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_translation_key = "source_timestamp"

    def __init__(self, coordinator: PackstationCoordinator) -> None:
        """Initialize the timestamp entity."""
        super().__init__(coordinator, "source_timestamp")

    @property
    def native_value(self) -> datetime | None:
        """Return the time of DHL's observation, not our HTTP request."""
        return self.coordinator.data.source_timestamp
