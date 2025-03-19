# Real-Time Speech Transcription with Whisper

![Demo gif](demo.gif)

## Introduction

This project demonstrates real-time speech-to-text transcription using OpenAI's Whisper model. It continuously records audio from your microphone, processes it through the Whisper model, and displays the transcription in your terminal, updating in near real-time.

## Features

- Real-time audio transcription from microphone input
- Batch mode for efficient API usage (recommended for Azure OpenAI API)
- Supports multiple Whisper model sizes (tiny, base, small, medium, large)
- Adjustable sensitivity for speech detection
- Configurable timing parameters for real-time behavior
- Support for English and non-English transcription
- Linux microphone device selection

## Prerequisites

- Python 3.7 or higher
- FFmpeg installed on your system
- CUDA-compatible GPU (optional, for faster processing)

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/oshorefueled/whisper_real_time.git
   cd whisper_real_time
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Install FFmpeg (required by Whisper):

   ```
   # on Ubuntu or Debian
   sudo apt update && sudo apt install ffmpeg

   # on Arch Linux
   sudo pacman -S ffmpeg

   # on MacOS using Homebrew (https://brew.sh/)
   brew install ffmpeg

   # on Windows using Chocolatey (https://chocolatey.org/)
   choco install ffmpeg

   # on Windows using Scoop (https://scoop.sh/)
   scoop install ffmpeg
   ```

## Configuration

This project uses a YAML configuration file for settings. For security reasons, the actual configuration file (`config.yaml`) is not included in the repository.

1. Copy the sample configuration file:
   ```bash
   cp config.sample.yaml config.yaml
   ```

2. Edit `config.yaml` with your Azure OpenAI API credentials and preferences:
   ```yaml
   azure:
     api_key: "your-azure-api-key"
     endpoint: "https://your-resource-name.openai.azure.com"
     deployment_name: "whisper"
     language: "en-US"
   ```

3. Set batch mode (recommended for Azure API):
    ```yaml
    behavior:
      batch_mode: true  # Process audio only after recording completes
    ```

4. Customize other settings as needed (hotkeys, behavior, audio parameters)

> **Security Note**: Never commit your `config.yaml` file with real API keys to version control. The file is included in `.gitignore` to help prevent accidental exposure of your credentials.

For detailed setup instructions, see:
- [Azure API Setup](docs/AZURE_SETUP.md)
- [Batch Mode Documentation](docs/BATCH_MODE.md)

## Usage

Run the transcription demo with default settings:

```
python transcribe_demo.py
```

### Command-line Arguments

The script accepts several command-line arguments to customize its behavior:

- `--model`: Model size to use (tiny, base, small, medium, large). Default: medium
- `--non_english`: Flag to use the multilingual model instead of the English-specific model
- `--energy_threshold`: Energy level for microphone to detect. Default: 1000
- `--record_timeout`: How real-time the recording is in seconds. Default: 2
- `--phrase_timeout`: Empty space between recordings before considering it a new line. Default: 3
- `--default_microphone`: (Linux only) Name of the default microphone to use. Use with 'list' to view available microphones

Example with custom settings:
```
python transcribe_demo.py --model small --energy_threshold 800 --record_timeout 1.5
```

## How It Works

1. The script uses SpeechRecognition library to continuously record audio from your microphone
2. Audio is recorded in short segments (default: 2 seconds) and passed to a queue
3. The raw audio bytes are concatenated over multiple recordings
4. The audio is processed through the Whisper model to generate transcription text
5. The console is cleared and updated with the latest transcription
6. If a pause is detected between recordings (default: 3 seconds), a new line is started in the transcription

## Resources

- [OpenAI Whisper GitHub Repository](https://github.com/openai/whisper)

## License

The code in this repository is in the public domain.