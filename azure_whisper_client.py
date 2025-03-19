import os
import requests
import yaml
import json
import numpy as np
import tempfile
import wave
import time
import logging
from threading import Lock

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("AzureWhisperClient")

class AzureWhisperClient:
    """Client to handle Azure OpenAI Whisper model for speech-to-text"""
    
    # Azure Whisper model limitations
    MAX_AUDIO_SIZE_BYTES = 25 * 1024 * 1024  # 25MB max request size
    MAX_REQUESTS_PER_MINUTE = 3  # Rate limit of 3 requests per minute
    
    def __init__(self, config_path='config.yaml'):
        # Load config
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        # Azure API settings
        self.api_key = self.config['azure']['api_key']
        self.endpoint = self.config['azure']['endpoint']
        self.deployment_name = self.config['azure']['deployment_name']
        
        # Get API version from config or use default
        self.API_VERSION = self.config['azure'].get('api_version', "2024-06-01")
        
        # Clean up endpoint URL if it already contains deployment info
        if '/deployments/' in self.endpoint:
            # Extract the base endpoint URL
            base_url_parts = self.endpoint.split('/openai/')
            if len(base_url_parts) > 1:
                self.endpoint = base_url_parts[0]
                logger.info(f"Extracted base endpoint: {self.endpoint}")
        
        # Rate limiting tracker
        self.request_timestamps = []
        self.request_lock = Lock()
        
        logger.info("Azure OpenAI Whisper client initialized")
        logger.info(f"Using model: whisper large v2 (001)")
        logger.info(f"API endpoint: {self.endpoint}")
        logger.info(f"Deployment name: {self.deployment_name}")
        logger.info(f"Max audio size: {self.MAX_AUDIO_SIZE_BYTES/1024/1024:.1f}MB")
        logger.info(f"Rate limit: {self.MAX_REQUESTS_PER_MINUTE} requests per minute")

    def _check_rate_limit(self):
        """
        Check if we're within rate limits, and if not, wait until we can make another request
        Returns: Seconds to wait before making request (0 if no wait needed)
        """
        with self.request_lock:
            # Remove timestamps older than 1 minute
            current_time = time.time()
            self.request_timestamps = [ts for ts in self.request_timestamps 
                                     if current_time - ts < 60]
            
            # If we haven't hit the rate limit, return 0 (no wait needed)
            if len(self.request_timestamps) < self.MAX_REQUESTS_PER_MINUTE:
                return 0
            
            # Calculate time to wait until oldest timestamp is 60 seconds old
            wait_time = 60 - (current_time - self.request_timestamps[0])
            return max(0, wait_time)
    
    def _record_request(self):
        """Record that a request was made for rate limiting purposes"""
        with self.request_lock:
            self.request_timestamps.append(time.time())

    def transcribe_audio(self, audio_data, sample_rate=16000):
        """
        Transcribe audio using Azure OpenAI Whisper API
        
        Args:
            audio_data (numpy.ndarray): Audio data as numpy array
            sample_rate (int): Sample rate of audio data
            
        Returns:
            str: Transcription result
        """
        try:
            # Check audio size
            audio_size_bytes = len(audio_data) * 2  # 16-bit audio = 2 bytes per sample
            audio_size_mb = audio_size_bytes / (1024 * 1024)
            
            if audio_size_bytes > self.MAX_AUDIO_SIZE_BYTES:
                logger.warning(f"Audio size ({audio_size_mb:.2f}MB) exceeds maximum ({self.MAX_AUDIO_SIZE_BYTES/1024/1024:.1f}MB). Truncating.")
                max_samples = self.MAX_AUDIO_SIZE_BYTES // 2
                audio_data = audio_data[:max_samples]
                audio_size_bytes = len(audio_data) * 2
                audio_size_mb = audio_size_bytes / (1024 * 1024)
            
            # Create temporary WAV file
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=True) as temp_file:
                with wave.open(temp_file.name, 'wb') as wf:
                    wf.setnchannels(1)
                    wf.setsampwidth(2)  # 16-bit audio
                    wf.setframerate(sample_rate)
                    wf.writeframes(audio_data.tobytes())
                
                # Check rate limiting
                wait_time = self._check_rate_limit()
                if wait_time > 0:
                    logger.warning(f"Rate limit reached. Waiting {wait_time:.1f} seconds before making request.")
                    time.sleep(wait_time)
                    
                logger.info(f"Sending {audio_size_mb:.2f}MB audio to Azure OpenAI Whisper API")
                
                # Record this request for rate limiting
                self._record_request()
                
                # Construct the Azure OpenAI API URL
                if '/openai/' in self.endpoint:
                    url = f"{self.endpoint}/deployments/{self.deployment_name}/audio/transcriptions?api-version={self.API_VERSION}"
                else:
                    url = f"{self.endpoint}/openai/deployments/{self.deployment_name}/audio/transcriptions?api-version={self.API_VERSION}"
                
                # Set up headers
                headers = {
                    'api-key': self.api_key
                }
                
                # Convert language code to ISO-639-1 format if needed
                language = self.config['azure']['language']
                if '-' in language:
                    language = language.split('-')[0].lower()
                
                # Prepare the multipart form data
                files = {
                    'file': (os.path.basename(temp_file.name), open(temp_file.name, 'rb'), 'audio/wav')
                }
                data = {
                    'model': 'whisper-1',
                    'language': language
                }
                
                # Make the API request
                response = requests.post(
                    url=url,
                    headers=headers,
                    files=files,
                    data=data
                )
                
                response.raise_for_status()  # Raise exception for HTTP errors
                result = response.json()
                
                # Extract transcription from the response
                if 'text' in result:
                    return result['text']
                else:
                    logger.warning(f"Unexpected response format: {result}")
                    return ""
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error calling Azure OpenAI API: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response status: {e.response.status_code}")
                logger.error(f"Response content: {e.response.text}")
            return ""

    def _numpy_to_temp_wav_file(self, audio_np, sample_rate):
        """Convert numpy array to a temporary WAV file and return the file object"""
        temp_wav = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
        
        # Ensure the audio is in the right format (16-bit PCM)
        if audio_np.dtype != np.int16:
            audio_np = (audio_np * 32767).astype(np.int16)
        
        # Write WAV file
        with wave.open(temp_wav.name, 'wb') as wf:
            wf.setnchannels(1)  # Mono
            wf.setsampwidth(2)  # 16-bit
            wf.setframerate(sample_rate)
            wf.writeframes(audio_np.tobytes())
        
        return temp_wav

# Example usage
if __name__ == "__main__":
    # Test with a sample audio file
    client = AzureWhisperClient()
    
    # Load sample audio (replace with your own test file)
    import speech_recognition as sr
    
    # Record a short sample
    r = sr.Recognizer()
    with sr.Microphone(sample_rate=16000) as source:
        print("Say something...")
        audio = r.listen(source)
        print("Processing...")
    
    # Get raw audio data and transcribe
    audio_data = np.frombuffer(audio.get_raw_data(), dtype=np.int16).astype(np.float32) / 32768.0
    transcription = client.transcribe_audio(audio_data)
    print(f"Transcription: {transcription}")
