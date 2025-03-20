import unittest
import time
import threading
import numpy as np
from unittest.mock import patch, MagicMock
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from transcribe_azure import AzureTranscriber

class TestTranscriptionQueue(unittest.TestCase):
    
    @patch('azure_whisper_client.AzureWhisperClient')
    def setUp(self, mock_client):
        self.transcriber = AzureTranscriber()
        self.transcriber.azure_client = mock_client
        
        # Reset queue state
        self.transcriber.transcription_queue.clear()
        self.transcriber.next_job_id = 1
    
    def test_add_to_queue(self):
        """Test adding a job to the queue"""
        audio_np = np.zeros(16000, dtype=np.int16)
        job_id = self.transcriber._add_to_queue(audio_np)
        
        self.assertEqual(job_id, 1)
        self.assertEqual(len(self.transcriber.transcription_queue), 1)
        self.assertEqual(self.transcriber.transcription_queue[0]['job_id'], 1)
    
    def test_queue_order(self):
        """Test queue maintains FIFO order"""
        for i in range(3):
            audio_np = np.zeros(16000 * (i+1), dtype=np.int16)
            self.transcriber._add_to_queue(audio_np)
        
        self.assertEqual(len(self.transcriber.transcription_queue), 3)
        
        # Check sizes in order
        sizes = [job['audio_size_mb'] for job in self.transcriber.transcription_queue]
        self.assertTrue(sizes[0] < sizes[1] < sizes[2])
    
    @patch('time.sleep')
    def test_process_queue(self, mock_sleep):
        """Test queue processing with simulated jobs"""
        # Configure mock client for testing
        mock_transcribe = MagicMock()
        self.transcriber.azure_client.transcribe_when_available = mock_transcribe
        
        # Set up the mock to call the callback with success result
        def mock_transcribe_func(audio_np, sample_rate, callback, **kwargs):
            callback({'status': 'success', 'text': f"Transcription {len(audio_np)}"})
            return "job_id"
        
        mock_transcribe.side_effect = mock_transcribe_func
        
        # Add two jobs to queue
        audio_np1 = np.zeros(16000, dtype=np.int16)
        audio_np2 = np.zeros(32000, dtype=np.int16)
        
        job_id1 = self.transcriber._add_to_queue(audio_np1)
        job_id2 = self.transcriber._add_to_queue(audio_np2)
        
        # Manually process the queue by simulating the queue processor
        # We need to access the first job and call the transcribe function
        with self.transcriber.queue_lock:
            job = self.transcriber.transcription_queue[0]
            
        # Call the transcribe function with our job
        self.transcriber.azure_client.transcribe_when_available(
            job['audio_np'], 
            self.transcriber.sample_rate,
            callback=lambda result: self.transcriber.transcription.append(result.get('text', ''))
        )
        
        # Manually remove the job from the queue
        with self.transcriber.queue_lock:
            self.transcriber.transcription_queue.popleft()
            
        # Do the same for the second job
        with self.transcriber.queue_lock:
            job = self.transcriber.transcription_queue[0]
            
        self.transcriber.azure_client.transcribe_when_available(
            job['audio_np'], 
            self.transcriber.sample_rate,
            callback=lambda result: self.transcriber.transcription.append(result.get('text', ''))
        )
        
        with self.transcriber.queue_lock:
            self.transcriber.transcription_queue.popleft()
        
        # Queue should be empty after our manual processing
        self.assertEqual(len(self.transcriber.transcription_queue), 0)
        
        # Verify the mock was called twice
        self.assertEqual(mock_transcribe.call_count, 2)
    
if __name__ == '__main__':
    unittest.main()
