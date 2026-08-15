# FuelWatch WA

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)

Monitor Western Australian fuel prices from FuelWatch in Home Assistant.

## Features

- 🔄 Real-time fuel price monitoring
- 📊 Statistical summaries (min, max, avg, price spread)
- 🏪 Station count and cheapest station details
- 🎯 Top 3 cheapest stations tracking
- 📅 Today/tomorrow price forecasting
- 🔢 Multiple fuel types per location
- 🎨 Device grouping for clean organization
- 📈 State class support for long-term analytics

## Supported Fuel Types

- Unleaded Petrol (91 RON) - `ulp_91`
- Premium Unleaded (95 RON) - `premium_95`
- Diesel - `diesel`
- LPG (Autogas) - `lpg`
- Premium Unleaded (98 RON) - `premium_98`
- E85 Ethanol - `e85`
- Brand Diesel - `brand_diesel`

## Installation

### Via HACS (Recommended)

1. Open HACS
2. Go to Integrations
3. Click the three dots (⋮) in the top right
4. Select "Custom repositories"
5. Add `https://github.com/sniereffo/fuelwatchwa`
6. Category: Integration
7. Click "Install"
8. Restart Home Assistant

### Manual Installation

1. Copy `custom_components/fuelwatchwa` to your `config/custom_components/` directory
2. Restart Home Assistant

## Configuration

1. Go to **Settings** → **Devices & Services**
2. Click **+ Add Integration**
3. Search for "FuelWatch WA"
4. Enter configuration:
   - **Location**: Your suburb (e.g., "Perth", "Fremantle")
   - **Fuel Types**: Comma-separated (e.g., `diesel,premium_98`)
   - **Day**: `today` or `tomorrow`

## Sensors

For each fuel type, the integration creates **8 sensors** grouped under a logical device.

**Entity naming:** `sensor.{location}_{fuel_type}_{sensor_name}`

**Example device:** "Caversham Diesel" with all 8 sensors grouped together.

### Summary Statistics
- `minimum_price` - Lowest price (⬇️ AUD/L)
- `average_price` - Average price (📈 AUD/L)
- `maximum_price` - Highest price (⬆️ AUD/L)
- `price_spread` - Min/max difference (Δ AUD/L)
- `station_count` - Number of stations (⛽)

### Cheapest Station
- `cheapest_price` - Best price (💲 AUD/L)
- `cheapest_brand` - Station brand (⛽)
- `cheapest_address` - Station address (📍)

### Attributes
All sensors include:
- `location` - Configured location
- `fuel_type` - Fuel type key
- `day` - Today or tomorrow
- `top_3` - Top 3 cheapest stations
- `fetched_at` - Last update timestamp

## Example Dashboard

See `examples/dashboards/fuelwatchwa-dashboard.yaml` for a complete dashboard example with:
- Price summary cards
- Cheapest station details
- Price history graphs
- Top 3 stations list

## Data History

Use Home Assistant Recorder or InfluxDB to track price trends over time.

## Support

- [Documentation](https://github.com/sniereffo/fuelwatchwa)
- [Report Issues](https://github.com/sniereffo/fuelwatchwa/issues)

## Credits

Built on the [fuelwatcher](https://github.com/danielmichaels/fuelwatcher) Python library by Daniel Michaels.
Originally created by [Damian Rosair (@drosair)](https://github.com/drosair/fuelwatchwa).

Data sourced from [FuelWatch WA Government](https://www.fuelwatch.wa.gov.au/).
