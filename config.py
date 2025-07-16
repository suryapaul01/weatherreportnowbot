import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    ADMIN_ID = int(os.getenv('ADMIN_ID', 0))
    DATABASE_URL = os.getenv('DATABASE_URL', 'weather_bot.db')
    CACHE_EXPIRE_HOURS = int(os.getenv('CACHE_EXPIRE_HOURS', 1))
    RATE_LIMIT_REQUESTS = int(os.getenv('RATE_LIMIT_REQUESTS', 20))
    RATE_LIMIT_WINDOW_HOURS = int(os.getenv('RATE_LIMIT_WINDOW_HOURS', 24))
    
    # Bot info
    BOT_USERNAME = "@WeatherReportNowBot"
    BOT_NAME = "Weather Report Now Bot"

    # Donation settings
    TON_WALLET = "UQBDqo-7oD872RRk0kD4YbYhDGeO_0fN_b7potiQqqCQ7eDz"  # Replace with actual TON wallet
    
    # Weather API settings
    WEATHER_API_BASE = "https://api.open-meteo.com/v1"
    GEOCODING_API_BASE = "https://geocoding-api.open-meteo.com/v1"
    
    # Messages
    WELCOME_MESSAGE = """
🌤️ Welcome to Weather Report Now Bot!

I can provide you with current weather conditions and forecasts for any location worldwide.

🔹 Send me a city name
🔹 Share your location
🔹 Send GPS coordinates

Use the buttons below to get started!
    """
    
    HELP_MESSAGE = """
🌤️ Weather Report Now Bot Help

Available commands:
/start - Start the bot
/help - Show this help message
/donate - Support the bot development

How to get weather:
• Type a city name (e.g., "New York")
• Share your location using the button
• Send GPS coordinates

Features:
• Current weather conditions
• 7-day forecast
• Location-based weather
• Real-time updates
    """
