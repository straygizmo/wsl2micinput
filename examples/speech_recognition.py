#!/usr/bin/env python3
"""
Speech recognition example for WSL2
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import logging
import argparse
from src import VoiceInput

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description='Speech recognition example')
    parser.add_argument('--device', type=int, default=None,
                       help='Audio device index (default: auto-detect)')
    parser.add_argument('--engine', type=str, default='google',
                       choices=['google', 'sphinx', 'google_cloud'],
                       help='Speech recognition engine (default: google)')
    parser.add_argument('--calibrate', action='store_true',
                       help='Calibrate microphone before recognition')
    parser.add_argument('--timeout', type=float, default=None,
                       help='Timeout for speech detection (seconds)')
    parser.add_argument('--phrase-limit', type=float, default=None,
                       help='Maximum phrase duration (seconds)')
    
    args = parser.parse_args()
    
    try:
        print("\nInitializing speech recognition...")
        print(f"Using recognition engine: {args.engine}")
        
        # Create voice input
        voice = VoiceInput(
            device_index=args.device,
            recognition_engine=args.engine
        )
        
        # Calibrate if requested
        if args.calibrate:
            print("\nCalibrating microphone...")
            print("Please remain quiet for 3 seconds...")
            calibration = voice.calibrate(duration=3.0)
            print(f"Calibration complete:")
            print(f"  Noise level: {calibration['noise_level']:.2f}")
            print(f"  Energy threshold: {calibration['energy_threshold']}")
        
        print("\n" + "=" * 50)
        print("Speech Recognition Ready!")
        print("=" * 50)
        print("\nInstructions:")
        print("- Speak clearly into your microphone")
        print("- The system will detect when you start and stop speaking")
        print("- Press Ctrl+C to exit")
        
        if args.timeout:
            print(f"- Timeout: {args.timeout} seconds")
        if args.phrase_limit:
            print(f"- Max phrase duration: {args.phrase_limit} seconds")
        
        print("\nListening... (speak now)")
        
        # Single recognition
        text = voice.listen(
            timeout=args.timeout,
            phrase_time_limit=args.phrase_limit
        )
        
        if text:
            print(f"\n✓ Recognized: \"{text}\"")
        else:
            print("\n✗ No speech detected or recognition failed")
            print("\nTroubleshooting tips:")
            print("- Speak louder and clearer")
            print("- Try calibrating first with --calibrate")
            print("- Check your microphone with basic_recording.py")
        
    except KeyboardInterrupt:
        print("\n\nStopped by user")
    except Exception as e:
        logger.error(f"Error: {e}")
        print("\nTroubleshooting tips:")
        print("1. Make sure you have an active internet connection (for Google engine)")
        print("2. For offline recognition, use --engine sphinx")
        print("3. Check if your microphone is working with basic_recording.py")


if __name__ == "__main__":
    main()