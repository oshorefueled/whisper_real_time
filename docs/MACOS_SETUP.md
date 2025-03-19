# macOS Setup Guide for Whisper Real-Time

This guide provides specific instructions for setting up and running Whisper Real-Time on macOS.

## Prerequisites

1. **Python 3.7 or higher**
   - macOS usually comes with Python, but you can ensure you have the latest version:
   ```bash
   brew install python
   ```

2. **FFmpeg**
   - Install via Homebrew:
   ```bash
   brew install ffmpeg
   ```

3. **Virtual Environment (Recommended)**
   - Create a virtual environment to avoid conflicts with system Python:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

## Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/oshorefueled/whisper_real_time.git
   cd whisper_real_time
   ```

2. **Create and activate virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

## macOS-Specific Configuration

### Microphone Permissions

macOS requires explicit permissions for microphone access:

1. Go to **System Preferences** → **Security & Privacy** → **Privacy** → **Microphone**
2. Ensure that **Terminal** (or the application you're using to run the script) has permission to access the microphone

### Keyboard Monitoring Permissions

For global hotkey functionality, you'll need to allow keyboard monitoring:

1. Go to **System Preferences** → **Security & Privacy** → **Privacy** → **Input Monitoring**
2. Add and enable **Terminal** (or the application you're using to run the script)
3. You may need to restart your terminal or application after granting these permissions

### Potential Issues and Solutions

#### Missing PortAudio

If you encounter an error about PortAudio when installing PyAudio:

```bash
brew install portaudio
pip install --global-option='build_ext' --global-option='-I/usr/local/include' --global-option='-L/usr/local/lib' pyaudio
```

#### Accessibility Permissions

If hotkeys aren't working properly:

1. Go to **System Preferences** → **Security & Privacy** → **Privacy** → **Accessibility**
2. Add and enable **Terminal** (or the application you're using)

## Azure API Configuration

1. Edit the `config.yaml` file to add your Azure API credentials:
   ```yaml
   azure:
     api_key: "your-azure-api-key"
     endpoint: "your-azure-endpoint-url"
     region: "your-azure-region"
   ```

2. Customize hotkey as needed (default is Ctrl+Alt+D):
   ```yaml
   hotkeys:
     start_stop: "cmd+alt+d"  # Common macOS alternative
   ```

## Running the Application

1. Make sure your virtual environment is activated:
   ```bash
   source venv/bin/activate
   ```

2. Run the transcription application:
   ```bash
   python3 transcribe_azure.py
   ```

3. Use the configured hotkey (default: Ctrl+Alt+D) to start and stop dictation

## Testing Mac Compatibility

You can verify that all components work correctly on your Mac:

```bash
python3 mac_compatibility_test.py
```

This will test platform detection, keyboard functionality, and clipboard access.

## Troubleshooting

- **Hotkey not working**: Check Input Monitoring and Accessibility permissions in System Preferences
- **Microphone not detected**: Check Microphone permissions in System Preferences
- **PyAudio installation fails**: Install PortAudio using the commands above
- **Clipboard access fails**: Check if you have a clipboard manager that might be interfering

## macOS Keyboard Notes

macOS uses slightly different key combinations than Windows/Linux:

- The Command (⌘) key is often used instead of Ctrl for shortcuts
- Option (⌥) is the same as Alt
- If you prefer Mac-style shortcuts, consider changing your hotkey configuration to use `cmd` instead of `ctrl`
