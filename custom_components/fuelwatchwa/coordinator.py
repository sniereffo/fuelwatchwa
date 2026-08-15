"""Coordinator for the FuelWatch WA integration."""
from __future__ import annotations

import logging

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import FuelWatchAPI
from .const import DEFAULT_SCAN_INTERVAL, DEFAULT_SURROUNDING, DOMAIN

_LOGGER = logging.getLogger(__name__)


class FuelWatchCoordinator(DataUpdateCoordinator):
    """Coordinate FuelWatch API calls for one location/fuel/day combination."""

    def __init__(
        self,
        hass,
        location: str,
        fuel_type: str,
        surrounding: bool = DEFAULT_SURROUNDING,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{location}_{fuel_type}",
            update_interval=DEFAULT_SCAN_INTERVAL,
        )
        self.api = FuelWatchAPI(hass)
        self.location = location
        self.fuel_type = fuel_type
        self.surrounding = surrounding

    async def _async_update_data(self):
        data = await self.api.fetch(self.location, self.fuel_type, self.surrounding)
        if data is None:
            raise UpdateFailed(
                f"No FuelWatch data returned for {self.location} / {self.fuel_type}"
            )
        return data
