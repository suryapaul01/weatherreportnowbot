import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from telegram.constants import ParseMode

from config import Config
from database import Database
from weather_api import WeatherAPI
from rate_limiter import RateLimiter
from keyboards import Keyboards
from message_formatter import MessageFormatter
from security import SecurityManager
from payment_handler import PaymentHandler
from health_check import HealthCheckServer


class WeatherBot:
    def __init__(self):
        self.config = Config()
        self.db = Database()
        self.weather_api = WeatherAPI()
        self.rate_limiter = RateLimiter()
        self.keyboards = Keyboards()
        self.formatter = MessageFormatter()
        self.security = SecurityManager()
        self.payment_handler = PaymentHandler(self.db)
        self.health_server = HealthCheckServer()
        
        # Setup logging
        logging.basicConfig(
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            level=logging.INFO
        )
        self.logger = logging.getLogger(__name__)
        
        # Build application
        self.application = Application.builder().token(self.config.BOT_TOKEN).build()
        self._setup_handlers()

    def _setup_handlers(self):
        """Setup command and message handlers."""
        # Command handlers
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("donate", self.donate_command))
        
        # Admin commands
        self.application.add_handler(CommandHandler("stats", self.stats_command))
        self.application.add_handler(CommandHandler("users", self.users_command))
        
        # Message handlers
        self.application.add_handler(MessageHandler(filters.LOCATION, self.location_handler))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.text_handler))
        
        # Callback query handler
        self.application.add_handler(CallbackQueryHandler(self.callback_handler))
        
        # Error handler
        self.application.add_error_handler(self.error_handler)

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command."""
        user = update.effective_user
        
        # Add user to database
        await self.db.add_user(
            user_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            language_code=user.language_code,
            is_premium=user.is_premium
        )
        
        # Send welcome message with keyboard
        keyboard = self.keyboards.get_main_keyboard()
        welcome_message = self.formatter.format_welcome_message(user.first_name or "there")

        await update.message.reply_text(
            welcome_message,
            reply_markup=keyboard,
            parse_mode=ParseMode.HTML
        )

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command."""
        await update.message.reply_text(
            self.config.HELP_MESSAGE,
            parse_mode=ParseMode.HTML
        )

    async def donate_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /donate command."""
        keyboard = self.keyboards.get_donation_keyboard()
        
        message = """
💝 Support Weather Report Now Bot

Your donations help keep this bot running and improve its features!

Choose your preferred donation method:
        """
        
        await update.message.reply_text(
            message,
            reply_markup=keyboard,
            parse_mode=ParseMode.HTML
        )

    async def settings_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /settings command."""
        user_id = update.effective_user.id
        settings = await self.db.get_user_settings(user_id)
        
        keyboard = self.keyboards.get_settings_keyboard(settings)
        
        message = f"""
⚙️ Settings

Current preferences:
🌡️ Temperature: {settings.get('temperature_unit', 'celsius').title()}
💨 Wind Speed: {settings.get('wind_speed_unit', 'kmh').upper()}
🌧️ Precipitation: {settings.get('precipitation_unit', 'mm').upper()}

Tap to change:
        """
        
        await update.message.reply_text(
            message,
            reply_markup=keyboard,
            parse_mode=ParseMode.HTML
        )

    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /stats command (admin only)."""
        user_id = update.effective_user.id
        
        if user_id != self.config.ADMIN_ID:
            await update.message.reply_text("❌ You don't have permission to use this command.")
            return
        
        # Get statistics
        total_users = await self.db.get_user_count()
        active_users_24h = await self.db.get_active_users_count(24)
        active_users_7d = await self.db.get_active_users_count(168)  # 7 days
        
        # Get request stats
        request_stats = await self.db.get_request_stats(7)
        total_requests_7d = sum(stat["count"] for stat in request_stats)
        
        # Update daily stats
        await self.db.update_daily_stats()
        
        keyboard = self.keyboards.get_admin_stats_keyboard()
        
        message = f"""
📊 Bot Statistics

👥 Users:
• Total: {total_users:,}
• Active (24h): {active_users_24h:,}
• Active (7d): {active_users_7d:,}

📈 Requests:
• Last 7 days: {total_requests_7d:,}
• Average per day: {total_requests_7d // 7:,}

🕐 Last updated: {datetime.now().strftime('%H:%M:%S')}
        """
        
        await update.message.reply_text(
            message,
            reply_markup=keyboard,
            parse_mode=ParseMode.HTML
        )

    async def users_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /users command (admin only)."""
        user_id = update.effective_user.id
        
        if user_id != self.config.ADMIN_ID:
            await update.message.reply_text("❌ You don't have permission to use this command.")
            return
        
        # Get recent users
        recent_users = await self.db.get_recent_users(10)
        total_users = await self.db.get_user_count()
        
        keyboard = self.keyboards.get_admin_users_keyboard()
        
        message = f"👥 Users Management\n\nTotal users: {total_users:,}\n\n📋 Recent users:\n"
        
        for i, user in enumerate(recent_users, 1):
            username = user.get('username', 'No username')
            first_name = user.get('first_name', 'Unknown')
            joined_date = datetime.fromisoformat(user['joined_at']).strftime('%Y-%m-%d %H:%M')
            
            message += f"{i}. {first_name} (@{username})\n   Joined: {joined_date}\n\n"
        
        await update.message.reply_text(
            message,
            reply_markup=keyboard,
            parse_mode=ParseMode.HTML
        )

    async def location_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle location messages."""
        user_id = update.effective_user.id
        location = update.message.location

        # Check security permissions
        if not await self.security.check_user_permissions(user_id, "location_message"):
            await update.message.reply_text(
                "⚠️ Access denied. Please try again later or contact support if you believe this is an error."
            )
            return

        # Validate coordinates
        if not await self.security.validate_coordinates(location.latitude, location.longitude):
            await update.message.reply_text(
                "❌ Invalid location coordinates. Please try sharing your location again."
            )
            return

        # Check rate limit
        if not await self.rate_limiter.check_rate_limit(user_id):
            await update.message.reply_text(
                "⚠️ You've reached your daily limit of 20 weather requests. Please try again tomorrow."
            )
            return

        # Send "typing" action
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        
        try:
            # Get user settings
            user_settings = await self.db.get_user_settings(user_id)
            
            # Get weather data
            weather_data = await self.weather_api.get_weather_by_coordinates(
                location.latitude, location.longitude, user_settings
            )
            
            if weather_data:
                # Log the request
                await self.db.log_weather_request(
                    user_id, weather_data["location"], 
                    location.latitude, location.longitude
                )
                await self.db.increment_request_count(user_id)
                
                # Format and send weather message
                message = self.formatter.format_current_weather(weather_data)
                keyboard = self.keyboards.get_weather_keyboard(
                    location.latitude, location.longitude
                )
                
                await update.message.reply_text(
                    message,
                    reply_markup=keyboard,
                    parse_mode=ParseMode.HTML
                )
            else:
                await update.message.reply_text(
                    "❌ Sorry, I couldn't get weather data for your location. Please try again later."
                )
                
        except Exception as e:
            self.logger.error(f"Error handling location: {e}")
            await update.message.reply_text(
                "❌ An error occurred while getting weather data. Please try again."
            )

    async def text_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle text messages (location names and keyboard buttons)."""
        user_id = update.effective_user.id
        text = update.message.text.strip()

        # Check security permissions
        if not await self.security.check_user_permissions(user_id, "text_message"):
            await update.message.reply_text(
                "⚠️ Access denied. Please try again later or contact support if you believe this is an error."
            )
            return

        # Handle keyboard button presses
        if text == "💝 Donate":
            await self.donate_command(update, context)
            return
        elif text == "ℹ️ Help":
            await self.help_command(update, context)
            return

        # Handle location search
        # Check rate limit
        if not await self.rate_limiter.check_rate_limit(user_id):
            await update.message.reply_text(
                "⚠️ You've reached your daily limit of 20 weather requests. Please try again tomorrow."
            )
            return

        # Sanitize and validate input
        sanitized_text = await self.security.sanitize_input(text)
        if not await self.security.validate_location_input(sanitized_text):
            await update.message.reply_text(
                "❌ Invalid location format. Please enter a valid city or location name."
            )
            return

        # Send "typing" action
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

        try:
            # Get user settings
            user_settings = await self.db.get_user_settings(user_id)

            # Get weather data
            weather_data = await self.weather_api.get_weather_by_location(sanitized_text, user_settings)

            if weather_data:
                # Log the request
                await self.db.log_weather_request(
                    user_id, weather_data["location"],
                    weather_data["latitude"], weather_data["longitude"]
                )
                await self.db.increment_request_count(user_id)

                # Format and send weather message
                message = self.formatter.format_current_weather(weather_data)
                keyboard = self.keyboards.get_weather_keyboard(
                    weather_data["latitude"], weather_data["longitude"]
                )

                await update.message.reply_text(
                    message,
                    reply_markup=keyboard,
                    parse_mode=ParseMode.HTML
                )
            else:
                await update.message.reply_text(
                    f"❌ Sorry, I couldn't find weather data for '{sanitized_text}'. Please check the location name and try again."
                )

        except Exception as e:
            self.logger.error(f"Error handling text: {e}")
            await update.message.reply_text(
                "❌ An error occurred while getting weather data. Please try again."
            )

    async def callback_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle callback queries from inline keyboards."""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        user_id = update.effective_user.id
        
        try:
            if data.startswith("refresh_"):
                await self._handle_refresh_callback(query, context)
            elif data.startswith("forecast_"):
                await self._handle_forecast_callback(query, context)
            elif data.startswith("current_"):
                await self._handle_current_callback(query, context)
            elif data.startswith("settings_"):
                await self._handle_settings_callback(query, context)
            elif data.startswith("donate_") or data.startswith("stars_") or data.startswith("ton_") or data in ["back_to_donate", "back_to_menu"]:
                await self._handle_donation_callback(query, context)
            elif data.startswith("admin_"):
                await self._handle_admin_callback(query, context)
                
        except Exception as e:
            self.logger.error(f"Error handling callback: {e}")
            await query.edit_message_text("❌ An error occurred. Please try again.")

    async def _handle_refresh_callback(self, query, context):
        """Handle weather refresh callbacks."""
        try:
            # Extract coordinates from callback data
            parts = query.data.split("_")
            if len(parts) >= 3:
                latitude = float(parts[1])
                longitude = float(parts[2])
            else:
                await query.answer("❌ Invalid refresh data", show_alert=True)
                return

            user_id = query.from_user.id

            # Check rate limit
            if not await self.rate_limiter.check_rate_limit(user_id):
                await query.answer("⚠️ You've reached your daily limit of 20 weather requests. Please try again tomorrow.", show_alert=True)
                return

            # Get user settings and weather data
            user_settings = await self.db.get_user_settings(user_id)
            weather_data = await self.weather_api.get_weather_by_coordinates(
                latitude, longitude, user_settings
            )

            if weather_data:
                await self.db.increment_request_count(user_id)

                message = self.formatter.format_current_weather(weather_data)
                keyboard = self.keyboards.get_weather_keyboard(latitude, longitude)

                try:
                    await query.edit_message_text(
                        message,
                        reply_markup=keyboard,
                        parse_mode=ParseMode.HTML
                    )
                except Exception as e:
                    if "not modified" in str(e).lower():
                        await query.answer("Weather data is already up to date! 🌤️")
                    else:
                        await query.answer("❌ Error refreshing weather data")
            else:
                await query.answer("❌ Sorry, I couldn't refresh the weather data. Please try again later.", show_alert=True)

        except Exception as e:
            self.logger.error(f"Error in refresh callback: {e}")
            await query.answer("❌ An error occurred while refreshing", show_alert=True)

    async def _handle_current_callback(self, query, context):
        """Handle current weather callbacks (back to current weather from forecast)."""
        try:
            # Extract coordinates from callback data
            parts = query.data.split("_")
            if len(parts) >= 3:
                latitude = float(parts[1])
                longitude = float(parts[2])
            else:
                await query.answer("❌ Invalid data", show_alert=True)
                return

            user_id = query.from_user.id

            # Check rate limit
            if not await self.rate_limiter.check_rate_limit(user_id):
                await query.answer("⚠️ You've reached your daily limit of 20 weather requests. Please try again tomorrow.", show_alert=True)
                return

            # Get user settings and weather data
            user_settings = await self.db.get_user_settings(user_id)
            weather_data = await self.weather_api.get_weather_by_coordinates(
                latitude, longitude, user_settings
            )

            if weather_data:
                await self.db.increment_request_count(user_id)

                message = self.formatter.format_current_weather(weather_data)
                keyboard = self.keyboards.get_weather_keyboard(latitude, longitude)

                try:
                    await query.edit_message_text(
                        message,
                        reply_markup=keyboard,
                        parse_mode=ParseMode.HTML
                    )
                except Exception as e:
                    if "not modified" in str(e).lower():
                        await query.answer("Already showing current weather! 🌤️")
                    else:
                        await query.answer("❌ Error loading current weather")
            else:
                await query.answer("❌ Sorry, I couldn't load the weather data. Please try again later.", show_alert=True)

        except Exception as e:
            self.logger.error(f"Error in current callback: {e}")
            await query.answer("❌ An error occurred", show_alert=True)

    async def _handle_forecast_callback(self, query, context):
        """Handle forecast callbacks."""
        try:
            # Extract coordinates from callback data
            parts = query.data.split("_")
            if len(parts) >= 3:
                latitude = float(parts[1])
                longitude = float(parts[2])
            else:
                await query.answer("❌ Invalid forecast data", show_alert=True)
                return

            user_id = query.from_user.id

            # Check rate limit
            if not await self.rate_limiter.check_rate_limit(user_id):
                await query.answer("⚠️ You've reached your daily limit of 20 weather requests. Please try again tomorrow.", show_alert=True)
                return

            # Get user settings and forecast data
            user_settings = await self.db.get_user_settings(user_id)
            forecast_data = await self.weather_api.get_weather_forecast(
                latitude, longitude, 7,
                user_settings.get("temperature_unit", "celsius"),
                user_settings.get("wind_speed_unit", "kmh"),
                user_settings.get("precipitation_unit", "mm")
            )

            if forecast_data:
                await self.db.increment_request_count(user_id)

                message = self.formatter.format_forecast_weather(forecast_data)
                keyboard = self.keyboards.get_forecast_keyboard(latitude, longitude)

                try:
                    await query.edit_message_text(
                        message,
                        reply_markup=keyboard,
                        parse_mode=ParseMode.HTML
                    )
                except Exception as e:
                    if "not modified" in str(e).lower():
                        await query.answer("Forecast data is already up to date! 📅")
                    else:
                        await query.answer("❌ Error refreshing forecast")
            else:
                await query.answer("❌ Sorry, I couldn't get forecast data. Please try again later.", show_alert=True)

        except Exception as e:
            self.logger.error(f"Error in forecast callback: {e}")
            await query.answer("❌ An error occurred while loading forecast", show_alert=True)

    async def _handle_settings_callback(self, query, context):
        """Handle settings callbacks."""
        data = query.data
        user_id = query.from_user.id

        if data == "settings_back":
            # Show main settings menu
            settings = await self.db.get_user_settings(user_id)
            message = self.formatter.format_settings_message(settings)
            keyboard = self.keyboards.get_settings_keyboard(settings)

            await query.edit_message_text(
                message,
                reply_markup=keyboard,
                parse_mode=ParseMode.HTML
            )
        elif data.startswith("settings_temp_"):
            # Handle temperature unit change
            unit = data.split("_")[-1]
            if unit in ["celsius", "fahrenheit"]:
                await self.db.update_user_settings(user_id, {"temperature_unit": unit})

                settings = await self.db.get_user_settings(user_id)
                message = self.formatter.format_settings_message(settings)
                keyboard = self.keyboards.get_settings_keyboard(settings)

                await query.edit_message_text(
                    message,
                    reply_markup=keyboard,
                    parse_mode=ParseMode.HTML
                )
        elif data.startswith("settings_wind_"):
            # Handle wind unit change
            unit = data.split("_")[-1]
            if unit in ["kmh", "mph", "ms", "kn"]:
                await self.db.update_user_settings(user_id, {"wind_speed_unit": unit})

                settings = await self.db.get_user_settings(user_id)
                message = self.formatter.format_settings_message(settings)
                keyboard = self.keyboards.get_settings_keyboard(settings)

                await query.edit_message_text(
                    message,
                    reply_markup=keyboard,
                    parse_mode=ParseMode.HTML
                )
        elif data.startswith("settings_precip_"):
            # Handle precipitation unit change
            unit = data.split("_")[-1]
            if unit in ["mm", "inch"]:
                await self.db.update_user_settings(user_id, {"precipitation_unit": unit})

                settings = await self.db.get_user_settings(user_id)
                message = self.formatter.format_settings_message(settings)
                keyboard = self.keyboards.get_settings_keyboard(settings)

                await query.edit_message_text(
                    message,
                    reply_markup=keyboard,
                    parse_mode=ParseMode.HTML
                )

    async def _handle_donation_callback(self, query, context):
        """Handle donation callbacks."""
        try:
            data = query.data
            user_id = query.from_user.id
            user_name = query.from_user.first_name or "Friend"

            if data == "donate_main" or data == "back_to_donate":
                message = self.formatter.format_donation_message("main")
                keyboard = self.keyboards.get_donation_keyboard()

                await query.edit_message_text(
                    message,
                    reply_markup=keyboard,
                    parse_mode=ParseMode.HTML
                )

            elif data == "donate_stars":
                message = self.formatter.format_donation_message("stars")
                keyboard = self.keyboards.get_stars_donation_keyboard()

                await query.edit_message_text(
                    message,
                    reply_markup=keyboard,
                    parse_mode=ParseMode.HTML
                )

            elif data == "donate_ton":
                message = self.formatter.format_donation_message("ton")
                keyboard = self.keyboards.get_ton_donation_keyboard()

                await query.edit_message_text(
                    message,
                    reply_markup=keyboard,
                    parse_mode=ParseMode.HTML
                )

            elif data.startswith("stars_"):
                amount = int(data.split("_")[1])
                await self._process_stars_donation(query, amount, user_name)

            elif data.startswith("ton_"):
                amount = float(data.split("_")[1])
                await self._process_ton_donation(query, amount, user_name)

            elif data == "back_to_menu":
                # Go back to main menu
                keyboard = self.keyboards.get_main_keyboard()
                welcome_message = self.formatter.format_welcome_message(user_name)

                await query.edit_message_text(
                    welcome_message,
                    reply_markup=None,
                    parse_mode=ParseMode.HTML
                )

                # Send new message with keyboard
                await context.bot.send_message(
                    chat_id=query.message.chat_id,
                    text="🏠 <b>Main Menu</b>\n\nChoose an option below:",
                    reply_markup=keyboard,
                    parse_mode=ParseMode.HTML
                )

        except Exception as e:
            self.logger.error(f"Error in donation callback: {e}")
            await query.answer("❌ An error occurred", show_alert=True)

    async def _handle_admin_callback(self, query, context):
        """Handle admin callbacks."""
        try:
            data = query.data
            user_id = query.from_user.id

            # Check admin permission
            if user_id != self.config.ADMIN_ID:
                await query.answer("❌ Access denied", show_alert=True)
                return

            if data == "admin_refresh_stats":
                # Check if we're in detailed analytics mode by looking at the current message
                current_text = query.message.text or ""
                if "Last 30 days:" in current_text or "Detailed Analytics" in current_text:
                    # We're in detailed analytics, refresh that
                    await self._show_detailed_analytics(query)
                else:
                    # We're in main stats, refresh main stats
                    await self._show_stats_dashboard(query)

            elif data == "admin_view_users" or data == "admin_refresh_users":
                # Show users list
                recent_users = await self.db.get_recent_users(10)
                total_users = await self.db.get_user_count()

                users_data = {
                    'total_users': total_users,
                    'recent_users': recent_users
                }

                message = self.formatter.format_users_message(users_data)
                keyboard = self.keyboards.get_admin_users_keyboard()

                try:
                    await query.edit_message_text(
                        message,
                        reply_markup=keyboard,
                        parse_mode=ParseMode.HTML
                    )
                except Exception as e:
                    if "not modified" in str(e).lower():
                        await query.answer("User list is already up to date! 👥")
                    else:
                        await query.answer("❌ Error refreshing user list")

            elif data == "admin_analytics":
                # Show detailed analytics
                await self._show_detailed_analytics(query)

            elif data == "admin_back_stats":
                # Go back to stats - call refresh stats
                await self._show_stats_dashboard(query)

        except Exception as e:
            self.logger.error(f"Error in admin callback: {e}")
            await query.answer("❌ An error occurred", show_alert=True)

    async def _show_detailed_analytics(self, query):
        """Show detailed analytics."""
        try:
            # Get comprehensive analytics
            total_users = await self.db.get_user_count()
            active_users_24h = await self.db.get_active_users_count(24)
            active_users_7d = await self.db.get_active_users_count(168)

            request_stats = await self.db.get_request_stats(30)  # Last 30 days
            total_requests_30d = sum(stat["count"] for stat in request_stats)

            popular_locations = await self.db._get_popular_locations(10)

            message = f"""
📊 <b>Detailed Analytics</b>

👥 <b>User Statistics:</b>
• Total Users: {total_users:,}
• Active (24h): {active_users_24h:,}
• Active (7d): {active_users_7d:,}
• Active (30d): {await self.db.get_active_users_count(720):,}

📈 <b>Request Statistics:</b>
• Last 30 days: {total_requests_30d:,}
• Daily average: {total_requests_30d // 30 if total_requests_30d > 0 else 0:,}
• Peak day: {max([stat["count"] for stat in request_stats]) if request_stats else 0:,}

📍 <b>Popular Locations (Top 10):</b>
"""

            for i, location in enumerate(popular_locations[:10], 1):
                message += f"{i}. {location['location_name']} ({location['count']} requests)\n"

            if not popular_locations:
                message += "No location data available yet.\n"

            message += f"\n🕐 <i>Generated: {datetime.now().strftime('%H:%M:%S')}</i>"

            keyboard = self.keyboards.get_admin_stats_keyboard()

            await query.edit_message_text(
                message,
                reply_markup=keyboard,
                parse_mode=ParseMode.HTML
            )

        except Exception as e:
            self.logger.error(f"Error showing detailed analytics: {e}")
            await query.answer("❌ Error loading analytics", show_alert=True)

    async def _show_stats_dashboard(self, query):
        """Show main stats dashboard."""
        try:
            # Get statistics
            total_users = await self.db.get_user_count()
            active_users_24h = await self.db.get_active_users_count(24)
            active_users_7d = await self.db.get_active_users_count(168)

            request_stats = await self.db.get_request_stats(7)
            total_requests_7d = sum(stat["count"] for stat in request_stats)

            await self.db.update_daily_stats()

            stats_data = {
                'total_users': total_users,
                'active_24h': active_users_24h,
                'active_7d': active_users_7d,
                'requests_7d': total_requests_7d,
                'avg_per_day': total_requests_7d // 7 if total_requests_7d > 0 else 0,
                'popular_locations': await self.db._get_popular_locations()
            }

            message = self.formatter.format_stats_message(stats_data)
            keyboard = self.keyboards.get_admin_stats_keyboard()

            await query.edit_message_text(
                message,
                reply_markup=keyboard,
                parse_mode=ParseMode.HTML
            )

        except Exception as e:
            self.logger.error(f"Error showing stats dashboard: {e}")
            await query.answer("❌ Error loading stats", show_alert=True)

    async def _process_stars_donation(self, query, amount: int, user_name: str):
        """Process Stars donation."""
        try:
            # For now, show success message since Stars API is not fully available
            # When Stars API is available, uncomment the invoice code below

            # Create Stars invoice (when API is available)
            # from telegram import LabeledPrice
            # prices = [LabeledPrice(f"{amount} Telegram Stars", amount)]
            # await query.message.reply_invoice(
            #     title=f"Donate {amount} ⭐ Stars",
            #     description=f"Support Weather Report Now Bot with {amount} Telegram Stars",
            #     payload=f"stars_donation_{amount}_{query.from_user.id}",
            #     provider_token="",  # Empty for Stars
            #     currency="XTR",  # Telegram Stars currency
            #     prices=prices,
            #     start_parameter="stars_donation"
            # )

            # Show success message
            success_message = f"""
🎉 <b>Donation Successful!</b> 🎉

💖 Thank you so much, {user_name}! Your generous donation of {amount} ⭐ stars means the world to us!

🚀 <b>Your contribution helps us:</b>
• Keep the bot running 24/7
• Add new amazing features
• Provide faster and better service
• Support our development team

🌟 You're now part of our amazing supporter community! We're incredibly grateful for your kindness and support.

💝 <b>With heartfelt thanks,</b>
The Weather Report Now Team ❤️

🏠 <b>You're back to the main menu - ready to check more weather!</b>
            """

            keyboard = self.keyboards.get_main_keyboard()

            await query.edit_message_text(
                success_message,
                reply_markup=None,
                parse_mode=ParseMode.HTML
            )

            # Log the donation
            await self.db.log_donation(query.from_user.id, amount, "STARS", "telegram_stars")

        except Exception as e:
            self.logger.error(f"Error processing Stars donation: {e}")
            # Fallback message
            await query.edit_message_text(
                f"⭐ <b>Stars Donation: {amount} ⭐</b>\n\n"
                f"Thank you for wanting to donate {amount} Stars!\n\n"
                f"💖 Your support means everything to us!\n\n"
                f"<i>Note: Stars payment processing will be fully implemented when Telegram's Stars API becomes available.</i>",
                parse_mode=ParseMode.HTML
            )

    async def _process_ton_donation(self, query, amount: float, user_name: str):
        """Process TON donation."""
        try:
            ton_wallet = self.config.TON_WALLET
            amount_nanotons = int(amount * 1000000000)  # Convert to nanotons

            # Create TON payment link
            ton_payment_link = f"https://app.tonkeeper.com/transfer/{ton_wallet}?amount={amount_nanotons}&text=Donation%20to%20WeatherReportNow%20Bot"

            message = f"""
💎 <b>TON Donation: {amount} TON</b>

Thank you for choosing to donate {amount} TON!

<b>Payment Instructions:</b>
1. Click the link below to open TON Keeper
2. Confirm the transaction
3. Your donation will be processed automatically

🔗 <b>Payment Link:</b>
<a href="{ton_payment_link}">Pay {amount} TON</a>

💝 <b>Alternative:</b>
Send {amount} TON directly to:
<code>{ton_wallet}</code>

🙏 <b>Thank you for your generous support!</b>
Your donation helps keep our weather bot running 24/7!

❤️ <b>With gratitude,</b>
The Weather Report Now Team
            """

            # Create keyboard with payment link
            from telegram import InlineKeyboardButton, InlineKeyboardMarkup
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton(f"💎 Pay {amount} TON", url=ton_payment_link)],
                [InlineKeyboardButton("🔙 Back to Donations", callback_data="back_to_donate")]
            ])

            await query.edit_message_text(
                message,
                reply_markup=keyboard,
                parse_mode=ParseMode.HTML
            )

            # Log the donation intent
            await self.db.log_donation(query.from_user.id, amount, "TON", "ton_wallet")

        except Exception as e:
            self.logger.error(f"Error processing TON donation: {e}")
            await query.answer("❌ Error processing TON donation", show_alert=True)

    async def error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE):
        """Handle errors."""
        self.logger.error(f"Exception while handling an update: {context.error}")

    def run(self):
        """Run the bot."""
        import asyncio

        async def setup(application):
            # Connect to database
            await self.db.connect()
            # Start health check server
            self.health_server.start()
            self.logger.info("Bot started successfully!")

        async def cleanup(application):
            # Cleanup
            self.health_server.stop()
            await self.db.close()
            self.logger.info("Bot stopped")

        # Set up the application with proper lifecycle
        self.application.post_init = setup
        self.application.post_shutdown = cleanup

        # Run the bot with polling
        self.application.run_polling()

    def stop(self):
        """Stop the bot."""
        self.health_server.stop()


if __name__ == "__main__":
    bot = WeatherBot()
    asyncio.run(bot.run())
