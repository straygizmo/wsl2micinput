#!/usr/bin/env python3
"""
Basic audio recording example for WSL2
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Check if running in virtual environment
if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
    print("\n" + "="*60)
    print("WARNING: Not running in a virtual environment!")
    print("="*60)
    print("\nPlease activate the virtual environment first:")
    print("  source venv/bin/activate")
    print("\nOr run the setup script if you haven't already:")
    print("  ./setup/install_dependencies.sh")
    print("\nThen try running this script again.")
    print("="*60 + "\n")
    sys.exit(1)

import logging
import argparse
from src import VoiceInput, list_audio_devices, check_wsl2_audio

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description='Basic audio recording example')
    parser.add_argument('-d', '--duration', type=float, default=5.0,
                       help='Recording duration in seconds (default: 5.0)')
    parser.add_argument('-o', '--output', type=str, default='recording.wav',
                       help='Output filename (default: recording.wav)')
    parser.add_argument('--device', type=int, default=None,
                       help='Audio device index (default: auto-detect)')
    parser.add_argument('--list-devices', action='store_true',
                       help='List available audio devices')
    parser.add_argument('--check-audio', action='store_true',
                       help='Check WSL2 audio configuration')
    
    args = parser.parse_args()
    
    # Check audio configuration
    if args.check_audio:
        print("\nWSL2 Audio Configuration:")
        print("-" * 40)
        status = check_wsl2_audio()
        for key, value in status.items():
            if key != "issues":
                print(f"{key}: {value}")
        
        if status["issues"]:
            print("\nIssues detected:")
            for issue in status["issues"]:
                print(f"  - {issue}")
        else:
            print("\nNo issues detected!")
        return
    
    # List devices
    if args.list_devices:
        print("\nAvailable Audio Input Devices:")
        print("-" * 40)
        devices = list_audio_devices()
        
        if not devices:
            print("No audio input devices found!")
            print("\nTroubleshooting tips:")
            print("1. Run: wsl --update")
            print("2. Restart WSL: wsl --shutdown")
            print("3. Check if PULSE_SERVER is set: echo $PULSE_SERVER")
            return
        
        for device in devices:
            print(f"[{device['index']}] {device['name']}")
            print(f"    Channels: {device['channels']}, Sample Rate: {device['sample_rate']} Hz")
            print(f"    Backend: {device['backend']}")
            print()
        return
    
    # Create voice input
    try:
        print("\nInitializing voice input...")
        voice = VoiceInput(device_index=args.device)
        
        # Test the device
        print("Testing audio device...")
        if not voice.test_device():
            print("ERROR: Audio device test failed!")
            print("Please check your microphone connection and permissions.")
            return
        
        print(f"\nRecording for {args.duration} seconds...")
        print("Speak into your microphone now!")
        
        # Record audio
        audio_data = voice.record(args.duration)
        
        # Save recording
        voice.save_recording(audio_data, args.output)
        print(f"\nRecording saved to: {args.output}")
        
        # Show some statistics
        import numpy as np
        print(f"\nRecording statistics:")
        print(f"  Duration: {len(audio_data) / voice.backend.sample_rate:.2f} seconds")
        print(f"  Samples: {len(audio_data)}")
        print(f"  Max amplitude: {np.max(np.abs(audio_data))}")
        print(f"  RMS level: {np.sqrt(np.mean(audio_data**2)):.2f}")
        
    except Exception as e:
        logger.error(f"Error: {e}")
        print("\nTroubleshooting tips:")
        print("1. Run the setup script: ./setup/install_dependencies.sh")
        print("2. Check audio devices: python examples/basic_recording.py --list-devices")
        print("3. Check WSL2 audio: python examples/basic_recording.py --check-audio")


if __name__ == "__main__":
    main()