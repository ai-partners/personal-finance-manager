import os
import logging
from dotenv import load_dotenv
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from utilities import Utilities
from azure.ai.projects.models import (
    Agent,
    AgentThread,
    FileSearchTool,
    FilePurpose,
)

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

AGENT_NAME = os.getenv("AZURE_AI_FOUNDRY_AGENT_NAME")
PROJECT_CONNECTION_STRING = os.getenv("PROJECT_CONNECTION_STRING")
MODEL_DEPLOYMENT_NAME = os.getenv("MODEL_DEPLOYMENT_NAME")

MAX_COMPLETION_TOKENS = 10240
MAX_PROMPT_TOKENS = 20480

# Set the temperature and top_p low to get more deterministic results.
TEMPERATURE = 0.1
TOP_P = 0.1
INSTRUCTIONS_FILE = "agent_instructions.txt"

# Initialize the toolset and utilities
utilities = Utilities()

# Initialize the AIProjectClient
project_client = AIProjectClient.from_connection_string(
    credential=DefaultAzureCredential(),
    conn_str=PROJECT_CONNECTION_STRING,
)


def initialize() -> tuple[Agent, AgentThread]:
    """Initialize the agent and its thread."""
    
    # Upload the documentation file
    file = project_client.agents.upload_file_and_poll(file_path="files/PFM_WhitePaper.docx", purpose=FilePurpose.AGENTS)
    print(f"Uploaded file, file ID: {file.id}")

    # Create a vector store with the file you uploaded
    vector_store = project_client.agents.create_vector_store_and_poll(file_ids=[file.id], name="HostAgentVectorStore")
    print(f"Created vector store, vector store ID: {vector_store.id}")

    file_search_tool = FileSearchTool(vector_store_ids=[vector_store.id])

    if not INSTRUCTIONS_FILE:
        return None, None

    try:
        instructions = utilities.load_instructions(INSTRUCTIONS_FILE)

        print("Creating agent...")       
        agent = project_client.agents.create_agent(
            model=MODEL_DEPLOYMENT_NAME,
            name=AGENT_NAME,
            instructions=instructions,
            tools=file_search_tool.definitions,
            tool_resources=file_search_tool.resources,
            temperature=TEMPERATURE,
        )
        print(f"Created agent, ID: {agent.id}")

        print("Creating thread...")
        thread = project_client.agents.create_thread()
        print(f"Created thread, ID: {thread.id}")

        return agent, thread
    
    except Exception as e:
        logger.error("An error occurred initializing the agent: %s", str(e))
        logger.error("Please ensure you've enabled an instructions file.")

def cleanup(agent: Agent, thread: AgentThread) -> None:
    """Cleanup resources."""
    # Close the project client connection
    project_client.agents.delete_thread(thread.id)
    project_client.agents.delete_agent(agent.id)
    project_client.close()

def post_message(thread_id: str, content: str, agent: Agent, thread: AgentThread) -> None:
    """Post a message to the Azure AI Agent Service."""
    try:
        # Create a new message in the thread
        project_client.agents.create_message(
            thread_id=thread_id,
            content=content,
            role="user",
        )
        
        stream = project_client.agents.create_stream(
            thread_id=thread.id,
            agent_id=agent.id,
            max_completion_tokens=MAX_COMPLETION_TOKENS,
            max_prompt_tokens=MAX_PROMPT_TOKENS,
            temperature=TEMPERATURE,
            top_p=TOP_P,
            instructions=agent.instructions,
        )
        with stream as s:
            print(f"\n[AGENT]\n")
            for event in s:
                try:
                    if event[0] == "thread.message.delta":
                        value = event[1]["delta"]["content"][0]["text"].get("value", "")
                        print(value, end="", flush=True)
                except Exception as e:
                    logging.warning("Unexpected event format: %s", event)
            s.until_done()

    except Exception as e:
        logging.error(f"An error occurred while posting a message: {e}")

def main() -> None:
    """
    Example questions to ask the agent: Add an expense of $50 for groceries, from today.
    """
    agent, thread = initialize()
    if not agent or not thread:
        print("Failed to initialize agent or thread.")
        print("Exiting...")
        return

    cmd = None

    while True:
        prompt = input(
            f"\n\n[USER] Enter your query (type exit or save to finish): ").strip()
        if not prompt:
            continue

        cmd = prompt.lower()
        if cmd in {"exit", "save"}:
            break

        post_message(agent=agent, thread_id=thread.id, content=prompt, thread=thread)

    if cmd == "save":
        print("The agent has not been deleted, so you can continue experimenting with it in the Azure AI Foundry.")
        print(
            f"Navigate to https://ai.azure.com, select your project, then playgrounds, agents playgound, then select agent id: {agent.id}"
        )
    else:
        cleanup(agent, thread)
        print("The agent resources have been cleaned up.")

if __name__ == "__main__":
    print("Starting program...")
    main()  # Direct call instead of asyncio.run()
    print("Program finished.")