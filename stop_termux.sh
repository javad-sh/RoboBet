#!/data/data/com.termux/files/usr/bin/bash

# Script to stop RoboBet in Termux
echo "=========================================="
echo "Stopping RoboBet..."
echo "=========================================="

# Find and kill all Python processes related to the bot
echo "Finding Python processes..."
PROCS=$(ps aux | grep -E "python.*(main|bot)\.py" | grep -v grep)

if [ -z "$PROCS" ]; then
    echo "ℹ️  No RoboBet processes found running"
    exit 0
fi

echo "Found processes:"
echo "$PROCS"
echo ""

# Kill processes
echo "Stopping bot.py..."
pkill -f "python.*bot.py"

echo "Stopping main.py..."
pkill -f "python.*main.py"

# Wait a moment
sleep 2

# Verify they're stopped
REMAINING=$(ps aux | grep -E "python.*(main|bot)\.py" | grep -v grep)

if [ -z "$REMAINING" ]; then
    echo ""
    echo "=========================================="
    echo "✅ RoboBet stopped successfully"
    echo "=========================================="
else
    echo ""
    echo "⚠️  Some processes might still be running:"
    echo "$REMAINING"
    echo ""
    echo "Use 'kill -9 <PID>' to force stop if needed"
fi
