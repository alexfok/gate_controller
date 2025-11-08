#!/bin/bash
#
# Raspberry Pi Initial Setup Script
# Run this ONCE on the Raspberry Pi to prepare it for gate controller
#
# Usage: ssh pi@fokhomerpi.local 'bash -s' < setup_rpi.sh
#

set -e

echo "═══════════════════════════════════════════════"
echo "  Raspberry Pi Setup for Gate Controller"
echo "═══════════════════════════════════════════════"
echo ""

# Update system
echo "▶ Updating system packages..."
sudo apt update
sudo apt upgrade -y

# Install required system packages
echo "▶ Installing required packages..."
sudo apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    bluetooth \
    bluez \
    libbluetooth-dev \
    libglib2.0-dev \
    git \
    rsync \
    htop

# Enable Bluetooth
echo "▶ Enabling Bluetooth..."
sudo systemctl enable bluetooth
sudo systemctl start bluetooth

# Add pi user to bluetooth group
echo "▶ Adding user to bluetooth group..."
sudo usermod -a -G bluetooth pi

# Configure Bluetooth for BLE scanning
echo "▶ Configuring Bluetooth for BLE..."
sudo setcap 'cap_net_raw,cap_net_admin+eip' $(readlink -f $(which python3))

# Create application directory
echo "▶ Creating application directory..."
mkdir -p /home/pi/gate_controller
mkdir -p /home/pi/gate_controller/logs

# Set permissions
echo "▶ Setting permissions..."
chown -R pi:pi /home/pi/gate_controller

echo ""
echo "✓ Raspberry Pi setup completed!"
echo ""
echo "Next steps:"
echo "  1. Run the deployment script from your local machine:"
echo "     ./deployment/scripts/deploy.sh"
echo ""
echo "Note: You may need to reboot for group changes to take effect:"
echo "  sudo reboot"
echo ""

