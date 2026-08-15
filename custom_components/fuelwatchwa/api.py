"""API client helpers for the FuelWatch WA integration."""
from __future__ import annotations

import logging
from datetime import UTC, datetime
from statistics import mean

from homeassistant.core import HomeAssistant
from fuelwatcher import FuelWatch

from .const import DEFAULT_SURROUNDING, FUEL_TYPE_OPTIONS

_LOGGER = logging.getLogger(__name__)


class FuelWatchAPI:
    """Wrapper around fuelwatcher that returns normalized summary data."""

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass

    def _fetch_sync(self, location: str, fuel_type: str, day: str, surrounding: bool):
        """Run the blocking FuelWatch request synchronously."""
        product_id = FUEL_TYPE_OPTIONS[fuel_type]
        client = FuelWatch()
        client.query(
            suburb=location, product=product_id, day=day, surrounding=surrounding
        )
        return client.xml

    async def fetch(
        self,
        location: str,
        fuel_type: str,
        surrounding: bool = DEFAULT_SURROUNDING,
    ) -> dict | None:
        """Fetch FuelWatch data for both today and tomorrow, return summary statistics."""
        # Fetch both today and tomorrow data
        try:
            today_data = await self.hass.async_add_executor_job(
                self._fetch_sync, location, fuel_type, "today", surrounding
            )
            tomorrow_data = await self.hass.async_add_executor_job(
                self._fetch_sync, location, fuel_type, "tomorrow", surrounding
            )
        except Exception as err:
            _LOGGER.warning(
                "FuelWatch query failed for %s / %s: %s", location, fuel_type, err
            )
            return None

        if not today_data:
            return None

        prices = []
        for row in today_data:
            try:
                if row.get("price") is not None:
                    prices.append(float(row["price"]))
            except (TypeError, ValueError):
                continue

        if not prices:
            return None

        min_price = min(prices)
        max_price = max(prices)
        avg_price = round(mean(prices), 2)
        price_spread = round(max_price - min_price, 2)
        cheapest = today_data[0]

        top_3 = []
        for row in today_data[:3]:
            try:
                price = float(row.get("price")) if row.get("price") is not None else None
            except (TypeError, ValueError):
                price = None

            top_3.append(
                {
                    "brand": row.get("brand"),
                    "price": price,
                    "address": row.get("address"),
                    "location": row.get("location"),
                }
            )

        try:
            cheapest_price = (
                float(cheapest.get("price")) if cheapest.get("price") is not None else None
            )
        except (TypeError, ValueError):
            cheapest_price = None

        # Process tomorrow's data if available
        tomorrow_summary = None
        price_change = None
        if tomorrow_data:
            tomorrow_prices = []
            for row in tomorrow_data:
                try:
                    if row.get("price") is not None:
                        tomorrow_prices.append(float(row["price"]))
                except (TypeError, ValueError):
                    continue

            if tomorrow_prices:
                tomorrow_min = min(tomorrow_prices)
                tomorrow_max = max(tomorrow_prices)
                tomorrow_avg = round(mean(tomorrow_prices), 2)
                tomorrow_cheapest = tomorrow_data[0]

                try:
                    tomorrow_cheapest_price = (
                        float(tomorrow_cheapest.get("price"))
                        if tomorrow_cheapest.get("price") is not None
                        else None
                    )
                except (TypeError, ValueError):
                    tomorrow_cheapest_price = None

                tomorrow_summary = {
                    "min_price": tomorrow_min,
                    "max_price": tomorrow_max,
                    "avg_price": tomorrow_avg,
                    "price_spread": round(tomorrow_max - tomorrow_min, 2),
                    "cheapest_price": tomorrow_cheapest_price,
                    "cheapest_brand": tomorrow_cheapest.get("brand"),
                    "cheapest_address": tomorrow_cheapest.get("address"),
                    "station_count": len(tomorrow_data),
                }

                # Calculate price change
                if cheapest_price is not None and tomorrow_cheapest_price is not None:
                    price_change = round(tomorrow_cheapest_price - cheapest_price, 2)

        return {
            "location": location,
            "fuel_type": fuel_type,
            "fetched_at": datetime.now(UTC).isoformat(),
            # Today's prices (primary)
            "station_count": len(today_data),
            "min_price": min_price,
            "max_price": max_price,
            "avg_price": avg_price,
            "price_spread": price_spread,
            "cheapest": {
                "price": cheapest_price,
                "brand": cheapest.get("brand"),
                "address": cheapest.get("address"),
                "location": cheapest.get("location"),
            },
            "top_3": top_3,
            "stations": today_data,
            # Tomorrow's prices
            "tomorrow": tomorrow_summary,
            "price_change": price_change,
        }
