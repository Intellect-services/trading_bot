#!/bin/bash

# Script to set up the isbot alias
# Run this script to add isbot command to your shell configuration

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
ISBOT_SCRIPT="$PROJECT_ROOT/scripts/isbot.sh"

# Detect shell
SHELL_NAME=$(basename "$SHELL")

# Determine config file
if [ "$SHELL_NAME" = "zsh" ]; then
    CONFIG_FILE="$HOME/.zshrc"
elif [ "$SHELL_NAME" = "bash" ]; then
    CONFIG_FILE="$HOME/.bashrc"
else
    CONFIG_FILE="$HOME/.profile"
fi

# Check if alias already exists
if grep -q "alias isbot=" "$CONFIG_FILE" 2>/dev/null; then
    echo "Alias 'isbot' already exists in $CONFIG_FILE"
    echo "Would you like to update it? (y/n)"
    read -r response
    if [ "$response" != "y" ] && [ "$response" != "Y" ]; then
        echo "Aborted."
        exit 0
    fi
    # Remove old alias
    sed -i.bak '/alias isbot=/d' "$CONFIG_FILE"
fi

# Add alias
echo "" >> "$CONFIG_FILE"
echo "# IntellectScout Trading Bot Management" >> "$CONFIG_FILE"
echo "alias isbot='$ISBOT_SCRIPT'" >> "$CONFIG_FILE"

echo "✓ Alias 'isbot' has been added to $CONFIG_FILE"
echo ""
echo "To use it immediately, run:"
echo "  source $CONFIG_FILE"
echo ""
echo "Or open a new terminal window."
echo ""
echo "Usage examples:"
echo "  isbot start      # Start both backend and frontend"
echo "  isbot stop       # Stop both services"
echo "  isbot restart    # Restart both services"
echo "  isbot status     # Check status"
echo "  isbot logs       # Show logs"
echo "  isbot help       # Show help"
