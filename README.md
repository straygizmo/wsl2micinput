# WSL2 Microphone Input

A Python library for enabling voice input and speech recognition on Windows Subsystem for Linux 2 (WSL2). This project provides a simple interface for capturing audio from microphones and performing speech-to-text conversion in the WSL2 environment.

## Features

- 🎤 Native microphone support through WSLg
- 🗣️ Speech recognition with multiple engines (Google, Sphinx, etc.)
- 🔧 Automatic audio configuration for WSL2
- 📊 Device enumeration and testing utilities
- 🛡️ Robust error handling for WSL2-specific issues

## Requirements

- Windows 10 Build 19044+ or Windows 11
- WSL2 with WSLg support (for native audio)
- Python 3.8 or higher
- Ubuntu 20.04+ or other compatible Linux distribution

## Quick Start

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/wsl2micinput.git
cd wsl2micinput
```

2. Run the setup script (this creates a virtual environment and installs dependencies):
```bash
chmod +x setup/install_dependencies.sh
./setup/install_dependencies.sh
```

3. Activate the virtual environment:
```bash
source venv/bin/activate
```

**Important:** Always activate the virtual environment before running any scripts to avoid import errors.

### Basic Usage

```python
from wsl2micinput import VoiceInput

# Initialize voice input
voice = VoiceInput()

# Record and recognize speech
text = voice.listen()
print(f"You said: {text}")

# Continuous listening
for text in voice.listen_continuous():
    print(f"Heard: {text}")
    if text.lower() == "stop":
        break
```

## WSL2 Audio Setup Guide

### Option 1: Native WSLg Support (Recommended)

If you have Windows 10 Build 19044+ or Windows 11, audio should work out of the box with WSLg:

1. Update WSL to the latest version:
```powershell
wsl --update
```

2. Verify WSLg is installed:
```bash
echo $PULSE_SERVER
# Should show: /mnt/wslg/PulseServer
```

### Option 2: USB Microphone via USB/IP

For USB microphones, you can use USBIPD-WIN:

1. Install USBIPD-WIN on Windows (requires admin):
```powershell
winget install --interactive --exact dorssel.usbipd-win
```

2. Share your USB microphone:
```powershell
# List devices
usbipd wsl list

# Attach microphone (replace <BUSID> with your device's ID)
usbipd wsl attach --busid <BUSID>
```

## Troubleshooting

### Common Issues

1. **`AttributeError: module 'speech_recognition' has no attribute 'Recognizer'`**
   - This means you're not running in the virtual environment
   - Solution: `source venv/bin/activate`
   - Or use the wrapper script: `./run_example.sh examples/basic_recording.py`

2. **No audio devices found**
   - Ensure WSL2 is updated: `wsl --update`
   - Restart WSL2: `wsl --shutdown` then reopen

3. **ALSA errors**
   - These are usually harmless warnings from Ubuntu's ALSA package
   - The library will still function correctly

4. **Permission denied errors**
   - Add your user to the audio group: `sudo usermod -a -G audio $USER`
   - Log out and back in for changes to take effect

## Examples

Check the `examples/` directory for more usage examples:

- `basic_recording.py` - Simple audio recording
- `speech_recognition.py` - Speech-to-text conversion
- `continuous_listening.py` - Real-time voice commands

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.