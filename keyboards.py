from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from typing import Dict, List


class Keyboards:
    def __init__(self):
        pass

    def get_main_keyboard(self) -> ReplyKeyboardMarkup:
        """Get the main reply keyboard with location sharing."""
        keyboard = [
            [KeyboardButton("📍 Share Location", request_location=True)],
            [KeyboardButton("💝 Donate"), KeyboardButton("ℹ️ Help")]
        ]

        return ReplyKeyboardMarkup(
            keyboard,
            resize_keyboard=True,
            one_time_keyboard=False,
            input_field_placeholder="Type a city name or share your location..."
        )

    def get_weather_keyboard(self, latitude: float, longitude: float) -> InlineKeyboardMarkup:
        """Get inline keyboard for weather messages."""
        keyboard = [
            [
                InlineKeyboardButton("🔄 Refresh", callback_data=f"refresh_{latitude}_{longitude}"),
                InlineKeyboardButton("📅 7-Day Forecast", callback_data=f"forecast_{latitude}_{longitude}")
            ],
            [
                InlineKeyboardButton("💝 Donate", callback_data="donate_main"),
                InlineKeyboardButton("🏠 Main Menu", callback_data="back_to_menu")
            ]
        ]

        return InlineKeyboardMarkup(keyboard)

    def get_settings_keyboard(self, current_settings: Dict) -> InlineKeyboardMarkup:
        """Get settings keyboard."""
        temp_unit = current_settings.get('temperature_unit', 'celsius')
        wind_unit = current_settings.get('wind_speed_unit', 'kmh')
        precip_unit = current_settings.get('precipitation_unit', 'mm')
        
        keyboard = [
            [
                InlineKeyboardButton(
                    f"🌡️ Temperature: {temp_unit.title()}", 
                    callback_data=f"settings_temp_{temp_unit}"
                )
            ],
            [
                InlineKeyboardButton(
                    f"💨 Wind: {wind_unit.upper()}", 
                    callback_data=f"settings_wind_{wind_unit}"
                )
            ],
            [
                InlineKeyboardButton(
                    f"🌧️ Precipitation: {precip_unit.upper()}", 
                    callback_data=f"settings_precip_{precip_unit}"
                )
            ]
        ]
        
        return InlineKeyboardMarkup(keyboard)

    def get_donation_keyboard(self) -> InlineKeyboardMarkup:
        """Get donation keyboard."""
        keyboard = [
            [
                InlineKeyboardButton("⭐ Telegram Stars", callback_data="donate_stars"),
                InlineKeyboardButton("💎 TON Crypto", callback_data="donate_ton")
            ],
            [
                InlineKeyboardButton("🔙 Back", callback_data="back_to_menu")
            ]
        ]

        return InlineKeyboardMarkup(keyboard)

    def get_admin_stats_keyboard(self) -> InlineKeyboardMarkup:
        """Get admin statistics keyboard."""
        keyboard = [
            [
                InlineKeyboardButton("🔄 Refresh Stats", callback_data="admin_refresh_stats"),
                InlineKeyboardButton("👥 View Users", callback_data="admin_view_users")
            ],
            [
                InlineKeyboardButton("📊 Detailed Analytics", callback_data="admin_analytics")
            ],
            [
                InlineKeyboardButton("🏠 Main Menu", callback_data="back_to_menu")
            ]
        ]

        return InlineKeyboardMarkup(keyboard)

    def get_admin_users_keyboard(self) -> InlineKeyboardMarkup:
        """Get admin users management keyboard."""
        keyboard = [
            [
                InlineKeyboardButton("🔄 Refresh Users", callback_data="admin_refresh_users"),
                InlineKeyboardButton("📊 Back to Stats", callback_data="admin_back_stats")
            ],
            [
                InlineKeyboardButton("🏠 Main Menu", callback_data="back_to_menu")
            ]
        ]

        return InlineKeyboardMarkup(keyboard)

    def get_forecast_keyboard(self, latitude: float, longitude: float) -> InlineKeyboardMarkup:
        """Get forecast keyboard."""
        keyboard = [
            [
                InlineKeyboardButton("🔄 Refresh Forecast", callback_data=f"forecast_{latitude}_{longitude}"),
                InlineKeyboardButton("🌤️ Current Weather", callback_data=f"current_{latitude}_{longitude}")
            ],
            [
                InlineKeyboardButton("💝 Donate", callback_data="donate_main"),
                InlineKeyboardButton("🏠 Main Menu", callback_data="back_to_menu")
            ]
        ]

        return InlineKeyboardMarkup(keyboard)

    def get_stars_donation_keyboard(self) -> InlineKeyboardMarkup:
        """Get Stars donation amounts keyboard."""
        keyboard = [
            [
                InlineKeyboardButton("1 ⭐", callback_data="stars_1"),
                InlineKeyboardButton("5 ⭐", callback_data="stars_5"),
                InlineKeyboardButton("10 ⭐", callback_data="stars_10")
            ],
            [
                InlineKeyboardButton("20 ⭐", callback_data="stars_20"),
                InlineKeyboardButton("50 ⭐", callback_data="stars_50"),
                InlineKeyboardButton("100 ⭐", callback_data="stars_100")
            ],
            [
                InlineKeyboardButton("500 ⭐", callback_data="stars_500"),
                InlineKeyboardButton("1000 ⭐", callback_data="stars_1000")
            ],
            [
                InlineKeyboardButton("🔙 Back", callback_data="back_to_donate")
            ]
        ]

        return InlineKeyboardMarkup(keyboard)

    def get_ton_donation_keyboard(self) -> InlineKeyboardMarkup:
        """Get TON donation keyboard."""
        keyboard = [
            [
                InlineKeyboardButton("0.1 TON", callback_data="ton_0.1"),
                InlineKeyboardButton("0.2 TON", callback_data="ton_0.2"),
                InlineKeyboardButton("0.5 TON", callback_data="ton_0.5")
            ],
            [
                InlineKeyboardButton("1 TON", callback_data="ton_1"),
                InlineKeyboardButton("2 TON", callback_data="ton_2")
            ],
            [
                InlineKeyboardButton("5 TON", callback_data="ton_5"),
                InlineKeyboardButton("10 TON", callback_data="ton_10")
            ],
            [
                InlineKeyboardButton("🔙 Back", callback_data="back_to_donate")
            ]
        ]

        return InlineKeyboardMarkup(keyboard)

    def get_temperature_unit_keyboard(self) -> InlineKeyboardMarkup:
        """Get temperature unit selection keyboard."""
        keyboard = [
            [
                InlineKeyboardButton("🌡️ Celsius (°C)", callback_data="settings_temp_celsius"),
                InlineKeyboardButton("🌡️ Fahrenheit (°F)", callback_data="settings_temp_fahrenheit")
            ],
            [
                InlineKeyboardButton("⬅️ Back to Settings", callback_data="settings_back")
            ]
        ]
        
        return InlineKeyboardMarkup(keyboard)

    def get_wind_unit_keyboard(self) -> InlineKeyboardMarkup:
        """Get wind speed unit selection keyboard."""
        keyboard = [
            [
                InlineKeyboardButton("💨 km/h", callback_data="settings_wind_kmh"),
                InlineKeyboardButton("💨 mph", callback_data="settings_wind_mph")
            ],
            [
                InlineKeyboardButton("💨 m/s", callback_data="settings_wind_ms"),
                InlineKeyboardButton("💨 knots", callback_data="settings_wind_kn")
            ],
            [
                InlineKeyboardButton("⬅️ Back to Settings", callback_data="settings_back")
            ]
        ]
        
        return InlineKeyboardMarkup(keyboard)

    def get_precipitation_unit_keyboard(self) -> InlineKeyboardMarkup:
        """Get precipitation unit selection keyboard."""
        keyboard = [
            [
                InlineKeyboardButton("🌧️ mm", callback_data="settings_precip_mm"),
                InlineKeyboardButton("🌧️ inch", callback_data="settings_precip_inch")
            ],
            [
                InlineKeyboardButton("⬅️ Back to Settings", callback_data="settings_back")
            ]
        ]
        
        return InlineKeyboardMarkup(keyboard)
