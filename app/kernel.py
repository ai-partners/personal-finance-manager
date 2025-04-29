import os
import datetime
from dotenv import load_dotenv
from azure.ai.projects.aio import AIProjectClient
from azure.identity.aio import DefaultAzureCredential
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.agents.strategies import KernelFunctionSelectionStrategy, KernelFunctionTerminationStrategy
from semantic_kernel.agents import AgentGroupChat, AzureAIAgent, AzureAIAgentSettings, ChatCompletionAgent
from semantic_kernel.contents import ChatHistoryTruncationReducer, ChatMessageContent, ChatHistory, ImageContent, TextContent
from semantic_kernel.functions import KernelFunctionFromPrompt
import chainlit as cl

from utilities import Utilities

utilities = Utilities()

#Load environment variables
load_dotenv()

HOST_AGENT_NAME = os.getenv("HOST_AGENT_NAME")
HOST_AGENT_ID = os.getenv("HOST_AGENT_ID")

AGENT1_NAME = os.getenv("AGENT1_NAME")
AGENT1_ID = os.getenv("AGENT1_ID")

AGENT2_NAME = os.getenv("AGENT2_NAME")
AGENT2_ID = os.getenv("AGENT2_ID")

AGENT3_NAME = os.getenv("AGENT3_NAME")
AGENT3_ID = os.getenv("AGENT3_ID")

PROJECT_CONNECTION_STRING = os.getenv("PROJECT_CONNECTION_STRING")
MODEL_DEPLOYMENT_NAME = os.getenv("MODEL_DEPLOYMENT_NAME")

TERMINATION_KEYWORD = "FINISHED"

# Initialize the AIProjectClient
project_client = AIProjectClient.from_connection_string(
    credential=DefaultAzureCredential(),
    conn_str=PROJECT_CONNECTION_STRING,
)

class KernelChatGroup:
    
    async def initialize_chat_group(self,)->AgentGroupChat:
        print("Initializing kernel...")
        # Instantiate client settings
        ai_agent_settings = AzureAIAgentSettings()
        
        # Instantiate kernel
        kernel = Kernel()
        chat_completion_service = AzureChatCompletion(
            service_id="open-ai-service"
        )
        kernel.add_service(chat_completion_service)
        
        # Configure the kernel
        selection_function = self.selection_function()
        termination_function = self.termination_function()
        history_reducer = ChatHistoryTruncationReducer(target_count=10)

        # Initialize host agent
        print("Getting host agent...")
        host = await self.initialize_agent(
            kernel=kernel,
            agent_id=HOST_AGENT_ID,
            )
        
        # Initialize agent 1
        print("Getting agent 1...")
        agent1 = await self.initialize_agent(
            kernel=kernel,
            agent_id=AGENT1_ID,
            )

        # Initialize agent 2
        print("Getting agent 2...")
        agent2 = await self.initialize_agent(
            kernel=kernel,
            agent_id=AGENT2_ID,
        )

        # Initialize agent 3
        print("Getting agent 3...")
        agent3 = await self.initialize_agent(
            kernel=kernel,
            agent_id=AGENT3_ID,
        )

        # Create the vision agent using the kernel
        vision = ChatCompletionAgent(
            kernel=kernel, 
            name="VisionAgent", 
            instructions="""
            You are an agent specialized in reading receipts, invoices, or any proof of financial transactions provided through an image.
            Your goal is to extract the relevant data from the document so that other agents can make use of the information.

            You should focus on extracting the following information:
            - Date
            - Category (e.g., restaurant receipt, parking ticket, clothing, footwear, etc.)
            - Description (Generate a brief description based on the elements found in the receipt or invoice.)
            - Total amount

            If any of the above data is not present, simply indicate that it was not identified in the document.
            When you finish the extraction, inform the user that you have successfully completed the task and ask them to confirm that the information is correct so that another agent can take over and record the transaction.
            """,
        )

        # Create the AgentGroupChat with selection and termination strategies
        print("Creating AgentGroupChat...")
        chat = AgentGroupChat(
            agents=[host, agent1, agent2, agent3, vision],
            selection_strategy=KernelFunctionSelectionStrategy(
                function=selection_function,
                kernel=kernel,
                result_parser=lambda result: str(result.value[0]).strip() if result.value[0] is not None else HOST_AGENT_NAME,
                history_variable_name="history",
                history_reducer=history_reducer,
            ),
            termination_strategy=KernelFunctionTerminationStrategy(
                agents=[host, agent1, agent2, agent3, vision],
                function=termination_function,
                kernel=kernel,
                result_parser=lambda result: TERMINATION_KEYWORD in str(result.value[0]).lower(),
                history_variable_name="history",
                maximum_iterations=1,
                history_reducer=history_reducer,
            ),
        )
        print("AgentGroupChat created.")
        return chat

    async def initialize_agent(self, kernel: Kernel, agent_id: str,) -> AzureAIAgent:
        # Get the agent definition
        agent_definition = await project_client.agents.get_agent(
            agent_id=agent_id,
        )

        # Create the agent according to the obtained definition
        agent = AzureAIAgent(
            client=project_client,
            definition=agent_definition,
            kernel=kernel,
        )
        return agent
    
    def selection_function(self,)->KernelFunctionFromPrompt:
        return KernelFunctionFromPrompt(
            function_name="selection",
            prompt=f"""
            Examine the provided HISTORY and determine which participant should respond next.
            Indicate only the name of the chosen participant, without explanation.

            Choose only one of the following agents:

            - {AGENT1_NAME}: This agent is responsible for creating accounts and categories of income and expenses.
            - {AGENT2_NAME}: This agent records financial movements and transactions.
            - {AGENT3_NAME}: This agent is responsible for analyzing the transactions data made by the user.
            - VisionAgent: If the user provides an image, this agent will extract the relevant information from it.
            - {HOST_AGENT_NAME}: For any other information requests related to the personal finance app.

            Rules:

            When should the same agent continue?  
            - If an agent is in the middle of a process (creating accounts, categories, or transactions).  
            - If an agent is requesting more information from the user to complete the task.

            When should a change of agent be considered?  
            - When the agent indicates that they have completed their task or have provided the information requested by the user.  
            - When the user indicates that they have changed their mind or want to perform a different task.

            HISTORY:
            {{{{$history}}}}
            """,
            )
    
    def termination_function(self,)->KernelFunctionFromPrompt:
        return KernelFunctionFromPrompt(
            function_name="termination",
            prompt=f"""
            Examine the HISTORY and determine if the user's goal has been achieved.
            - If the goal is satisfactory, respond with a single word without explanation: {TERMINATION_KEYWORD}.
            - If specific suggestions are being provided, it is not satisfactory.
            - If no correction is suggested, it is satisfactory.
            - If the user does not respond with the requested information or changes their mind, the turn should also be ended.

            HISTORY:
            {{{{$history}}}}
            """,
            )

    def context_assistant_message(self,) -> ChatMessageContent:
        return ChatMessageContent(
            content=f"""
            CONTEXT: 
            - The user ID I am talking to is: {cl.user_session.get("user").metadata["UserId"]}
            - Today's date is: {datetime.datetime.now().strftime("%d-%b-%Y")}
            """,
            role="assistant"
        )

    async def add_user_message_to_chat(self, chat: AgentGroupChat, message: cl.Message) -> AgentGroupChat:
        chat_messages = []

        # If history reducer erase context message, add it again (11 = current target_count + 1 )
        if len(chat.history.messages) % 11 == 0:
            context_message = self.context_assistant_message()
            chat_messages.append(context_message)
        
        # If message has images, add image to the message
        images = [file for file in message.elements if "image" in file.mime]
        if images:
            uri = utilities.upload_to_azure_blob(file_path=images[0].path, blob_name=images[0].name)
            user_message = ChatMessageContent(
                role="user",
                items=[
                    TextContent(text=f"{message.content} (Image url: {uri})"),
                    ImageContent(uri=uri),
                ]
                )
        else:
            user_message = ChatMessageContent(
                role="user",
                items=[
                    TextContent(text=message.content),
                ]
                )
        chat_messages.append(user_message)

        await chat.add_chat_messages(chat_messages)

        return chat
    
    async def add_chat_completion_agent_response_to_history(self, chat: AgentGroupChat, response: str) -> AgentGroupChat:
        host_response = ChatMessageContent(
            role="assistant",
            content=response,
        )
        chat.history.add_message(host_response)
        
        return chat