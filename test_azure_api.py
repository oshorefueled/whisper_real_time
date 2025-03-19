#!/usr/bin/env python3
"""
Test script to verify Azure Whisper API connection and functionality.
This script records a short audio sample and sends it to the Azure API for transcription.
"""

import os
import time
import wave
import tempfile
import pyaudio
import numpy as np
import yaml
import logging

from azure_whisper_client import AzureWhisperClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def record_audio(duration=5, sample_rate=16000):
    """Record audio from microphone for specified duration."""
    logger.info(f"Recording {duration} seconds of audio...")
    
    # PyAudio setup
    p = pyaudio.PyAudio()
    stream = p.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=sample_rate,
        input=True,
        frames_per_buffer=1024
    )
    
    # Record audio
    frames = []
    for _ in range(0, int(sample_rate / 1024 * duration)):
        data = stream.read(1024)
        frames.append(data)
    
    # Stop and close the stream
    stream.stop_stream()
    stream.close()
    p.terminate()
    
    # Convert to numpy array
    audio_data = np.frombuffer(b''.join(frames), dtype=np.int16)
    
    logger.info(f"Recorded {len(audio_data) / sample_rate:.1f} seconds of audio")
    return audio_data, sample_rate

def save_audio_to_file(audio_data, sample_rate, filename="test_recording.wav"):
    """Save audio data to a WAV file."""
    with wave.open(filename, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)  # 16-bit audio
        wf.setframerate(sample_rate)
        wf.writeframes(audio_data.tobytes())
    
    file_size = os.path.getsize(filename) / (1024 * 1024)  # Size in MB
    logger.info(f"Saved audio to {filename} ({file_size:.2f} MB)")
    return filename

def main():
    """Main function to test Azure Whisper API."""
    # Initialize Azure client
    client = AzureWhisperClient()
    
    # Record audio
    print("Please speak for 5 seconds...")
    audio_data, sample_rate = record_audio(duration=5, sample_rate=16000)
    
    # Save audio to file (for debugging purposes)
    temp_dir = tempfile.gettempdir()
    audio_file = os.path.join(temp_dir, "azure_test_recording.wav")
    save_audio_to_file(audio_data, sample_rate, audio_file)
    
    # Send to Azure API
    print("\nSending to Azure Whisper API...")
    start_time = time.time()
    
    try:
        result = client.transcribe_audio(audio_data, sample_rate)
        
        # Print results
        elapsed_time = time.time() - start_time
        print(f"\n--- Results (took {elapsed_time:.2f} seconds) ---")
        print(f"Transcription: {result}")
        print("\nAPI test completed successfully!")
        
    except Exception as e:
        print(f"\nError during transcription: {str(e)}")
        logger.error(f"Transcription failed: {str(e)}", exc_info=True)
        print(f"\nCheck the audio file at: {audio_file}")

if __name__ == "__main__":
    main()
