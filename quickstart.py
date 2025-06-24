#!/usr/bin/env python3
"""Quick start script for WSL2 microphone input."""

from src import VoiceInput, list_microphones
from src.utils import check_wsl_audio


def main():
    print("WSL2 Microphone Input - Quick Start")
    print("=" * 40)
    
    # Check environment
    print("\nChecking WSL2 audio support...")
    status = check_wsl_audio()
    
    if not status['has_audio']:
        print("\n⚠️  Audio support not detected!")
        print("Please ensure:")
        print("1. You're running WSL2 (not WSL1)")
        print("2. WSL is updated: wsl --update")
        print("3. You have Windows 10 19044+ or Windows 11")
        return
    
    print("✓ Audio support detected")
    
    # List devices
    print("\nAvailable microphones:")
    devices = list_microphones()
    if not devices:
        print("No microphones found!")
        return
    
    for d in devices:
        print(f"  [{d['index']}] {d['name']}")
    
    # Simple test
    print("\nInitializing voice input...")
    voice = VoiceInput()
    
    print("\nSpeak something (I'll listen for 5 seconds)...")
    text = voice.listen(timeout=5)
    
    if text:
        print(f"\nYou said: '{text}'")
        print("\n✓ Voice input is working!")
    else:
        print("\nNo speech detected.")
        print("Make sure your microphone is not muted.")
    
    print("\nFor more examples, see the examples/ directory")


if __name__ == "__main__":
    main()