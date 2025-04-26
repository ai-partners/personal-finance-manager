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

AGENT1_NAME = os.getenv("AGENT1_NAME")
AGENT1_ID = os.getenv("AGENT1_ID")

AGENT2_NAME = os.getenv("AGENT2_NAME")
AGENT2_ID = os.getenv("AGENT2_ID")

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
        
        # Create the agent using the kernel
        host = ChatCompletionAgent(
            kernel=kernel, 
            name="HostAgent", 
            instructions="""
            You are an agent that serves as a host in a group chat of agents. Your goal is to welcome the user to the personal finance manager, which can help them:
                1. Create transactional accounts and income/expense categories
                2. Create financial transactions or movements such as income and expenses
            Your goal is only to provide information about the application's context. If the user requests to perform any particular action, it will be the responsibility of the other agents in the group chat.
            If the user makes a request that includes attached receipts or invoices, you must perform the image reading and then pass the data to the other agents.
            """,
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

        # Create the AgentGroupChat with selection and termination strategies
        print("Creating AgentGroupChat...")
        chat = AgentGroupChat(
            agents=[host, agent1, agent2],
            selection_strategy=KernelFunctionSelectionStrategy(
                initial_agent=host,
                function=selection_function,
                kernel=kernel,
                result_parser=lambda result: str(result.value[0]).strip() if result.value[0] is not None else AGENT1_NAME,
                history_variable_name="history",
                history_reducer=history_reducer,
            ),
            termination_strategy=KernelFunctionTerminationStrategy(
                agents=[host, agent1, agent2],
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
            Indicate only the name of the chosen participant without explanation.

            Choose only one of the following agents:
            - {AGENT1_NAME}: Creation of accounts and categories of income and expenses.
            - {AGENT2_NAME}: Records financial movements and transactions.
            - HostAgent: For any other request that the previous agents cannot resolve, for example read receipts or images.

            Rules:
                1. An agent must complete its objective before another agent can take the turn.
                2. If an agent is in the middle of a process (creating accounts, categories, or movements), that same agent must continue.
                3. Only when an agent explicitly indicates that it has finished its task, another agent can intervene.
                4. If an agent mentions that it needs more information or is waiting for a user response, that same agent must continue.
                5. If an agent uses phrases like "I need to complete," "let's continue with," "to finalize," it means it has not yet finished its task.
                6. Only when an agent indicates "I have completed my part" or "successfully registered" or similar, consider switching agents.

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
            user_message = ChatMessageContent(
                role="user",
                items=[
                    TextContent(text=message.content),
                    ImageContent(uri=utilities.upload_to_azure_blob(file_path=images[0].path, blob_name=images[0].name)),
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
    
    async def add_host_response_to_history(self, chat: AgentGroupChat, response: str) -> AgentGroupChat:
        host_response = ChatMessageContent(
            role="assistant",
            content=response,
        )
        chat.history.add_message(host_response)
        
        return chat