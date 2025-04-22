import datetime
import os

import dotenv
import azure.identity
from openai import AsyncAzureOpenAI, AsyncOpenAI
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion

from azure.core.exceptions import ClientAuthenticationError
from azure.identity import DefaultAzureCredential
from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from semantic_kernel.connectors.ai import FunctionChoiceBehavior
from semantic_kernel.connectors.ai.open_ai.prompt_execution_settings.azure_chat_prompt_execution_settings import \
    AzureChatPromptExecutionSettings
from semantic_kernel.connectors.ai.open_ai.services.azure_chat_completion import \
    AzureChatCompletion
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.core_plugins.sessions_python_tool.sessions_python_plugin import \
    SessionsPythonTool
from semantic_kernel.exceptions.function_exceptions import \
    FunctionExecutionException
from semantic_kernel.functions.kernel_arguments import KernelArguments

dotenv.load_dotenv()

app = FastAPI()

API_HOST = os.getenv("API_HOST", "github")

def auth_callback_factory(scope):
    auth_token = None
    async def auth_callback() -> str:
        """Auth callback for the SessionsPythonTool.
        This is a sample auth callback that shows how to use Azure's DefaultAzureCredential
        to get an access token.
        """
        nonlocal auth_token
        current_utc_timestamp = int(datetime.datetime.now(datetime.timezone.utc).timestamp())

        if not auth_token or auth_token.expires_on < current_utc_timestamp:
            credential = DefaultAzureCredential()

            try:
                auth_token = credential.get_token(scope)
            except ClientAuthenticationError as cae:
                err_messages = getattr(cae, "messages", [])
                raise FunctionExecutionException(
                    f"Failed to retrieve the client auth token with messages: {' '.join(err_messages)}"
                ) from cae

        return auth_token.token
    
    return auth_callback

def create_kernel() -> Kernel:
    """Creates a Kernel instance with an Azure OpenAI ChatCompletion service."""
    kernel = Kernel()

    if API_HOST == "azure":
        token_provider = azure.identity.get_bearer_token_provider(azure.identity.DefaultAzureCredential(), "https://cognitiveservices.azure.com/.default")
        chat_client = AsyncAzureOpenAI(
            api_version=os.environ["AZURE_OPENAI_VERSION"],
            azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
            azure_ad_token_provider=token_provider,
        )
        chat_completion_service = OpenAIChatCompletion(ai_model_id=os.environ["AZURE_OPENAI_CHAT_MODEL"], async_client=chat_client)
    else:
        chat_client = AsyncOpenAI(api_key=os.environ["GITHUB_TOKEN"], base_url="https://models.inference.ai.azure.com")
        chat_completion_service = OpenAIChatCompletion(ai_model_id=os.getenv("GITHUB_MODEL", "gpt-4o"), async_client=chat_client)
    kernel.add_service(chat_completion_service)
    return kernel

@app.get("/")
async def root():
    return RedirectResponse("/docs")


@app.get("/chat")
async def chat(message: str):
    # Create a single kernel instance for all agents.
    kernel = create_kernel()

    service_id = "sessions-tool"
    # chat_service = AzureChatCompletion(
    #     service_id=service_id,
    #     ad_token_provider=auth_callback_factory("https://cognitiveservices.azure.com/.default"),
    #     endpoint=azure_openai_endpoint,
    #     deployment_name="gpt-35-turbo",
    # )
    # kernel.add_service(chat_service)

    

    chat_function = kernel.add_function(
        prompt="{{$chat_history}}{{$user_input}}",
        plugin_name="ChatBot",
        function_name="Chat",
    )

    req_settings = AzureChatPromptExecutionSettings(service_id=service_id, tool_choice="auto")

    filter = {"excluded_plugins": ["ChatBot"]}
    req_settings.function_choice_behavior = FunctionChoiceBehavior.Auto(auto_invoke=True, filters=filter)

    
    arguments = KernelArguments(settings=req_settings)

    history = ChatHistory()

    arguments["chat_history"] = history
    arguments["user_input"] = message
    answer = await kernel.invoke(
        function=chat_function,
        arguments=arguments,
    )

    response = {
        "output": str(answer),
    }

    return response