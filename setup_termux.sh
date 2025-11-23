#!/data/data/com.termux/files/usr/bin/bash

# Script to set up RoboBet project in Termux
echo "=========================================="
echo "RoboBet - Termux Setup Script"
echo "=========================================="

# Update and upgrade packages
echo "Updating packages..."
pkg update -y && pkg upgrade -y

# Install required packages
echo "Installing required packages..."
echo "Step 1/3: Installing Python..."
pkg install -y python

echo "Step 2/3: Installing x11-repo (for GUI support)..."
pkg install -y x11-repo

echo "Step 3/3: Installing Chromium..."
pkg install -y chromium

# Note: chromedriver might not be available in Termux repos
# Check if chromedriver is available
if pkg search chromedriver 2>/dev/null | grep -q chromedriver; then
    echo "Installing chromedriver..."
    pkg install -y chromedriver
else
    echo "⚠️  Warning: chromedriver package not found in repos"
    echo "   Selenium will try to use Selenium Manager to download it"
fi

# Install Python packages
echo "Installing Python packages..."
# Don't upgrade pip in Termux - it breaks the system
pip install -r requirements.txt --no-cache-dir

# Create necessary JSON files if they don't exist
echo "Setting up data files..."
[ ! -f "chat_ids.json" ] && echo "[]" > chat_ids.json
[ ! -f "betforward_odds.json" ] && echo "[]" > betforward_odds.json
[ ! -f "betforward_results.json" ] && echo "[]" > betforward_results.json

# Make start script executable
chmod +x start_termux.sh

echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo "To start the bot, run: ./start_termux.sh"
echo ""
echo "Note: Make sure you've set your bot token in main.py and bot.py"
