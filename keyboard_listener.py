import yaml
import threading
import time
import platform
from pynput import keyboard
import pyperclip
from pynput.keyboard import Key, Controller

# Only import if on Windows
if platform.system() == 'Windows':
    try:
        import win32gui
        import win32con
    except ImportError:
        pass

class HotkeyManager:
    """Manages global hotkeys for controlling transcription"""
    
    def __init__(self, config_path='config.yaml', transcription_callback=None):
        # Load config
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
            
        # Parse hotkey from config
        self.hotkey_str = self.config['hotkeys']['start_stop']
        self.hotkey_combination = self._parse_hotkey(self.hotkey_str)
        
        # Transcription callback (function to start/stop transcription)
        self.transcription_callback = transcription_callback
        
        # Keyboard controller for simulating key presses
        self.keyboard_controller = Controller()
        
        # State tracking
        self.currently_pressed = set()
        self.is_recording = False
        self.listener = None
        
    def _parse_hotkey(self, hotkey_str):
        """Parse a string like 'ctrl+alt+d' into keyboard keys"""
        keys = []
        parts = hotkey_str.lower().split('+')
        
        for part in parts:
            if part == 'ctrl':
                keys.append(Key.ctrl)
            elif part == 'alt':
                keys.append(Key.alt)
            elif part == 'shift':
                keys.append(Key.shift)
            elif part == 'cmd' or part == 'command':
                keys.append(Key.cmd)
            elif part == 'fn':
                keys.append(Key.f1)  # Not really fn, but pynput doesn't have fn key
            elif len(part) == 1:
                keys.append(part)
            else:
                try:
                    keys.append(getattr(Key, part))
                except AttributeError:
                    print(f"Unknown key: {part}")
        
        return keys
    
    def start(self):
        """Start listening for hotkeys"""
        if self.listener is None or not self.listener.is_alive():
            self.listener = keyboard.Listener(
                on_press=self._on_press,
                on_release=self._on_release
            )
            self.listener.start()
            print(f"Hotkey listener started. Use {self.hotkey_str} to start/stop transcription.")
    
    def stop(self):
        """Stop listening for hotkeys"""
        if self.listener and self.listener.is_alive():
            self.listener.stop()
            print("Hotkey listener stopped.")
    
    def _on_press(self, key):
        """Handle key press events"""
        # Normalize the key
        if hasattr(key, 'char'):
            key = key.char
        
        # Add to currently pressed keys
        self.currently_pressed.add(key)
        
        # Check if hotkey combination is pressed
        if all(k in self.currently_pressed for k in self.hotkey_combination):
            # Toggle recording state
            self.is_recording = not self.is_recording
            
            if self.is_recording:
                print("Recording started...")
                if self.transcription_callback:
                    threading.Thread(target=self.transcription_callback, args=(True,)).start()
            else:
                print("Recording stopped...")
                if self.transcription_callback:
                    result = self.transcription_callback(False)
                    if result and self.config['behavior']['append_to_clipboard']:
                        self._handle_transcription_result(result)
    
    def _on_release(self, key):
        """Handle key release events"""
        # Normalize the key
        if hasattr(key, 'char'):
            key = key.char
            
        # Remove from currently pressed keys if present
        if key in self.currently_pressed:
            self.currently_pressed.remove(key)
    
    def _handle_transcription_result(self, text):
        """Handle the transcription result by copying to clipboard and optionally pasting"""
        if not text:
            return
            
        # Get existing clipboard content if append mode is on
        if self.config['behavior'].get('append_to_clipboard', False):
            current_clipboard = pyperclip.paste()
            if current_clipboard:
                text = current_clipboard + " " + text
        
        # Copy to clipboard
        pyperclip.copy(text)
        print(f"Copied to clipboard: {text}")
        
        # Auto paste if enabled
        if self.config['behavior'].get('auto_paste', False):
            time.sleep(0.2)  # Small delay to ensure clipboard is updated
            self._simulate_paste()
    
    def _simulate_paste(self):
        """Simulate ctrl+v or cmd+v to paste text"""
        try:
            # On Mac, use Command+V
            if hasattr(Key, 'cmd'):
                with self.keyboard_controller.pressed(Key.cmd):
                    self.keyboard_controller.press('v')
                    self.keyboard_controller.release('v')
            # On Windows/Linux use Ctrl+V
            else:
                with self.keyboard_controller.pressed(Key.ctrl):
                    self.keyboard_controller.press('v')
                    self.keyboard_controller.release('v')
            
            print("Auto-pasted text")
        except Exception as e:
            print(f"Error simulating paste: {e}")

# Example usage
if __name__ == "__main__":
    # Just for testing hotkey detection
    def dummy_callback(is_start):
        if is_start:
            print("Would start transcription here")
            return None
        else:
            print("Would stop transcription here")
            return "This is a test transcription"
    
    hotkey_manager = HotkeyManager(transcription_callback=dummy_callback)
    hotkey_manager.start()
    
    try:
        # Keep script running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        hotkey_manager.stop()
        print("Exiting...")
