#!/usr/bin/env python3
"""
Deployment script for Weather Report Now Bot

This script helps deploy the bot to various platforms.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path


def check_requirements():
    """Check if all requirements are met."""
    print("🔍 Checking requirements...")
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        return False
    
    # Check if .env file exists
    if not os.path.exists('.env'):
        print("❌ .env file not found. Please create it with your bot token and admin ID.")
        return False
    
    # Check if requirements.txt exists
    if not os.path.exists('requirements.txt'):
        print("❌ requirements.txt not found")
        return False
    
    print("✅ Requirements check passed")
    return True


def install_dependencies():
    """Install Python dependencies."""
    print("📦 Installing dependencies...")
    
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                      check=True, capture_output=True, text=True)
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False


def run_tests():
    """Run the test suite."""
    print("🧪 Running tests...")
    
    try:
        result = subprocess.run([sys.executable, "test_bot.py"], 
                              check=True, capture_output=True, text=True)
        print("✅ All tests passed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Tests failed: {e}")
        print(e.stdout)
        print(e.stderr)
        return False


def create_systemd_service():
    """Create a systemd service file for Linux deployment."""
    service_content = f"""[Unit]
Description=Weather Report Now Bot
After=network.target

[Service]
Type=simple
User=weatherbot
WorkingDirectory={os.getcwd()}
Environment=PATH={os.getcwd()}/venv/bin
ExecStart={sys.executable} main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
"""
    
    service_file = "weather-bot.service"
    with open(service_file, 'w') as f:
        f.write(service_content)
    
    print(f"✅ Systemd service file created: {service_file}")
    print("To install the service:")
    print(f"  sudo cp {service_file} /etc/systemd/system/")
    print("  sudo systemctl daemon-reload")
    print("  sudo systemctl enable weather-bot")
    print("  sudo systemctl start weather-bot")


def create_docker_files():
    """Create Docker files for containerized deployment."""
    dockerfile_content = """FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    gcc \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 weatherbot && chown -R weatherbot:weatherbot /app
USER weatherbot

# Expose port (if needed for health checks)
EXPOSE 8000

# Run the bot
CMD ["python", "main.py"]
"""
    
    docker_compose_content = """version: '3.8'

services:
  weather-bot:
    build: .
    container_name: weather-report-now-bot
    restart: unless-stopped
    environment:
      - BOT_TOKEN=${BOT_TOKEN}
      - ADMIN_ID=${ADMIN_ID}
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    env_file:
      - .env
"""
    
    with open("Dockerfile", 'w') as f:
        f.write(dockerfile_content)
    
    with open("docker-compose.yml", 'w') as f:
        f.write(docker_compose_content)
    
    print("✅ Docker files created: Dockerfile, docker-compose.yml")
    print("To deploy with Docker:")
    print("  docker-compose up -d")


def create_heroku_files():
    """Create files for Heroku deployment."""
    procfile_content = "worker: python main.py"
    
    runtime_content = f"python-{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    
    with open("Procfile", 'w') as f:
        f.write(procfile_content)
    
    with open("runtime.txt", 'w') as f:
        f.write(runtime_content)
    
    print("✅ Heroku files created: Procfile, runtime.txt")
    print("To deploy to Heroku:")
    print("  heroku create your-weather-bot")
    print("  heroku config:set BOT_TOKEN=your_bot_token")
    print("  heroku config:set ADMIN_ID=your_admin_id")
    print("  git push heroku main")


def create_directories():
    """Create necessary directories."""
    directories = ["data", "logs", ".cache"]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✅ Created directory: {directory}")


def main():
    """Main deployment function."""
    print("🚀 Weather Report Now Bot Deployment Script")
    print("=" * 50)
    
    # Check requirements
    if not check_requirements():
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        sys.exit(1)
    
    # Run tests
    if not run_tests():
        print("⚠️ Tests failed. Continue anyway? (y/N): ", end="")
        if input().lower() != 'y':
            sys.exit(1)
    
    # Create directories
    create_directories()
    
    # Ask user for deployment type
    print("\n📋 Choose deployment method:")
    print("1. Local development")
    print("2. Linux server (systemd)")
    print("3. Docker")
    print("4. Heroku")
    print("5. All deployment files")
    
    choice = input("Enter your choice (1-5): ").strip()
    
    if choice == "1":
        print("✅ Ready for local development!")
        print("Run: python main.py")
    elif choice == "2":
        create_systemd_service()
    elif choice == "3":
        create_docker_files()
    elif choice == "4":
        create_heroku_files()
    elif choice == "5":
        create_systemd_service()
        create_docker_files()
        create_heroku_files()
    else:
        print("❌ Invalid choice")
        sys.exit(1)
    
    print("\n🎉 Deployment preparation complete!")
    print("\n📝 Next steps:")
    print("1. Make sure your .env file has the correct BOT_TOKEN and ADMIN_ID")
    print("2. Test the bot locally: python main.py")
    print("3. Deploy using your chosen method")
    print("4. Monitor the logs for any issues")


if __name__ == "__main__":
    main()
