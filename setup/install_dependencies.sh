#!/bin/bash

# WSL2 Microphone Input - Dependency Installation Script
# This script installs all necessary dependencies for voice input on WSL2

set -e

echo "=== WSL2 Microphone Input Setup ==="
echo

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to print colored output
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# Check if running on WSL2
if ! grep -qi microsoft /proc/version; then
    print_error "This script is designed for WSL2. Please run on WSL2."
    exit 1
fi

echo "Updating package lists..."
sudo apt-get update -qq

echo
echo "Installing system dependencies..."

# Audio libraries
echo "Installing audio libraries..."
sudo apt-get install -y \
    pulseaudio \
    pulseaudio-utils \
    libpulse-dev \
    portaudio19-dev \
    python3-pyaudio \
    alsa-utils \
    libasound2-dev

print_success "Audio libraries installed"

# Python development dependencies
echo
echo "Installing Python development dependencies..."
sudo apt-get install -y \
    python3-dev \
    python3-pip \
    python3-venv \
    build-essential \
    swig

print_success "Python development dependencies installed"

# Additional tools for speech recognition
echo
echo "Installing additional tools..."
sudo apt-get install -y \
    flac \
    ffmpeg \
    libav-tools 2>/dev/null || true  # libav-tools might not be available on newer Ubuntu

print_success "Additional tools installed"

# Check PulseAudio server
echo
echo "Checking audio configuration..."

if [ -n "$PULSE_SERVER" ]; then
    print_success "PulseAudio server detected: $PULSE_SERVER"
else
    print_warning "PulseAudio server not detected. Audio might not work correctly."
    print_warning "Try running: wsl --shutdown and restart WSL2"
fi

# Test audio devices
echo
echo "Testing audio devices..."
if pactl info &>/dev/null; then
    print_success "PulseAudio is working"
    
    # List audio sources (microphones)
    echo
    echo "Available audio input devices:"
    pactl list sources short | grep -v monitor || print_warning "No input devices found"
else
    print_error "PulseAudio connection failed"
fi

# Create Python virtual environment
echo
echo "Setting up Python virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    print_success "Virtual environment created"
else
    print_warning "Virtual environment already exists"
fi

# Activate virtual environment and install Python packages
echo
echo "Installing Python packages..."
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip setuptools wheel

# Install requirements if file exists
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    print_success "Python packages installed"
else
    print_warning "requirements.txt not found. Please run: pip install -r requirements.txt"
fi

# Add user to audio group
echo
echo "Configuring user permissions..."
if ! groups | grep -q audio; then
    sudo usermod -a -G audio $USER
    print_success "User added to audio group"
    print_warning "Please log out and back in for audio group changes to take effect"
else
    print_success "User already in audio group"
fi

echo
echo "=== Setup Complete ==="
echo
echo "Next steps:"
echo "1. If you were added to the audio group, log out and back in"
echo "2. Activate the virtual environment: source venv/bin/activate"
echo "3. Run the test script: python examples/basic_recording.py"
echo
print_success "Installation completed successfully!"