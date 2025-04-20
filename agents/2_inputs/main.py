import os
import logging
from dotenv import load_dotenv
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import ConnectionType
from azure.identity import DefaultAzureCredential

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def load_env_variable(var_name):
    """Load an environment variable and raise an error if it's missing."""
    value = os.getenv(var_name)
    if not value:
        logging.error(f"Environment variable '{var_name}' is not set.")
        raise ValueError(f"Environment variable '{var_name}' is required but not set.")
    return value

def main():
    # Load environment variables from the .env file
    load_dotenv()

    try:
        # Load required environment variables
        project_connection_string = load_env_variable("PROJECT_CONNECTION_STRING")
        model_name = load_env_variable("MODEL_DEPLOYMENT_NAME")
        agent_name = load_env_variable("AZURE_AI_FOUNDRY_AGENT_NAME")

        # Initialize agent instructions, tools, and tool resources
        agent_instructions = (
            "You are a helpful agent. "
            "Assist users with their queries using the available tools. "
            "Always provide clear and concise answers."
        )

        # Example: Initialize tools and tool_resources
        tools = ""
        tool_resources = ""

        # Create an Azure AI client using the connection string
        project_client = AIProjectClient.from_connection_string(
            credential=DefaultAzureCredential(),
            conn_str=project_connection_string,
        )

        with project_client:
            # Create an agent with the specified model and tools
            agent = project_client.agents.create_agent(
                model=model_name,
                name=agent_name,
                instructions=agent_instructions
            )
            logging.info(f"Created agent successfully, agent ID: {agent.id}")

    except Exception as e:
        logging.error(f"An error occurred: {e}")
        raise

if __name__ == "__main__":
    main()