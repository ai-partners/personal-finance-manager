import os
import logging
from dotenv import load_dotenv
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import ConnectionType
from azure.identity import DefaultAzureCredential
from azure.ai.projects.models import FunctionTool, ToolSet

from user_functions import (
    user_functions
)

# Add libraries to interact with Azure services
import pyodbc

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
            "You are a financial transaction assistant that helps users record their financial activities. "
            "Your main function is to process user inputs and add transactions to the financial database. "
            "\n\n"
            "INPUT HANDLING INSTRUCTIONS:"
            "\n1. Accept inputs in multiple formats:"
            "\n   - Text descriptions (e.g., 'I spent $25 on lunch today')"
            "\n   - Voice recordings (transcribe and extract transaction details)"
            "\n   - Images (e.g., receipts, invoices - extract relevant transaction information)"
            "\n\n"
            "TRANSACTION PROCESSING INSTRUCTIONS:"
            "\n1. For each transaction input, extract the following required information:"
            "\n   - Transaction type (income, expense, transfer)"
            "\n   - Amount"
            "\n   - Date (use current date if not specified)"
            "\n   - Description"
            "\n   - Category (e.g., groceries, utilities, entertainment)"
            "\n   - Payment method (e.g., credit card, cash, bank transfer)"
            "\n\n"
            "2. Category Classification:"
            "\n   - Match the transaction to the most appropriate category in the Categories table"
            "\n   - Ask the user to confirm or correct the category if uncertain"
            "\n   - For new categories, suggest adding them to the Categories table"
            "\n\n"
            "Always be conversational and helpful. Guide users through the process of recording transactions "
            "by asking for missing information and confirming details. Maintain user context between interactions "
            "and refer to their transaction history when relevant."
        )

        # Example: Initialize tools and tool_resources
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "get_user_accounts",
                    "description": "Retrieves a list of accounts for the user",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "user_id": {
                                "type": "integer",
                                "description": "ID of the user"
                            }
                        },
                        "required": ["user_id"]
                    }
                }
            }
        ]
        tool_resources = {
            "get_user_accounts": user_functions
        }

        # Initialize agent toolset with user functions
        functions = FunctionTool(user_functions)
        toolset = ToolSet()
        toolset.add(functions)

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
                instructions=agent_instructions,
                toolset=toolset,
            )
            logging.info(f"Created agent successfully, agent ID: {agent.id}")

    except Exception as e:
        logging.error(f"An error occurred: {e}")
        raise

if __name__ == "__main__":
    main()