"""API client helpers for the FuelWatch WA integration."""
from __future__ import annotations

import logging
from datetime import UTC, datetime
from statistics import mean
from xml.etree import ElementTree

import aiohttp

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DEFAULT_SURROUNDING, FUEL_TYPE_OPTIONS

_LOGGER = logging.getLogger(__name__)

RSS_URL = "https://www.fuelwatch.wa.gov.au/fuelwatch/fuelWatchRSS"
# FuelWatch rejects default python HTTP client user agents
USER_AGENT = "Mozilla/5.0 (compatible; HomeAssistant-FuelWatchWA)"
REQUEST_TIMEOUT = aiohttp.ClientTimeout(total=30)


class FuelWatchAPI:
    """Client that queries the FuelWatch RSS feed and returns normalized summary data.

    Queries the feed directly rather than via the fuelwatcher library: the
    library validates suburbs against a hardcoded list that goes stale as new
    suburbs gain stations (e.g. Casuarina, Tapping), while FuelWatch itself
    accepts any suburb and simply returns an empty feed for unknown ones.
    """

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass

    async def _fetch_day(
        self, location: str, fuel_type: str, day: str, surrounding: bool
    ) -> list[dict[str, str | None]]:
        """Fetch and parse one day's prices, cheapest first."""
        params = {
            "Product": FUEL_TYPE_OPTIONS[fuel_type],
            "Suburb": location,
            "Surrounding": "yes" if surrounding else "no",
            "Day": day,
        }
        session = async_get_clientsession(self.hass)
        async with session.get(
            RSS_URL,
            params=params,
            headers={"User-Agent": USER_AGENT},
            timeout=REQUEST_TIMEOUT,
        ) as response:
            response.raise_for_status()
            raw = await response.read()

        dom = ElementTree.fromstring(raw)
        rows = [
            {child.tag: child.text for child in item}
            for item in dom.findall("channel/item")
        ]

        def price_key(row: dict) -> float:
            try:
                return float(row.get("price"))
            except (TypeError, ValueError):
                return float("inf")

        rows.sort(key=price_key)
        return rows

    async def fetch(
        self,
        location: str,
        fuel_type: str,
        surrounding: bool = DEFAULT_SURROUNDING,
    ) -> dict | None:
        """Fetch FuelWatch data for both today and tomorrow, return summary statistics."""
        # Fetch both today and tomorrow data
        try:
            today_data = await self._fetch_day(location, fuel_type, "today", surrounding)
            tomorrow_data = await self._fetch_day(
                location, fuel_type, "tomorrow", surrounding
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
