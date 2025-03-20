#!/usr/bin/env python3
"""
Utility functions for creating text-based progress bars
"""

def create_progress_bar(progress, width=40, fill_char='█', empty_char='░'):
    """
    Create a text-based progress bar
    
    Args:
        progress (float): Progress value between 0.0 and 1.0
        width (int): Width of the progress bar in characters
        fill_char (str): Character for filled portion
        empty_char (str): Character for empty portion
        
    Returns:
        str: Text progress bar
    """
    # Clamp progress to valid range
    progress = max(0.0, min(1.0, progress))
    
    # Calculate filled width
    filled_width = int(width * progress)
    
    # Create bar
    bar = fill_char * filled_width + empty_char * (width - filled_width)
    
    return f"[{bar}] {progress*100:.0f}%"
