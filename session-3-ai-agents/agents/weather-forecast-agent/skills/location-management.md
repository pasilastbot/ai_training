---
name: location-management
description: Managing saved locations for quick weather checks
tools: [store_location, retrieve_locations, delete_location]
---

## Purpose
Manage a personal list of favorite locations for quick weather information access.

## When to Use
Use this skill when the user:
- Wants to save frequently-checked locations ("Save 'Home' as Helsinki")
- Needs to quickly check weather for their locations ("How's the weather at all my places?")
- Wants to remove a location ("Delete my old work location")
- Asks about their saved places ("What locations have I saved?")

## Tools Required

### store_location
- **Purpose**: Save a new location or update an existing one
- **Parameters**:
  - `name` (required): User-friendly identifier (e.g., "Home", "Work", "Cabin")
  - `location` (required): City name or coordinates
  - `lat` (optional): Latitude
  - `lon` (optional): Longitude
  - `timezone` (optional): Timezone identifier

### retrieve_locations
- **Purpose**: Get all saved locations
- **Parameters**: none
- **Returns**: List of all saved locations with details

### delete_location
- **Purpose**: Remove a saved location
- **Parameters**:
  - `name` (required): Location name to remove

## Location Naming Best Practices
- Use short, memorable names: "Home", "Work", "Parents", "Cabin"
- Avoid special characters or spaces when possible
- Use consistent naming convention
- Consider adding context: "Home-Helsinki", "Work-Downtown"

## Example Usage

### Save a Location
```
User: "Save 'Home' as Helsinki, Finland"
Tool Call: store_location(name="Home", location="Helsinki, Finland")
Response: {"status": "success", "id": "loc_...", "action": "stored"}
```

### Retrieve All Locations
```
User: "Show me all my saved places"
Tool Call: retrieve_locations()
Response:
{
  "locations": [
    {"name": "Home", "city": "Helsinki, Finland", "id": "loc_1"},
    {"name": "Work", "city": "Downtown, Seattle, WA", "id": "loc_2"},
    {"name": "Parents", "city": "Oslo, Norway", "id": "loc_3"}
  ]
}
```

### Get Weather for Multiple Locations
```
User: "What's the weather at all my saved places?"
Workflow:
1. retrieve_locations() → Get list
2. For each location: get_weather(location=location.city)
3. Present summary table
```

### Delete a Location
```
User: "Remove 'Old Work' from my places"
Tool Call: delete_location(name="Old Work")
Response: {"status": "success", "message": "Location 'Old Work' removed"}
```

## Common Use Cases

### Morning Weather Check
```
User: "How's the weather at my usual places?"
→ Get all saved locations
→ Fetch weather for each
→ Present in compact table format
```

### Travel Planning
```
User: "I'm going to London next week. Add it to my places, then show weather for all."
→ store_location(name="London Trip", location="London")
→ retrieve_locations()
→ Get weather for all saved places
```

### Location Management
```
User: "Clean up my saved locations - I don't need the old ones."
→ retrieve_locations() → Show current
→ Ask user which to remove
→ delete_location() for each selection
```

## Best Practices
1. Offer to save locations after user checks weather multiple times
2. Present locations in a clear, scannable format (table or list)
3. Include timezone information when available for time-sensitive queries
4. Suggest removing unused locations after time
5. Use location names in weather summaries for personalization