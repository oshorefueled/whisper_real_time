# Azure OpenAI Whisper API Setup Guide

This guide provides step-by-step instructions for setting up and configuring the Azure OpenAI Whisper API for use with this application.

## Step 1: Set Up Azure OpenAI Service

1. **Create an Azure OpenAI Service**:
   - Go to the [Azure portal](https://portal.azure.com)
   - Search for "Azure OpenAI" and select "Azure OpenAI"
   - Click "Create" to create a new Azure OpenAI Service resource
   - Select a subscription, resource group, and name for your resource
   - For "Region", select one that supports the Whisper model (e.g., East US, West Europe)
   - Choose a pricing tier (typically "Standard S0")
   - Click "Review + create" and then "Create"

2. **Deploy a Whisper Model**:
   - Once your Azure OpenAI Service is created, go to the resource
   - Click on "Go to Azure OpenAI Studio" or navigate to [Azure OpenAI Studio](https://oai.azure.com/)
   - In the Azure OpenAI Studio, go to "Deployments" in the left sidebar
   - Click "Create new deployment"
   - Select "Whisper" as the model
   - Name your deployment (e.g., "whisper")
   - Click "Create"

## Step 2: Get API Credentials

1. **Get Endpoint and API Key**:
   - Go back to your Azure OpenAI Service resource in the Azure portal
   - Navigate to the "Keys and Endpoint" section
   - Copy the endpoint URL (it should look like `https://your-resource-name.openai.azure.com/`)
   - Copy one of the API keys (either "Key 1" or "Key 2")

## Step 3: Configure the Application

1. **Update the config.yaml file**:
   - Open the `config.yaml` file in this project
   - Update the following fields in the `azure` section:
     ```yaml
     azure:
       api_key: "your-azure-api-key"  # Paste your API key here
       endpoint: "https://your-resource-name.openai.azure.com"  # Paste your endpoint URL here
       deployment_name: "whisper"  # The name you gave to your Whisper model deployment
       language: "en-US"  # The language code for transcription
     ```

## Step 4: Test the Connection

1. **Run the test script**:
   ```bash
   python azure_whisper_client.py
   ```
   This will record a short audio sample and attempt to transcribe it using your Azure OpenAI Whisper API configuration.

## API Limitations

Be aware of the following limitations when using the Azure OpenAI Whisper API:

1. **Request Size Limit**: Maximum 25MB of audio can be converted from speech to text per API request
2. **Rate Limiting**: Limited to 3 requests per minute per API key
3. **Model Version**: The API uses Whisper large v2 (model version 001)

## Troubleshooting

If you encounter issues with the API connection:

1. **Check your API key and endpoint**: Ensure they are correctly copied from the Azure portal
2. **Verify your deployment name**: Make sure the deployment name in config.yaml matches the name you gave to your Whisper model deployment
3. **Check API response errors**: Look at the application logs for detailed error messages from the API
4. **Region availability**: Make sure you created your Azure OpenAI resource in a region that supports the Whisper model
5. **Quota limits**: Check if you have exceeded your quota for the Azure OpenAI Service

For more information, refer to the [Azure OpenAI Service documentation](https://learn.microsoft.com/en-us/azure/ai-services/openai/).
