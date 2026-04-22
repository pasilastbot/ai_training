#!/usr/bin/env python3
"""
Memory CLI — File-based memory for the Lunch Selection Agent

Provides persistent storage for:
- Restaurants and their menus
- User food preferences
- Past lunch selections

Usage:
  python memory.py get-preferences                    # Get user preferences
  python memory.py set-preferences --file prefs.json  # Set preferences from file
  python memory.py update-preference --key liked_cuisines --value '["Italian", "Thai"]'
  python memory.py get-restaurants --city Helsinki    # Get restaurants in city
  python memory.py get-selections --days 7            # Get recent selections
  python memory.py list --collection restaurants      # List all in collection
"""

import argparse
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

MEMORY_DIR = Path(__file__).parent / "data"


class MemoryStore:
    """File-based memory store for the lunch selection agent."""
    
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
    
    # ==================== Preferences ====================
    
    def get_preferences(self, user_id: str = "default") -> Optional[Dict[str, Any]]:
        """Get user preferences."""
        data = self._load_file("preferences")
        return data.get(user_id)
    
    def set_preferences(self, preferences: Dict[str, Any], user_id: str = "default") -> bool:
        """Set user preferences."""
        preferences["user_id"] = user_id
        preferences["updated_at"] = datetime.utcnow().isoformat()
        
        data = self._load_file("preferences")
        data[user_id] = preferences
        self._save_file("preferences", data)
        return True
    
    def update_preference(self, key: str, value: Any, user_id: str = "default") -> bool:
        """Update a specific preference field."""
        prefs = self.get_preferences(user_id) or {"user_id": user_id}
        prefs[key] = value
        return self.set_preferences(prefs, user_id)
    
    # ==================== Restaurants ====================
    
    def get_restaurant(self, restaurant_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific restaurant by ID."""
        data = self._load_file("restaurants")
        return data.get(restaurant_id)
    
    def get_restaurants(self, city: Optional[str] = None, cuisine: Optional[str] = None,
                       price_range: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Get restaurants with optional filters."""
        data = self._load_file("restaurants")
        restaurants = list(data.values())
        
        if city:
            city_lower = city.lower()
            restaurants = [r for r in restaurants if r.get("city", "").lower() == city_lower]
        
        if cuisine:
            cuisine_lower = cuisine.lower()
            restaurants = [r for r in restaurants 
                          if any(c.lower() == cuisine_lower for c in r.get("cuisine_types", []))]
        
        if price_range:
            restaurants = [r for r in restaurants if r.get("price_range") == price_range]
        
        restaurants.sort(key=lambda r: r.get("updated_at", ""), reverse=True)
        return restaurants[:limit]
    
    def store_restaurant(self, restaurant: Dict[str, Any]) -> Dict[str, Any]:
        """Store or update a restaurant."""
        data = self._load_file("restaurants")
        
        restaurant_id = restaurant.get("id")
        if not restaurant_id:
            restaurant_id = f"rest_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{len(data)}"
            restaurant["id"] = restaurant_id
        
        now = datetime.utcnow().isoformat()
        if restaurant_id in data:
            restaurant["updated_at"] = now
            restaurant["created_at"] = data[restaurant_id].get("created_at", now)
        else:
            restaurant["created_at"] = now
            restaurant["updated_at"] = now
        
        data[restaurant_id] = restaurant
        self._save_file("restaurants", data)
        
        return {"status": "success", "id": restaurant_id, "action": "stored"}
    
    def update_restaurant_menu(self, restaurant_id: str, menu: Dict[str, Any]) -> bool:
        """Update the cached menu for a restaurant."""
        data = self._load_file("restaurants")
        if restaurant_id not in data:
            return False
        
        data[restaurant_id]["cached_menu"] = menu
        data[restaurant_id]["last_menu_fetch"] = datetime.utcnow().isoformat()
        data[restaurant_id]["updated_at"] = datetime.utcnow().isoformat()
        self._save_file("restaurants", data)
        return True
    
    def search_restaurants(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Search restaurants by name or cuisine."""
        data = self._load_file("restaurants")
        query_lower = query.lower()
        
        results = []
        for restaurant in data.values():
            name = restaurant.get("name", "").lower()
            cuisines = " ".join(restaurant.get("cuisine_types", [])).lower()
            city = restaurant.get("city", "").lower()
            
            if query_lower in name or query_lower in cuisines or query_lower in city:
                results.append(restaurant)
        
        return results[:limit]
    
    # ==================== Selections ====================
    
    def get_selection(self, selection_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific selection by ID."""
        data = self._load_file("selections")
        return data.get(selection_id)
    
    def get_selections(self, days: Optional[int] = None, restaurant_id: Optional[str] = None,
                       min_rating: Optional[int] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Get selections with optional filters."""
        data = self._load_file("selections")
        selections = list(data.values())
        
        if days:
            cutoff = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d")
            selections = [s for s in selections if s.get("date", "") >= cutoff]
        
        if restaurant_id:
            selections = [s for s in selections if s.get("restaurant_id") == restaurant_id]
        
        if min_rating:
            selections = [s for s in selections if (s.get("rating") or 0) >= min_rating]
        
        selections.sort(key=lambda s: s.get("date", ""), reverse=True)
        return selections[:limit]
    
    def get_recent_dishes(self, days: int = 14) -> List[str]:
        """Get dish names from recent selections to avoid repetition."""
        selections = self.get_selections(days=days)
        return [s.get("dish_name", "") for s in selections if s.get("dish_name")]
    
    def get_recent_restaurants(self, days: int = 7) -> List[str]:
        """Get restaurant IDs from recent selections."""
        selections = self.get_selections(days=days)
        return list(set(s.get("restaurant_id", "") for s in selections if s.get("restaurant_id")))
    
    def store_selection(self, selection: Dict[str, Any]) -> Dict[str, Any]:
        """Store a lunch selection."""
        data = self._load_file("selections")
        
        selection_id = selection.get("id")
        if not selection_id:
            selection_id = f"sel_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{len(data)}"
            selection["id"] = selection_id
        
        if "date" not in selection:
            selection["date"] = datetime.utcnow().strftime("%Y-%m-%d")
        
        selection["created_at"] = datetime.utcnow().isoformat()
        
        data[selection_id] = selection
        self._save_file("selections", data)
        
        self._update_implicit_preferences(selection)
        
        return {"status": "success", "id": selection_id, "action": "stored"}
    
    def _update_implicit_preferences(self, selection: Dict[str, Any]):
        """Update implicit preferences based on a new selection."""
        prefs = self.get_preferences() or {"user_id": "default"}
        implicit = prefs.get("implicit_preferences", {"cuisine_weights": {}, "restaurant_weights": {}})
        
        rating = selection.get("rating", 3)
        weight_delta = (rating - 3) * 0.1
        
        cuisine = selection.get("cuisine_type")
        if cuisine:
            current = implicit["cuisine_weights"].get(cuisine, 0)
            implicit["cuisine_weights"][cuisine] = current + weight_delta
        
        rest_id = selection.get("restaurant_id")
        if rest_id:
            current = implicit["restaurant_weights"].get(rest_id, 0)
            implicit["restaurant_weights"][rest_id] = current + weight_delta
        
        prefs["implicit_preferences"] = implicit
        self.set_preferences(prefs)
    
    # ==================== Statistics ====================
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about stored data."""
        restaurants = self._load_file("restaurants")
        selections = self._load_file("selections")
        prefs = self.get_preferences()
        
        cities = {}
        cuisines = {}
        for r in restaurants.values():
            city = r.get("city", "Unknown")
            cities[city] = cities.get(city, 0) + 1
            for c in r.get("cuisine_types", []):
                cuisines[c] = cuisines.get(c, 0) + 1
        
        ratings = [s.get("rating") for s in selections.values() if s.get("rating")]
        avg_rating = sum(ratings) / len(ratings) if ratings else None
        
        return {
            "total_restaurants": len(restaurants),
            "total_selections": len(selections),
            "restaurants_by_city": cities,
            "cuisines": cuisines,
            "average_rating": round(avg_rating, 2) if avg_rating else None,
            "has_preferences": prefs is not None
        }
    
    # ==================== Clear ====================
    
    def clear(self, collection: str) -> bool:
        """Clear all items in a collection."""
        self._save_file(collection, {})
        return True


def main():
    parser = argparse.ArgumentParser(
        description="Memory CLI for Lunch Selection Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # get-preferences
    get_prefs = subparsers.add_parser("get-preferences", help="Get user preferences")
    get_prefs.add_argument("--user", default="default", help="User ID")
    
    # set-preferences
    set_prefs = subparsers.add_parser("set-preferences", help="Set preferences from JSON file")
    set_prefs.add_argument("--file", "-f", required=True, help="Path to preferences JSON file")
    set_prefs.add_argument("--user", default="default", help="User ID")
    
    # update-preference
    update_pref = subparsers.add_parser("update-preference", help="Update a specific preference")
    update_pref.add_argument("--key", "-k", required=True, help="Preference key to update")
    update_pref.add_argument("--value", "-v", required=True, help="New value (JSON)")
    update_pref.add_argument("--user", default="default", help="User ID")
    
    # get-restaurants
    get_rest = subparsers.add_parser("get-restaurants", help="Get restaurants")
    get_rest.add_argument("--city", "-c", help="Filter by city")
    get_rest.add_argument("--cuisine", help="Filter by cuisine")
    get_rest.add_argument("--price", help="Filter by price range")
    get_rest.add_argument("--limit", type=int, default=50, help="Max results")
    
    # get-selections
    get_sel = subparsers.add_parser("get-selections", help="Get lunch selections")
    get_sel.add_argument("--days", "-d", type=int, help="Get selections from last N days")
    get_sel.add_argument("--restaurant", "-r", help="Filter by restaurant ID")
    get_sel.add_argument("--min-rating", type=int, help="Minimum rating")
    get_sel.add_argument("--limit", type=int, default=50, help="Max results")
    
    # stats
    subparsers.add_parser("stats", help="Get statistics")
    
    # list
    list_cmd = subparsers.add_parser("list", help="List all items in collection")
    list_cmd.add_argument("--collection", "-c", required=True, 
                         choices=["restaurants", "selections", "preferences"],
                         help="Collection name")
    
    # clear
    clear_cmd = subparsers.add_parser("clear", help="Clear a collection")
    clear_cmd.add_argument("--collection", "-c", required=True, help="Collection name")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    memory = MemoryStore()
    
    if args.command == "get-preferences":
        prefs = memory.get_preferences(args.user)
        if prefs:
            print(json.dumps(prefs, indent=2))
        else:
            print(json.dumps({"message": "No preferences found", "user_id": args.user}))
    
    elif args.command == "set-preferences":
        with open(args.file, "r") as f:
            prefs = json.load(f)
        if memory.set_preferences(prefs, args.user):
            print(json.dumps({"status": "success", "message": "Preferences updated"}))
        else:
            print(json.dumps({"status": "error", "message": "Failed to update preferences"}))
            sys.exit(1)
    
    elif args.command == "update-preference":
        try:
            value = json.loads(args.value)
        except json.JSONDecodeError:
            value = args.value
        
        if memory.update_preference(args.key, value, args.user):
            print(json.dumps({"status": "success", "key": args.key}))
        else:
            print(json.dumps({"status": "error", "message": "Failed to update preference"}))
            sys.exit(1)
    
    elif args.command == "get-restaurants":
        restaurants = memory.get_restaurants(
            city=args.city,
            cuisine=args.cuisine,
            price_range=args.price,
            limit=args.limit
        )
        print(json.dumps({"count": len(restaurants), "restaurants": restaurants}, indent=2))
    
    elif args.command == "get-selections":
        selections = memory.get_selections(
            days=args.days,
            restaurant_id=args.restaurant,
            min_rating=args.min_rating,
            limit=args.limit
        )
        print(json.dumps({"count": len(selections), "selections": selections}, indent=2))
    
    elif args.command == "stats":
        stats = memory.get_stats()
        print(json.dumps(stats, indent=2))
    
    elif args.command == "list":
        data = memory._load_file(args.collection)
        items = list(data.values()) if args.collection != "preferences" else data
        print(json.dumps({"collection": args.collection, "count": len(data), "items": items}, indent=2))
    
    elif args.command == "clear":
        if memory.clear(args.collection):
            print(json.dumps({"status": "success", "collection": args.collection}))
        else:
            print(json.dumps({"status": "error", "message": "Failed to clear"}))
            sys.exit(1)


if __name__ == "__main__":
    main()
