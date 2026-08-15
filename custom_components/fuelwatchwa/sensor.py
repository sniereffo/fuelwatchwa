"""Sensor platform for FuelWatch WA."""
from __future__ import annotations

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.device_registry import DeviceInfo

from .const import DOMAIN


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
):
    data = hass.data[DOMAIN][entry.entry_id]
    coordinators = data["coordinators"]

    entities = []

    for fuel_type, coordinator in coordinators.items():
        entities.extend(
            [
                FuelNumericSensor(coordinator, fuel_type, "min_price"),
                FuelNumericSensor(coordinator, fuel_type, "avg_price"),
                FuelNumericSensor(coordinator, fuel_type, "max_price"),
                FuelNumericSensor(coordinator, fuel_type, "price_spread"),
                FuelNumericSensor(coordinator, fuel_type, "station_count"),
                FuelCheapestSensor(coordinator, fuel_type, "price"),
                FuelCheapestSensor(coordinator, fuel_type, "brand"),
                FuelCheapestSensor(coordinator, fuel_type, "address"),
            ]
        )

    async_add_entities(entities)
    
    # Set up analytics sensors
    from .analytics_sensor import async_setup_analytics_sensors
    await async_setup_analytics_sensors(hass, entry, async_add_entities, coordinators)


class BaseFuelSensor(SensorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator, fuel_type: str):
        self.coordinator = coordinator
        self.fuel_type = fuel_type
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{coordinator.location}_{fuel_type}")},
            name=f"{coordinator.location} {self._format_fuel_name(fuel_type)}",
            manufacturer="FuelWatch WA",
            model=f"{self._format_fuel_name(fuel_type)} Prices",
            entry_type="service",
        )

    def _format_fuel_name(self, fuel_type: str) -> str:
        """Convert fuel_type key to display name."""
        names = {
            "ulp_91": "ULP 91",
            "premium_95": "Premium 95",
            "diesel": "Diesel",
            "lpg": "LPG",
            "premium_98": "Premium 98",
            "e85": "E85",
            "brand_diesel": "Brand Diesel",
        }
        return names.get(fuel_type, fuel_type.replace("_", " ").title())

    async def async_update(self):
        await self.coordinator.async_request_refresh()

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success

    @property
    def extra_state_attributes(self):
        if not self.coordinator.data:
            return None

        attrs = {
            "location": self.coordinator.data.get("location"),
            "fuel_type": self.coordinator.data.get("fuel_type"),
            "top_3": self.coordinator.data.get("top_3"),
            "fetched_at": self.coordinator.data.get("fetched_at"),
        }
        
        # Add tomorrow's data if available (after 2:30pm)
        tomorrow = self.coordinator.data.get("tomorrow")
        if tomorrow:
            attrs["tomorrow"] = tomorrow
            attrs["price_change"] = self.coordinator.data.get("price_change")
        
        return attrs


class FuelNumericSensor(BaseFuelSensor):
    def __init__(self, coordinator, fuel_type: str, key: str):
        super().__init__(coordinator, fuel_type)
        self.key = key
        self._setup_metadata()

    def _setup_metadata(self):
        """Setup sensor metadata based on key."""
        metadata = {
            "min_price": {
                "name": "Minimum Price",
                "icon": "mdi:arrow-down-bold",
                "unit": "¢/L",
                "device_class": None,
                "state_class": SensorStateClass.MEASUREMENT,
            },
            "avg_price": {
                "name": "Average Price",
                "icon": "mdi:chart-line",
                "unit": "¢/L",
                "device_class": None,
                "state_class": SensorStateClass.MEASUREMENT,
            },
            "max_price": {
                "name": "Maximum Price",
                "icon": "mdi:arrow-up-bold",
                "unit": "¢/L",
                "device_class": None,
                "state_class": SensorStateClass.MEASUREMENT,
            },
            "price_spread": {
                "name": "Price Spread",
                "icon": "mdi:delta",
                "unit": "¢/L",
                "device_class": None,
                "state_class": SensorStateClass.MEASUREMENT,
            },
            "station_count": {
                "name": "Station Count",
                "icon": "mdi:gas-station",
                "unit": "stations",
                "device_class": None,
                "state_class": SensorStateClass.MEASUREMENT,
            },
        }
        meta = metadata.get(self.key, {})
        self._attr_name = meta.get("name", self.key.replace("_", " ").title())
        self._attr_icon = meta.get("icon")
        self._attr_native_unit_of_measurement = meta.get("unit")
        self._attr_device_class = meta.get("device_class")
        self._attr_state_class = meta.get("state_class")

    @property
    def unique_id(self):
        return f"fuelwatchwa_{self.coordinator.location}_{self.fuel_type}_{self.key}"

    @property
    def native_value(self):
        if self.coordinator.data:
            return self.coordinator.data.get(self.key)
        return None


class FuelCheapestSensor(BaseFuelSensor):
    def __init__(self, coordinator, fuel_type: str, field: str):
        super().__init__(coordinator, fuel_type)
        self.field = field
        self._setup_metadata()

    def _setup_metadata(self):
        """Setup sensor metadata based on field."""
        metadata = {
            "price": {
                "name": "Cheapest Price",
                "icon": "mdi:currency-usd",
                "unit": "¢/L",
                "device_class": None,
            },
            "brand": {
                "name": "Cheapest Brand",
                "icon": "mdi:gas-station",
                "unit": None,
                "device_class": None,
            },
            "address": {
                "name": "Cheapest Address",
                "icon": "mdi:map-marker",
                "unit": None,
                "device_class": None,
            },
        }
        meta = metadata.get(self.field, {})
        self._attr_name = meta.get("name", self.field.replace("_", " ").title())
        self._attr_icon = meta.get("icon")
        self._attr_native_unit_of_measurement = meta.get("unit")
        self._attr_device_class = meta.get("device_class")
        if self.field == "price":
            self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def unique_id(self):
        return f"fuelwatchwa_{self.coordinator.location}_{self.fuel_type}_cheapest_{self.field}"

    @property
    def native_value(self):
        if self.coordinator.data:
            cheapest = self.coordinator.data.get("cheapest", {})
            return cheapest.get(self.field)
        return None
