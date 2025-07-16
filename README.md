# Weather Report Now Bot

A comprehensive Telegram weather bot that provides current weather conditions and forecasts for any location worldwide.

## Features

- **Current Weather**: Get real-time weather data for any location
- **7-Day Forecast**: View detailed weather forecasts for the upcoming week
- **Location Sharing**: Share your GPS location for precise weather data
- **Multiple Input Formats**: Search by city name, district, or coordinates
- **Customizable Units**: Choose your preferred temperature, wind speed, and precipitation units
- **Admin Dashboard**: Monitor bot usage statistics and user activity
- **Donation System**: Accept Telegram Stars and TON cryptocurrency donations
- **Rate Limiting**: 20 requests per day per user to prevent API abuse
- **Security Features**: Input validation, spam protection, and flood control

## Setup Instructions

### Prerequisites

- Python 3.8 or higher
- Telegram Bot Token (from [@BotFather](https://t.me/BotFather))
- Admin Telegram User ID

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/weather-report-now-bot.git
   cd weather-report-now-bot
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure environment variables:
   - Copy `.env.example` to `.env`
   - Update the values in `.env` with your bot token and admin ID

4. Run the bot:
   ```bash
   python main.py
   ```

### Testing

Run the test suite to verify all components are working correctly:

```bash
python test_bot.py
```

## Bot Commands

- `/start` - Start the bot and get a welcome message
- `/help` - Show help information
- `/settings` - Configure your preferred units
- `/donate` - Support the bot development with donations
- `/stats` - View bot statistics (admin only)
- `/users` - Manage users (admin only)

## Project Structure

- `main.py` - Main entry point for the bot
- `bot.py` - Core bot class with command handlers
- `database.py` - Database operations and schema
- `weather_api.py` - Weather API integration
- `rate_limiter.py` - Request rate limiting
- `security.py` - Security features and validation
- `keyboards.py` - Telegram keyboard layouts
- `message_formatter.py` - Message formatting utilities
- `payment_handler.py` - Donation processing
- `config.py` - Configuration settings
- `test_bot.py` - Test suite

## Weather API

This bot uses the [Open-Meteo API](https://open-meteo.com/) for weather data, which provides:

- Current weather conditions
- 7-day forecasts
- Geocoding for location search
- No API key required for basic usage

## Deployment

### Server Requirements

- 512MB RAM minimum (1GB recommended)
- 10GB disk space
- Python 3.8 or higher
- Internet connectivity

### Deployment Options

1. **VPS/Dedicated Server**:
   - Install dependencies
   - Set up environment variables
   - Run with a process manager like Supervisor or PM2

2. **Docker**:
   - Build the Docker image: `docker build -t weather-bot .`
   - Run the container: `docker run -d --name weather-bot weather-bot`

3. **Heroku**:
   - Push to Heroku: `git push heroku main`
   - Set environment variables in Heroku dashboard

## Donation System

The bot supports two donation methods:

1. **Telegram Stars**: In-app currency that can be converted to TON
2. **TON Cryptocurrency**: Direct cryptocurrency donations

To configure the donation system:

1. Update the TON wallet address in `payment_handler.py`
2. Set up Telegram payment provider token when available

## Admin Dashboard

Access the admin dashboard with these commands:

- `/stats` - View bot statistics and usage metrics
- `/users` - Manage users and see recent registrations

Only the user with the Admin ID specified in the `.env` file can access these commands.

## Rate Limiting

The bot implements rate limiting to prevent API abuse:

- 20 weather requests per day per user
- Resets every 24 hours
- Configurable in `.env` file

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m 'Add some amazing feature'`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) library
- [Open-Meteo](https://open-meteo.com/) for the weather data API
- All contributors and users of the bot
