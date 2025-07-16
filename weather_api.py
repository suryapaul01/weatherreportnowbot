import openmeteo_requests
import requests_cache
import pandas as pd
from retry_requests import retry
from typing import Dict, List, Optional, Tuple, Any
import asyncio
import aiohttp
import json
from datetime import datetime, timedelta
from config import Config


class WeatherAPI:
    def __init__(self):
        # Setup the Open-Meteo API client with cache and retry on error
        cache_session = requests_cache.CachedSession('.cache', expire_after=3600)
        retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
        self.openmeteo = openmeteo_requests.Client(session=retry_session)
        
        # API endpoints
        self.weather_url = "https://api.open-meteo.com/v1/forecast"
        self.geocoding_url = "https://geocoding-api.open-meteo.com/v1/search"

    async def get_coordinates_from_location(self, location: str) -> Optional[Tuple[float, float, str]]:
        """Get coordinates from location name using geocoding API."""
        try:
            async with aiohttp.ClientSession() as session:
                params = {
                    "name": location,
                    "count": 1,
                    "language": "en",
                    "format": "json"
                }
                
                async with session.get(self.geocoding_url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("results"):
                            result = data["results"][0]
                            latitude = result["latitude"]
                            longitude = result["longitude"]
                            name = result["name"]
                            country = result.get("country", "")
                            admin1 = result.get("admin1", "")
                            
                            # Format location name
                            location_parts = [name]
                            if admin1 and admin1 != name:
                                location_parts.append(admin1)
                            if country:
                                location_parts.append(country)
                            
                            formatted_name = ", ".join(location_parts)
                            return latitude, longitude, formatted_name
                        
            return None
        except Exception as e:
            print(f"Error getting coordinates: {e}")
            return None

    async def get_current_weather(self, latitude: float, longitude: float,
                                 temperature_unit: str = "celsius",
                                 wind_speed_unit: str = "kmh",
                                 precipitation_unit: str = "mm") -> Optional[Dict]:
        """Get current weather for given coordinates."""
        try:
            # Use simple HTTP request instead of openmeteo client
            async with aiohttp.ClientSession() as session:
                params = {
                    "latitude": latitude,
                    "longitude": longitude,
                    "current": "temperature_2m,relative_humidity_2m,apparent_temperature,is_day,precipitation,weather_code,cloud_cover,pressure_msl,wind_speed_10m,wind_direction_10m,wind_gusts_10m",
                    "temperature_unit": "celsius",
                    "wind_speed_unit": "kmh",
                    "precipitation_unit": "mm",
                    "timezone": "auto"
                }

                async with session.get(self.weather_url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        current = data.get("current", {})

                        weather_data = {
                            "temperature": round(current.get("temperature_2m", 0), 1),
                            "humidity": round(current.get("relative_humidity_2m", 0), 1),
                            "apparent_temperature": round(current.get("apparent_temperature", 0), 1),
                            "is_day": bool(current.get("is_day", 1)),
                            "precipitation": round(current.get("precipitation", 0), 1),
                            "weather_code": int(current.get("weather_code", 0)),
                            "cloud_cover": round(current.get("cloud_cover", 0), 1),
                            "pressure_msl": round(current.get("pressure_msl", 1013), 1),
                            "wind_speed": round(current.get("wind_speed_10m", 0), 1),
                            "wind_direction": round(current.get("wind_direction_10m", 0), 1),
                            "wind_gusts": round(current.get("wind_gusts_10m", 0), 1),
                            "timestamp": datetime.now().isoformat(),  # Always use current time
                            "units": {
                                "temperature": "°C",
                                "wind_speed": "km/h",
                                "precipitation": "mm",
                                "pressure": "hPa",
                                "humidity": "%"
                            }
                        }

                        return weather_data
                    else:
                        print(f"Weather API error: {response.status}")
                        return None

        except Exception as e:
            print(f"Error getting current weather: {e}")
            return None

    async def get_weather_forecast(self, latitude: float, longitude: float,
                                  days: int = 7,
                                  temperature_unit: str = "celsius",
                                  wind_speed_unit: str = "kmh",
                                  precipitation_unit: str = "mm") -> Optional[Dict]:
        """Get weather forecast for given coordinates."""
        try:
            # Use simple HTTP request
            async with aiohttp.ClientSession() as session:
                params = {
                    "latitude": latitude,
                    "longitude": longitude,
                    "daily": "weather_code,temperature_2m_max,temperature_2m_min,sunrise,sunset,precipitation_sum,wind_speed_10m_max,wind_direction_10m_dominant",
                    "temperature_unit": "celsius",
                    "wind_speed_unit": "kmh",
                    "precipitation_unit": "mm",
                    "timezone": "auto",
                    "forecast_days": days
                }

                async with session.get(self.weather_url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        daily_data = data.get("daily", {})

                        if not daily_data:
                            return None

                        # Extract daily data
                        dates = daily_data.get("time", [])
                        weather_codes = daily_data.get("weather_code", [])
                        temp_max = daily_data.get("temperature_2m_max", [])
                        temp_min = daily_data.get("temperature_2m_min", [])
                        sunrise = daily_data.get("sunrise", [])
                        sunset = daily_data.get("sunset", [])
                        precipitation = daily_data.get("precipitation_sum", [])
                        wind_max = daily_data.get("wind_speed_10m_max", [])
                        wind_dir = daily_data.get("wind_direction_10m_dominant", [])
            
                        # Convert to list of dictionaries
                        forecast_days = []
                        for i in range(len(dates)):
                            try:
                                # Parse sunrise/sunset times
                                sunrise_time = sunrise[i].split('T')[1] if i < len(sunrise) and sunrise[i] else "06:00"
                                sunset_time = sunset[i].split('T')[1] if i < len(sunset) and sunset[i] else "18:00"

                                day_data = {
                                    "date": dates[i],
                                    "weather_code": int(weather_codes[i]) if i < len(weather_codes) and weather_codes[i] is not None else 0,
                                    "temperature_max": round(float(temp_max[i]), 1) if i < len(temp_max) and temp_max[i] is not None else 0.0,
                                    "temperature_min": round(float(temp_min[i]), 1) if i < len(temp_min) and temp_min[i] is not None else 0.0,
                                    "sunrise": sunrise_time,
                                    "sunset": sunset_time,
                                    "precipitation_sum": round(float(precipitation[i]), 1) if i < len(precipitation) and precipitation[i] is not None else 0.0,
                                    "wind_speed_max": round(float(wind_max[i]), 1) if i < len(wind_max) and wind_max[i] is not None else 0.0,
                                    "wind_direction": round(float(wind_dir[i]), 1) if i < len(wind_dir) and wind_dir[i] is not None else 0.0
                                }
                                forecast_days.append(day_data)
                            except Exception as e:
                                print(f"Error processing day {i}: {e}")
                                continue
            
                        return {
                            "forecast": forecast_days,
                            "units": {
                                "temperature": "°C",
                                "wind_speed": "km/h",
                                "precipitation": "mm",
                                "humidity": "%"
                            }
                        }
                    else:
                        print(f"Forecast API error: {response.status}")
                        return None

        except Exception as e:
            print(f"Error getting weather forecast: {e}")
            return None

    def get_weather_description(self, weather_code: int, is_day: bool = True) -> str:
        """Get weather description from WMO weather code."""
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
        
        return weather_codes.get(weather_code, "Unknown")

    def get_weather_emoji(self, weather_code: int, is_day: bool = True) -> str:
        """Get weather emoji from WMO weather code."""
        day_emojis = {
            0: "☀️",  # Clear sky
            1: "🌤️",  # Mainly clear
            2: "⛅",  # Partly cloudy
            3: "☁️",  # Overcast
            45: "🌫️",  # Fog
            48: "🌫️",  # Depositing rime fog
            51: "🌦️",  # Light drizzle
            53: "🌦️",  # Moderate drizzle
            55: "🌧️",  # Dense drizzle
            56: "🌨️",  # Light freezing drizzle
            57: "🌨️",  # Dense freezing drizzle
            61: "🌦️",  # Slight rain
            63: "🌧️",  # Moderate rain
            65: "🌧️",  # Heavy rain
            66: "🌨️",  # Light freezing rain
            67: "🌨️",  # Heavy freezing rain
            71: "🌨️",  # Slight snow fall
            73: "❄️",  # Moderate snow fall
            75: "❄️",  # Heavy snow fall
            77: "❄️",  # Snow grains
            80: "🌦️",  # Slight rain showers
            81: "🌧️",  # Moderate rain showers
            82: "⛈️",  # Violent rain showers
            85: "🌨️",  # Slight snow showers
            86: "❄️",  # Heavy snow showers
            95: "⛈️",  # Thunderstorm
            96: "⛈️",  # Thunderstorm with slight hail
            99: "⛈️"   # Thunderstorm with heavy hail
        }
        
        night_emojis = {
            0: "🌙",  # Clear sky
            1: "🌙",  # Mainly clear
            2: "☁️",  # Partly cloudy
            3: "☁️",  # Overcast
        }
        
        if not is_day and weather_code in night_emojis:
            return night_emojis[weather_code]
        
        return day_emojis.get(weather_code, "🌤️")

    def get_wind_direction(self, degrees: float) -> str:
        """Convert wind direction degrees to compass direction."""
        directions = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
                     "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
        index = round(degrees / 22.5) % 16
        return directions[index]

    async def get_weather_by_location(self, location: str, user_settings: Dict = None) -> Optional[Dict]:
        """Get weather data by location name."""
        if user_settings is None:
            user_settings = {"temperature_unit": "celsius", "wind_speed_unit": "kmh", "precipitation_unit": "mm"}
        
        # Get coordinates from location
        coords = await self.get_coordinates_from_location(location)
        if not coords:
            return None
        
        latitude, longitude, formatted_name = coords
        
        # Get current weather and forecast
        current_weather = await self.get_current_weather(
            latitude, longitude,
            user_settings.get("temperature_unit", "celsius"),
            user_settings.get("wind_speed_unit", "kmh"),
            user_settings.get("precipitation_unit", "mm")
        )
        
        forecast = await self.get_weather_forecast(
            latitude, longitude, 7,
            user_settings.get("temperature_unit", "celsius"),
            user_settings.get("wind_speed_unit", "kmh"),
            user_settings.get("precipitation_unit", "mm")
        )
        
        if current_weather and forecast:
            return {
                "location": formatted_name,
                "latitude": latitude,
                "longitude": longitude,
                "current": current_weather,
                "forecast": forecast
            }
        
        return None

    async def get_weather_by_coordinates(self, latitude: float, longitude: float, user_settings: Dict = None) -> Optional[Dict]:
        """Get weather data by coordinates."""
        if user_settings is None:
            user_settings = {"temperature_unit": "celsius", "wind_speed_unit": "kmh", "precipitation_unit": "mm"}
        
        # Get current weather and forecast
        current_weather = await self.get_current_weather(
            latitude, longitude,
            user_settings.get("temperature_unit", "celsius"),
            user_settings.get("wind_speed_unit", "kmh"),
            user_settings.get("precipitation_unit", "mm")
        )
        
        forecast = await self.get_weather_forecast(
            latitude, longitude, 7,
            user_settings.get("temperature_unit", "celsius"),
            user_settings.get("wind_speed_unit", "kmh"),
            user_settings.get("precipitation_unit", "mm")
        )
        
        if current_weather and forecast:
            return {
                "location": f"{latitude:.4f}, {longitude:.4f}",
                "latitude": latitude,
                "longitude": longitude,
                "current": current_weather,
                "forecast": forecast
            }
        
        return None
