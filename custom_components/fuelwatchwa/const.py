"""Constants for the FuelWatch WA integration."""
from __future__ import annotations

from datetime import timedelta

DOMAIN = "fuelwatchwa"
PLATFORMS = ["sensor"]

CONF_LOCATION = "location"
CONF_DAY = "day"
CONF_FUEL_TYPES = "fuel_types"
CONF_SURROUNDING = "surrounding"

DEFAULT_DAY = "today"
DEFAULT_SURROUNDING = True
DEFAULT_FUEL_TYPES = ["ulp_91"]
DEFAULT_SCAN_INTERVAL = timedelta(minutes=30)

DAY_OPTIONS = ["today", "tomorrow"]

FUEL_TYPE_OPTIONS = {
    "ulp_91": 1,
    "premium_95": 2,
    "diesel": 4,
    "lpg": 5,
    "premium_98": 6,
    "e85": 10,
    "brand_diesel": 11,
}

FUEL_TYPE_NAMES = {
    "ulp_91": "Unleaded Petrol (91 RON)",
    "premium_95": "Premium Unleaded (95 RON)",
    "diesel": "Diesel",
    "lpg": "LPG (Autogas)",
    "premium_98": "Premium Unleaded (98 RON)",
    "e85": "E85 Ethanol",
    "brand_diesel": "Brand Diesel",
}

COMMON_SUBURBS = [
    "Perth",
    "Fremantle",
    "Joondalup",
    "Rockingham",
    "Mandurah",
    "Armadale",
    "Midland",
    "Cannington",
    "Morley",
    "Booragoon",
    "Canning Vale",
    "Subiaco",
    "Victoria Park",
    "Northbridge",
    "West Perth",
    "East Perth",
    "South Perth",
    "Mount Lawley",
    "Maylands",
    "Bayswater",
    "Bassendean",
    "Belmont",
    "Caversham",
    "Ellenbrook",
    "Baldivis",
    "Butler",
    "Clarkson",
    "Alkimos",
    "Two Rocks",
    "Yanchep",
    "Wanneroo",
    "Bullsbrook",
    "Byford",
    "Serpentine",
    "Kwinana",
    "Casuarina",
    "Secret Harbour",
    "Gosnells",
    "Thornlie",
    "Maddington",
    "Forrestfield",
    "High Wycombe",
    "Kalamunda",
    "Mundaring",
]

ATTR_TOP_3 = "top_3"
ATTR_FETCHED_AT = "fetched_at"
ATTR_LOCATION = "location"
ATTR_FUEL_TYPE = "fuel_type"
ATTR_DAY = "day"
ATTR_STATION_COUNT = "station_count"
