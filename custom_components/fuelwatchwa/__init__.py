from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import CONF_SURROUNDING, DEFAULT_SURROUNDING, DOMAIN, PLATFORMS
from .coordinator import FuelWatchCoordinator
from .services import async_setup_services


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.data.setdefault(DOMAIN, {})

    # Register services (only once)
    if not hass.services.has_service(DOMAIN, "import_historical_data"):
        await async_setup_services(hass)

    location = entry.data.get("location")
    fuel_types = entry.data.get("fuel_types", ["ulp_91"])
    surrounding = entry.options.get(
        CONF_SURROUNDING, entry.data.get(CONF_SURROUNDING, DEFAULT_SURROUNDING)
    )

    coordinators = {}
    for fuel_type in fuel_types:
        coordinator = FuelWatchCoordinator(hass, location, fuel_type, surrounding)
        await coordinator.async_config_entry_first_refresh()
        coordinators[fuel_type] = coordinator

    hass.data[DOMAIN][entry.entry_id] = {
        "coordinators": coordinators,
        "location": location,
    }
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    return True


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload the entry when options change."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok
