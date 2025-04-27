import chainlit as cl

from utilities import Utilities
from kernel import KernelChatGroup

utilities = Utilities()
kernel = KernelChatGroup()

@cl.password_auth_callback
def auth_callback(username: str, password: str):
    identifier, metadata = utilities.authenticate_user(username, password)
    if identifier :
        return cl.User(
                identifier=identifier, 
                metadata=metadata
                )
    else:
        return None 

@cl.set_starters
async def set_starters():
    return [
        cl.Starter(
            label="Create an account",
            message="I want to create an account",
            icon="/public/starters/create_account.svg",
            ),

        cl.Starter(
            label="Create a category",
            message="I want to create a category",
            icon="/public/starters/create_category.svg",
            ),
        cl.Starter(
            label="Record a transaction",
            message="I want to create a transaction (I've already created a accounts and categories)",
            icon="/public/starters/create_transaction.svg",
            ),
        cl.Starter(
            label="Analyze my data",
            message="I want to analyze my transactions of the last month",
            icon="/public/starters/analyze_data.svg",
            ),
        ]

@cl.on_chat_start
async def on_chat_start():
    chat = await kernel.initialize_chat_group()
    cl.user_session.set("chat", chat)

@cl.on_message
async def on_message(message: cl.Message):
    chat = cl.user_session.get("chat")
    answer = cl.Message(content="")

    # Add needed messages to the chat group
    chat = await kernel.add_user_message_to_chat(chat=chat, message=message) 

    # Invoke the chat group
    async for response in chat.invoke_stream():
        if response.content:
            answer.author=str(response.name)
            await answer.stream_token(str(response.content))

    # Add vision agent response to the agent chat group history
    # It's not a default behavior of the ChatCompletionAgent
    if answer.author == "VisionAgent":
        chat = await kernel.add_chat_completion_agent_response_to_history(chat=chat, response=answer.content)

    await answer.send()

"""
# Enable only for testing or debugging purposes
if __name__ == "__main__":
    from chainlit.cli import run_chainlit
    run_chainlit(__file__)

# For running the app, use the command:
# chainlit run main.py
"""