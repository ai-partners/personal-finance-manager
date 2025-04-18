import json
import requests
from typing import Dict, Any, Callable

from azure.identity import DefaultAzureCredential
from azure.mgmt.logic import LogicManagementClient


class AzureLogicAppTool:
    """
    A service that manages multiple Logic Apps by retrieving and storing their callback URLs,
    and then invoking them with an appropriate payload.
    """

    def __init__(self, subscription_id: str, resource_group: str, credential=None):
        if credential is None:
            credential = DefaultAzureCredential()
        self.subscription_id = subscription_id
        self.resource_group = resource_group
        self.logic_client = LogicManagementClient(credential, subscription_id)

        self.callback_urls: Dict[str, str] = {}

    def register_logic_app(self, logic_app_name: str, trigger_name: str) -> None:
        """
        Retrieves and stores a callback URL for a specific Logic App + trigger.
        Raises a ValueError if the callback URL is missing.
        """
        callback = self.logic_client.workflow_triggers.list_callback_url(
            resource_group_name=self.resource_group,
            workflow_name=logic_app_name,
            trigger_name=trigger_name,
        )

        if callback.value is None:
            raise ValueError(f"No callback URL returned for Logic App '{logic_app_name}'.")

        self.callback_urls[logic_app_name] = callback.value

    def invoke_logic_app(self, logic_app_name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Invokes the registered Logic App (by name) with the given JSON payload.
        Returns a dictionary summarizing success/failure.
        """
        if logic_app_name not in self.callback_urls:
            raise ValueError(f"Logic App '{logic_app_name}' has not been registered.")

        url = self.callback_urls[logic_app_name]
        response = requests.post(url=url, json=payload)

        if response.ok:
            return {"result": f"Successfully invoked {logic_app_name}."}
        else:
            return {"error": (f"Error invoking {logic_app_name} " f"({response.status_code}): {response.text}")}


def create_record_account_function(service: AzureLogicAppTool, logic_app_name: str) -> Callable[[str, str, str], str]:
    """
    Return a function that registers an account in the database using logic apps.
    This keeps the LogicAppService instance out of global scope by capturing it in a closure.
    """

    def record_account(name: str, description: str, type: str, user_id: str) -> str:
        """
        Registra un medio transaccional en la tabla de cuentas.

        :param name (str): El nombre de la cuenta a registrar.
        :param description (str): Una descripción breve de la cuenta que se va a registrar.
        :param type (str): El tipo de la cuenta a registrar, puede ser de tipo Activo o Pasivo.
        :param user_id (str): El identificador del usuario que registra la cuenta.
        :return: El resultado de la operación de creación en la base de datos.
        :rtype: str
        """
        payload = {
            "Name": name,
            "Description": description,
            "Type": type,
            "UserId": user_id,
        }
        result = service.invoke_logic_app(logic_app_name, payload)
        return json.dumps(result)

    return record_account

def create_record_category_function(service: AzureLogicAppTool, logic_app_name: str) -> Callable[[str, str, str], str]:
    """
    Return a function that registers an category in the database using logic apps.
    This keeps the LogicAppService instance out of global scope by capturing it in a closure.
    """

    def record_category(name: str, description: str, type: str, user_id: str) -> str:
        """
        Registra una categoría de ingreso o gasto en la tabla de categorías.

        :param name (str): El nombre de la categoría a registrar.
        :param description (str): Una descripción breve de la categoría que se va a registrar.
        :param type (str): El tipo de la categoría a registrar, puede ser de tipo Ingreso o Gasto.
        :param user_id (str): El identificador del usuario que registra la cuenta.
        :return: El resultado de la operación de creación en la base de datos.
        :rtype: str
        """
        payload = {
            "Name": name,
            "Description": description,
            "Type": type,
            "UserId": user_id,
        }
        result = service.invoke_logic_app(logic_app_name, payload)
        return json.dumps(result)

    return record_category