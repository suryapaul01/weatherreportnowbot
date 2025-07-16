#!/usr/bin/env python3
"""
Health check server for Weather Report Now Bot

This provides a simple HTTP endpoint for monitoring the bot's health.
"""

import asyncio
import json
import logging
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import os
import sqlite3
from config import Config


class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Handle GET requests."""
        if self.path == '/health':
            self.handle_health_check()
        elif self.path == '/status':
            self.handle_status_check()
        else:
            self.send_error(404, "Not Found")

    def handle_health_check(self):
        """Handle basic health check."""
        try:
            # Check if database file exists and is accessible
            config = Config()
            db_path = config.DATABASE_URL
            
            if os.path.exists(db_path):
                # Try to connect to database
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM users")
                user_count = cursor.fetchone()[0]
                conn.close()
                
                response = {
                    "status": "healthy",
                    "timestamp": datetime.now().isoformat(),
                    "database": "connected",
                    "user_count": user_count
                }
                status_code = 200
            else:
                response = {
                    "status": "unhealthy",
                    "timestamp": datetime.now().isoformat(),
                    "database": "not_found",
                    "error": "Database file not found"
                }
                status_code = 503
                
        except Exception as e:
            response = {
                "status": "unhealthy",
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }
            status_code = 503
        
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(response, indent=2).encode())

    def handle_status_check(self):
        """Handle detailed status check."""
        try:
            config = Config()
            db_path = config.DATABASE_URL
            
            # Database stats
            db_stats = {"status": "disconnected"}
            if os.path.exists(db_path):
                try:
                    conn = sqlite3.connect(db_path)
                    cursor = conn.cursor()
                    
                    # Get user count
                    cursor.execute("SELECT COUNT(*) FROM users")
                    user_count = cursor.fetchone()[0]
                    
                    # Get recent activity
                    cursor.execute("""
                        SELECT COUNT(*) FROM weather_requests 
                        WHERE timestamp >= datetime('now', '-24 hours')
                    """)
                    requests_24h = cursor.fetchone()[0]
                    
                    # Get database size
                    db_size = os.path.getsize(db_path)
                    
                    db_stats = {
                        "status": "connected",
                        "user_count": user_count,
                        "requests_24h": requests_24h,
                        "size_bytes": db_size
                    }
                    
                    conn.close()
                except Exception as e:
                    db_stats = {"status": "error", "error": str(e)}
            
            # System stats
            import psutil
            system_stats = {
                "cpu_percent": psutil.cpu_percent(),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_percent": psutil.disk_usage('/').percent
            }
            
            response = {
                "status": "running",
                "timestamp": datetime.now().isoformat(),
                "bot_token_configured": bool(config.BOT_TOKEN),
                "admin_id_configured": bool(config.ADMIN_ID),
                "database": db_stats,
                "system": system_stats,
                "config": {
                    "rate_limit_requests": config.RATE_LIMIT_REQUESTS,
                    "rate_limit_window_hours": config.RATE_LIMIT_WINDOW_HOURS,
                    "cache_expire_hours": config.CACHE_EXPIRE_HOURS
                }
            }
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response, indent=2).encode())
            
        except Exception as e:
            response = {
                "status": "error",
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }
            
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response, indent=2).encode())

    def log_message(self, format, *args):
        """Override to use our logger."""
        logging.getLogger('health_check').info(format % args)


class HealthCheckServer:
    def __init__(self, port=8000):
        self.port = port
        self.server = None
        self.thread = None
        self.logger = logging.getLogger('health_check')

    def start(self):
        """Start the health check server."""
        try:
            self.server = HTTPServer(('0.0.0.0', self.port), HealthCheckHandler)
            self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
            self.thread.start()
            self.logger.info(f"Health check server started on port {self.port}")
        except Exception as e:
            self.logger.error(f"Failed to start health check server: {e}")

    def stop(self):
        """Stop the health check server."""
        if self.server:
            self.server.shutdown()
            self.server.server_close()
            self.logger.info("Health check server stopped")


if __name__ == "__main__":
    # Run standalone health check server
    logging.basicConfig(level=logging.INFO)
    server = HealthCheckServer()
    server.start()
    
    try:
        while True:
            import time
            time.sleep(1)
    except KeyboardInterrupt:
        server.stop()
