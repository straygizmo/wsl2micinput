#!/bin/bash

# WSL2 Version and Audio Support Checker
# This script checks if the current WSL2 environment supports audio input

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}=== WSL2 Audio Support Checker ===${NC}"
echo

# Check if running on WSL
if grep -qi microsoft /proc/version; then
    echo -e "${GREEN}✓ Running on WSL${NC}"
    
    # Check WSL version
    if grep -qi "WSL2" /proc/version; then
        echo -e "${GREEN}✓ WSL2 detected${NC}"
    else
        echo -e "${YELLOW}⚠ WSL1 detected - audio support limited${NC}"
    fi
else
    echo -e "${RED}✗ Not running on WSL${NC}"
    exit 1
fi

echo

# Check Windows version through interop
if command -v powershell.exe &> /dev/null; then
    echo "Checking Windows version..."
    WIN_VER=$(powershell.exe -Command "[System.Environment]::OSVersion.Version.Build" 2>/dev/null | tr -d '\r')
    
    if [ -n "$WIN_VER" ] && [ "$WIN_VER" -ge 19044 ]; then
        echo -e "${GREEN}✓ Windows Build $WIN_VER - Audio support available${NC}"
    else
        echo -e "${YELLOW}⚠ Windows Build $WIN_VER - Update to 19044+ for audio support${NC}"
    fi
else
    echo -e "${YELLOW}⚠ Cannot check Windows version${NC}"
fi

echo

# Check for WSLg
echo "Checking WSLg support..."
if [ -d "/mnt/wslg" ]; then
    echo -e "${GREEN}✓ WSLg detected${NC}"
    
    # Check PULSE_SERVER
    if [ -n "$PULSE_SERVER" ]; then
        echo -e "${GREEN}✓ PulseAudio server: $PULSE_SERVER${NC}"
    else
        echo -e "${YELLOW}⚠ PULSE_SERVER not set${NC}"
    fi
    
    # Check DISPLAY
    if [ -n "$DISPLAY" ]; then
        echo -e "${GREEN}✓ Display server: $DISPLAY${NC}"
    fi
else
    echo -e "${RED}✗ WSLg not detected - run 'wsl --update'${NC}"
fi

echo

# Check audio subsystem
echo "Checking audio subsystem..."

# Check for PulseAudio
if command -v pactl &> /dev/null; then
    echo -e "${GREEN}✓ PulseAudio installed${NC}"
    
    # Try to connect to PulseAudio
    if pactl info &> /dev/null; then
        echo -e "${GREEN}✓ PulseAudio connection successful${NC}"
        
        # Get server info
        PA_SERVER=$(pactl info | grep "Server String" | cut -d: -f2- | xargs)
        echo -e "  Server: $PA_SERVER"
        
        # Count audio sources
        SOURCE_COUNT=$(pactl list sources short | grep -v monitor | wc -l)
        echo -e "  Input devices: $SOURCE_COUNT"
        
        if [ "$SOURCE_COUNT" -gt 0 ]; then
            echo -e "${GREEN}✓ Microphone input available${NC}"
        else
            echo -e "${YELLOW}⚠ No microphone detected${NC}"
        fi
    else
        echo -e "${RED}✗ Cannot connect to PulseAudio${NC}"
    fi
else
    echo -e "${RED}✗ PulseAudio not installed${NC}"
fi

echo

# Check for ALSA
if command -v arecord &> /dev/null; then
    echo -e "${GREEN}✓ ALSA installed${NC}"
    
    # List recording devices
    ALSA_DEVICES=$(arecord -l 2>/dev/null | grep -c "card" || true)
    if [ "$ALSA_DEVICES" -gt 0 ]; then
        echo -e "  ALSA recording devices: $ALSA_DEVICES"
    fi
else
    echo -e "${YELLOW}⚠ ALSA not installed${NC}"
fi

echo

# Check Python audio libraries
echo "Checking Python audio support..."

# Check for Python
if command -v python3 &> /dev/null; then
    echo -e "${GREEN}✓ Python3 installed${NC}"
    
    # Check PyAudio
    if python3 -c "import pyaudio" 2>/dev/null; then
        echo -e "${GREEN}✓ PyAudio available${NC}"
    else
        echo -e "${YELLOW}⚠ PyAudio not installed${NC}"
    fi
else
    echo -e "${RED}✗ Python3 not installed${NC}"
fi

echo
echo -e "${BLUE}=== Summary ===${NC}"

# Overall status
if [ -n "$PULSE_SERVER" ] && pactl info &> /dev/null; then
    echo -e "${GREEN}✓ Audio input should work!${NC}"
    echo
    echo "You can now use the voice input library."
else
    echo -e "${YELLOW}⚠ Audio setup incomplete${NC}"
    echo
    echo "Recommendations:"
    echo "1. Run: wsl --update"
    echo "2. Restart WSL: wsl --shutdown"
    echo "3. Run the installation script: ./setup/install_dependencies.sh"
fi