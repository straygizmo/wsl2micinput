#!/usr/bin/env python3
"""
Continuous speech recognition example for WSL2
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import logging
import argparse
import time
from datetime import datetime
from src import VoiceInput

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


class VoiceCommands:
    """Simple voice command processor"""
    
    def __init__(self):
        self.commands = {
            "what time is it": self.tell_time,
            "hello": self.say_hello,
            "help": self.show_help,
        }
    
    def tell_time(self):
        current_time = datetime.now().strftime("%I:%M %p")
        print(f"The time is {current_time}")
    
    def say_hello(self):
        print("Hello! I'm listening to your commands.")
    
    def show_help(self):
        print("\nAvailable commands:")
        for cmd in self.commands:
            print(f"  - {cmd}")
        print("  - stop listening (to exit)")
    
    def process(self, text):
        """Process recognized text and execute commands"""
        text_lower = text.lower()
        
        # Check for exact commands
        for command, action in self.commands.items():
            if command in text_lower:
                action()
                return True
        
        # Default: just echo the text
        print(f"You said: \"{text}\"")
        return False


def main():
    parser = argparse.ArgumentParser(description='Continuous speech recognition example')
    parser.add_argument('--device', type=int, default=None,
                       help='Audio device index (default: auto-detect)')
    parser.add_argument('--engine', type=str, default='google',
                       choices=['google', 'sphinx', 'google_cloud'],
                       help='Speech recognition engine (default: google)')
    parser.add_argument('--stop-phrase', type=str, default='stop listening',
                       help='Phrase to stop listening (default: "stop listening")')
    parser.add_argument('--commands', action='store_true',
                       help='Enable voice command processing')
    
    args = parser.parse_args()
    
    try:
        print("\nInitializing continuous speech recognition...")
        print(f"Using recognition engine: {args.engine}")
        
        # Create voice input
        voice = VoiceInput(
            device_index=args.device,
            recognition_engine=args.engine
        )
        
        # Create command processor if enabled
        command_processor = VoiceCommands() if args.commands else None
        
        print("\n" + "=" * 60)
        print("Continuous Speech Recognition Active!")
        print("=" * 60)
        print(f"\nSay '{args.stop_phrase}' to stop")
        print("Press Ctrl+C to force exit")
        
        if args.commands:
            print("\nVoice commands are enabled. Say 'help' for available commands.")
        
        print("\nListening continuously...\n")
        
        # Define callback for recognized text
        def on_recognized(text):
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] ", end="")
            
            if command_processor:
                command_processor.process(text)
            else:
                print(f"Recognized: \"{text}\"")
        
        # Start continuous listening
        for text in voice.listen_continuous(
            callback=None,  # We'll handle printing in the loop
            stop_phrase=args.stop_phrase
        ):
            on_recognized(text)
        
        print("\n\nContinuous listening stopped.")
        
    except KeyboardInterrupt:
        print("\n\nStopped by user")
    except Exception as e:
        logger.error(f"Error: {e}")
        print("\nTroubleshooting tips:")
        print("1. Make sure you have an active internet connection (for Google engine)")
        print("2. For offline recognition, use --engine sphinx")
        print("3. Try reducing background noise")
        print("4. Speak clearly and not too fast")


if __name__ == "__main__":
    main()