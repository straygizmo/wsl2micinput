"""
Main voice input module for WSL2
"""

import logging
import time
import threading
import queue
from typing import Optional, List, Dict, Callable, Any, Iterator
from dataclasses import dataclass

import numpy as np

from .audio_backends import AudioBackend, get_audio_backend
from .utils import setup_wsl2_audio_env, check_wsl2_audio, get_default_input_device

logger = logging.getLogger(__name__)


@dataclass
class AudioDevice:
    """Represents an audio input device."""
    index: int
    name: str
    channels: int
    sample_rate: int
    backend: str
    
    def __str__(self):
        return f"{self.name} ({self.channels}ch @ {self.sample_rate}Hz)"


class VoiceInput:
    """
    Main class for voice input on WSL2.
    
    This class provides a simple interface for recording audio and
    performing speech recognition in the WSL2 environment.
    """
    
    def __init__(self, 
                 backend: Optional[str] = None,
                 device_index: Optional[int] = None,
                 sample_rate: int = 16000,
                 channels: int = 1,
                 chunk_size: int = 1024,
                 recognition_engine: str = "google"):
        """
        Initialize VoiceInput.
        
        Args:
            backend: Audio backend to use ('pyaudio' or 'sounddevice')
            device_index: Index of the audio device to use
            sample_rate: Sample rate for audio recording
            channels: Number of audio channels
            chunk_size: Size of audio chunks for streaming
            recognition_engine: Speech recognition engine to use
        """
        # Set up WSL2 audio environment
        setup_wsl2_audio_env()
        
        # Check audio configuration
        audio_status = check_wsl2_audio()
        if audio_status["issues"]:
            logger.warning(f"Audio configuration issues: {audio_status['issues']}")
        
        # Initialize audio backend
        self.backend = get_audio_backend(backend)
        self.backend.sample_rate = sample_rate
        self.backend.channels = channels
        self.backend.chunk_size = chunk_size
        
        # Set device index
        if device_index is None:
            device = get_default_input_device()
            if device:
                self.device_index = device["index"]
                logger.info(f"Using default device: {device['name']}")
            else:
                self.device_index = None
                logger.warning("No default audio device found")
        else:
            self.device_index = device_index
        
        # Initialize speech recognition
        self.recognition_engine = recognition_engine
        self._init_speech_recognition()
        
        # Streaming state
        self.is_listening = False
        self.audio_queue = queue.Queue()
        
    def _init_speech_recognition(self):
        """Initialize speech recognition engine."""
        try:
            import speech_recognition as sr
            self.recognizer = sr.Recognizer()
            
            # Configure recognizer for WSL2
            self.recognizer.energy_threshold = 300  # Lower threshold for WSL2
            self.recognizer.dynamic_energy_threshold = True
            self.recognizer.pause_threshold = 0.8
            
        except ImportError as e:
            logger.warning("SpeechRecognition not installed. Install with: pip install SpeechRecognition")
            logger.warning("Make sure you have activated the virtual environment: source venv/bin/activate")
            self.recognizer = None
        except AttributeError as e:
            logger.error(f"Error initializing speech recognition: {e}")
            logger.error("This might be due to an incompatible version of SpeechRecognition")
            logger.error("Try reinstalling: pip install --upgrade SpeechRecognition")
            self.recognizer = None
    
    def list_devices(self) -> List[AudioDevice]:
        """
        List available audio input devices.
        
        Returns:
            List of AudioDevice objects
        """
        devices = []
        for device_info in self.backend.list_devices():
            devices.append(AudioDevice(
                index=device_info["index"],
                name=device_info["name"],
                channels=device_info["channels"],
                sample_rate=device_info["sample_rate"],
                backend=device_info.get("backend", type(self.backend).__name__)
            ))
        return devices
    
    def test_device(self, device_index: Optional[int] = None) -> bool:
        """
        Test if an audio device is working.
        
        Args:
            device_index: Device index to test (None for default)
            
        Returns:
            True if device is working, False otherwise
        """
        index = device_index if device_index is not None else self.device_index
        return self.backend.test_device(index)
    
    def record(self, duration: float) -> np.ndarray:
        """
        Record audio for a specified duration.
        
        Args:
            duration: Duration in seconds
            
        Returns:
            NumPy array of audio data
        """
        logger.info(f"Recording for {duration} seconds...")
        audio_data = self.backend.record(duration, self.device_index)
        logger.info(f"Recording complete. Got {len(audio_data)} samples")
        return audio_data
    
    def listen(self, timeout: Optional[float] = None, 
               phrase_time_limit: Optional[float] = None) -> Optional[str]:
        """
        Listen for speech and convert to text.
        
        Args:
            timeout: Maximum time to wait for speech to start
            phrase_time_limit: Maximum time for the phrase
            
        Returns:
            Recognized text or None if no speech detected
        """
        if not self.recognizer:
            raise RuntimeError("Speech recognition not initialized")
        
        try:
            import speech_recognition as sr
            
            # Create audio source from backend
            logger.info("Listening for speech...")
            
            # Record audio until silence
            with sr.Microphone(device_index=self.device_index, 
                             sample_rate=self.backend.sample_rate) as source:
                # Adjust for ambient noise
                logger.debug("Adjusting for ambient noise...")
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                
                # Listen for speech
                try:
                    audio = self.recognizer.listen(
                        source, 
                        timeout=timeout,
                        phrase_time_limit=phrase_time_limit
                    )
                    logger.info("Speech detected, recognizing...")
                except sr.WaitTimeoutError:
                    logger.info("No speech detected within timeout")
                    return None
            
            # Recognize speech
            return self._recognize_speech(audio)
            
        except Exception as e:
            logger.error(f"Error during listening: {e}")
            return None
    
    def _recognize_speech(self, audio) -> Optional[str]:
        """Recognize speech from audio data."""
        try:
            if self.recognition_engine == "google":
                text = self.recognizer.recognize_google(audio)
            elif self.recognition_engine == "sphinx":
                text = self.recognizer.recognize_sphinx(audio)
            elif self.recognition_engine == "google_cloud":
                # Requires credentials
                text = self.recognizer.recognize_google_cloud(audio)
            else:
                raise ValueError(f"Unknown recognition engine: {self.recognition_engine}")
            
            logger.info(f"Recognized: {text}")
            return text
            
        except Exception as e:
            logger.error(f"Recognition failed: {e}")
            return None
    
    def listen_continuous(self, 
                         callback: Optional[Callable[[str], Any]] = None,
                         stop_phrase: str = "stop listening") -> Iterator[str]:
        """
        Continuously listen for speech.
        
        Args:
            callback: Optional callback function for each recognized phrase
            stop_phrase: Phrase to stop listening
            
        Yields:
            Recognized text phrases
        """
        if not self.recognizer:
            raise RuntimeError("Speech recognition not initialized")
        
        logger.info("Starting continuous listening...")
        logger.info(f"Say '{stop_phrase}' to stop")
        
        self.is_listening = True
        
        try:
            while self.is_listening:
                text = self.listen(timeout=1.0, phrase_time_limit=5.0)
                
                if text:
                    # Check for stop phrase
                    if text.lower() == stop_phrase.lower():
                        logger.info("Stop phrase detected")
                        self.is_listening = False
                        break
                    
                    # Call callback if provided
                    if callback:
                        callback(text)
                    
                    # Yield the text
                    yield text
                    
        finally:
            self.is_listening = False
            logger.info("Continuous listening stopped")
    
    def calibrate(self, duration: float = 3.0) -> Dict[str, Any]:
        """
        Calibrate the microphone for ambient noise.
        
        Args:
            duration: Duration to sample ambient noise
            
        Returns:
            Dictionary with calibration results
        """
        logger.info(f"Calibrating microphone for {duration} seconds...")
        logger.info("Please remain quiet during calibration")
        
        # Record ambient noise
        ambient_audio = self.record(duration)
        
        # Calculate noise levels
        noise_level = np.std(ambient_audio)
        max_amplitude = np.max(np.abs(ambient_audio))
        
        # Adjust recognizer threshold if available
        if self.recognizer:
            # Set energy threshold based on noise level
            self.recognizer.energy_threshold = max(300, noise_level * 4)
            logger.info(f"Set energy threshold to {self.recognizer.energy_threshold}")
        
        results = {
            "noise_level": float(noise_level),
            "max_amplitude": float(max_amplitude),
            "energy_threshold": self.recognizer.energy_threshold if self.recognizer else None,
            "calibrated": True
        }
        
        logger.info(f"Calibration complete: {results}")
        return results
    
    def save_recording(self, audio_data: np.ndarray, filename: str):
        """
        Save audio data to a file.
        
        Args:
            audio_data: NumPy array of audio data
            filename: Output filename (should end with .wav)
        """
        import wave
        
        # Ensure audio data is int16
        if audio_data.dtype != np.int16:
            audio_data = (audio_data * 32767).astype(np.int16)
        
        with wave.open(filename, 'wb') as wf:
            wf.setnchannels(self.backend.channels)
            wf.setsampwidth(2)  # 16-bit audio
            wf.setframerate(self.backend.sample_rate)
            wf.writeframes(audio_data.tobytes())
        
        logger.info(f"Audio saved to {filename}")


# Convenience function
def create_voice_input(**kwargs) -> VoiceInput:
    """
    Create a VoiceInput instance with automatic configuration for WSL2.
    
    Args:
        **kwargs: Arguments to pass to VoiceInput constructor
        
    Returns:
        Configured VoiceInput instance
    """
    return VoiceInput(**kwargs)