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
pkg install -y python chromium chromedriver x11-repo

# Install Python packages
echo "Installing Python packages..."
pip install --upgrade pip
pip install -r requirements.txt

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
