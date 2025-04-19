import os
import jsonref
from typing import Set
from dotenv import load_dotenv

from azure.ai.projects.models import OpenApiTool, OpenApiAnonymousAuthDetails
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential


def main():
    
    load_dotenv()

    # 1. Authenticate with the Azure AI project service
    project_client = AIProjectClient.from_connection_string(
        credential=DefaultAzureCredential(),
        conn_str=os.environ.get("PROJECT_CONNECTION_STRING"),
    )
 
    # 2. Add functions to the agent
    auth = OpenApiAnonymousAuthDetails()

    # Add record_account_logic_app openapi definition
    with open("./record_account_logic_app.json", "r") as f:
        openapi_record_account_logic_app = jsonref.loads(f.read())

    openapi_tool = OpenApiTool(
    name="record_account_logic_app",
    spec=openapi_record_account_logic_app,
    description="Registra un medio transaccional en la tabla de cuentas",
    auth=auth,
    default_parameters=["format"],
    )

    # Add record_category_logic_app openapi definition
    with open("./record_category_logic_app.json", "r") as f:
        openapi_record_category_logic_app = jsonref.loads(f.read())

    openapi_tool.add_definition(
    name="record_category_logic_app",
    spec=openapi_record_category_logic_app,
    description="Registra una categoría de ingreso o gasto en la tabla de categorías",
    auth=auth,
    )
    
    # 3. Define agent instructions
    agent_instructions="""
    Eres un asistente inteligente especializado en ayudar a nuevos usuarios a configurar una app de finanzas personales. 
    Tu objetivo es guiar de manera clara y amigable el proceso de onboarding, ayudando al usuario a registrar sus cuentas transaccionales, así como las categorías de ingresos y gastos.
    
    1. Registrar medios transaccionales (tabla “Cuentas”). 
    Utiliza la función disponible para registrar estos datos.
    Ayuda al usuario a registrar todas las cuentas que usará para manejar su dinero. Algunos ejemplos de cuentas que puede configurar:
    - Cuentas de ahorro
    - Tarjetas de crédito
    - Billeteras digitales
    - Billeteras físicas o efectivo

    Cuando un usuario desee registrar una cuenta, debes determinar el tipo de cuenta de acuerdo con:
        - Activo: Cuando la cuenta represente un deposito o capital disponible por parte del usuario.
        - Pasivo: Cuando la cuenta represente una deuda del usuario.

    2. Registrar categorías de ingreso (tabla “Categorías”).
    Utiliza la función disponible para registrar estos datos.
    Pregunta o sugiere al usuario que registre las fuentes por las que recibe dinero, como por ejemplo:
    - Salario
    - Pensión
    - Dividendos
    - Ventas
    - Honorarios
    Registra estas categorías en la tabla “Categorías”, bajo el tipo “Ingreso”. 

    3. Registrar categorías de gasto (tabla “Categorías”).
    Utiliza la función disponible para registrar estos datos.
    Ayuda al usuario a identificar los principales motivos de gasto, por ejemplo:
    - Comida
    - Arriendo
    - Transporte
    - Educación
    - Servicios públicos
    - Entretenimiento
    Registra estas categorías en la tabla “Categorías”, bajo el tipo “Gasto”. 

    4. Comportamiento del agente:
    - Si el usuario menciona una cuenta o categoría que no está registrada aún, ofrece registrarla de inmediato.
    - Confirma con el usuario antes de realizar cualquier acción, para evitar errores.
    - Mantén un tono amigable, claro y útil, como si fueras un guía que acompaña paso a paso.
    - Sugiere ejemplos si el usuario no sabe qué cuentas o categorías añadir.
    - Sé breve y directo, sin abrumar con demasiada información a la vez.
    - Reafirma cada paso con frases como: “Perfecto, ya registré tu cuenta 'Ahorros Bancolombia'”.
    """
    
    with project_client:

        agent = project_client.agents.create_agent(
            model=os.environ["MODEL_DEPLOYMENT_NAME"],
            name="Agent1-Onboarding",
            instructions=agent_instructions,
            tools=openapi_tool.definitions,
        )
        print(f"Created agent, ID: {agent.id}")
        
        # Create a thread for communication
        thread = project_client.agents.create_thread()
        print(f"Created thread, ID: {thread.id}")

        # Create a message in the thread
        # Test account creation
        # msgcontent = "Quiero registrar una cuenta que se llama Davivienda, es de ahorros. Es mi cuenta de nómina. Mi ID de usuario es 1."
        # Test category creation
        msgcontent = "Quiero registrar una categoría que se llame 'Comida', es el gasto relacionado a alimentación. Mi ID de usuario es 1."
        message = project_client.agents.create_message(
            thread_id=thread.id,
            role="user",
            content=msgcontent,
        )
        print(f"Created message, ID: {message.id}")

        # Create and process an agent run in the thread
        run = project_client.agents.create_and_process_run(thread_id=thread.id, agent_id=agent.id)
        print(f"Run finished with status: {run.status}")

        if run.status == "failed" or run.status == "incomplete":
            print(f"Run failed: {run.last_error}")

        # Delete the agent when done
        project_client.agents.delete_agent(agent.id)
        print("Deleted agent")

        # Fetch and log all messages
        messages = project_client.agents.list_messages(thread_id=thread.id)
        print(f"Messages: {messages}")


if __name__ == "__main__":
    main()