"""Common device identity for all station entities."""

from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import PackstationCoordinator


class PackstationEntity(CoordinatorEntity[PackstationCoordinator]):
    """An entity belonging to a public Packstation service."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: PackstationCoordinator, key: str) -> None:
        """Set a stable identity and device metadata."""
        super().__init__(coordinator)
        self._key = key
        station = coordinator.data
        self._attr_unique_id = f"{station.primary_key}_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, station.primary_key)},
            entry_type=DeviceEntryType.SERVICE,
            manufacturer="DHL",
            model="Packstation",
            name=f"Packstation {station.station_number} · {station.postal_code}",
            configuration_url=(
                "https://www.dhl.de/de/privatkunden/dhl-standorte-finden.html"
                f"?address={station.postal_code}%3A{station.station_number}"
                "&locationType=packstationen"
            ),
        )

    @property
    def extra_state_attributes(self) -> dict[str, str]:
        """Let bundled cards find entities independently of names and language."""
        station = self.coordinator.data
        return {
            "dhl_packstation_id": station.primary_key,
            "dhl_packstation_key": self._key,
            "station_number": station.station_number,
            "postal_code": station.postal_code,
            "city": station.city,
            "address": station.address,
            "location_name": station.name,
        }
