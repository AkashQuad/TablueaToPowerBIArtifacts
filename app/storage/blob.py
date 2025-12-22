import os
from azure.storage.blob import BlobServiceClient
from pathlib import Path

conn = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
container = os.getenv("AZURE_STORAGE_CONTAINER")

if not conn or not container:
    raise Exception("Azure Blob settings missing")

service = BlobServiceClient.from_connection_string(conn)
container_client = service.get_container_client(container)


def upload_file(file_path: Path, blob_path: str) -> str:
    blob = container_client.get_blob_client(blob_path)

    with open(file_path, "rb") as data:
        blob.upload_blob(data, overwrite=True)

    return f"https://{service.account_name}.blob.core.windows.net/{container}/{blob_path}"


def download_file(blob_path: str, local_path: Path):
    blob = container_client.get_blob_client(blob_path)

    with open(local_path, "wb") as f:
        f.write(blob.download_blob().readall())

    return local_path
