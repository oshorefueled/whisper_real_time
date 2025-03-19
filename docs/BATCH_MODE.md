# Batch Mode Feature

## Overview

The Batch Mode feature is designed to optimize the usage of the Azure Whisper API by only sending one transcription request at the end of a recording session, rather than attempting to provide real-time transcription.

## Why Batch Mode?

Azure's Whisper API has strict rate limits:

- **3 requests per minute per API key**
- **25MB maximum audio size per request**

These limitations make true real-time transcription impractical, as a typical conversation would quickly exhaust the request quota, leading to forced pauses in transcription.

## How Batch Mode Works

When Batch Mode is enabled:

1. The application records your audio continuously while the hotkey is active
2. No API requests are made during recording
3. When you stop recording (by pressing the hotkey again), all recorded audio is sent as a single request to the API
4. The transcription is returned as a complete text and copied to your clipboard

This approach ensures:
- Maximum efficiency of API usage
- No rate limit errors during extended recording sessions
- Better transcription quality as the API has more context

## Configuration

To enable or disable Batch Mode, edit your `config.yaml` file:

```yaml
behavior:
  batch_mode: true  # Set to false if you want to attempt real-time transcription
```

## Best Practices

- **Keep recordings under 25MB**: While the system will truncate audio if it exceeds the maximum size, it's best to keep individual recording sessions reasonably short.
- **Wait between recordings**: Remember that even with Batch Mode, you're still limited to 3 API requests per minute.
- **Use for dictation**: Batch Mode is ideal for dictation or transcribing pre-recorded content, rather than live conversations.

## Troubleshooting

If you encounter issues with Batch Mode:

1. Check your API key and endpoint in the config file
2. Verify that your microphone is working correctly
3. Look for error messages in the application output
4. Try shorter recording sessions if you're hitting size limits

## Technical Implementation

Batch Mode modifies the standard recording flow:

- Disables the real-time processing thread
- Accumulates all audio data during recording
- Only processes audio once at the end of recording
- Uses a single API call regardless of recording length (as long as it's under 25MB)
