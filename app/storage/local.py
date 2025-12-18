# from pathlib import Path
# import shutil

# def save_file(upload_file, target_path: Path):
#     target_path.parent.mkdir(parents=True, exist_ok=True)
#     with open(target_path, "wb") as f:
#         shutil.copyfileobj(upload_file.file, f)
#     return str(target_path)



from pathlib import Path
import shutil
import os

#
# BASE DIRECTORY FOR FILE STORAGE
#
# Local Development:
#   Uses ./work/ inside your project
#
# Azure Deployment:
#   Uses /home/site/wwwroot/work (Azure writable folder)
#

if os.getenv("WEBSITE_SITE_NAME"):  # running on Azure
    BASE_DIR = Path("/home/site/wwwroot/work")
else:  # running locally
    BASE_DIR = Path("./work")

# Ensure base directory exists
BASE_DIR.mkdir(parents=True, exist_ok=True)


def save_file(upload_file, target_filename: str):
    """
    Saves uploaded file to the BASE_DIR.
    Automatically creates directories if needed.
    """

    target_path = BASE_DIR / target_filename
    target_path.parent.mkdir(parents=True, exist_ok=True)

    with open(target_path, "wb") as f:
        shutil.copyfileobj(upload_file.file, f)

    return str(target_path)
