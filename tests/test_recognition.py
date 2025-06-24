#!/usr/bin/env python3
"""
Tests for speech recognition functionality
"""

import pytest
import numpy as np
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src import VoiceInput, AudioDevice
from unittest.mock import Mock, patch, MagicMock


class TestVoiceInput:
    """Test VoiceInput class"""
    
    @patch('src.voice_input.get_audio_backend')
    @patch('src.voice_input.check_wsl2_audio')
    def test_voice_input_initialization(self, mock_check_audio, mock_get_backend):
        """Test VoiceInput initialization"""
        # Mock audio status
        mock_check_audio.return_value = {
            "is_wsl2": True,
            "audio_available": True,
            "issues": []
        }
        
        # Mock backend
        mock_backend = Mock()
        mock_get_backend.return_value = mock_backend
        
        # Create VoiceInput
        voice = VoiceInput()
        
        # Check initialization
        assert voice.backend == mock_backend
        assert voice.recognition_engine == "google"
        mock_check_audio.assert_called_once()
    
    @patch('src.voice_input.get_audio_backend')
    def test_list_devices(self, mock_get_backend):
        """Test device listing"""
        # Mock backend with devices
        mock_backend = Mock()
        mock_backend.list_devices.return_value = [
            {
                "index": 0,
                "name": "Test Device",
                "channels": 2,
                "sample_rate": 44100,
                "backend": "test"
            }
        ]
        mock_get_backend.return_value = mock_backend
        
        voice = VoiceInput()
        devices = voice.list_devices()
        
        # Check result
        assert len(devices) == 1
        assert isinstance(devices[0], AudioDevice)
        assert devices[0].name == "Test Device"
        assert devices[0].channels == 2
    
    @patch('src.voice_input.get_audio_backend')
    def test_record(self, mock_get_backend):
        """Test audio recording"""
        # Mock backend
        mock_backend = Mock()
        mock_audio_data = np.zeros(16000, dtype=np.int16)  # 1 second at 16kHz
        mock_backend.record.return_value = mock_audio_data
        mock_get_backend.return_value = mock_backend
        
        voice = VoiceInput()
        audio = voice.record(1.0)
        
        # Check recording
        assert isinstance(audio, np.ndarray)
        assert len(audio) == 16000
        mock_backend.record.assert_called_once_with(1.0, None)
    
    @patch('src.voice_input.get_audio_backend')
    def test_calibrate(self, mock_get_backend):
        """Test microphone calibration"""
        # Mock backend
        mock_backend = Mock()
        mock_backend.sample_rate = 16000
        mock_audio_data = np.random.randint(-1000, 1000, 48000, dtype=np.int16)
        mock_backend.record.return_value = mock_audio_data
        mock_get_backend.return_value = mock_backend
        
        voice = VoiceInput()
        
        # Mock recognizer
        voice.recognizer = Mock()
        voice.recognizer.energy_threshold = 300
        
        # Calibrate
        result = voice.calibrate(3.0)
        
        # Check results
        assert "noise_level" in result
        assert "max_amplitude" in result
        assert "energy_threshold" in result
        assert result["calibrated"] is True
        mock_backend.record.assert_called_once_with(3.0, None)
    
    @patch('src.voice_input.get_audio_backend')
    def test_save_recording(self, mock_get_backend):
        """Test saving audio to file"""
        # Mock backend
        mock_backend = Mock()
        mock_backend.channels = 1
        mock_backend.sample_rate = 16000
        mock_get_backend.return_value = mock_backend
        
        voice = VoiceInput()
        
        # Create test audio
        test_audio = np.zeros(16000, dtype=np.int16)
        
        # Mock wave.open
        with patch('wave.open', create=True) as mock_wave:
            mock_file = MagicMock()
            mock_wave.return_value.__enter__.return_value = mock_file
            
            # Save recording
            voice.save_recording(test_audio, "test.wav")
            
            # Check wave file configuration
            mock_file.setnchannels.assert_called_once_with(1)
            mock_file.setsampwidth.assert_called_once_with(2)
            mock_file.setframerate.assert_called_once_with(16000)
            mock_file.writeframes.assert_called_once()


class TestSpeechRecognition:
    """Test speech recognition functionality"""
    
    @patch('src.voice_input.get_audio_backend')
    @patch('speech_recognition.Microphone')
    @patch('speech_recognition.Recognizer')
    def test_listen_with_speech(self, mock_recognizer_class, mock_microphone_class, mock_get_backend):
        """Test listening with successful speech recognition"""
        # Mock backend
        mock_backend = Mock()
        mock_backend.sample_rate = 16000
        mock_get_backend.return_value = mock_backend
        
        # Mock recognizer
        mock_recognizer = Mock()
        mock_recognizer_class.return_value = mock_recognizer
        
        # Mock successful recognition
        mock_audio = Mock()
        mock_recognizer.listen.return_value = mock_audio
        mock_recognizer.recognize_google.return_value = "Hello world"
        
        # Create VoiceInput
        voice = VoiceInput()
        voice.recognizer = mock_recognizer
        
        # Test listen
        result = voice.listen()
        
        assert result == "Hello world"
        mock_recognizer.listen.assert_called_once()
        mock_recognizer.recognize_google.assert_called_once_with(mock_audio)
    
    @patch('src.voice_input.get_audio_backend')
    def test_continuous_listening(self, mock_get_backend):
        """Test continuous listening generator"""
        # Mock backend
        mock_backend = Mock()
        mock_get_backend.return_value = mock_backend
        
        voice = VoiceInput()
        
        # Mock the listen method to return test phrases
        test_phrases = ["hello", "world", "stop listening"]
        phrase_iter = iter(test_phrases)
        
        def mock_listen(*args, **kwargs):
            try:
                return next(phrase_iter)
            except StopIteration:
                return None
        
        voice.listen = mock_listen
        
        # Test continuous listening
        results = list(voice.listen_continuous())
        
        # Should stop at "stop listening"
        assert results == ["hello", "world"]
        assert voice.is_listening is False


class TestAudioDevice:
    """Test AudioDevice dataclass"""
    
    def test_audio_device_creation(self):
        """Test creating AudioDevice"""
        device = AudioDevice(
            index=0,
            name="Test Microphone",
            channels=2,
            sample_rate=48000,
            backend="pyaudio"
        )
        
        assert device.index == 0
        assert device.name == "Test Microphone"
        assert device.channels == 2
        assert device.sample_rate == 48000
        assert device.backend == "pyaudio"
    
    def test_audio_device_str(self):
        """Test AudioDevice string representation"""
        device = AudioDevice(
            index=0,
            name="Test Microphone",
            channels=2,
            sample_rate=48000,
            backend="pyaudio"
        )
        
        device_str = str(device)
        assert "Test Microphone" in device_str
        assert "2ch" in device_str
        assert "48000Hz" in device_str