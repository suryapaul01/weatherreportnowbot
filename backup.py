#!/usr/bin/env python3
"""
Backup and restore script for Weather Report Now Bot

This script handles database backups and restoration.
"""

import os
import shutil
import sqlite3
import json
import gzip
import argparse
from datetime import datetime
from pathlib import Path
from config import Config


class BotBackup:
    def __init__(self):
        self.config = Config()
        self.db_path = self.config.DATABASE_URL
        self.backup_dir = Path("backups")
        self.backup_dir.mkdir(exist_ok=True)

    def create_backup(self, compress=True):
        """Create a backup of the database and configuration."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"weather_bot_backup_{timestamp}"
        backup_path = self.backup_dir / backup_name
        
        print(f"🔄 Creating backup: {backup_name}")
        
        try:
            # Create backup directory
            backup_path.mkdir(exist_ok=True)
            
            # Backup database
            if os.path.exists(self.db_path):
                db_backup_path = backup_path / "database.db"
                shutil.copy2(self.db_path, db_backup_path)
                print(f"✅ Database backed up to {db_backup_path}")
            else:
                print("⚠️ Database file not found, skipping database backup")
            
            # Backup configuration (without sensitive data)
            config_backup = {
                "rate_limit_requests": self.config.RATE_LIMIT_REQUESTS,
                "rate_limit_window_hours": self.config.RATE_LIMIT_WINDOW_HOURS,
                "cache_expire_hours": self.config.CACHE_EXPIRE_HOURS,
                "backup_timestamp": timestamp,
                "bot_username": self.config.BOT_USERNAME,
                "bot_name": self.config.BOT_NAME
            }
            
            config_path = backup_path / "config.json"
            with open(config_path, 'w') as f:
                json.dump(config_backup, f, indent=2)
            print(f"✅ Configuration backed up to {config_path}")
            
            # Export database data as JSON
            if os.path.exists(self.db_path):
                self.export_database_json(backup_path / "data_export.json")
            
            # Create backup info file
            info = {
                "backup_name": backup_name,
                "timestamp": timestamp,
                "database_size": os.path.getsize(self.db_path) if os.path.exists(self.db_path) else 0,
                "files": [
                    "database.db",
                    "config.json",
                    "data_export.json",
                    "backup_info.json"
                ]
            }
            
            info_path = backup_path / "backup_info.json"
            with open(info_path, 'w') as f:
                json.dump(info, f, indent=2)
            
            # Compress backup if requested
            if compress:
                archive_path = self.backup_dir / f"{backup_name}.tar.gz"
                shutil.make_archive(str(archive_path).replace('.tar.gz', ''), 'gztar', backup_path)
                shutil.rmtree(backup_path)
                print(f"✅ Backup compressed to {archive_path}")
                return archive_path
            else:
                print(f"✅ Backup created at {backup_path}")
                return backup_path
                
        except Exception as e:
            print(f"❌ Backup failed: {e}")
            return None

    def export_database_json(self, output_path):
        """Export database data to JSON format."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            
            export_data = {}
            
            # Get all table names
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            # Export each table
            for table in tables:
                cursor.execute(f"SELECT * FROM {table}")
                rows = cursor.fetchall()
                export_data[table] = [dict(row) for row in rows]
            
            conn.close()
            
            # Write to JSON file
            with open(output_path, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)
            
            print(f"✅ Database data exported to {output_path}")
            
        except Exception as e:
            print(f"❌ Database export failed: {e}")

    def list_backups(self):
        """List all available backups."""
        print("📋 Available backups:")
        
        backups = []
        
        # List compressed backups
        for backup_file in self.backup_dir.glob("*.tar.gz"):
            stat = backup_file.stat()
            backups.append({
                "name": backup_file.name,
                "path": backup_file,
                "size": stat.st_size,
                "modified": datetime.fromtimestamp(stat.st_mtime),
                "type": "compressed"
            })
        
        # List directory backups
        for backup_dir in self.backup_dir.iterdir():
            if backup_dir.is_dir() and backup_dir.name.startswith("weather_bot_backup_"):
                stat = backup_dir.stat()
                backups.append({
                    "name": backup_dir.name,
                    "path": backup_dir,
                    "size": sum(f.stat().st_size for f in backup_dir.rglob('*') if f.is_file()),
                    "modified": datetime.fromtimestamp(stat.st_mtime),
                    "type": "directory"
                })
        
        # Sort by modification time (newest first)
        backups.sort(key=lambda x: x["modified"], reverse=True)
        
        if not backups:
            print("  No backups found")
            return []
        
        for i, backup in enumerate(backups, 1):
            size_mb = backup["size"] / (1024 * 1024)
            print(f"  {i}. {backup['name']} ({backup['type']}) - {size_mb:.1f} MB - {backup['modified']}")
        
        return backups

    def restore_backup(self, backup_path, confirm=True):
        """Restore from a backup."""
        backup_path = Path(backup_path)
        
        if confirm:
            print(f"⚠️ This will restore from backup: {backup_path.name}")
            print("⚠️ Current database will be backed up before restoration")
            response = input("Continue? (y/N): ")
            if response.lower() != 'y':
                print("❌ Restoration cancelled")
                return False
        
        try:
            # Create a backup of current state first
            print("🔄 Creating backup of current state...")
            current_backup = self.create_backup(compress=True)
            if current_backup:
                print(f"✅ Current state backed up to {current_backup}")
            
            # Extract backup if it's compressed
            if backup_path.suffix == '.gz':
                print("🔄 Extracting backup archive...")
                extract_path = self.backup_dir / "temp_restore"
                if extract_path.exists():
                    shutil.rmtree(extract_path)
                shutil.unpack_archive(backup_path, extract_path)
                
                # Find the actual backup directory
                backup_dirs = [d for d in extract_path.iterdir() if d.is_dir()]
                if backup_dirs:
                    restore_from = backup_dirs[0]
                else:
                    restore_from = extract_path
            else:
                restore_from = backup_path
            
            # Restore database
            db_backup_path = restore_from / "database.db"
            if db_backup_path.exists():
                if os.path.exists(self.db_path):
                    os.remove(self.db_path)
                shutil.copy2(db_backup_path, self.db_path)
                print(f"✅ Database restored from {db_backup_path}")
            else:
                print("⚠️ No database file found in backup")
            
            # Clean up temporary extraction
            if backup_path.suffix == '.gz':
                shutil.rmtree(extract_path)
            
            print("✅ Restoration completed successfully")
            return True
            
        except Exception as e:
            print(f"❌ Restoration failed: {e}")
            return False

    def cleanup_old_backups(self, keep_count=10):
        """Clean up old backups, keeping only the most recent ones."""
        backups = self.list_backups()
        
        if len(backups) <= keep_count:
            print(f"📋 {len(backups)} backups found, no cleanup needed (keeping {keep_count})")
            return
        
        to_delete = backups[keep_count:]
        print(f"🗑️ Cleaning up {len(to_delete)} old backups...")
        
        for backup in to_delete:
            try:
                if backup["type"] == "compressed":
                    backup["path"].unlink()
                else:
                    shutil.rmtree(backup["path"])
                print(f"  ✅ Deleted {backup['name']}")
            except Exception as e:
                print(f"  ❌ Failed to delete {backup['name']}: {e}")


def main():
    """Main backup function."""
    parser = argparse.ArgumentParser(description="Weather Bot Backup Tool")
    parser.add_argument("action", choices=["create", "list", "restore", "cleanup"],
                       help="Action to perform")
    parser.add_argument("--backup", "-b", help="Backup name/path for restore action")
    parser.add_argument("--no-compress", action="store_true", help="Don't compress backup")
    parser.add_argument("--keep", type=int, default=10, help="Number of backups to keep during cleanup")
    parser.add_argument("--yes", "-y", action="store_true", help="Skip confirmation prompts")
    
    args = parser.parse_args()
    
    backup_tool = BotBackup()
    
    if args.action == "create":
        result = backup_tool.create_backup(compress=not args.no_compress)
        if result:
            print(f"🎉 Backup created successfully: {result}")
        else:
            exit(1)
    
    elif args.action == "list":
        backup_tool.list_backups()
    
    elif args.action == "restore":
        if not args.backup:
            print("❌ Please specify a backup to restore with --backup")
            exit(1)
        
        success = backup_tool.restore_backup(args.backup, confirm=not args.yes)
        if not success:
            exit(1)
    
    elif args.action == "cleanup":
        backup_tool.cleanup_old_backups(args.keep)


if __name__ == "__main__":
    main()
