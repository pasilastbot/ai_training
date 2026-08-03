---
name: apartment-memory
description: Store and retrieve customer apartment details for personalized energy advice
tools: [memory]
---

## Purpose

Manage customer apartment profiles in SQLite database to provide personalized energy advice based on building characteristics, heating systems, and energy consumption patterns.

## When to Use

- Registering new customer apartments
- Looking up existing customer details
- Updating energy consumption data
- Searching apartments by criteria
- Creating energy recommendations

## Tools Required

| Tool | Purpose |
|------|---------|
| `memory/memory.py` | CLI for apartment CRUD operations |

## Data Schema

### Apartment Properties

| Field | Description |
|-------|-------------|
| `customer_id` | Unique customer identifier |
| `customer_name` | Customer name |
| `address.city` | City location |
| `building_info.building_type` | apartment, house, townhouse, commercial |
| `building_info.construction_year` | Year built |
| `apartment_details.size_sqm` | Size in square meters |
| `heating_system.type` | district_heating, electric, heat_pump |
| `heating_system.has_smart_controls` | Boolean |
| `energy_consumption.annual_heating_kwh` | Annual heating consumption |
| `energy_consumption.annual_cost_eur` | Annual energy cost |
| `energy_consumption.energy_class` | A-G rating |
| `occupancy.residents_count` | Number of residents |
| `preferences.preferred_temp_c` | Preferred temperature |

## Example

```bash
# Initialize database
python memory/memory.py --init

# Create apartment
python memory/memory.py --apartment create

# List all apartments
python memory/memory.py --apartment list

# Get specific apartment
python memory/memory.py --apartment get apt123

# Search apartments
python memory/memory.py --apartment search "Helsinki"

# View statistics
python memory/memory.py --stats
```

## Database Location

`memory/data/energy_advisor.db`

## Integration with Agent

The agent uses apartment context to:
1. Personalize energy advice for specific building types
2. Calculate potential savings based on current consumption
3. Recommend appropriate optimization strategies
4. Track recommendations per apartment
