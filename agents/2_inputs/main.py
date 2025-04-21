import os
import asyncio
import logging
from dotenv import load_dotenv
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from utilities import Utilities
from azure.ai.projects.models import (
    Agent,
    AgentThread,
    AsyncToolSet,
    OpenApiTool,
    OpenApiAnonymousAuthDetails,
)

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

load_dotenv()

AGENT_NAME = os.getenv("AZURE_AI_FOUNDRY_AGENT_NAME")
PROJECT_CONNECTION_STRING = os.getenv("PROJECT_CONNECTION_STRING")
MODEL_DEPLOYMENT_NAME = os.getenv("MODEL_DEPLOYMENT_NAME")

MAX_COMPLETION_TOKENS = 10240
MAX_PROMPT_TOKENS = 20480

# The LLM is used to generate the SQL queries.
# Set the temperature and top_p low to get more deterministic results.
TEMPERATURE = 0.1
TOP_P = 0.1
INSTRUCTIONS_FILE = "instructions/agent_instructions.txt"

toolset = AsyncToolSet()
utilities = Utilities()

project_client = AIProjectClient.from_connection_string(
    credential=DefaultAzureCredential(),
    conn_str=PROJECT_CONNECTION_STRING,
)

async def add_agent_tools() -> None:
    """Add tools to the agent."""
    
    # Add fetch_data_using_sql_query tool
    auth = OpenApiAnonymousAuthDetails()
    # Load the OpenAPI specification for the tool
    fetch_data_using_sql_query_spec = utilities.read_json_file("tools/fetch_data_using_sql_query.json")
    # Create the OpenApiTool instance
    fetch_data_using_sql_query = OpenApiTool(
        name="fetch_data_using_sql_query",
        description="Fetch data from the database using a SQL query.",
        auth=auth,
        spec=fetch_data_using_sql_query_spec
    )
    # Add the tool to the toolset
    toolset.add(fetch_data_using_sql_query)

    # Add function tools (if any)
    # Example: toolset.add(FunctionTool(name="function_name", function=function))
    return

async def initialize() -> tuple[Agent, AgentThread]:
    """Initialize the agent and its thread."""

    if not INSTRUCTIONS_FILE:
        return None, None
    
    add_agent_tools()

    database_schema_string = utilities.read_text_file("azure-sql-schema.sql")

    try:
        instructions = utilities.load_instructions(INSTRUCTIONS_FILE)
        # Replace the placeholder with the database schema string
        instructions = instructions.replace(
            "{database_schema_string}", database_schema_string)
        
        print("Creating agent...")
        # Create the agent with the specified model and tools
        agent = await project_client.agents.create_agent(
            model=MODEL_DEPLOYMENT_NAME,
            name=AGENT_NAME,
            instructions=instructions,
            toolset=toolset,
            temperature=TEMPERATURE,
        )

        print(f"Created agent, ID: {agent.id}")

        print("Creating thread...")
        thread = await project_client.agents.create_thread()
        print(f"Created thread, ID: {thread.id}")

        return agent, thread
    
    except Exception as e:
        logger.error("An error occurred initializing the agent: %s", str(e))
        logger.error("Please ensure you've enabled an instructions file.")

async def cleanup(agent: Agent, thread: AgentThread) -> None:
    """Cleanup resources."""
    # Close the project client connection
    await project_client.agents.delete_thread(thread.id)
    await project_client.agents.delete_agent(agent.id)
    await project_client.close()

async def post_message(thread_id: str, content: str, agent: Agent, thread: AgentThread) -> None:
    """Post a message to the Azure AI Agent Service."""
    try:
        # Create a new message in the thread
        await project_client.agents.create_message(
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
        async with stream as s:
            await s.until_done()

    except Exception as e:
        logging.error(f"An error occurred while posting a message: {e}")

async def main() -> None:
    """
    Example questions to ask the agent: Add an expense of $50 for groceries, from today.
    """
    agent, thread = await initialize()
    if not agent or not thread:
        print("Failed to initialize agent or thread.")
        print("Exiting...")
        return

    cmd = None

    while True:
        prompt = input(
            f"\n\nEnter your query (type exit or save to finish):").strip()
        if not prompt:
            continue

        cmd = prompt.lower()
        if cmd in {"exit", "save"}:
            break

        await post_message(agent=agent, thread_id=thread.id, content=prompt, thread=thread)

    if cmd == "save":
        print("The agent has not been deleted, so you can continue experimenting with it in the Azure AI Foundry.")
        print(
            f"Navigate to https://ai.azure.com, select your project, then playgrounds, agents playgound, then select agent id: {agent.id}"
        )
    else:
        await cleanup(agent, thread)
        print("The agent resources have been cleaned up.")

if __name__ == "__main__":
    print("Starting async program...")
    asyncio.run(main())
    print("Program finished.")