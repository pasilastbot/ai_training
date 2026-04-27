#!/usr/bin/env python3
"""
Memory CLI — File-based memory for the Weather Forecast Agent

Provides persistent storage for:
- Saved user locations
- Cached weather data

Usage:
  python memory.py get-locations                        # Get saved locations
  python memory.py store-location --name Home --location "Helsinki, Finland"
  python memory.py delete-location --name Home
  python memory.py list --collection locations          # List all locations
"""

import argparse
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

MEMORY_DIR = Path(__file__).parent / "data"


class MemoryStore:
    """File-based memory store for the weather forecast agent."""
    
    def __init__(self):
        self.memory_dir = MEMORY_DIR
        self.memory_dir.mkdir(parents=True, exist_ok=True)
    
    def _file_path(self, collection: str) -> Path:
        """Get file path for a collection."""
        return self.memory_dir / f"{collection}.json"
    
    def _load_file(self, collection: str) -> Dict[str, Any]:
        """Load data from file."""
        path = self._file_path(collection)
        if path.exists():
            with open(path, "r") as f:
                return json.load(f)
        return {}
    
    def _save_file(self, collection: str, data: Dict[str, Any]):
        """Save data to file."""
        path = self._file_path(collection)
        with open(path, "w") as f:
            json.dump(data, f, indent=2, default=str)
    
    def _get_location_id(self, name: str) -> Optional[str]:
        """Find location ID by name."""
        data = self._load_file("locations")
        for loc_id, loc_data in data.items():
            if loc_data.get("name") == name:
                return loc_id
        return None
    
    def clean_expired_cache(self):
        """Remove expired weather cache entries."""
        data = self._load_file("weather_cache")
        now = datetime.utcnow()
        
        expired_keys = []
        for key, entry in data.items():
            expires_at = entry.get("expires_at")
            if expires_at:
                try:
                    expire_time = datetime.fromisoformat(expires_at)
                    if expire_time < now:
                        expired_keys.append(key)
                except Exception:
                    pass
        
        for key in expired_keys:
            del data[key]
        
        if expired_keys:
            self._save_file("weather_cache", data)
    
    
    # ==================== Locations ====================
    
    def get_locations(self) -> List[Dict[str, Any]]:
        """Get all saved locations."""
        data = self._load_file("locations")
        return sorted(
            [loc for loc in data.values()],
            key=lambda x: x.get("created_at", ""),
            reverse=True
        )
    
    def get_location(self, name: str) -> Optional[Dict[str, Any]]:
        """Get a specific location by name."""
        location_id = self._get_location_id(name)
        if location_id:
            data = self._load_file("locations")
            return data.get(location_id)
        return None
    
    def store_location(self, name: str, location: str, coordinates: Optional[Dict[str, float]] = None,
                      timezone: Optional[str] = None) -> Dict[str, Any]:
        """Store or update a location."""
        data = self._load_file("locations")
        
        location_id = self._get_location_id(name)
        if not location_id:
            location_id = f"loc_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{len(data)}"
        
        now = datetime.utcnow().isoformat()
        
        location_data = {
            "id": location_id,
            "name": name,
            "city": location,
            "coordinates": coordinates,
            "timezone": timezone,
            "updated_at": now
        }
        
        if location_id in data:
            location_data["created_at"] = data[location_id].get("created_at", now)
        else:
            location_data["created_at"] = now
        
        data[location_id] = location_data
        self._save_file("locations", data)
        
        return {"status": "success", "id": location_id, "action": "stored"}
    
    def delete_location(self, name: str) -> Dict[str, Any]:
        """Remove a location by name."""
        location_id = self._get_location_id(name)
        if not location_id:
            return {"status": "error", "message": f"Location '{name}' not found"}
        
        data = self._load_file("locations")
        if location_id in data:
            del data[location_id]
            self._save_file("locations", data)
            return {"status": "success", "message": f"Location '{name}' removed"}
        
        return {"status": "error", "message": "Location not found"}
    
    # ==================== Weather Cache ====================
    
    def cache_weather(self, location: str, weather_data: Dict[str, Any], ttl_minutes: int = 30) -> bool:
        """Cache weather data with a TTL."""
        self.clean_expired_cache()
        
        data = self._load_file("weather_cache")
        
        location_key = location.lower().strip()
        now = datetime.utcnow()
        
        data[location_key] = {
            "location": location,
            "data": weather_data,
            "fetched_at": now.isoformat(),
            "expires_at": (now + timedelta(minutes=ttl_minutes)).isoformat()
        }
        
        self._save_file("weather_cache", data)
        return True
    
    def get_cached_weather(self, location: str) -> Optional[Dict[str, Any]]:
        """Get cached weather data if still valid."""
        self.clean_expired_cache()
        
        location_key = location.lower().strip()
        data = self._load_file("weather_cache")
        
        if location_key not in data:
            return None
        
        entry = data[location_key]
        expires_at = entry.get("expires_at")
        
        if expires_at:
            try:
                expire_time = datetime.fromisoformat(expires_at)
                if expire_time < datetime.utcnow():
                    return None
            except Exception:
                return None
        
        return entry.get("data")
    
    # ==================== Statistics ====================
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about stored data."""
        locations = self._load_file("locations")
        cache = self._load_file("weather_cache")
        
        return {
            "total_locations": len(locations),
            "cached_weather_entries": len(cache)
        }
    
    # ==================== Clear ====================
    
    def clear(self, collection: str) -> bool:
        """Clear all items in a collection."""
        self._save_file(collection, {})
        return True


def main():
    parser = argparse.ArgumentParser(
        description="Memory CLI for Weather Forecast Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # get-locations
    get_locs = subparsers.add_parser("get-locations", help="Get all saved locations")
    
    # store-location
    store_loc = subparsers.add_parser("store-location", help="Store a location")
    store_loc.add_argument("--name", "-n", required=True, help="Location name (e.g., 'Home')")
    store_loc.add_argument("--location", "-l", required=True, help="City name or coordinates")
    store_loc.add_argument("--lat", type=float, help="Latitude")
    store_loc.add_argument("--lon", type=float, help="Longitude")
    store_loc.add_argument("--timezone", "-tz", help="Timezone (e.g., 'Europe/Helsinki')")
    
    # delete-location
    del_loc = subparsers.add_parser("delete-location", help="Delete a location")
    del_loc.add_argument("--name", "-n", required=True, help="Location name to remove")
    
    # stats
    subparsers.add_parser("stats", help="Get statistics")
    
    # list
    list_cmd = subparsers.add_parser("list", help="List all items in collection")
    list_cmd.add_argument("--collection", "-c", required=True, 
                         choices=["locations", "weather_cache"],
                         help="Collection name")
    
    # clear
    clear_cmd = subparsers.add_parser("clear", help="Clear a collection")
    clear_cmd.add_argument("--collection", "-c", required=True, help="Collection name")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    memory = MemoryStore()
    
    if args.command == "get-locations":
        locations = memory.get_locations()
        print(json.dumps({"count": len(locations), "locations": locations}, indent=2))
    
    elif args.command == "store-location":
        coordinates = None
        if args.lat is not None and args.lon is not None:
            coordinates = {"lat": args.lat, "lon": args.lon}
        
        result = memory.store_location(
            name=args.name,
            location=args.location,
            coordinates=coordinates,
            timezone=args.timezone
        )
        print(json.dumps(result, indent=2))
    
    elif args.command == "delete-location":
        result = memory.delete_location(args.name)
        print(json.dumps(result, indent=2))
        if result.get("status") == "error":
            sys.exit(1)
    
    elif args.command == "stats":
        stats = memory.get_stats()
        print(json.dumps(stats, indent=2))
    
    elif args.command == "list":
        data = memory._load_file(args.collection)
        items = list(data.values())
        print(json.dumps({"collection": args.collection, "count": len(data), "items": items}, indent=2))
    
    elif args.command == "clear":
        if memory.clear(args.collection):
            print(json.dumps({"status": "success", "collection": args.collection}))
        else:
            print(json.dumps({"status": "error", "message": "Failed to clear"}))
            sys.exit(1)


if __name__ == "__main__":
    main()