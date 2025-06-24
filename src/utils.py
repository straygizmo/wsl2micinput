"""
Utility functions for WSL2 audio support
"""

import os
import subprocess
import platform
from typing import List, Dict, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


def is_wsl2() -> bool:
    """Check if running on WSL2."""
    try:
        with open("/proc/version", "r") as f:
            version_info = f.read().lower()
            return "microsoft" in version_info and "wsl2" in version_info
    except:
        return False


def check_wsl2_audio() -> Dict[str, any]:
    """
    Check WSL2 audio configuration and support.
    
    Returns:
        Dictionary with audio configuration status
    """
    result = {
        "is_wsl2": is_wsl2(),
        "wslg_available": os.path.exists("/mnt/wslg"),
        "pulse_server": os.environ.get("PULSE_SERVER"),
        "display": os.environ.get("DISPLAY"),
        "audio_available": False,
        "issues": []
    }
    
    if not result["is_wsl2"]:
        result["issues"].append("Not running on WSL2")
        return result
    
    if not result["wslg_available"]:
        result["issues"].append("WSLg not detected - run 'wsl --update'")
    
    if not result["pulse_server"]:
        result["issues"].append("PULSE_SERVER not set - audio may not work")
    
    # Check PulseAudio connection
    try:
        subprocess.run(
            ["pactl", "info"], 
            capture_output=True, 
            check=True,
            timeout=2
        )
        result["audio_available"] = True
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
        result["issues"].append("Cannot connect to PulseAudio server")
    
    return result


def list_audio_devices() -> List[Dict[str, any]]:
    """
    List available audio input devices.
    
    Returns:
        List of dictionaries containing device information
    """
    devices = []
    
    # Try PyAudio first
    try:
        import pyaudio
        p = pyaudio.PyAudio()
        
        for i in range(p.get_device_count()):
            info = p.get_device_info_by_index(i)
            if info["maxInputChannels"] > 0:
                devices.append({
                    "index": i,
                    "name": info["name"],
                    "channels": info["maxInputChannels"],
                    "sample_rate": int(info["defaultSampleRate"]),
                    "backend": "pyaudio"
                })
        
        p.terminate()
    except Exception as e:
        logger.warning(f"PyAudio device enumeration failed: {e}")
    
    # Try sounddevice as fallback
    if not devices:
        try:
            import sounddevice as sd
            for i, device in enumerate(sd.query_devices()):
                if device["max_input_channels"] > 0:
                    devices.append({
                        "index": i,
                        "name": device["name"],
                        "channels": device["max_input_channels"],
                        "sample_rate": int(device["default_samplerate"]),
                        "backend": "sounddevice"
                    })
        except Exception as e:
            logger.warning(f"Sounddevice enumeration failed: {e}")
    
    return devices


def get_default_input_device() -> Optional[Dict[str, any]]:
    """
    Get the default audio input device.
    
    Returns:
        Device information dictionary or None if no device found
    """
    devices = list_audio_devices()
    
    if not devices:
        return None
    
    # Try to find a device with "default" in the name
    for device in devices:
        if "default" in device["name"].lower():
            return device
    
    # Return the first available device
    return devices[0]


def test_audio_input(duration: float = 1.0) -> Tuple[bool, str]:
    """
    Test if audio input is working.
    
    Args:
        duration: Duration of test recording in seconds
        
    Returns:
        Tuple of (success, message)
    """
    try:
        import pyaudio
        import numpy as np
        
        p = pyaudio.PyAudio()
        
        # Get default device
        device = get_default_input_device()
        if not device:
            return False, "No audio input device found"
        
        # Try to open stream
        stream = p.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=16000,
            input=True,
            input_device_index=device["index"],
            frames_per_buffer=1024
        )
        
        # Record some audio
        frames = []
        for _ in range(int(16000 / 1024 * duration)):
            data = stream.read(1024, exception_on_overflow=False)
            frames.append(data)
        
        stream.stop_stream()
        stream.close()
        p.terminate()
        
        # Check if we got any audio
        audio_data = b''.join(frames)
        audio_array = np.frombuffer(audio_data, dtype=np.int16)
        
        # Check if audio has any signal (not just silence)
        if np.max(np.abs(audio_array)) > 100:  # Threshold for noise
            return True, "Audio input working correctly"
        else:
            return False, "Audio input detected but only silence recorded"
            
    except Exception as e:
        return False, f"Audio test failed: {str(e)}"


def setup_wsl2_audio_env():
    """
    Set up environment variables for WSL2 audio if needed.
    """
    # Check if PULSE_SERVER is already set
    if os.environ.get("PULSE_SERVER"):
        return
    
    # Check for WSLg PulseAudio server
    if os.path.exists("/mnt/wslg/PulseServer"):
        os.environ["PULSE_SERVER"] = "/mnt/wslg/PulseServer"
        logger.info("Set PULSE_SERVER to WSLg PulseAudio server")
    
    # Ensure DISPLAY is set for WSLg
    if not os.environ.get("DISPLAY") and os.path.exists("/mnt/wslg"):
        os.environ["DISPLAY"] = ":0"
        logger.info("Set DISPLAY to :0 for WSLg")