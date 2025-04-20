import os, time, base64
from dotenv import load_dotenv
from typing import List
import pytest
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from azure.ai.projects.models import MessageTextContent
from azure.ai.projects.models import (
    MessageTextContent,
    MessageInputContentBlock,
    MessageImageUrlParam,
    MessageInputTextBlock,
    MessageInputImageUrlBlock,
)

# Load environment variables from .env file
load_dotenv()

@pytest.fixture(scope="module")
def agent_and_client():
    # Load variables from environment
    project_connection_string = os.getenv("PROJECT_CONNECTION_STRING")
    agent_id = os.getenv("AZURE_AI_FOUNDRY_AGENT_ID")
    project_client = AIProjectClient.from_connection_string(
        credential=DefaultAzureCredential(),
        conn_str=project_connection_string,
    )
    with project_client:
        agent = project_client.agents.get_agent(agent_id=agent_id)
        yield agent, project_client

def process_run_and_get_messages(project_client, thread_id, agent):
    # Create a message in the thread (content_blocks should be provided by the caller)
    # Example: message = project_client.agents.create_message(thread_id=thread_id, role="user", content=content_blocks)
    # For test, assume content_blocks is a string or list of blocks
    # This function should be called after message creation

    # Start the run
    run = project_client.agents.create_run(thread_id=thread_id, agent_id=agent.id)

    # Poll the run as long as run status is queued or in progress
    while run.status in ["queued", "in_progress", "requires_action"]:
        time.sleep(1)
        run = project_client.agents.get_run(thread_id=thread_id, run_id=run.id)
        print(f"Run status: {run.status}")

    if run.status == "failed":
        print(f"Run failed: {run.last_error}")

    messages = project_client.agents.list_messages(thread_id=thread_id)

    # Output only text contents in correct order
    for data_point in reversed(messages.data):
        last_message_content = data_point.content[-1]
        if isinstance(last_message_content, MessageTextContent):
            print(f"{data_point.role}: {last_message_content.text.value}")

    print(f"Messages: {messages}")
    return messages

# Code function taken from the repository: https://github.com/Azure/azure-sdk-for-python/blob/azure-ai-projects_1.0.0b9/sdk/ai/azure-ai-projects/samples/agents/sample_agents_image_input_base64.py#L105
## Convert an image file to a Base64-encoded string
## This function is used to convert an image file to a Base64-encoded string.
def image_to_base64(image_path: str) -> str:
    """
    Convert an image file to a Base64-encoded string.

    :param image_path: The path to the image file (e.g. 'image_file.png')
    :return: A Base64-encoded string representing the image.
    :raises FileNotFoundError: If the provided file path does not exist.
    :raises OSError: If there's an error reading the file.
    """
    if not os.path.isfile(image_path):
        raise FileNotFoundError(f"File not found at: {image_path}")

    try:
        with open(image_path, "rb") as image_file:
            file_data = image_file.read()
        return base64.b64encode(file_data).decode("utf-8")
    except Exception as exc:
        raise OSError(f"Error reading file '{image_path}'") from exc


def test_text_input(agent_and_client):
    """
    Prueba la funcionalidad de entrada de texto para un agente.

    Este caso de prueba verifica que un agente pueda procesar un mensaje de entrada
    de texto correctamente y que la respuesta contenga información relevante sobre
    el balance de la cuenta.

    Args:
        agent_and_client (tuple): Una tupla que contiene el agente y el cliente del proyecto.

    Pasos:
    1. Imprime los detalles del agente, incluyendo su ID y nombre.
    2. Crea un hilo (thread) asociado al agente.
    3. Envía un mensaje al hilo con el contenido "What is my account balance?" y el rol "user".
    4. Procesa los mensajes en el hilo y verifica que la respuesta contenga la palabra "balance".

    Assertions:
        - Se asegura de que la palabra "balance" esté presente en el contenido de la respuesta.

    """
    agent, project_client = agent_and_client
    # Print agent details
    print(f"Agent ID: {agent.id}")
    print(f"Agent Name: {agent.name}")
    # Create a thread for the agent
    thread = project_client.agents.create_thread()
    print(f"Thread ID: {thread.id}")
    # Create a message in the thread
    message = project_client.agents.create_message(
        thread_id=thread.id,
        content="What is my account balance?",
        role="user",
    )
    messages = process_run_and_get_messages(project_client, thread.id, agent)
    all_content = " ".join([msg.content[-1].text.value for msg in messages.data])
    assert "balance" in all_content.lower()


def test_image_input(agent_and_client):
    """
    Prueba un caso en el que se envía una imagen como entrada a un agente y se verifica la respuesta.
    Args:
        agent_and_client (tuple): Una tupla que contiene el agente y el cliente del proyecto.
    Pasos:
        1. Crea un hilo para el agente utilizando el cliente del proyecto.
        2. Convierte una imagen de ejemplo a formato base64 y la incluye como parte del mensaje.
        3. Envía un mensaje al agente que contiene texto y una imagen en formato base64.
        4. Procesa la ejecución del agente y recupera los mensajes generados.
        5. Verifica que la respuesta del agente contiene palabras clave relacionadas con el recibo o el monto.
    Notas:
        - La imagen utilizada en este caso de prueba es "restaurant-bar-receipt-sample.jpg".
        - Se espera que el agente pueda interpretar correctamente la imagen y responder con información relevante.
    """
    agent, project_client = agent_and_client
    # Create a thread for the agent
    thread = project_client.agents.create_thread()
    print(f"Thread ID: {thread.id}")

    input_message =  "What is the total amount on this receipt?"
    image_base64 = image_to_base64("restaurant-bar-receipt-sample.jpg")
    img_url = f"data:image/png;base64,{image_base64}"
    url_param = MessageImageUrlParam(url=img_url, detail="high")
    content_blocks: List[MessageInputContentBlock] = [
        MessageInputTextBlock(text=input_message),
        MessageInputImageUrlBlock(image_url=url_param),
    ]

    message = project_client.agents.create_message(thread_id=thread.id, role="user", content=content_blocks)
    print(f"Created message, message ID: {message.id}")

    messages = process_run_and_get_messages(project_client, thread.id, agent)
    all_content = " ".join([msg.content[-1].text.value for msg in messages.data])
    print(f"All content: {all_content}")
    assert "receipt" in all_content.lower() or "amount" in all_content.lower()

# def test_voice_input(agent):
#     with open("sample_query.wav", "rb") as audio_file:
#         audio_bytes = audio_file.read()
#     voice_input = {"type": "audio", "data": audio_bytes}
#     response = agent.run(inputs=[voice_input])
#     assert "account" in response.lower() or "balance" in response.lower()