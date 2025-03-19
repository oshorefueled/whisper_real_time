# Implementation Plan for Whisper Real-Time Enhancements

## Current Implementation

The project has been enhanced with Azure API integration, global hotkey support, and clipboard functionality. Below is a detailed overview of the implementation.

### Project Structure

```
whisper_real_time/
├── azure_whisper_client.py     # Azure API integration
├── keyboard_listener.py        # Global hotkey handling
├── transcribe_azure.py         # Main application
├── transcribe_demo.py          # Original local Whisper demo
├── config.yaml                 # Configuration settings
├── requirements.txt            # Project dependencies
├── README.md                   # Project documentation
└── Implementation.MD           # Implementation details (this file)
```

### Core Components

#### 1. Azure Whisper API Client (`azure_whisper_client.py`)

This module handles communication with the Azure Cognitive Services Speech-to-Text API, replacing the local Whisper model in the original implementation.

Key features:
- Authentication with Azure API using credentials from config.yaml
- Audio format conversion for API compatibility
- Error handling and retry logic
- Transcription result processing

Core methods:
- `transcribe_audio()`: Sends audio data to Azure API and returns transcription
- `_numpy_to_wav_bytes()`: Converts numpy audio array to WAV format for API

#### 2. Keyboard Hook System (`keyboard_listener.py`)

Manages global hotkeys to start and stop dictation from anywhere in the system.

Key features:
- Cross-platform support (Mac, Windows, Linux)
- Configurable hotkey combinations via config.yaml
- Clipboard integration for transcription results
- Optional auto-paste functionality

Core methods:
- `start()`: Begins listening for configured hotkeys
- `_on_press()` and `_on_release()`: Handle keyboard events
- `_handle_transcription_result()`: Processes transcription for clipboard
- `_simulate_paste()`: Platform-specific paste simulation

#### 3. Audio Recording and Transcription (`transcribe_azure.py`)

The main application that coordinates audio recording and transcription.

Key features:
- Continuous audio recording using SpeechRecognition library
- Queuing and processing of audio segments
- Integration with Azure client and hotkey system
- Real-time feedback during transcription

Core methods:
- `start_stop_recording()`: Toggles recording state
- `record_callback()`: Receives audio data from microphone
- `_process_audio()`: Processes audio queue and manages transcription

#### 4. Configuration System (`config.yaml`)

YAML-based configuration for all application settings:

```yaml
azure:
  api_key: "your-azure-api-key"
  endpoint: "your-azure-endpoint-url"
  region: "your-azure-region"
  language: "en-US"

hotkeys:
  start_stop: "ctrl+alt+d"

behavior:
  append_to_clipboard: true
  auto_paste: true
  batch_mode: true  # New batch mode setting

audio:
  sample_rate: 16000
  energy_threshold: 1000
  record_timeout: 2.0
  phrase_timeout: 3.0
```

### Data Flow and Processing

1. **Initialization**:
   - Load configuration from config.yaml
   - Set up Azure client with API credentials
   - Initialize audio recording with specified parameters
   - Start keyboard listener with configured hotkey

2. **Recording Process**:
   - User presses hotkey to start recording
   - Audio is captured in short segments (default: 2 seconds)
   - Raw audio data is queued for processing
   - Real-time feedback is provided in console

3. **Transcription Process**:
   - Audio data is converted to appropriate format
   - Data is sent to Azure API for transcription
   - Results are continuously updated and displayed
   - Phrase boundaries are detected based on silence

4. **Result Handling**:
   - User presses hotkey again to stop recording
   - Final transcription is returned
   - Text is copied to clipboard
   - If auto-paste is enabled, text is pasted at cursor position

### Azure Whisper API Integration

### API Limitations

The Azure Whisper model (which corresponds to whisper large v2) has the following limitations that our implementation addresses:

1. **Request Size Limit**: Maximum 25MB of audio can be converted from speech to text per API request
   - Implementation: The `AzureWhisperClient` enforces this limit by checking audio size before sending and truncating if necessary

2. **Rate Limiting**: Limited to 3 requests per minute per API key
   - Implementation: The client maintains a queue of request timestamps and enforces rate limiting with a wait mechanism

3. **Model Capabilities**: Supports both speech recognition and translation tasks, with the ability to transcribe speech audio into text in the language it is spoken, as well as translate into English

### Optimizations

To work within these limitations while providing a seamless user experience, our implementation includes:

1. **Buffered Audio Processing**: Audio is accumulated into buffers to optimize API usage
   - The system calculates an optimal buffer size based on the rate limitations (20 seconds of audio per API call)
   - This reduces the number of API calls made for short audio fragments

2. **Adaptive API Calling**: The transcriber only sends API requests when:
   - A complete phrase is detected (natural pause in speech)
   - Enough audio has accumulated to warrant an API call
   - The recording is being stopped
   
3. **Transparent User Feedback**: Users receive real-time information about:
   - Current buffer size
   - Accumulated audio time
   - Available API calls within the rate limit
   - Current transcription status

### Batch Mode Processing

The latest addition to the implementation is batch mode processing. This feature allows users to process audio after recording stops, optimizing API usage by making a single request per recording. The batch mode is configurable via the `batch_mode` setting in config.yaml.

### Mac Compatibility

The implementation is fully compatible with macOS:

- Uses pynput library for cross-platform keyboard handling
- Detects Mac-specific keyboard layout (using Cmd instead of Ctrl for paste)
- Uses platform-agnostic audio capture via SpeechRecognition
- Conditionally imports Windows-specific libraries only when on Windows

### Future Enhancements

The following areas can be further enhanced:

1. **Error Handling and Resilience**:
   - More robust error recovery for API failures
   - Offline fallback options

2. **Performance Optimization**:
   - Reduce latency in audio processing
   - Optimize memory usage for long recordings

3. **Advanced Language Features**:
   - Punctuation and formatting improvements
   - Domain-specific terminology support

4. **Additional Integration Options**:
   - Support for other speech recognition APIs
   - Integration with text editors via plugins

## How to Extend

To extend the implementation, developers can:

1. **Add New API Providers**:
   - Create a new client class similar to AzureWhisperClient
   - Implement the same interface for transcription
   - Update config.yaml to include provider selection

2. **Enhance Hotkey Functionality**:
   - Add more hotkey combinations for different actions
   - Implement context-sensitive hotkeys

3. **Improve Text Processing**:
   - Add post-processing for transcription results
   - Implement text formatting options

4. **Add Logging and Analytics**:
   - Implement logging system for debugging
   - Add usage analytics for performance tuning

## Required Dependencies

```
pynput  # For keyboard hooks
pyperclip  # For clipboard access
requests  # For API calls (if not using Azure SDK)
azure-cognitiveservices-speech  # For Azure Speech Services
pyyaml  # For config file parsing
SpeechRecognition  # For audio recording and processing
```

## Minimal Project Structure

```
whisper_real_time/
├── azure_whisper_client.py     # Azure API integration
├── keyboard_listener.py        # Global hotkey handling
├── transcribe_azure.py         # Main application
├── transcribe_demo.py          # Original local Whisper demo
├── config.yaml                 # Configuration settings
├── requirements.txt            # Project dependencies
├── README.md                   # Project documentation
└── Implementation.MD           # Implementation details (this file)
```

## Usage Workflow

1. User configures Azure API credentials and hotkey in config.yaml
2. User runs the application (it stays in the background)
3. When the user presses the configured hotkey, recording starts
4. User speaks what they want transcribed
5. User presses the hotkey again to stop recording
6. Transcribed text is placed in the clipboard
7. If auto-paste is enabled, text is automatically pasted
