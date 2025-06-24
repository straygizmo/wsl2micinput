#!/usr/bin/env python3
"""
Tests for audio device detection and configuration
"""

import pytest
import numpy as np
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src import utils, audio_backends


class TestWSL2Environment:
    """Test WSL2 environment detection and configuration"""
    
    def test_wsl2_detection(self):
        """Test if we can detect WSL2 environment"""
        # This will be True if running on WSL2, False otherwise
        is_wsl = utils.is_wsl2()
        assert isinstance(is_wsl, bool)
    
    def test_audio_configuration_check(self):
        """Test audio configuration checking"""
        config = utils.check_wsl2_audio()
        
        # Should return a dictionary with expected keys
        assert isinstance(config, dict)
        assert "is_wsl2" in config
        assert "wslg_available" in config
        assert "pulse_server" in config
        assert "audio_available" in config
        assert "issues" in config
        assert isinstance(config["issues"], list)
    
    def test_audio_env_setup(self):
        """Test audio environment setup"""
        # Should not raise any exceptions
        utils.setup_wsl2_audio_env()


class TestAudioDevices:
    """Test audio device enumeration and access"""
    
    def test_list_devices(self):
        """Test listing audio devices"""
        devices = utils.list_audio_devices()
        
        # Should return a list
        assert isinstance(devices, list)
        
        # If devices are found, check structure
        if devices:
            device = devices[0]
            assert "index" in device
            assert "name" in device
            assert "channels" in device
            assert "sample_rate" in device
            assert "backend" in device
    
    def test_get_default_device(self):
        """Test getting default audio device"""
        device = utils.get_default_input_device()
        
        # Could be None if no devices found
        if device is not None:
            assert isinstance(device, dict)
            assert "index" in device
            assert "name" in device
    
    @pytest.mark.skip(reason="Requires actual audio hardware")
    def test_audio_input(self):
        """Test actual audio input (skipped by default)"""
        success, message = utils.test_audio_input(duration=0.1)
        assert isinstance(success, bool)
        assert isinstance(message, str)


class TestAudioBackends:
    """Test different audio backend implementations"""
    
    def test_get_audio_backend(self):
        """Test audio backend factory"""
        # Should return some backend
        backend = audio_backends.get_audio_backend()
        assert isinstance(backend, audio_backends.AudioBackend)
    
    def test_pyaudio_backend_import(self):
        """Test PyAudio backend can be imported"""
        try:
            backend = audio_backends.PyAudioBackend()
            assert hasattr(backend, "list_devices")
            assert hasattr(backend, "record")
            assert hasattr(backend, "stream")
        except ImportError:
            pytest.skip("PyAudio not installed")
    
    def test_sounddevice_backend_import(self):
        """Test Sounddevice backend can be imported"""
        try:
            backend = audio_backends.SoundDeviceBackend()
            assert hasattr(backend, "list_devices")
            assert hasattr(backend, "record")
            assert hasattr(backend, "stream")
        except ImportError:
            pytest.skip("Sounddevice not installed")
    
    def test_backend_device_listing(self):
        """Test device listing through backends"""
        try:
            backend = audio_backends.get_audio_backend()
            devices = backend.list_devices()
            assert isinstance(devices, list)
        except ImportError:
            pytest.skip("No audio backend available")


class TestAudioRecording:
    """Test audio recording functionality"""
    
    @pytest.fixture
    def audio_backend(self):
        """Get an audio backend for testing"""
        try:
            return audio_backends.get_audio_backend()
        except ImportError:
            pytest.skip("No audio backend available")
    
    def test_backend_parameters(self, audio_backend):
        """Test backend parameter configuration"""
        assert audio_backend.sample_rate == 16000
        assert audio_backend.channels == 1
        assert audio_backend.chunk_size == 1024
    
    @pytest.mark.skip(reason="Requires actual audio hardware")
    def test_short_recording(self, audio_backend):
        """Test short audio recording"""
        # Record 0.1 seconds
        audio_data = audio_backend.record(0.1)
        
        # Check we got audio data
        assert isinstance(audio_data, np.ndarray)
        assert len(audio_data) > 0
        assert audio_data.dtype == np.int16
    
    @pytest.mark.skip(reason="Requires actual audio hardware")
    def test_device_test(self, audio_backend):
        """Test device testing functionality"""
        result = audio_backend.test_device()
        assert isinstance(result, bool)