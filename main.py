#!/usr/bin/env python3
"""
Weather Report Now Bot - Main Entry Point

A comprehensive Telegram bot that provides weather information using Open-Meteo API.
Features include current weather, forecasts, location sharing, admin dashboard, and donations.

Author: Weather Bot Team
Version: 1.0.0
"""

import logging
import sys
from bot import WeatherBot


def setup_logging():
    """Setup logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('weather_bot.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )


def main():
    """Main function to run the bot."""
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)

    logger.info("Starting Weather Report Now Bot...")

    # Create and run bot
    bot = WeatherBot()

    try:
        bot.run()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot crashed with error: {e}")
        raise
    finally:
        logger.info("Cleaning up...")
        bot.stop()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nBot stopped by user")
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)
