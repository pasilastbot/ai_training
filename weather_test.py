import requests
import json

def check_weather(location):
    try:
        # Try to geocode the location to get coordinates
        # In a real-world scenario, you should use a proper geocoding API
        # For now, we'll use a simple dictionary for common locations
        geocode_map = {
            "new york": {"lat": 40.71, "lon": -74.01},
            "london": {"lat": 51.51, "lon": -0.13},
            "paris": {"lat": 48.85, "lon": 2.35},
            "tokyo": {"lat": 35.68, "lon": 139.76},
            "berlin": {"lat": 52.52, "lon": 13.41},
            "sydney": {"lat": -33.87, "lon": 151.21},
            "san francisco": {"lat": 37.77, "lon": -122.42},
            "los angeles": {"lat": 34.05, "lon": -118.24},
            "chicago": {"lat": 41.88, "lon": -87.63},
            "seattle": {"lat": 47.61, "lon": -122.33},
        }
        
        # Convert location to lowercase for case-insensitive matching
        location_lower = location.lower()
        
        # Get coordinates for the location
        if location_lower in geocode_map:
            coords = geocode_map[location_lower]
        else:
            # Default to Berlin if location not found
            coords = {"lat": 52.52, "lon": 13.41}
            
        # Make request to Open-Meteo API
        url = f"https://api.open-meteo.com/v1/forecast?latitude={coords['lat']}&longitude={coords['lon']}&current=temperature_2m,wind_speed_10m,precipitation,weather_code&daily=weather_code,temperature_2m_max,temperature_2m_min,precipitation_sum"
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            
            # Extract current weather information
            current = data.get('current', {})
            temperature = current.get('temperature_2m', 'N/A')
            wind_speed = current.get('wind_speed_10m', 'N/A')
            precipitation = current.get('precipitation', 'N/A')
            
            # Weather code interpretation
            weather_codes = {
                0: "Clear sky",
                1: "Mainly clear",
                2: "Partly cloudy",
                3: "Overcast",
                45: "Fog",
                48: "Depositing rime fog",
                51: "Light drizzle",
                53: "Moderate drizzle",
                55: "Dense drizzle",
                56: "Light freezing drizzle",
                57: "Dense freezing drizzle",
                61: "Slight rain",
                63: "Moderate rain",
                65: "Heavy rain",
                66: "Light freezing rain",
                67: "Heavy freezing rain",
                71: "Slight snow fall",
                73: "Moderate snow fall",
                75: "Heavy snow fall",
                77: "Snow grains",
                80: "Slight rain showers",
                81: "Moderate rain showers",
                82: "Violent rain showers",
                85: "Slight snow showers",
                86: "Heavy snow showers",
                95: "Thunderstorm",
                96: "Thunderstorm with slight hail",
                99: "Thunderstorm with heavy hail"
            }
            
            weather_code = current.get('weather_code', 0)
            weather_description = weather_codes.get(weather_code, "Unknown")
            
            # Format the response
            weather_info = f"Current weather in {location}:\n"
            weather_info += f"- Condition: {weather_description}\n"
            weather_info += f"- Temperature: {temperature}°C\n"
            weather_info += f"- Wind Speed: {wind_speed} km/h\n"
            weather_info += f"- Precipitation: {precipitation} mm\n"
            
            # Add forecast information if available
            if 'daily' in data:
                daily = data['daily']
                if 'temperature_2m_max' in daily and len(daily['temperature_2m_max']) > 0:
                    weather_info += f"\nToday's Forecast:\n"
                    weather_info += f"- High: {daily['temperature_2m_max'][0]}°C\n"
                    weather_info += f"- Low: {daily['temperature_2m_min'][0]}°C\n"
                    
                    if 'precipitation_sum' in daily:
                        weather_info += f"- Precipitation Sum: {daily['precipitation_sum'][0]} mm\n"

            # Also print the raw response for debugging
            print("Raw API response:")
            print(json.dumps(data, indent=2))
            
            return weather_info
        else:
            return f"Error: Unable to get weather data. Status code: {response.status_code}"
    
    except Exception as e:
        return f"Error checking weather: {str(e)}"

# Test the function
if __name__ == "__main__":
    # Test with New York
    print("\n=== Testing with New York ===")
    print(check_weather("New York"))
    
    # Test with London
    print("\n=== Testing with London ===")
    print(check_weather("London"))
    
    # Test with an unknown location (will default to Berlin)
    print("\n=== Testing with Unknown Location ===")
    print(check_weather("Unknown City")) 