#!/data/data/com.termux/files/usr/bin/bash

# Script to run RoboBet in Termux
echo "Starting RoboBet..."

# Check if bot is already running
echo "Checking for existing processes..."
EXISTING_PROCS=$(ps aux | grep -E "python.*(main|bot)\.py" | grep -v grep)

if [ ! -z "$EXISTING_PROCS" ]; then
    echo "⚠️  Found existing Python processes:"
    echo "$EXISTING_PROCS"
    echo ""
    echo "Stopping existing processes..."
    pkill -f "python.*main.py"
    pkill -f "python.*bot.py"
    sleep 2
    echo "✅ Existing processes stopped"
fi

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "Stopping all processes..."
    kill $BOT_PID $MAIN_PID 2>/dev/null
    exit 0
}

# Trap CTRL+C and call cleanup
trap cleanup SIGINT SIGTERM

# Start bot.py in background
echo "Starting Telegram bot (bot.py)..."
python bot.py &
BOT_PID=$!
echo "Bot PID: $BOT_PID"

# Wait a bit before starting main
sleep 3

# Start main.py in background
echo "Starting main scraper (main.py)..."
python main.py &
MAIN_PID=$!
echo "Main PID: $MAIN_PID"

echo ""
echo "=========================================="
echo "RoboBet is running!"
echo "=========================================="
echo "Bot PID: $BOT_PID"
echo "Main PID: $MAIN_PID"
echo ""
echo "Press CTRL+C to stop all processes"
echo "=========================================="

# Wait for both processes
wait $BOT_PID $MAIN_PID
