#!/usr/bin/env python3
"""
Test script for rate limit UI enhancements
"""

import os
import time
import numpy as np
from azure_whisper_client import AzureWhisperClient
from utils.progress_bar import create_progress_bar

def simulate_rate_limit():
    """Simulate hitting the rate limit"""
    client = AzureWhisperClient()
    
    # Create dummy audio data (1 second of silence)
    sample_rate = 16000
    audio_data = np.zeros(sample_rate, dtype=np.int16)
    
    # Make multiple requests to trigger rate limit
    results = []
    
    for i in range(5):
        print(f"\nRequest {i+1}/5:")
        
        # Get wait time without actually waiting
        wait_time, requests_available = client._check_rate_limit()
        print(f"Requests available: {requests_available}/3")
        
        if wait_time > 0:
            print(f"Rate limit hit! Would need to wait {wait_time:.1f} seconds")
            
            # Show a progress bar simulation
            print("Progress simulation:")
            for progress in range(0, 101, 10):
                bar = create_progress_bar(progress/100)
                print(f"\r{bar}", end='', flush=True)
                time.sleep(0.2)
            print()
        else:
            # Make the request and record it
            print("Request would be sent now")
            client._record_request()
            
        # Show current timestamp buffer
        print(f"Current timestamps: {len(client.request_timestamps)}")
        
        time.sleep(1)

def test_queue_system():
    """Test the transcription queue system"""
    from transcribe_azure import AzureTranscriber
    
    # Initialize the transcriber
    transcriber = AzureTranscriber()
    
    # Create some dummy audio data
    sample_rate = 16000
    audio_data1 = np.zeros(sample_rate, dtype=np.int16)  # 1 second
    audio_data2 = np.zeros(sample_rate * 2, dtype=np.int16)  # 2 seconds
    audio_data3 = np.zeros(sample_rate * 3, dtype=np.int16)  # 3 seconds
    
    # Add jobs to the queue
    print("Adding jobs to queue...")
    job_id1 = transcriber._add_to_queue(audio_data1)
    print(f"Added job {job_id1} (1 second audio)")
    
    job_id2 = transcriber._add_to_queue(audio_data2)
    print(f"Added job {job_id2} (2 seconds audio)")
    
    job_id3 = transcriber._add_to_queue(audio_data3)
    print(f"Added job {job_id3} (3 seconds audio)")
    
    # Display queue status
    print(f"\nQueue size: {len(transcriber.transcription_queue)}")
    
    # Let the queue processor run for a bit
    print("\nProcessing queue (will take some time due to rate limits)...")
    print("Press Ctrl+C to stop the test")
    
    try:
        while len(transcriber.transcription_queue) > 0:
            # Show current status
            if transcriber.current_status:
                status = transcriber.current_status
                print(f"\rStatus: {status['message']}", end='', flush=True)
                
                # Show progress bar if waiting
                if status['status'] == 'waiting' and 'progress' in status:
                    progress = status['progress']
                    bar = create_progress_bar(progress)
                    print(f" {bar}", end='', flush=True)
            
            time.sleep(0.5)
            
        print("\nAll jobs processed!")
    except KeyboardInterrupt:
        print("\nTest stopped by user")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test rate limit UI enhancements")
    parser.add_argument('--test', choices=['rate_limit', 'queue'], default='rate_limit',
                        help='Which test to run (rate_limit or queue)')
    
    args = parser.parse_args()
    
    if args.test == 'rate_limit':
        simulate_rate_limit()
    elif args.test == 'queue':
        test_queue_system()
