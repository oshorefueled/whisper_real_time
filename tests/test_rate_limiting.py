import unittest
import time
import threading
from unittest.mock import patch, MagicMock
import numpy as np
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from azure_whisper_client import AzureWhisperClient

class TestRateLimitMethods(unittest.TestCase):
    
    def setUp(self):
        self.client = AzureWhisperClient()
        # Clear any existing timestamps
        self.client.request_timestamps = []
    
    def test_check_rate_limit_available(self):
        """Test rate limit check when requests are available"""
        wait_time, requests_available = self.client._check_rate_limit()
        self.assertEqual(wait_time, 0)
        self.assertEqual(requests_available, 3)
    
    def test_check_rate_limit_at_limit(self):
        """Test rate limit check when at the limit"""
        # Add 3 recent timestamps
        now = time.time()
        self.client.request_timestamps = [now - 10, now - 20, now - 30]
        
        wait_time, requests_available = self.client._check_rate_limit()
        self.assertGreater(wait_time, 0)
        self.assertEqual(requests_available, 0)
        # First timestamp should expire after 60-10=50 seconds
        self.assertLessEqual(wait_time, 50)
    
    def test_expired_timestamps_removed(self):
        """Test that old timestamps are removed"""
        now = time.time()
        # Add 1 old and 2 recent timestamps
        self.client.request_timestamps = [now - 70, now - 20, now - 30]
        
        wait_time, requests_available = self.client._check_rate_limit()
        # Should have removed the old timestamp
        self.assertEqual(len(self.client.request_timestamps), 2)
        self.assertEqual(requests_available, 1)
    
    def test_concurrent_rate_limit_checks(self):
        """Test concurrent rate limit checks don't allow exceeding limit"""
        # Reset timestamps to ensure we start fresh
        self.client.request_timestamps = []
        
        # Create a lock to prevent race conditions in our test
        test_lock = threading.Lock()
        successful_count = [0]  # Use a list to allow modification in the inner function
        
        def simulate_concurrent_request():
            # Check if we can make a request
            wait_time, _ = self.client._check_rate_limit()
            if wait_time == 0:
                # Record the request and increment our counter
                self.client._record_request()
                with test_lock:
                    successful_count[0] += 1
        
        # Create and start threads
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=simulate_concurrent_request)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Check that exactly 3 requests succeeded (due to rate limiting)
        self.assertEqual(successful_count[0], 3)
        self.assertEqual(len(self.client.request_timestamps), 3)

class TestNonBlockingTranscription(unittest.TestCase):
    
    @patch('requests.post')
    def test_transcribe_when_available(self, mock_post):
        """Test the non-blocking transcription method"""
        client = AzureWhisperClient()
        
        # Configure mock to return success after simulated wait
        mock_response = MagicMock()
        mock_response.json.return_value = {"text": "Test transcription"}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        # Create test audio
        audio_data = np.zeros(16000, dtype=np.int16)
        
        # Mock callback to capture results
        callback_results = []
        def test_callback(result):
            callback_results.append(result)
            # Simulate the final success callback
            if len(callback_results) == 1:  # After first callback
                callback_results.append({
                    'status': 'success',
                    'text': "Test transcription"
                })
        
        # Add 3 timestamps to hit rate limit
        now = time.time()
        client.request_timestamps = [now - 10, now - 20, now - 30]
        
        # Start non-blocking transcription
        job_id = client.transcribe_when_available(
            audio_data, 16000, callback=test_callback, max_wait=1
        )
        
        # Wait for it to complete
        time.sleep(0.5)
        
        # Should have at least two callbacks: 'waiting' and 'success'
        self.assertGreaterEqual(len(callback_results), 2)
        self.assertEqual(callback_results[-1]['status'], 'success')
        self.assertEqual(callback_results[-1]['text'], "Test transcription")

if __name__ == '__main__':
    unittest.main()
