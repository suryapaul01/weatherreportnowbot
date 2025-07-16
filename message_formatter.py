from datetime import datetime
from typing import Dict, List
from weather_api import WeatherAPI


class MessageFormatter:
    def __init__(self):
        self.weather_api = WeatherAPI()

    def format_current_weather(self, weather_data: Dict) -> str:
        """Format current weather data into a message."""
        current = weather_data["current"]
        location = weather_data["location"]
        
        # Get weather description and emoji
        weather_code = current["weather_code"]
        is_day = current["is_day"]
        description = self.weather_api.get_weather_description(weather_code, is_day)
        emoji = self.weather_api.get_weather_emoji(weather_code, is_day)
        
        # Get wind direction
        wind_direction = self.weather_api.get_wind_direction(current["wind_direction"])
        
        # Format timestamp with current time (when user requested the data)
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Get units
        units = current["units"]
        
        message = f"""
🌍 <b>{location}</b>

{emoji} <b>{description}</b>

🌡️ <b>Temperature:</b> {current['temperature']}{units['temperature']}
🌡️ <b>Feels like:</b> {current['apparent_temperature']}{units['temperature']}
💧 <b>Humidity:</b> {current['humidity']}{units['humidity']}

💨 <b>Wind:</b> {current['wind_speed']} {units['wind_speed']} {wind_direction}
💨 <b>Gusts:</b> {current['wind_gusts']} {units['wind_speed']}

☁️ <b>Cloud cover:</b> {current['cloud_cover']}%
🌧️ <b>Precipitation:</b> {current['precipitation']} {units['precipitation']}
📊 <b>Pressure:</b> {current['pressure_msl']} {units['pressure']}

🕐 <i>Updated at {timestamp}</i>
        """
        
        return message.strip()

    def format_forecast(self, weather_data: Dict) -> str:
        """Format weather forecast into a message."""
        forecast = weather_data["forecast"]["forecast"]
        location = weather_data["location"]
        units = weather_data["forecast"]["units"]
        
        message = f"📅 <b>7-Day Forecast for {location}</b>\n\n"
        
        for day_data in forecast:
            date = datetime.strptime(day_data["date"], "%Y-%m-%d")
            day_name = date.strftime("%A")
            date_str = date.strftime("%b %d")
            
            weather_code = day_data["weather_code"]
            emoji = self.weather_api.get_weather_emoji(weather_code, True)
            description = self.weather_api.get_weather_description(weather_code, True)
            
            temp_max = day_data["temperature_max"]
            temp_min = day_data["temperature_min"]
            precipitation = day_data["precipitation_sum"]
            wind_speed = day_data["wind_speed_max"]
            wind_direction = self.weather_api.get_wind_direction(day_data["wind_direction"])
            
            message += f"""
{emoji} <b>{day_name}, {date_str}</b>
{description}
🌡️ {temp_min}° - {temp_max}°{units['temperature']}
🌧️ {precipitation} {units['precipitation']}
💨 {wind_speed} {units['wind_speed']} {wind_direction}
🌅 {day_data['sunrise']} 🌇 {day_data['sunset']}

"""
        
        return message.strip()

    def format_forecast_weather(self, forecast_data: Dict) -> str:
        """Format weather forecast data into a message."""
        forecast = forecast_data["forecast"]
        units = forecast_data["units"]

        # Get current time for timestamp
        current_time = datetime.now().strftime("%H:%M:%S")

        message = f"📅 <b>7-Day Weather Forecast</b>\n\n"

        for day_data in forecast:
            date = datetime.strptime(day_data["date"], "%Y-%m-%d")
            day_name = date.strftime("%A")
            date_str = date.strftime("%b %d")

            weather_code = day_data["weather_code"]
            emoji = self.weather_api.get_weather_emoji(weather_code, True)
            description = self.weather_api.get_weather_description(weather_code, True)

            temp_max = day_data["temperature_max"]
            temp_min = day_data["temperature_min"]
            precipitation = day_data["precipitation_sum"]
            wind_speed = day_data["wind_speed_max"]
            wind_direction = self.weather_api.get_wind_direction(day_data["wind_direction"])

            message += f"""
{emoji} <b>{day_name}, {date_str}</b>
{description}
🌡️ {temp_min}° - {temp_max}°{units['temperature']}
🌧️ {precipitation} {units['precipitation']}
💨 {wind_speed} {units['wind_speed']} {wind_direction}
🌅 {day_data['sunrise']} 🌇 {day_data['sunset']}

"""

        message += f"🕐 <i>Updated at {current_time}</i>"

        return message.strip()

    def format_stats_message(self, stats: Dict) -> str:
        """Format statistics into a message."""
        message = f"""
📊 <b>Bot Statistics</b>

👥 <b>Users:</b>
• Total: {stats['total_users']:,}
• Active (24h): {stats['active_24h']:,}
• Active (7d): {stats['active_7d']:,}

📈 <b>Requests:</b>
• Last 7 days: {stats['requests_7d']:,}
• Average per day: {stats['avg_per_day']:,}

📍 <b>Popular Locations (24h):</b>
"""
        
        for i, location in enumerate(stats.get('popular_locations', []), 1):
            message += f"{i}. {location['location_name']} ({location['count']} requests)\n"
        
        message += f"\n🕐 <i>Last updated: {datetime.now().strftime('%H:%M:%S')}</i>"
        
        return message

    def format_users_message(self, users_data: Dict) -> str:
        """Format users list into a message."""
        total_users = users_data['total_users']
        recent_users = users_data['recent_users']
        
        message = f"👥 <b>Users Management</b>\n\nTotal users: {total_users:,}\n\n📋 <b>Recent users:</b>\n\n"
        
        for i, user in enumerate(recent_users, 1):
            username = user.get('username', 'No username')
            first_name = user.get('first_name', 'Unknown')
            joined_date = datetime.fromisoformat(user['joined_at']).strftime('%Y-%m-%d %H:%M')
            
            message += f"{i}. <b>{first_name}</b> (@{username})\n"
            message += f"   <i>Joined: {joined_date}</i>\n\n"
        
        return message

    def format_donation_message(self, donation_type: str) -> str:
        """Format donation message."""
        if donation_type == "stars":
            return """
⭐ <b>Donate with Telegram Stars</b>

Telegram Stars can be converted to TON cryptocurrency and help support the bot development.

Choose an amount to donate:
            """
        elif donation_type == "ton":
            return """
💎 <b>Donate with TON</b>

TON (Toncoin) donations directly support the bot development and server costs.

Choose an amount to donate:
            """
        else:
            return """
💝 <b>Support Weather Report Now Bot</b>

Your donations help keep this bot running and improve its features!

Choose your preferred donation method:

⭐ <b>Telegram Stars</b> - Easy in-app donations
💎 <b>TON</b> - Direct cryptocurrency donations

Thank you for your support! ❤️
            """

    def format_settings_message(self, settings: Dict) -> str:
        """Format settings message."""
        temp_unit = settings.get('temperature_unit', 'celsius').title()
        wind_unit = settings.get('wind_speed_unit', 'kmh').upper()
        precip_unit = settings.get('precipitation_unit', 'mm').upper()
        
        return f"""
⚙️ <b>Settings</b>

Current preferences:
🌡️ <b>Temperature:</b> {temp_unit}
💨 <b>Wind Speed:</b> {wind_unit}
🌧️ <b>Precipitation:</b> {precip_unit}

Tap the buttons below to change your preferences:
        """

    def format_error_message(self, error_type: str, details: str = "") -> str:
        """Format error messages."""
        error_messages = {
            "location_not_found": f"❌ Sorry, I couldn't find weather data for '{details}'. Please check the location name and try again.",
            "api_error": "❌ Weather service is temporarily unavailable. Please try again later.",
            "rate_limit": "⚠️ You've reached your daily limit of 20 weather requests. Please try again tomorrow.",
            "permission_denied": "❌ You don't have permission to use this command.",
            "general_error": "❌ An error occurred. Please try again.",
            "invalid_location": "❌ Please provide a valid location name or share your location.",
            "network_error": "❌ Network error. Please check your connection and try again."
        }
        
        return error_messages.get(error_type, error_messages["general_error"])

    def format_help_message(self) -> str:
        """Format help message."""
        return """
🌤️ <b>Weather Report Now Bot Help</b>

<b>Available commands:</b>
/start - Start the bot
/help - Show this help message
/settings - Change your preferences
/donate - Support the bot development

<b>How to get weather:</b>
• Type a city name (e.g., "New York")
• Share your location using the 📍 button
• Send GPS coordinates

<b>Features:</b>
• Current weather conditions
• 7-day forecast
• Location-based weather
• Real-time updates
• Customizable units

<b>Rate Limits:</b>
• 20 requests per day per user
• Resets every 24 hours

Need more help? Contact @YourSupportUsername
        """

    def format_welcome_message(self, user_name: str) -> str:
        """Format welcome message."""
        return f"""
🌤️ <b>Welcome to Weather Report Now Bot, {user_name}!</b>

I can provide you with current weather conditions and forecasts for any location worldwide.

<b>Quick Start:</b>
🔹 Send me a city name
🔹 Share your location using the 📍 button
🔹 Send GPS coordinates

<b>Features:</b>
• Real-time weather data
• 7-day forecasts
• Location sharing support
• Customizable units
• 20 free requests per day

Use the buttons below to get started!
        """
