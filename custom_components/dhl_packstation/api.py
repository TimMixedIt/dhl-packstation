"""Read the public DHL website's location service."""

import re
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from email.utils import parsedate_to_datetime
from typing import Any

from aiohttp import ClientError, ClientSession, ClientTimeout

from .const import API_BASE, COMPARTMENTS


class PackstationError(Exception):
    """DHL could not provide a usable response."""


class StationNotFound(PackstationError):
    """The requested Packstation was not found."""


class InvalidResponse(PackstationError):
    """DHL returned unexpected data."""


class RateLimited(PackstationError):
    """DHL requested a pause."""

    def __init__(self, retry_after: int) -> None:
        """Keep the requested pause, with a conservative minimum."""
        super().__init__("DHL rate limit")
        self.retry_after = max(900, retry_after)


def normalize_location(postal_code: str, station_number: str) -> tuple[str, str]:
    """Validate identifiers before constructing a request."""
    postal_code, station_number = postal_code.strip(), station_number.strip()
    if not re.fullmatch(r"[0-9]{5}", postal_code) or not re.fullmatch(
        r"[0-9]{1,4}", station_number
    ):
        raise ValueError("Invalid postal code or Packstation number")
    if int(station_number) == 0:
        raise ValueError("Packstation number must be positive")
    return postal_code, str(int(station_number))


@dataclass(frozen=True)
class PackstationData:
    """One station and its reported availability."""

    primary_key: str
    postal_code: str
    station_number: str
    city: str
    address: str
    name: str
    compartments: dict[str, int | None]
    source_timestamp: datetime | None

    def is_fresh(self, now: datetime, max_age: timedelta) -> bool:
        """Reject missing, old, and implausibly future-dated observations."""
        return self.source_timestamp is not None and (
            -timedelta(minutes=5) <= now - self.source_timestamp < max_age
        )


class PackstationClient:
    """Use Home Assistant's existing HTTP session."""

    def __init__(self, session: ClientSession) -> None:
        """Initialize the client."""
        self._session = session

    async def _get(self, path: str, **params: str | int) -> dict[str, Any]:
        """Fetch JSON without following redirects to another service."""
        try:
            async with self._session.get(
                f"{API_BASE}/{path}",
                params=params,
                timeout=ClientTimeout(total=20),
                allow_redirects=False,
            ) as response:
                if response.status in (204, 404):
                    raise StationNotFound("No location data")
                if response.status == 429:
                    retry_after = response.headers.get("Retry-After", "900")
                    try:
                        seconds = int(retry_after)
                    except ValueError:
                        try:
                            until = parsedate_to_datetime(retry_after)
                            seconds = int((until - datetime.now(UTC)).total_seconds())
                        except (ValueError, TypeError, OverflowError):
                            seconds = 900
                    raise RateLimited(seconds)
                if response.status != 200:
                    raise PackstationError(f"DHL returned HTTP {response.status}")
                try:
                    data = await response.json(content_type=None)
                except (ValueError, UnicodeError) as err:
                    raise InvalidResponse("DHL did not return JSON") from err
        except (ClientError, TimeoutError) as err:
            raise PackstationError("Could not connect to DHL") from err
        if not isinstance(data, dict):
            raise InvalidResponse("DHL did not return an object")
        return data

    async def async_resolve(
        self, postal_code: str, station_number: str
    ) -> PackstationData:
        """Resolve the exact station and load its detailed response."""
        postal_code, station_number = normalize_location(postal_code, station_number)
        result = await self._get(
            "nearbySearch", address=f"{postal_code}:{station_number}", maxResults=1
        )
        locations = result.get("pfLocations")
        if not isinstance(locations, list):
            raise InvalidResponse("Missing locations list")
        if not locations:
            raise StationNotFound("No matching Packstation")
        location = locations[0]
        if not isinstance(location, dict):
            raise InvalidResponse("Invalid location")
        self._check_location(location, postal_code, station_number)
        primary_key = location.get("primaryKeyPF")
        if not isinstance(primary_key, str) or not re.fullmatch(
            r"[0-9]{1,2}-[0-9]{6,9}", primary_key
        ):
            raise InvalidResponse("Invalid location identifier")
        return await self.async_get_station(primary_key, postal_code, station_number)

    @staticmethod
    def _check_location(
        data: dict[str, Any], postal_code: str, station_number: str
    ) -> None:
        """Never silently accept a nearby or different kind of location."""
        if (
            data.get("locationType") != "PACKSTATION"
            or data.get("zipCode") != postal_code
            or data.get("primaryKeyZipRegion") != station_number
        ):
            raise StationNotFound(
                "The returned location is not the requested Packstation"
            )

    async def async_get_station(
        self, primary_key: str, postal_code: str, station_number: str
    ) -> PackstationData:
        """Read and validate one detail response."""
        if not re.fullmatch(r"[0-9]{1,2}-[0-9]{6,9}", primary_key):
            raise InvalidResponse("Invalid location identifier")
        data = await self._get(f"locationByPrimaryKeyPF/{primary_key}")
        self._check_location(data, postal_code, station_number)
        if data.get("primaryKeyPF") != primary_key:
            raise InvalidResponse("Location identifier changed")
        live = data.get("liveStatus")
        if live is None:
            live = {}
        if not isinstance(live, dict):
            raise InvalidResponse("Invalid live status")
        counts = {}
        for size, field in COMPARTMENTS.items():
            value = live.get(field)
            counts[size] = value if type(value) is int and value >= 0 else None
        timestamp = None
        raw_timestamp = live.get("sourceTimestamp")
        if isinstance(raw_timestamp, str):
            try:
                parsed = datetime.fromisoformat(raw_timestamp)
                timestamp = (
                    parsed.astimezone(UTC) if parsed.tzinfo is not None else None
                )
            except (ValueError, OverflowError):
                pass
        return PackstationData(
            primary_key=primary_key,
            postal_code=postal_code,
            station_number=station_number,
            city=data.get("city") if isinstance(data.get("city"), str) else "",
            address=" ".join(
                value
                for field in ("street", "houseNo")
                if isinstance(value := data.get(field), str) and value
            ),
            name=data.get("locationName")
            if isinstance(data.get("locationName"), str)
            else "",
            compartments=counts,
            source_timestamp=timestamp,
        )
