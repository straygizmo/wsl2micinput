"""
WSL2 Microphone Input Library

A Python library for enabling voice input and speech recognition on WSL2.
"""

from .voice_input import VoiceInput, AudioDevice
from .audio_backends import AudioBackend, PyAudioBackend, SoundDeviceBackend
from .utils import check_wsl2_audio, list_audio_devices

__version__ = "0.1.0"
__author__ = "WSL2 Microphone Input Contributors"

__all__ = [
    "VoiceInput",
    "AudioDevice",
    "AudioBackend",
    "PyAudioBackend",
    "SoundDeviceBackend",
    "check_wsl2_audio",
    "list_audio_devices",
]