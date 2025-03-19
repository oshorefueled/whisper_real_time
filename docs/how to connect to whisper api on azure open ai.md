<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" class="logo" width="120"/>

# 

---

# how to connect to whisper api on azure open ai

To connect to the Whisper API on Azure OpenAI, follow these steps:

## Step 1: Set Up Azure OpenAI Service

1. **Create an Azure OpenAI Service**: Go to the Azure portal and create a new Azure OpenAI Service resource. Ensure you select a region that supports the Whisper model, such as North Central US or West Europe[^2][^3].
2. **Deploy a Whisper Model**: Use Azure OpenAI Studio to deploy a Whisper model. You can name your deployment, for example, "whisper"[^2][^3].

## Step 2: Obtain Endpoint and API Key

1. **Get Endpoint and API Key**: Navigate to the "Keys and Endpoint" section of your Azure OpenAI Service resource. Copy the endpoint URL and one of the API keys (e.g., "Key 1")[^2][^3].

## Step 3: Use the Whisper API

You can use the Whisper API via REST or SDKs like Python or C\#.

### Using REST API

1. **Prepare the Request**: Use tools like `curl` or PowerShell to send a POST request to the Whisper API endpoint. Replace placeholders with your actual values.

**Example with `curl`:**

```bash
curl https://your-resource-name.openai.azure.com/openai/deployments/YourDeploymentName/audio/transcriptions?api-version=2024-02-01 \
-H "api-key: YourAPIKey" \
-H "Content-Type: multipart/form-data" \
-F file="@./your-audio-file.wav"
```

**Example with PowerShell:**

```powershell
$openai = @{
    api_key = $Env:AZURE_OPENAI_API_KEY
    api_base = $Env:AZURE_OPENAI_ENDPOINT
    api_version = '2024-02-01'
    name = 'YourDeploymentName'
}

$headers = [ordered]@{
    'api-key' = $openai.api_key
}

$form = @{ file = get-item -path './your-audio-file.wav' }

$url = "$($openai.api_base)/openai/deployments/$($openai.name)/audio/transcriptions?api-version=$($openai.api_version)"

$response = Invoke-RestMethod -Uri $url -Headers $headers -Form $form -Method Post -ContentType 'multipart/form-data'

return $response.text
```


### Using Python SDK

1. **Install Required Libraries**: Ensure you have Python installed and install necessary libraries using `pip install -r requirements.txt` from a sample repository[^4].
2. **Set Environment Variables**: Create a `.env` file with your Azure OpenAI endpoint and API key.
3. **Transcribe Audio**: Use the Azure OpenAI client to transcribe audio files.

**Example Code:**

```python
import os
from openai import AzureOpenAI

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Set Azure OpenAI configuration
client = AzureOpenAI(
    api_key=os.getenv('AZURE_OPENAI_API_KEY'),
    api_version="2023-12-01-preview",
    azure_endpoint=os.getenv('AZURE_OPENAI_ENDPOINT')
)

def transcribe_audio(file_path):
    transcript = client.audio.transcriptions.create(
        file_path=file_path,
        model="whisper"
    )
    return transcript

# Transcribe an audio file
audio_file_path = "./your-audio-file.wav"
transcript = transcribe_audio(audio_file_path)
print(transcript)
```


## Step 4: Secure Credentials

For production environments, store and access your credentials securely using services like Azure Key Vault[^1][^3].

<div style="text-align: center">⁂</div>

[^1]: https://learn.microsoft.com/en-us/azure/ai-services/openai/whisper-quickstart

[^2]: https://blog.pieeatingninjas.be/2023/10/03/exploring-whisper-model-in-azure-openai-service/

[^3]: https://pascalcase.com/Home/Blog/connecting-to-azure-openai-whisper-service-in-power-automate

[^4]: https://github.com/potofo/whisper-azure

[^5]: https://azureaggregator.wordpress.com/2024/07/11/running-open-ai-whisper-model-on-azure/

[^6]: https://learn.microsoft.com/en-us/azure/ai-services/speech-service/whisper-overview

[^7]: https://www.youtube.com/watch?v=9fQMmxmZEEs

[^8]: https://platform.openai.com/docs/guides/speech-to-text

