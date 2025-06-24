#!/usr/bin/env python3
"""
Test for speech recognition import issue
"""

import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


def test_speech_recognition_import():
    """Test that speech_recognition can be imported and has Recognizer class."""
    try:
        import speech_recognition as sr
        assert hasattr(sr, 'Recognizer'), "speech_recognition module missing Recognizer class"
        
        # Try to instantiate a Recognizer
        recognizer = sr.Recognizer()
        assert recognizer is not None, "Failed to create Recognizer instance"
        
    except ImportError:
        pytest.skip("SpeechRecognition not installed - run in virtual environment")


def test_voice_input_initialization():
    """Test that VoiceInput can be initialized without errors."""
    try:
        from src import VoiceInput
        
        # This should not raise AttributeError for speech_recognition.Recognizer
        voice = VoiceInput()
        assert voice is not None, "Failed to create VoiceInput instance"
        
        # Check that recognizer was initialized (or set to None if not available)
        assert hasattr(voice, 'recognizer'), "VoiceInput missing recognizer attribute"
        
    except ImportError:
        pytest.skip("Required dependencies not installed - run in virtual environment")


def test_virtual_environment_check():
    """Test that we can detect if running in a virtual environment."""
    # Check if running in virtual environment
    in_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
    
    # This test will pass in venv, skip otherwise
    if not in_venv:
        pytest.skip("Not running in virtual environment")
    
    assert in_venv, "Should be running in virtual environment"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])