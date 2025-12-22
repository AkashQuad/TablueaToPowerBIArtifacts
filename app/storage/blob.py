import os
from azure.storage.blob import BlobServiceClient
from pathlib import Path

# Load settings from Azure env variables
ACCOUNT_NAME = os.getenv("AZURE_STORAGE_ACCOUNT")
ACCOUNT_KEY = os.getenv("AZURE_STORAGE_KEY")
CONTAINER_NAME = os.getenv("AZURE_BLOB_CONTAINER")

if not ACCOUNT_NAME or not ACCOUNT_KEY or not CONTAINER_NAME:
    raise Exception("Azure Blob storage environment variables are missing")

# Construct blob service client
connection_string = (
    f"DefaultEndpointsProtocol=https;"
    f"AccountName={ACCOUNT_NAME};"
    f"AccountKey={ACCOUNT_KEY};"
    f"EndpointSuffix=core.windows.net"
)

blob_client_service = BlobServiceClient.from_connection_string(connection_string)
container_client = blob_client_service.get_container_client(CONTAINER_NAME)


def upload_file(file_path: Path, blob_path: str) -> str:
    """
    Upload local file to Blob storage
    file_path: Path("/tmp/work/parsed/file.json")
    blob_path: "parsed/file.json"
    """
    blob = container_client.get_blob_client(blob_path)

    with open(file_path, "rb") as data:
        blob.upload_blob(data, overwrite=True)

    return blob.url


def download_file(blob_path: str, local_path: Path):
    """
    Download blob to local temp path
    """
    blob = container_client.get_blob_client(blob_path)

    with open(local_path, "wb") as f:
        stream = blob.download_blob()
        f.write(stream.readall())

    return local_path
