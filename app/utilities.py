import os
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient
from dotenv import load_dotenv        

# Load environment variables 
load_dotenv()
AZURE_STORAGE_ACCOUNT_URL = os.getenv("AZURE_STORAGE_ACCOUNT_URL")
AZURE_STORAGE_CONTAINER_NAME = os.getenv("AZURE_STORAGE_CONTAINER_NAME")

class Utilities:

    def authenticate_user(self, username: str, password: str) -> tuple[str, dict]:
        # Emulate a user authentication process
        if (username, password) == ("daniel", "admin"):
            identifier="Daniel"
            metadata={"UserId": "1", "provider": "credentials"}
            return identifier, metadata

        if (username, password) == ("andres", "admin"):
            
            identifier="Andrés"
            metadata={"UserId": "2", "provider": "credentials"}
            return identifier, metadata

        else:
            return None
        
    def upload_to_azure_blob(self, file_path, blob_name=None):

        default_credential = DefaultAzureCredential()

        # Create the BlobServiceClient object
        blob_service_client = BlobServiceClient(AZURE_STORAGE_ACCOUNT_URL, credential=default_credential)
        
        # Get a reference to the container
        container_client = blob_service_client.get_container_client(AZURE_STORAGE_CONTAINER_NAME)
        
        # Create the container if it doesn't exist
        if not container_client.exists():
            container_client.create_container()
            print(f"Container '{AZURE_STORAGE_CONTAINER_NAME}' created")
        
        # If blob_name not specified, use the file name
        if blob_name is None:
            blob_name = os.path.basename(file_path)
        
        # Create blob client
        blob_client = blob_service_client.get_blob_client(
            container=AZURE_STORAGE_CONTAINER_NAME, 
            blob=blob_name
        )
        
        # Upload the file
        with open(file_path, "rb") as data:
            blob_client.upload_blob(data, overwrite=True)
        
        print(f"File '{file_path}' uploaded to container '{AZURE_STORAGE_CONTAINER_NAME}' as '{blob_name}'")
        
        # Return the URL of the blob
        return blob_client.url