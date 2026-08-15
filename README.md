# FuelWatch WA - Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)

A Home Assistant custom integration for fetching fuel prices in Western Australia from [FuelWatch](https://www.fuelwatch.wa.gov.au/).

## Features

- 🔄 Automatic polling of FuelWatch RSS feeds
- 📊 Statistical summaries (min, max, avg, price spread)
- 🏪 Station count and cheapest station details
- 🎯 Top 3 cheapest stations tracking
- 📅 Today/tomorrow price forecasting
- 🔢 Multiple fuel types per location
- 🎨 Device grouping for clean organization
- 📈 State class support for long-term analytics
- 🎯 Contextual icons and proper units

## Supported Fuel Types

The integration supports all official FuelWatch fuel types:

- `ulp_91` - Unleaded Petrol (91 RON)
- `premium_95` - Premium Unleaded (95 RON)
- `diesel` - Diesel
- `lpg` - LPG (Autogas)
- `premium_98` - Premium Unleaded (98 RON)
- `e85` - E85 Ethanol
- `brand_diesel` - Brand Diesel

## Installation

### HACS (Recommended)

This integration is distributed as a HACS custom repository:

1. Open HACS in Home Assistant
2. Click the three dots (⋮) in the top right and select **Custom repositories**
3. Add `https://github.com/sniereffo/fuelwatchwa` with type **Integration**
4. Search for "FuelWatch WA" in HACS and install it
5. Restart Home Assistant
6. Go to **Settings** → **Devices & Services** → **Add Integration**
7. Search for "FuelWatch WA" and follow the setup wizard

Updates are published as GitHub releases and will appear in Home Assistant's update list automatically.

### Manual Installation

1. Download or clone this repository
2. Copy the `custom_components/fuelwatchwa` folder to your Home Assistant `config/custom_components/` directory
3. Restart Home Assistant
4. Go to **Settings** → **Devices & Services** → **Add Integration**
5. Search for "FuelWatch WA" and follow the setup wizard

## Configuration

During setup, you'll be asked to provide:

- **Suburb**: Select from dropdown or enter custom location (e.g., "Perth", "Fremantle")
- **Fuel Types**: Multi-select dropdown with friendly names (e.g., Diesel, Premium 98)
- **Include surrounding suburbs**: On by default, prices cover stations in surrounding suburbs too. Turn off to only include stations physically in the selected suburb (useful to pin a single station, e.g. Costco Casuarina). Can be changed later on existing entries via **Configure**.

The integration automatically fetches **both today's and tomorrow's prices** in each update.

**Note**: Today's prices are available 24/7. Tomorrow's prices are available after 2:30pm daily.

## Sensors Created

For each configured fuel type, the integration creates **13 sensors** (8 current data + 5 analytics) grouped under a logical device.

### Entity Naming Pattern

```
sensor.{location}_{fuel_type}_{sensor_name}
```

**Examples:**
- `sensor.perth_diesel_minimum_price`
- `sensor.caversham_premium_98_cheapest_brand`
- `sensor.south_perth_ulp_91_station_count`

### Device Grouping

All sensors for a fuel type are grouped under a device named:
```
{Location} {Fuel Type}
```

**Example:** "Caversham Diesel" device contains all 13 diesel sensors.

### Summary Statistics
- `minimum_price` - Lowest price in area (icon: ⬇️, unit: ¢/L)
- `average_price` - Average price (icon: 📈, unit: ¢/L)
- `maximum_price` - Highest price (icon: ⬆️, unit: ¢/L)
- `price_spread` - Difference between min and max (icon: Δ, unit: ¢/L)
- `station_count` - Number of stations reporting (icon: ⛽, unit: stations)

### Cheapest Station
- `cheapest_price` - Cheapest price (icon: 💲, unit: ¢/L)
- `cheapest_brand` - Brand name (icon: ⛽)
- `cheapest_address` - Station address (icon: 📍)

### Analytics Sensors

Each fuel type also includes **5 analytics sensors** that provide historical trend analysis:

- **7-Day Average Price** - Rolling 7-day mean price (icon: 📊, unit: ¢/L)
  - Attributes: `minimum`, `maximum`, `data_points`, `period_days`
- **30-Day Average Price** - Monthly trend tracking (icon: 📈, unit: ¢/L)
  - Attributes: `minimum`, `maximum`, `data_points`, `period_days`
- **Price Trend** - Direction indicator: `increasing`, `decreasing`, or `stable` (icon: 📈/📉/➡️)
  - Attributes: `price_change`, `percent_change`, `period_days`
- **Price Volatility** - Standard deviation measure (icon: 📊, unit: ¢/L)
  - Attributes: `stability` (very_stable/stable/moderate/volatile), `data_points`
- **Weekly Change %** - Percentage price change over 7 days (icon: %, unit: %)
  - Attributes: `price_change`, `trend`, `period_days`

**Note**: Analytics sensors require historical data from Home Assistant Recorder. They update hourly and need at least 2 days of data to function.

### Sensor Attributes

All sensors include these attributes:
- `location` - Configured location
- `fuel_type` - Fuel type key
- `top_3` - List of 3 cheapest stations for today
- `fetched_at` - ISO timestamp of last fetch
- `tomorrow` - Complete price summary for tomorrow (available after 2:30pm):
  - `min_price`, `max_price`, `avg_price`, `price_spread`
  - `cheapest_price`, `cheapest_brand`, `cheapest_address`
  - `station_count`
- `price_change` - Price difference (tomorrow vs today cheapest price)

## Historical Data

### CSV Import & Backfill

Import years of historical FuelWatch data to power your analytics sensors.

**1. Download Historical Data**

```bash
python scripts/download_historical.py \
  --location Perth \
  --fuel-type diesel \
  --start-date 2023-01-01 \
  --end-date 2024-12-31 \
  --output /config/historical_data/perth_diesel.csv
```

**2. Import into Home Assistant**

Use the Developer Tools → Services:

```yaml
service: fuelwatchwa.import_historical_data
data:
  csv_path: /config/historical_data/perth_diesel.csv
  entity_id: sensor.perth_diesel_minimum_price
  source: FuelWatch Historical
```

**Benefits:**
- Import data from 2001 onwards (if available)
- Powers analytics sensors with long-term trends
- One-time import, persistent in Recorder database
- See complete documentation in `scripts/README.md`

### Using Home Assistant Recorder

All price sensors have `state_class: measurement` for automatic long-term statistics. The default SQLite recorder will track sensor states. Configure retention in `configuration.yaml`:

```yaml
recorder:
  purge_keep_days: 90
  include:
    entity_globs:
      - sensor.*_diesel_*
      - sensor.*_premium_98_*
      - sensor.*_ulp_91_*
```

### Energy Dashboard & Statistics

Price sensors use `state_class: measurement` (values in ¢/L, as FuelWatch publishes them) and are compatible with:
- Long-term statistics (automatic with Recorder)
- InfluxDB integration
- History graphs
- Statistics cards

### Using InfluxDB

For long-term analytics and Grafana dashboards:

```yaml
influxdb:
  host: your-influxdb-host
  port: 8086
  database: homeassistant
  include:
    entity_globs:
      - sensor.fuelwatch_*
```

## Example Usage

See `examples/dashboards/fuelwatchwa-dashboard.yaml` for a complete dashboard example.

## Known Limitations

- Single location per integration instance (add multiple instances for multiple locations)
- No region/grouped area support

## Troubleshooting

### Integration shows "Unavailable"
- Check that the suburb/location name is spelled the way FuelWatch knows it
- Check Home Assistant logs for the underlying API error

### No data returned
- If the suburb has no petrol station of its own, enable **Include surrounding suburbs** (Settings → Devices & Services → Configure)
- Some locations may not have all fuel types available
- Tomorrow's data is not published until about 2:30pm
- FuelWatch may be temporarily unavailable

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Test thoroughly in a live Home Assistant instance
4. Submit a pull request

## License

MIT License - see LICENSE file for details

## Credits

- Originally created by [Damian Rosair (@drosair)](https://github.com/drosair/fuelwatchwa) — this is a maintained fork
- Earlier versions were built on the [fuelwatcher](https://github.com/danielmichaels/fuelwatcher) Python library by Daniel Michaels (since v0.7.0 the integration queries the FuelWatch feed directly)
- Data sourced from [FuelWatch WA Government](https://www.fuelwatch.wa.gov.au/)

## Disclaimer

This is an unofficial integration. Not affiliated with or endorsed by FuelWatch or the Government of Western Australia.
