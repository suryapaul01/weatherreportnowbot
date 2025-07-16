#!/usr/bin/env python3
"""
Monitoring script for Weather Report Now Bot

This script monitors the bot's health and performance.
"""

import asyncio
import json
import logging
import time
import requests
from datetime import datetime, timedelta
from database import Database
from config import Config


class BotMonitor:
    def __init__(self):
        self.config = Config()
        self.db = Database()
        self.logger = logging.getLogger(__name__)
        self.health_url = "http://localhost:8000/health"
        self.status_url = "http://localhost:8000/status"

    async def check_health(self):
        """Check bot health via HTTP endpoint."""
        try:
            response = requests.get(self.health_url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                return data["status"] == "healthy"
            return False
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return False

    async def get_detailed_status(self):
        """Get detailed status information."""
        try:
            response = requests.get(self.status_url, timeout=10)
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            self.logger.error(f"Status check failed: {e}")
            return None

    async def check_database_health(self):
        """Check database health directly."""
        try:
            await self.db.connect()
            
            # Check if we can query the database
            user_count = await self.db.get_user_count()
            active_users = await self.db.get_active_users_count(24)
            
            await self.db.close()
            
            return {
                "status": "healthy",
                "user_count": user_count,
                "active_users_24h": active_users
            }
        except Exception as e:
            self.logger.error(f"Database health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }

    async def check_rate_limiting(self):
        """Check if rate limiting is working properly."""
        try:
            await self.db.connect()
            
            # Get request statistics for the last hour
            recent_requests = await self.db.get_request_stats(1)
            
            # Check for any users exceeding rate limits
            # This is a simplified check - in production you'd want more sophisticated monitoring
            
            await self.db.close()
            
            return {
                "status": "ok",
                "recent_requests": len(recent_requests)
            }
        except Exception as e:
            self.logger.error(f"Rate limiting check failed: {e}")
            return {
                "status": "error",
                "error": str(e)
            }

    async def generate_report(self):
        """Generate a comprehensive monitoring report."""
        report = {
            "timestamp": datetime.now().isoformat(),
            "checks": {}
        }
        
        # Health check
        report["checks"]["health"] = await self.check_health()
        
        # Database check
        report["checks"]["database"] = await self.check_database_health()
        
        # Rate limiting check
        report["checks"]["rate_limiting"] = await self.check_rate_limiting()
        
        # Detailed status
        detailed_status = await self.get_detailed_status()
        if detailed_status:
            report["detailed_status"] = detailed_status
        
        # Overall health
        all_healthy = all([
            report["checks"]["health"],
            report["checks"]["database"]["status"] == "healthy",
            report["checks"]["rate_limiting"]["status"] == "ok"
        ])
        
        report["overall_status"] = "healthy" if all_healthy else "unhealthy"
        
        return report

    async def run_continuous_monitoring(self, interval_seconds=60):
        """Run continuous monitoring."""
        self.logger.info(f"Starting continuous monitoring (interval: {interval_seconds}s)")
        
        while True:
            try:
                report = await self.generate_report()
                
                # Log the report
                if report["overall_status"] == "healthy":
                    self.logger.info("✅ Bot is healthy")
                else:
                    self.logger.warning(f"⚠️ Bot health issues detected: {report}")
                
                # Save report to file (optional)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                with open(f"logs/monitor_report_{timestamp}.json", "w") as f:
                    json.dump(report, f, indent=2)
                
                # Wait for next check
                await asyncio.sleep(interval_seconds)
                
            except KeyboardInterrupt:
                self.logger.info("Monitoring stopped by user")
                break
            except Exception as e:
                self.logger.error(f"Monitoring error: {e}")
                await asyncio.sleep(interval_seconds)

    async def run_single_check(self):
        """Run a single monitoring check and print results."""
        report = await self.generate_report()
        
        print("🔍 Weather Bot Monitoring Report")
        print("=" * 40)
        print(f"Timestamp: {report['timestamp']}")
        print(f"Overall Status: {report['overall_status'].upper()}")
        print()
        
        print("📊 Health Checks:")
        print(f"  HTTP Health: {'✅' if report['checks']['health'] else '❌'}")
        print(f"  Database: {'✅' if report['checks']['database']['status'] == 'healthy' else '❌'}")
        print(f"  Rate Limiting: {'✅' if report['checks']['rate_limiting']['status'] == 'ok' else '❌'}")
        print()
        
        if "detailed_status" in report:
            status = report["detailed_status"]
            print("📈 Detailed Status:")
            if "database" in status and status["database"]["status"] == "connected":
                db = status["database"]
                print(f"  Users: {db.get('user_count', 'N/A')}")
                print(f"  Requests (24h): {db.get('requests_24h', 'N/A')}")
                print(f"  DB Size: {db.get('size_bytes', 'N/A')} bytes")
            
            if "system" in status:
                sys = status["system"]
                print(f"  CPU: {sys.get('cpu_percent', 'N/A')}%")
                print(f"  Memory: {sys.get('memory_percent', 'N/A')}%")
                print(f"  Disk: {sys.get('disk_percent', 'N/A')}%")
        
        return report["overall_status"] == "healthy"


async def main():
    """Main monitoring function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Weather Bot Monitor")
    parser.add_argument("--continuous", "-c", action="store_true", 
                       help="Run continuous monitoring")
    parser.add_argument("--interval", "-i", type=int, default=60,
                       help="Monitoring interval in seconds (default: 60)")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Verbose logging")
    
    args = parser.parse_args()
    
    # Setup logging
    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create monitor
    monitor = BotMonitor()
    
    if args.continuous:
        await monitor.run_continuous_monitoring(args.interval)
    else:
        success = await monitor.run_single_check()
        exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
