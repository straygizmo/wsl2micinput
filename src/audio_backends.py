"""
Audio backend implementations for different audio libraries
"""

from abc import ABC, abstractmethod
from typing import Optional, Tuple, Callable, Any
import numpy as np
import logging
import queue
import threading

logger = logging.getLogger(__name__)


class AudioBackend(ABC):
    """Abstract base class for audio backends."""
    
    def __init__(self, sample_rate: int = 16000, channels: int = 1, 
                 chunk_size: int = 1024):
        self.sample_rate = sample_rate
        self.channels = channels
        self.chunk_size = chunk_size
        self.is_recording = False
        
    @abstractmethod
    def list_devices(self) -> list:
        """List available audio input devices."""
        pass
    
    @abstractmethod
    def record(self, duration: float, device_index: Optional[int] = None) -> np.ndarray:
        """Record audio for a specified duration."""
        pass
    
    @abstractmethod
    def stream(self, callback: Callable[[np.ndarray], Any], 
               device_index: Optional[int] = None):
        """Stream audio continuously to a callback function."""
        pass
    
    @abstractmethod
    def stop_stream(self):
        """Stop the audio stream."""
        pass
    
    @abstractmethod
    def test_device(self, device_index: Optional[int] = None) -> bool:
        """Test if a device is working."""
        pass


class PyAudioBackend(AudioBackend):
    """PyAudio backend implementation."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            import pyaudio
            self.pyaudio = pyaudio
            self.pa = pyaudio.PyAudio()
            self.stream = None
            
            # Suppress ALSA error messages on initialization
            self._suppress_alsa_errors()
            
        except ImportError:
            raise ImportError("PyAudio not installed. Run: pip install pyaudio")
    
    def _suppress_alsa_errors(self):
        """Suppress ALSA error messages that are common on WSL2."""
        try:
            import ctypes
            import os
            
            # Only suppress on Linux
            if os.name == 'posix':
                ERROR_HANDLER_FUNC = ctypes.CFUNCTYPE(None, ctypes.c_char_p, ctypes.c_int, 
                                                     ctypes.c_char_p, ctypes.c_int, 
                                                     ctypes.c_char_p)
                
                def py_error_handler(filename, line, function, err, fmt):
                    pass
                
                c_error_handler = ERROR_HANDLER_FUNC(py_error_handler)
                
                try:
                    asound = ctypes.cdll.LoadLibrary('libasound.so.2')
                    asound.snd_lib_error_set_handler(c_error_handler)
                except:
                    pass  # If we can't suppress, continue anyway
        except:
            pass
    
    def __del__(self):
        """Clean up PyAudio instance."""
        if hasattr(self, 'pa'):
            self.pa.terminate()
    
    def list_devices(self) -> list:
        """List available audio input devices."""
        devices = []
        for i in range(self.pa.get_device_count()):
            info = self.pa.get_device_info_by_index(i)
            if info["maxInputChannels"] > 0:
                devices.append({
                    "index": i,
                    "name": info["name"],
                    "channels": info["maxInputChannels"],
                    "sample_rate": int(info["defaultSampleRate"])
                })
        return devices
    
    def record(self, duration: float, device_index: Optional[int] = None) -> np.ndarray:
        """Record audio for a specified duration."""
        frames = []
        
        stream = self.pa.open(
            format=self.pyaudio.paInt16,
            channels=self.channels,
            rate=self.sample_rate,
            input=True,
            input_device_index=device_index,
            frames_per_buffer=self.chunk_size
        )
        
        try:
            num_chunks = int(self.sample_rate / self.chunk_size * duration)
            for _ in range(num_chunks):
                data = stream.read(self.chunk_size, exception_on_overflow=False)
                frames.append(data)
        finally:
            stream.stop_stream()
            stream.close()
        
        # Convert to numpy array
        audio_data = b''.join(frames)
        return np.frombuffer(audio_data, dtype=np.int16)
    
    def stream(self, callback: Callable[[np.ndarray], Any], 
               device_index: Optional[int] = None):
        """Stream audio continuously to a callback function."""
        self.is_recording = True
        
        def audio_callback(in_data, frame_count, time_info, status):
            if self.is_recording:
                audio_array = np.frombuffer(in_data, dtype=np.int16)
                callback(audio_array)
                return (in_data, self.pyaudio.paContinue)
            else:
                return (in_data, self.pyaudio.paComplete)
        
        self.stream = self.pa.open(
            format=self.pyaudio.paInt16,
            channels=self.channels,
            rate=self.sample_rate,
            input=True,
            input_device_index=device_index,
            frames_per_buffer=self.chunk_size,
            stream_callback=audio_callback
        )
        
        self.stream.start_stream()
    
    def stop_stream(self):
        """Stop the audio stream."""
        self.is_recording = False
        if self.stream and self.stream.is_active():
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None
    
    def test_device(self, device_index: Optional[int] = None) -> bool:
        """Test if a device is working."""
        try:
            audio = self.record(0.1, device_index)
            return len(audio) > 0 and np.max(np.abs(audio)) > 0
        except Exception as e:
            logger.error(f"Device test failed: {e}")
            return False


class SoundDeviceBackend(AudioBackend):
    """Sounddevice backend implementation."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            import sounddevice as sd
            self.sd = sd
            self.stream = None
            self.audio_queue = queue.Queue()
            
            # Set default sample rate for WSL2
            self.sd.default.samplerate = self.sample_rate
            self.sd.default.channels = self.channels
            
        except ImportError:
            raise ImportError("Sounddevice not installed. Run: pip install sounddevice")
    
    def list_devices(self) -> list:
        """List available audio input devices."""
        devices = []
        for i, device in enumerate(self.sd.query_devices()):
            if device["max_input_channels"] > 0:
                devices.append({
                    "index": i,
                    "name": device["name"],
                    "channels": device["max_input_channels"],
                    "sample_rate": int(device["default_samplerate"])
                })
        return devices
    
    def record(self, duration: float, device_index: Optional[int] = None) -> np.ndarray:
        """Record audio for a specified duration."""
        recording = self.sd.rec(
            int(duration * self.sample_rate),
            samplerate=self.sample_rate,
            channels=self.channels,
            dtype=np.int16,
            device=device_index
        )
        self.sd.wait()  # Wait for recording to complete
        return recording.flatten()
    
    def stream(self, callback: Callable[[np.ndarray], Any], 
               device_index: Optional[int] = None):
        """Stream audio continuously to a callback function."""
        self.is_recording = True
        
        def audio_callback(indata, frames, time, status):
            if status:
                logger.warning(f"Sounddevice status: {status}")
            if self.is_recording:
                callback(indata.flatten())
        
        self.stream = self.sd.InputStream(
            callback=audio_callback,
            channels=self.channels,
            samplerate=self.sample_rate,
            device=device_index,
            dtype=np.int16
        )
        
        self.stream.start()
    
    def stop_stream(self):
        """Stop the audio stream."""
        self.is_recording = False
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None
    
    def test_device(self, device_index: Optional[int] = None) -> bool:
        """Test if a device is working."""
        try:
            audio = self.record(0.1, device_index)
            return len(audio) > 0 and np.max(np.abs(audio)) > 0
        except Exception as e:
            logger.error(f"Device test failed: {e}")
            return False


def get_audio_backend(backend_name: Optional[str] = None) -> AudioBackend:
    """
    Get an audio backend instance.
    
    Args:
        backend_name: Name of the backend ('pyaudio' or 'sounddevice')
                     If None, tries PyAudio first, then Sounddevice
    
    Returns:
        An instance of AudioBackend
    """
    if backend_name == 'pyaudio':
        return PyAudioBackend()
    elif backend_name == 'sounddevice':
        return SoundDeviceBackend()
    else:
        # Try PyAudio first, fall back to Sounddevice
        try:
            return PyAudioBackend()
        except ImportError:
            logger.info("PyAudio not available, using Sounddevice")
            try:
                return SoundDeviceBackend()
            except ImportError:
                raise ImportError(
                    "No audio backend available. Install either PyAudio or sounddevice"
                )