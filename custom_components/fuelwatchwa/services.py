"""Services for FuelWatch WA integration."""
from __future__ import annotations

import csv
import logging
from datetime import datetime
from pathlib import Path

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.components.recorder import get_instance
from homeassistant.components.recorder.statistics import (
    async_import_statistics,
    get_metadata,
    async_add_external_statistics,
)
from homeassistant.util import dt as dt_util
import voluptuous as vol

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

SERVICE_IMPORT_HISTORICAL = "import_historical_data"

IMPORT_SCHEMA = vol.Schema(
    {
        vol.Required("csv_path"): str,
        vol.Required("entity_id"): str,
        vol.Optional("source", default="FuelWatch Historical"): str,
    }
)


async def async_setup_services(hass: HomeAssistant):
    """Set up services for FuelWatch WA."""

    async def handle_import_historical(call: ServiceCall):
        """Handle the import historical data service call."""
        csv_path = call.data["csv_path"]
        entity_id = call.data["entity_id"]
        source = call.data.get("source", "FuelWatch Historical")

        _LOGGER.info("Starting historical data import from %s", csv_path)

        try:
            await _import_csv_to_statistics(hass, csv_path, entity_id, source)
            _LOGGER.info("Successfully imported historical data for %s", entity_id)
        except Exception as err:
            _LOGGER.error("Error importing historical data: %s", err)
            raise

    hass.services.async_register(
        DOMAIN,
        SERVICE_IMPORT_HISTORICAL,
        handle_import_historical,
        schema=IMPORT_SCHEMA,
    )


async def _import_csv_to_statistics(
    hass: HomeAssistant,
    csv_path: str,
    entity_id: str,
    source: str,
):
    """Import CSV data into Home Assistant statistics."""
    
    # Read CSV file
    csv_file = Path(csv_path)
    if not csv_file.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    records = []
    with csv_file.open('r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            records.append(row)

    if not records:
        _LOGGER.warning("No records found in CSV file")
        return

    _LOGGER.info("Read %d records from CSV", len(records))

    # Get or create statistics metadata
    metadata_id = await _get_or_create_metadata(hass, entity_id, source)

    # Convert CSV records to statistics format
    statistics = []
    for record in records:
        try:
            # Parse date - handle both date-only and datetime formats
            date_str = record.get("date")
            if not date_str:
                continue
                
            # Try parsing as date first, then as datetime
            try:
                dt = datetime.strptime(date_str, "%Y-%m-%d")
            except ValueError:
                dt = datetime.fromisoformat(date_str)
            
            # Make timezone-aware (use UTC)
            if dt.tzinfo is None:
                dt = dt.replace(hour=12, minute=0, second=0, tzinfo=dt_util.UTC)

            # Create statistics entry for each price metric
            # We'll import the minimum price as the primary statistic
            min_price = float(record.get("min_price", 0))
            avg_price = float(record.get("avg_price", 0))
            max_price = float(record.get("max_price", 0))

            statistics.append({
                "start": dt,
                "mean": min_price,  # Using min_price as the primary metric
                "min": min_price,
                "max": max_price,
            })

        except (ValueError, TypeError) as err:
            _LOGGER.warning("Skipping invalid record: %s - Error: %s", record, err)
            continue

    if not statistics:
        _LOGGER.warning("No valid statistics to import")
        return

    _LOGGER.info("Prepared %d statistics entries for import", len(statistics))

    # Import statistics into recorder
    await hass.async_add_executor_job(
        _import_statistics_sync,
        hass,
        metadata_id,
        statistics,
    )

    _LOGGER.info("Successfully imported %d statistics entries", len(statistics))


def _import_statistics_sync(hass: HomeAssistant, metadata_id: int, statistics: list):
    """Import statistics synchronously (runs in executor)."""
    from homeassistant.components.recorder.statistics import (
        get_instance as get_recorder_instance,
    )
    
    # Use the recorder's statistics import
    instance = get_instance(hass)
    if not instance:
        raise RuntimeError("Recorder not available")
    
    # Import using the statistics table
    with instance.get_session() as session:
        from homeassistant.components.recorder.models import (
            Statistics,
            StatisticsMeta,
        )
        
        # Verify metadata exists
        metadata = session.query(StatisticsMeta).filter_by(id=metadata_id).first()
        if not metadata:
            raise ValueError(f"Metadata ID {metadata_id} not found")
        
        # Insert statistics
        for stat in statistics:
            # Check if statistics already exists for this timestamp
            existing = (
                session.query(Statistics)
                .filter_by(metadata_id=metadata_id, start=stat["start"])
                .first()
            )
            
            if existing:
                # Update existing
                existing.mean = stat["mean"]
                existing.min = stat["min"]
                existing.max = stat["max"]
            else:
                # Create new
                new_stat = Statistics(
                    metadata_id=metadata_id,
                    start=stat["start"],
                    mean=stat["mean"],
                    min=stat["min"],
                    max=stat["max"],
                )
                session.add(new_stat)
        
        session.commit()


async def _get_or_create_metadata(
    hass: HomeAssistant,
    entity_id: str,
    source: str,
) -> int:
    """Get or create statistics metadata for entity."""
    
    # Check if metadata exists
    metadata = await get_instance(hass).async_add_executor_job(
        get_metadata,
        hass,
        statistic_ids=[entity_id],
    )
    
    if entity_id in metadata:
        return metadata[entity_id][0]["statistic_id"]
    
    # Create new metadata
    metadata_entry = {
        "has_mean": True,
        "has_sum": False,
        "name": entity_id.split(".")[-1].replace("_", " ").title(),
        "source": source,
        "statistic_id": entity_id,
        "unit_of_measurement": "¢/L",
    }
    
    await get_instance(hass).async_add_executor_job(
        _create_metadata_sync,
        hass,
        metadata_entry,
    )
    
    # Fetch the newly created metadata ID
    metadata = await get_instance(hass).async_add_executor_job(
        get_metadata,
        hass,
        statistic_ids=[entity_id],
    )
    
    if entity_id in metadata:
        return metadata[entity_id][0]["id"]
    
    raise RuntimeError(f"Failed to create metadata for {entity_id}")


def _create_metadata_sync(hass: HomeAssistant, metadata: dict):
    """Create statistics metadata synchronously."""
    from homeassistant.components.recorder.models import StatisticsMeta
    
    instance = get_instance(hass)
    with instance.get_session() as session:
        meta = StatisticsMeta(
            statistic_id=metadata["statistic_id"],
            source=metadata["source"],
            unit_of_measurement=metadata["unit_of_measurement"],
            has_mean=metadata["has_mean"],
            has_sum=metadata["has_sum"],
            name=metadata.get("name"),
        )
        session.add(meta)
        session.commit()
