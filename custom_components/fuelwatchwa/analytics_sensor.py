"""Analytics sensors for FuelWatch WA integration."""
from __future__ import annotations

from datetime import timedelta
import logging

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.config_entries import ConfigEntry

from .analytics import get_price_statistics
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

ANALYTICS_UPDATE_INTERVAL = timedelta(hours=1)


async def async_setup_analytics_sensors(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
    coordinators: dict,
):
    """Set up analytics sensors for each fuel type."""
    entities = []
    
    for fuel_type, coordinator in coordinators.items():
        # Get the minimum price entity ID (we'll use this for analytics)
        location = coordinator.location.lower().replace(" ", "_")
        base_entity_id = f"sensor.{location}_{fuel_type}_minimum_price"
        
        entities.extend([
            FuelAnalyticsSensor(
                hass, coordinator, fuel_type, base_entity_id, "7day_average", 7
            ),
            FuelAnalyticsSensor(
                hass, coordinator, fuel_type, base_entity_id, "30day_average", 30
            ),
            FuelTrendSensor(
                hass, coordinator, fuel_type, base_entity_id, "trend", 7
            ),
            FuelVolatilitySensor(
                hass, coordinator, fuel_type, base_entity_id, "volatility", 7
            ),
            FuelChangePercentSensor(
                hass, coordinator, fuel_type, base_entity_id, "weekly_change", 7
            ),
        ])
    
    async_add_entities(entities)


class BaseAnalyticsSensor(SensorEntity):
    """Base class for analytics sensors."""
    
    _attr_has_entity_name = True
    
    def __init__(
        self,
        hass: HomeAssistant,
        coordinator,
        fuel_type: str,
        source_entity_id: str,
        sensor_type: str,
        days: int,
    ):
        """Initialize the analytics sensor."""
        self.hass = hass
        self.coordinator = coordinator
        self.fuel_type = fuel_type
        self.source_entity_id = source_entity_id
        self.sensor_type = sensor_type
        self.days = days
        self._attr_native_value = None
        self._analytics_data = None
        
        # Set up device info to group with main sensors
        from homeassistant.helpers.device_registry import DeviceInfo
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
    
    async def async_added_to_hass(self):
        """When entity is added to hass."""
        await super().async_added_to_hass()
        
        # Update immediately
        await self._async_update_analytics()
        
        # Schedule regular updates
        self.async_on_remove(
            async_track_time_interval(
                self.hass,
                self._async_update_analytics,
                ANALYTICS_UPDATE_INTERVAL,
            )
        )
    
    @callback
    async def _async_update_analytics(self, now=None):
        """Update analytics data."""
        try:
            self._analytics_data = await get_price_statistics(
                self.hass,
                self.source_entity_id,
                self.days,
            )
            self._update_from_analytics()
            self.async_write_ha_state()
        except Exception as err:
            _LOGGER.error(
                "Error updating analytics for %s: %s",
                self.entity_id,
                err,
            )
    
    def _update_from_analytics(self):
        """Update sensor value from analytics data. Override in subclass."""
        pass
    
    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self._analytics_data is not None


class FuelAnalyticsSensor(BaseAnalyticsSensor):
    """Sensor for average price over a period."""
    
    def __init__(self, hass, coordinator, fuel_type, source_entity_id, sensor_type, days):
        """Initialize the sensor."""
        super().__init__(hass, coordinator, fuel_type, source_entity_id, sensor_type, days)
        
        if days == 7:
            self._attr_name = "7-Day Average Price"
            self._attr_icon = "mdi:chart-line-variant"
        else:
            self._attr_name = "30-Day Average Price"
            self._attr_icon = "mdi:chart-bell-curve"
        
        self._attr_native_unit_of_measurement = "¢/L"
        self._attr_state_class = SensorStateClass.MEASUREMENT
    
    @property
    def unique_id(self):
        """Return unique ID."""
        return f"fuelwatchwa_{self.coordinator.location}_{self.fuel_type}_{self.sensor_type}"
    
    def _update_from_analytics(self):
        """Update sensor value from analytics data."""
        if self._analytics_data:
            self._attr_native_value = self._analytics_data.get("average")
    
    @property
    def extra_state_attributes(self):
        """Return additional attributes."""
        if not self._analytics_data:
            return None
        
        return {
            "minimum": self._analytics_data.get("minimum"),
            "maximum": self._analytics_data.get("maximum"),
            "data_points": self._analytics_data.get("data_points"),
            "period_days": self.days,
        }


class FuelTrendSensor(BaseAnalyticsSensor):
    """Sensor for price trend direction."""
    
    def __init__(self, hass, coordinator, fuel_type, source_entity_id, sensor_type, days):
        """Initialize the sensor."""
        super().__init__(hass, coordinator, fuel_type, source_entity_id, sensor_type, days)
        self._attr_name = "Price Trend"
        self._attr_icon = "mdi:trending-up"
    
    @property
    def unique_id(self):
        """Return unique ID."""
        return f"fuelwatchwa_{self.coordinator.location}_{self.fuel_type}_trend"
    
    def _update_from_analytics(self):
        """Update sensor value from analytics data."""
        if self._analytics_data:
            self._attr_native_value = self._analytics_data.get("trend", "unknown")
            
            # Update icon based on trend
            trend = self._analytics_data.get("trend")
            if trend == "increasing":
                self._attr_icon = "mdi:trending-up"
            elif trend == "decreasing":
                self._attr_icon = "mdi:trending-down"
            else:
                self._attr_icon = "mdi:trending-neutral"
    
    @property
    def extra_state_attributes(self):
        """Return additional attributes."""
        if not self._analytics_data:
            return None
        
        return {
            "price_change": self._analytics_data.get("price_change"),
            "percent_change": self._analytics_data.get("percent_change"),
            "period_days": self.days,
        }


class FuelVolatilitySensor(BaseAnalyticsSensor):
    """Sensor for price volatility (standard deviation)."""
    
    def __init__(self, hass, coordinator, fuel_type, source_entity_id, sensor_type, days):
        """Initialize the sensor."""
        super().__init__(hass, coordinator, fuel_type, source_entity_id, sensor_type, days)
        self._attr_name = "Price Volatility"
        self._attr_icon = "mdi:chart-scatter-plot"
        self._attr_native_unit_of_measurement = "¢/L"
        self._attr_state_class = SensorStateClass.MEASUREMENT
    
    @property
    def unique_id(self):
        """Return unique ID."""
        return f"fuelwatchwa_{self.coordinator.location}_{self.fuel_type}_volatility"
    
    def _update_from_analytics(self):
        """Update sensor value from analytics data."""
        if self._analytics_data:
            self._attr_native_value = self._analytics_data.get("volatility")
    
    @property
    def extra_state_attributes(self):
        """Return additional attributes."""
        if not self._analytics_data:
            return None
        
        volatility = self._analytics_data.get("volatility", 0)
        
        # Classify volatility
        if volatility < 2.0:
            stability = "very_stable"
        elif volatility < 5.0:
            stability = "stable"
        elif volatility < 10.0:
            stability = "moderate"
        else:
            stability = "volatile"
        
        return {
            "stability": stability,
            "period_days": self.days,
            "data_points": self._analytics_data.get("data_points"),
        }


class FuelChangePercentSensor(BaseAnalyticsSensor):
    """Sensor for percentage price change over period."""
    
    def __init__(self, hass, coordinator, fuel_type, source_entity_id, sensor_type, days):
        """Initialize the sensor."""
        super().__init__(hass, coordinator, fuel_type, source_entity_id, sensor_type, days)
        self._attr_name = "Weekly Change %"
        self._attr_icon = "mdi:percent"
        self._attr_native_unit_of_measurement = "%"
        self._attr_state_class = SensorStateClass.MEASUREMENT
    
    @property
    def unique_id(self):
        """Return unique ID."""
        return f"fuelwatchwa_{self.coordinator.location}_{self.fuel_type}_weekly_change"
    
    def _update_from_analytics(self):
        """Update sensor value from analytics data."""
        if self._analytics_data:
            self._attr_native_value = self._analytics_data.get("percent_change")
    
    @property
    def extra_state_attributes(self):
        """Return additional attributes."""
        if not self._analytics_data:
            return None
        
        return {
            "price_change": self._analytics_data.get("price_change"),
            "trend": self._analytics_data.get("trend"),
            "period_days": self.days,
        }
