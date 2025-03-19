#!/usr/bin/env python3
"""
Mac Compatibility Test for Whisper Real-Time

This script performs basic tests of the key components to verify 
they work correctly on macOS.
"""

import platform
import sys
import time
from pynput import keyboard
from pynput.keyboard import Key, Controller
import pyperclip

def test_platform_detection():
    """Test platform detection"""
    print(f"Detected platform: {platform.system()}")
    if platform.system() == "Darwin":
        print("✅ Running on macOS")
    else:
        print("❌ Not running on macOS")
    
    return platform.system() == "Darwin"

def test_keyboard_controller():
    """Test keyboard controller functionality"""
    kb = Controller()
    print("Testing keyboard controller...")
    
    # Test basic key attributes
    has_cmd = hasattr(Key, 'cmd')
    print(f"Command key available: {'✅ Yes' if has_cmd else '❌ No'}")
    
    # On Mac, we should have the cmd key
    expected = platform.system() == "Darwin"
    return has_cmd == expected

def test_clipboard():
    """Test clipboard functionality"""
    print("Testing clipboard functionality...")
    
    test_text = "Testing clipboard on macOS"
    
    try:
        # Save original clipboard
        original = pyperclip.paste()
        
        # Test clipboard
        pyperclip.copy(test_text)
        result = pyperclip.paste()
        
        # Restore original clipboard
        pyperclip.copy(original)
        
        if result == test_text:
            print(f"✅ Clipboard test passed")
            return True
        else:
            print(f"❌ Clipboard test failed")
            print(f"  Expected: {test_text}")
            print(f"  Got: {result}")
            return False
    except Exception as e:
        print(f"❌ Clipboard test error: {e}")
        return False

def test_hotkey_detection():
    """Test basic keyboard event detection"""
    print("Testing keyboard event detection...")
    print("Please press any key in the next 5 seconds...")
    
    key_detected = False
    
    def on_press(key):
        nonlocal key_detected
        key_detected = True
        print(f"Detected key: {key}")
        return False  # Stop listener
        
    # Set up temporary listener
    listener = keyboard.Listener(on_press=on_press)
    listener.start()
    
    # Wait for key press or timeout
    timeout = time.time() + 5
    while not key_detected and time.time() < timeout:
        time.sleep(0.1)
    
    if listener.is_alive():
        listener.stop()
    
    if key_detected:
        print("✅ Keyboard event detection works")
    else:
        print("❌ No keyboard event detected within timeout")
    
    return key_detected

def run_tests(interactive=True):
    """Run all compatibility tests"""
    print("=" * 50)
    print("WHISPER REAL-TIME MAC COMPATIBILITY TEST")
    print("=" * 50)
    print()
    
    tests = [
        ("Platform Detection", test_platform_detection),
        ("Keyboard Controller", test_keyboard_controller),
        ("Clipboard Functionality", test_clipboard),
    ]
    
    # Add interactive test if requested
    if interactive:
        tests.append(("Keyboard Event Detection", test_hotkey_detection))
    
    results = []
    
    for name, test_func in tests:
        print(f"\n--- Testing {name} ---")
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ Test error: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    
    all_passed = True
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")
        all_passed = all_passed and result
    
    print("\nOverall result:", "✅ ALL TESTS PASSED" if all_passed else "❌ SOME TESTS FAILED")
    
    return all_passed

if __name__ == "__main__":
    # Check if we should skip interactive tests
    interactive = "--no-interactive" not in sys.argv
    
    success = run_tests(interactive)
    sys.exit(0 if success else 1)
