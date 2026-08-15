# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0-alpha1] - 2026-03-26

### Added
- Initial HACS-ready release
- Config flow for UI-based setup
- Multi-fuel type support (7 fuel types)
- 8 sensors per fuel type (min/max/avg/spread/count + cheapest details)
- Async-safe API using Home Assistant executor jobs
- Example dashboard YAML
- Comprehensive documentation

### Fixed
- Blocking call detection in event loop
- Graceful handling of empty/malformed FuelWatch responses
- Correct fuel type product mappings per FuelWatch RSS specification

### Technical
- Async-first architecture with DataUpdateCoordinator
- 30-minute polling interval
- Stateless API layer
- Proper error handling and logging

## [0.2.1] - 2026-03-26

### Added
- Device grouping: each fuel type creates a logical device
- Enhanced sensor metadata with contextual icons
- Proper units (AUD/L, stations) for all sensors
- State class support for long-term statistics
- Device class MONETARY for price sensors
- Better sensor naming (e.g., "Minimum Price" vs "min_price")
- Availability tracking based on coordinator success
- Updated dashboard examples with new entity naming
- Auto-entities example in dashboard YAML

### Changed
- Entity IDs now include location: `sensor.{location}_{fuel_type}_{sensor_name}`
- Sensor names are more user-friendly
- Dashboard examples use 'perth' as location placeholder

### Improved
- Home Assistant Recorder integration for long-term analytics
- Better organization in UI with device grouping
- Historical graphing support with state_class
- Documentation with device grouping examples

## [0.3.0] - 2026-03-26

### Added
- Automatic fetching of both today's and tomorrow's prices
- Tomorrow's price summary in sensor attributes (available after 2:30pm)
- Price change calculation (tomorrow vs today)
- Suburb dropdown selector with 40+ common WA suburbs
- Fuel type multi-select dropdown with friendly names
- Custom suburb entry support

### Changed
- Removed 'day' selector from config flow (now fetches both automatically)
- Simplified configuration flow with better UX
- Tomorrow data gracefully handled when not yet available

### Breaking Changes
- Config flow changed - existing integrations need reconfiguration
- 'day' field removed from config (migration required for existing setups)

## [0.4.0] - 2026-03-26

### Added - Phase 3 Analytics
- **7-Day Average Price** sensor with rolling mean calculation
- **30-Day Average Price** sensor for monthly trend tracking
- **Price Trend** sensor (increasing/decreasing/stable indicator)
- **Price Volatility** sensor with stability classification
- **Weekly Change %** sensor for percentage price changes
- Analytics module using Home Assistant statistics API
- Hourly automatic analytics updates
- All analytics sensors grouped under same device

### Technical
- New `analytics.py` module for statistical calculations
- New `analytics_sensor.py` with 5 sensor classes
- Uses HA Recorder's `statistics_during_period` API
- Trend calculation via period halves comparison
- Volatility measured as standard deviation

### Requirements
- Requires at least 2 days of historical Recorder data
- Analytics sensors update every hour
- Works with existing recorder configuration

## [0.5.0] - 2026-03-26

### Added - Phase 4 Historical Data Import
- **Historical data download script** (`scripts/download_historical.py`)
- **HA Service**: `fuelwatchwa.import_historical_data` for CSV import
- **Statistics backfill** - Direct import into Recorder database
- **Complete documentation** in `scripts/README.md`

### Features
- Download historical FuelWatch data from any date range
- CLI tool with progress logging
- Import CSV files via HA service
- Automatic statistics metadata creation
- Supports bulk historical backfill (years of data)

### Technical
- `services.py` - Service implementation
- `services.yaml` - Service definition
- CSV parser with validation
- Direct Recorder database integration
- Handles duplicate timestamps gracefully

### Usage
1. Download: `python scripts/download_historical.py`
2. Import: Service call via Developer Tools
3. Analytics sensors automatically use imported data

### Bug Fixes
- Fixed analytics sensor Recorder state check

## [0.6.0] - 2026-08-15

### Fixed
- **Custom suburbs failing with "No FuelWatch data returned"** — upgraded
  `fuelwatcher` 0.2.2 → 1.0.0. The old version's hardcoded suburb whitelist
  predates newer suburbs (e.g. Casuarina), so queries for them raised
  `Invalid Suburb` before FuelWatch was ever contacted.
- API errors are now logged with the real cause instead of being silently
  swallowed and reported as "no data returned".
- Added missing `async_unload_entry` so config entries can be unloaded,
  reloaded, and removed cleanly.
- Replaced deprecated `get_xml` with the `xml` property (removes a
  DeprecationWarning in the HA log).

### Added
- **"Include surrounding suburbs" option** (per instance, on by default —
  matching previous behaviour). Turn it off to only show stations physically
  in the selected suburb, e.g. to pin a single station like Costco Casuarina.
- Options flow: the surrounding-suburbs setting can be changed on existing
  entries via Settings → Devices & Services → Configure.
- Casuarina added to the common suburbs dropdown.

## [0.6.1] - 2026-08-15

### Added
- Brand images (icon and logo derived from the FuelWatch logo, text removed
  from the icon) shipped inside the integration at
  `custom_components/fuelwatchwa/brand/`. Home Assistant 2026.3+ serves these
  locally, so the integration shows its own icon in Settings → Devices &
  Services without a home-assistant/brands entry.

## [Unreleased]

### Planned
- CSV import/backfill utility (Phase 4)
- Location intelligence and GPS integration (Phase 5)
- CarPlay/mobile experience (Phase 6)
- Region and group support (Phase 7)

[0.2.0-alpha1]: https://github.com/drosair/fuelwatchwa/releases/tag/v0.2.0-alpha1
