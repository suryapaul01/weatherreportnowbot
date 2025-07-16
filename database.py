import aiosqlite
import datetime
import json
from typing import Dict, List, Optional, Any, Tuple
from config import Config


class Database:
    def __init__(self, db_path: str = Config.DATABASE_URL):
        self.db_path = db_path
        self.conn = None

    async def connect(self):
        """Connect to the SQLite database."""
        self.conn = await aiosqlite.connect(self.db_path)
        self.conn.row_factory = aiosqlite.Row
        await self._create_tables()

    async def close(self):
        """Close the database connection."""
        if self.conn:
            await self.conn.close()

    async def _create_tables(self):
        """Create database tables if they don't exist."""
        async with self.conn.cursor() as cursor:
            # Users table
            await cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                language_code TEXT,
                is_premium BOOLEAN DEFAULT 0,
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                request_count INTEGER DEFAULT 0
            )
            ''')

            # Weather requests table
            await cursor.execute('''
            CREATE TABLE IF NOT EXISTS weather_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                location_name TEXT,
                latitude REAL,
                longitude REAL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
            ''')

            # User settings table
            await cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_settings (
                user_id INTEGER PRIMARY KEY,
                temperature_unit TEXT DEFAULT 'celsius',
                wind_speed_unit TEXT DEFAULT 'kmh',
                precipitation_unit TEXT DEFAULT 'mm',
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
            ''')

            # Donations table
            await cursor.execute('''
            CREATE TABLE IF NOT EXISTS donations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                amount REAL,
                currency TEXT,
                payment_method TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
            ''')

            # Daily stats table
            await cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_stats (
                date TEXT PRIMARY KEY,
                new_users INTEGER DEFAULT 0,
                active_users INTEGER DEFAULT 0,
                total_requests INTEGER DEFAULT 0,
                stats_data TEXT
            )
            ''')

            await self.conn.commit()

    # User methods
    async def add_user(self, user_id: int, username: str = None, first_name: str = None, 
                      last_name: str = None, language_code: str = None, is_premium: bool = False) -> bool:
        """Add a new user or update existing user."""
        try:
            async with self.conn.cursor() as cursor:
                # Check if user exists
                await cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
                user = await cursor.fetchone()
                
                if user:
                    # Update existing user
                    await cursor.execute('''
                    UPDATE users SET 
                        username = COALESCE(?, username),
                        first_name = COALESCE(?, first_name),
                        last_name = COALESCE(?, last_name),
                        language_code = COALESCE(?, language_code),
                        is_premium = COALESCE(?, is_premium),
                        last_activity = CURRENT_TIMESTAMP
                    WHERE user_id = ?
                    ''', (username, first_name, last_name, language_code, is_premium, user_id))
                else:
                    # Add new user
                    await cursor.execute('''
                    INSERT INTO users (user_id, username, first_name, last_name, language_code, is_premium)
                    VALUES (?, ?, ?, ?, ?, ?)
                    ''', (user_id, username, first_name, last_name, language_code, is_premium))
                    
                    # Create default settings for new user
                    await cursor.execute('''
                    INSERT INTO user_settings (user_id) VALUES (?)
                    ''', (user_id,))
                    
                await self.conn.commit()
                return True
        except Exception as e:
            print(f"Error adding/updating user: {e}")
            return False

    async def get_user(self, user_id: int) -> Optional[Dict]:
        """Get user by ID."""
        async with self.conn.cursor() as cursor:
            await cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            user = await cursor.fetchone()
            if user:
                return dict(user)
            return None

    async def increment_request_count(self, user_id: int) -> bool:
        """Increment the request count for a user."""
        try:
            async with self.conn.cursor() as cursor:
                await cursor.execute('''
                UPDATE users SET 
                    request_count = request_count + 1,
                    last_activity = CURRENT_TIMESTAMP
                WHERE user_id = ?
                ''', (user_id,))
                await self.conn.commit()
                return True
        except Exception as e:
            print(f"Error incrementing request count: {e}")
            return False

    # Weather request methods
    async def log_weather_request(self, user_id: int, location_name: str, latitude: float, longitude: float) -> bool:
        """Log a weather request."""
        try:
            async with self.conn.cursor() as cursor:
                await cursor.execute('''
                INSERT INTO weather_requests (user_id, location_name, latitude, longitude)
                VALUES (?, ?, ?, ?)
                ''', (user_id, location_name, latitude, longitude))
                await self.conn.commit()
                return True
        except Exception as e:
            print(f"Error logging weather request: {e}")
            return False

    # User settings methods
    async def get_user_settings(self, user_id: int) -> Dict:
        """Get user settings."""
        async with self.conn.cursor() as cursor:
            await cursor.execute("SELECT * FROM user_settings WHERE user_id = ?", (user_id,))
            settings = await cursor.fetchone()
            if settings:
                return dict(settings)
            return {"temperature_unit": "celsius", "wind_speed_unit": "kmh", "precipitation_unit": "mm"}

    async def update_user_settings(self, user_id: int, settings: Dict) -> bool:
        """Update user settings."""
        try:
            async with self.conn.cursor() as cursor:
                # Build the query dynamically based on provided settings
                query_parts = []
                values = []
                
                for key, value in settings.items():
                    if key in ["temperature_unit", "wind_speed_unit", "precipitation_unit"]:
                        query_parts.append(f"{key} = ?")
                        values.append(value)
                
                if not query_parts:
                    return False
                
                query = f"UPDATE user_settings SET {', '.join(query_parts)} WHERE user_id = ?"
                values.append(user_id)
                
                await cursor.execute(query, values)
                await self.conn.commit()
                return True
        except Exception as e:
            print(f"Error updating user settings: {e}")
            return False

    # Statistics methods
    async def get_user_count(self) -> int:
        """Get total number of users."""
        async with self.conn.cursor() as cursor:
            await cursor.execute("SELECT COUNT(*) as count FROM users")
            result = await cursor.fetchone()
            return result["count"] if result else 0

    async def get_recent_users(self, limit: int = 10) -> List[Dict]:
        """Get recently joined users."""
        async with self.conn.cursor() as cursor:
            await cursor.execute('''
            SELECT user_id, username, first_name, last_name, joined_at 
            FROM users 
            ORDER BY joined_at DESC 
            LIMIT ?
            ''', (limit,))
            users = await cursor.fetchall()
            return [dict(user) for user in users]

    async def get_active_users_count(self, hours: int = 24) -> int:
        """Get count of active users in the last X hours."""
        async with self.conn.cursor() as cursor:
            await cursor.execute('''
            SELECT COUNT(*) as count FROM users 
            WHERE last_activity >= datetime('now', ? || ' hours')
            ''', (f"-{hours}",))
            result = await cursor.fetchone()
            return result["count"] if result else 0

    async def get_request_stats(self, days: int = 7) -> List[Dict]:
        """Get request statistics for the last X days."""
        async with self.conn.cursor() as cursor:
            await cursor.execute('''
            SELECT date(timestamp) as date, COUNT(*) as count 
            FROM weather_requests 
            WHERE timestamp >= datetime('now', ? || ' days') 
            GROUP BY date(timestamp) 
            ORDER BY date
            ''', (f"-{days}",))
            stats = await cursor.fetchall()
            return [dict(stat) for stat in stats]

    # Donation methods
    async def log_donation(self, user_id: int, amount: float, currency: str, payment_method: str) -> bool:
        """Log a donation."""
        try:
            async with self.conn.cursor() as cursor:
                await cursor.execute('''
                INSERT INTO donations (user_id, amount, currency, payment_method)
                VALUES (?, ?, ?, ?)
                ''', (user_id, amount, currency, payment_method))
                await self.conn.commit()
                return True
        except Exception as e:
            print(f"Error logging donation: {e}")
            return False

    async def get_total_donations(self) -> Dict:
        """Get total donations by currency."""
        async with self.conn.cursor() as cursor:
            await cursor.execute('''
            SELECT currency, SUM(amount) as total 
            FROM donations 
            GROUP BY currency
            ''')
            donations = await cursor.fetchall()
            return {d["currency"]: d["total"] for d in donations}

    # Daily stats methods
    async def update_daily_stats(self) -> bool:
        """Update daily statistics."""
        try:
            today = datetime.datetime.now().strftime("%Y-%m-%d")
            new_users = await self._count_new_users_today()
            active_users = await self.get_active_users_count(24)
            total_requests = await self._count_requests_today()
            
            # Additional stats data
            stats_data = {
                "popular_locations": await self._get_popular_locations(),
                "hourly_activity": await self._get_hourly_activity(),
            }
            
            async with self.conn.cursor() as cursor:
                await cursor.execute('''
                INSERT OR REPLACE INTO daily_stats (date, new_users, active_users, total_requests, stats_data)
                VALUES (?, ?, ?, ?, ?)
                ''', (today, new_users, active_users, total_requests, json.dumps(stats_data)))
                await self.conn.commit()
                return True
        except Exception as e:
            print(f"Error updating daily stats: {e}")
            return False

    async def _count_new_users_today(self) -> int:
        """Count new users registered today."""
        async with self.conn.cursor() as cursor:
            await cursor.execute('''
            SELECT COUNT(*) as count FROM users 
            WHERE date(joined_at) = date('now')
            ''')
            result = await cursor.fetchone()
            return result["count"] if result else 0

    async def _count_requests_today(self) -> int:
        """Count weather requests made today."""
        async with self.conn.cursor() as cursor:
            await cursor.execute('''
            SELECT COUNT(*) as count FROM weather_requests 
            WHERE date(timestamp) = date('now')
            ''')
            result = await cursor.fetchone()
            return result["count"] if result else 0

    async def _get_popular_locations(self, limit: int = 5) -> List[Dict]:
        """Get most popular locations in the last 24 hours."""
        async with self.conn.cursor() as cursor:
            await cursor.execute('''
            SELECT location_name, COUNT(*) as count 
            FROM weather_requests 
            WHERE timestamp >= datetime('now', '-24 hours') 
            GROUP BY location_name 
            ORDER BY count DESC 
            LIMIT ?
            ''', (limit,))
            locations = await cursor.fetchall()
            return [dict(loc) for loc in locations]

    async def _get_hourly_activity(self) -> Dict[str, int]:
        """Get hourly activity distribution for the last 24 hours."""
        async with self.conn.cursor() as cursor:
            await cursor.execute('''
            SELECT strftime('%H', timestamp) as hour, COUNT(*) as count 
            FROM weather_requests 
            WHERE timestamp >= datetime('now', '-24 hours') 
            GROUP BY hour 
            ORDER BY hour
            ''')
            hours = await cursor.fetchall()
            return {h["hour"]: h["count"] for h in hours}

    async def get_daily_stats(self, days: int = 30) -> List[Dict]:
        """Get daily stats for the last X days."""
        async with self.conn.cursor() as cursor:
            await cursor.execute('''
            SELECT * FROM daily_stats 
            WHERE date >= date('now', ? || ' days') 
            ORDER BY date
            ''', (f"-{days}",))
            stats = await cursor.fetchall()
            result = []
            for stat in stats:
                stat_dict = dict(stat)
                stat_dict["stats_data"] = json.loads(stat_dict["stats_data"])
                result.append(stat_dict)
            return result
