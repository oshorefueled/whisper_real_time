#!/usr/bin/env python3

import argparse
import os
import yaml
import numpy as np
import speech_recognition as sr
import threading
import time
import logging
from datetime import datetime, timedelta
from queue import Queue
from sys import platform

from azure_whisper_client import AzureWhisperClient
from keyboard_listener import HotkeyManager

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("AzureTranscriber")

def load_config(config_path='config.yaml'):
    """Load configuration from YAML file"""
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")
        
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

class AzureTranscriber:
    """Handles audio recording and transcription using Azure Whisper API"""
    
    def __init__(self, config_path='config.yaml'):
        # Load configuration
        self.config = load_config(config_path)
        
        # Initialize Azure client
        self.azure_client = AzureWhisperClient(config_path)
        
        # Audio recording settings
        self.energy_threshold = self.config['audio']['energy_threshold']
        self.record_timeout = self.config['audio']['record_timeout']
        self.phrase_timeout = self.config['audio']['phrase_timeout']
        self.sample_rate = self.config['audio']['sample_rate']
        
        # Behavior settings
        self.batch_mode = self.config.get('behavior', {}).get('batch_mode', True)
        
        # Rate limiting buffer settings - calculated based on Azure limitations
        self.buffer_size_seconds = 60 / self.azure_client.MAX_REQUESTS_PER_MINUTE
        logger.info(f"Using buffer size of {self.buffer_size_seconds:.1f} seconds to optimize API usage")
        logger.info(f"Batch mode {'enabled' if self.batch_mode else 'disabled'}")
        
        # Recording state
        self.is_recording = False
        self.phrase_time = None
        self.data_queue = Queue()
        self.current_audio_data = b''
        self.transcription = ['']
        self.last_api_call_time = 0
        self.accumulated_audio_time = 0
        
        # Initialize recorder
        self.recorder = sr.Recognizer()
        self.recorder.energy_threshold = self.energy_threshold
        self.recorder.dynamic_energy_threshold = False
        
        # Setup microphone
        self._setup_microphone()
        
        # Recording thread
        self.recording_thread = None
        self.stop_recording = threading.Event()
        
    def _setup_microphone(self):
        """Setup the microphone source"""
        # Handle Linux-specific microphone selection
        if 'linux' in platform:
            for index, name in enumerate(sr.Microphone.list_microphone_names()):
                print(f"Microphone {index}: {name}")
            
            # Use the first microphone by default
            self.source = sr.Microphone(sample_rate=self.sample_rate, device_index=0)
        else:
            self.source = sr.Microphone(sample_rate=self.sample_rate)
        
        # Adjust for ambient noise - only do this once during setup
        with self.source as source:
            self.recorder.adjust_for_ambient_noise(source)
            
    def record_callback(self, _, audio):
        """Callback function for audio recording"""
        if self.is_recording:
            data = audio.get_raw_data()
            self.data_queue.put(data)
            self.accumulated_audio_time += self.record_timeout
            
    def start_stop_recording(self, start):
        """Start or stop recording based on hotkey press"""
        if start and not self.is_recording:
            # Start recording
            self.is_recording = True
            self.transcription = ['']
            self.current_audio_data = b''
            self.accumulated_audio_time = 0
            self.stop_recording.clear()
            
            logger.info("Starting recording")
            
            # Create a new background listener each time
            # This prevents the "audio source is already inside a context manager" error
            self.listener = self.recorder.listen_in_background(
                self.source, 
                self.record_callback, 
                phrase_time_limit=self.record_timeout
            )
            
            # Only start processing thread for real-time mode
            if not self.batch_mode:
                # Start processing thread
                self.recording_thread = threading.Thread(target=self._process_audio)
                self.recording_thread.daemon = True
                self.recording_thread.start()
            
            return None
            
        elif not start and self.is_recording:
            # Stop recording
            logger.info("Stopping recording")
            self.is_recording = False
            self.stop_recording.set()
            
            # Stop the background listener
            if hasattr(self, 'listener'):
                self.listener(wait_for_stop=False)
                
            # Wait for processing to complete if not in batch mode
            if not self.batch_mode and self.recording_thread and self.recording_thread.is_alive():
                self.recording_thread.join(timeout=2.0)
            
            # In batch mode, process all audio when recording stops
            if self.batch_mode:
                # Get all accumulated audio data
                audio_data = self._get_all_audio_data()
                
                if len(audio_data) > 0:
                    audio_size_mb = len(audio_data) / 1024 / 1024
                    audio_duration = len(audio_data) / 2 / self.sample_rate  # 16-bit = 2 bytes per sample
                    
                    logger.info(f"Processing {audio_size_mb:.2f}MB of audio in batch mode ({audio_duration:.1f} seconds)")
                    
                    try:
                        # Convert to numpy array
                        audio_np = np.frombuffer(audio_data, dtype=np.int16)
                        
                        # Transcribe the entire recording
                        transcript = self.azure_client.transcribe_audio(audio_np, self.sample_rate)
                        
                        if transcript:
                            logger.info(f"Transcription: {transcript}")
                            self.transcription = [transcript]
                            
                            # Handle clipboard operations
                            if self.config.get('behavior', {}).get('append_to_clipboard', False):
                                self._update_clipboard(transcript)
                    except Exception as e:
                        logger.error(f"Error in batch processing: {str(e)}")
                else:
                    logger.warning("No audio data to process")
                
            # Return the final transcription
            return ' '.join(self.transcription).strip()
        
        return None
            
    def _process_audio(self):
        """Process audio data and get transcriptions - only used in real-time mode"""
        while not self.stop_recording.is_set():
            now = datetime.utcnow()
            
            # Pull raw recorded audio from the queue
            if not self.data_queue.empty():
                phrase_complete = False
                
                # If enough time passed between recordings, consider the phrase complete
                if self.phrase_time and now - self.phrase_time > timedelta(seconds=self.phrase_timeout):
                    phrase_complete = True
                    
                # This is the last time we received new audio data
                self.phrase_time = now
                
                # Get audio data
                while not self.data_queue.empty():
                    self.current_audio_data += self.data_queue.get()
                
                # Only call the API if we've accumulated enough audio or if it's been forced
                # to optimize for Azure's rate limits
                audio_size_mb = len(self.current_audio_data) / 1024 / 1024
                time_since_last_call = time.time() - self.last_api_call_time
                
                should_transcribe = (
                    # Force transcription on phrase completion
                    phrase_complete or
                    # Or we've accumulated enough audio to optimize API calls (but not too much)
                    (self.accumulated_audio_time >= self.buffer_size_seconds and 
                     audio_size_mb < (self.azure_client.MAX_AUDIO_SIZE_BYTES / 1024 / 1024 * 0.9)) or
                    # Or this is the final processing before stopping
                    self.stop_recording.is_set()
                )
                
                if should_transcribe:
                    # Convert audio data to numpy array
                    audio_np = np.frombuffer(self.current_audio_data, dtype=np.int16)
                    
                    # Transcribe audio
                    logger.info(f"Transcribing {audio_size_mb:.2f}MB of audio "
                              f"({self.accumulated_audio_time:.1f} seconds)")
                    text = self.azure_client.transcribe_audio(audio_np, self.sample_rate)
                    self.last_api_call_time = time.time()
                    
                    # Reset accumulated audio time
                    self.accumulated_audio_time = 0
                    
                    # Update transcription
                    if phrase_complete:
                        self.transcription.append(text)
                    else:
                        self.transcription[-1] = text
                    
                    # Clear audio buffer after successful transcription
                    self.current_audio_data = b''
                    
                # Print current transcription status
                os.system('cls' if os.name=='nt' else 'clear')
                print("Recording in progress...")
                print(f"Buffer: {audio_size_mb:.2f}MB / {self.accumulated_audio_time:.1f}s")
                print(f"API calls available: {min(3, 3 - len(self.azure_client.request_timestamps))}/3 per minute")
                print("\nTranscription:")
                for line in self.transcription:
                    print(line)
                print('', end='', flush=True)
                    
            # Prevent CPU hogging
            time.sleep(0.1)
            
    def _get_all_audio_data(self):
        """Collect all audio data from the queue"""
        audio_data = self.current_audio_data
        
        # Get remaining audio from queue
        while not self.data_queue.empty():
            data = self.data_queue.get()
            audio_data += data
            
        return audio_data
        
    def _update_clipboard(self, text):
        """Update clipboard with transcription"""
        try:
            if self.config.get('behavior', {}).get('append_to_clipboard', False):
                import pyperclip
                
                if self.config.get('behavior', {}).get('auto_paste', False):
                    # Automatically paste the text
                    current = pyperclip.paste()
                    if current:
                        pyperclip.copy(current + " " + text)
                    else:
                        pyperclip.copy(text)
                    logger.info(f"Updated clipboard with transcription")
                else:
                    # Just copy the text
                    pyperclip.copy(text)
                    logger.info(f"Copied transcription to clipboard")
        except Exception as e:
            logger.error(f"Error updating clipboard: {str(e)}")
            
def main():
    parser = argparse.ArgumentParser(description="Real-time Azure Whisper Transcription")
    parser.add_argument('--config', default='config.yaml', help='Path to config file')
    args = parser.parse_args()
    
    # Initialize transcriber
    transcriber = AzureTranscriber(args.config)
    
    # Initialize hotkey manager
    hotkey_manager = HotkeyManager(
        config_path=args.config,
        transcription_callback=transcriber.start_stop_recording
    )
    
    print("Starting Azure Whisper Transcription Service")
    print(f"Press {hotkey_manager.hotkey_str} to start/stop recording")
    print("Note: Azure API limits to 3 requests per minute and 25MB per request")
    
    # Start the hotkey listener
    hotkey_manager.start()
    
    try:
        # Keep the program running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down...")
        hotkey_manager.stop()
        
if __name__ == "__main__":
    main()
