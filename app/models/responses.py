from pydantic import BaseModel
from typing import List, Optional

class FileResponse(BaseModel):
    path: str


class ArtifactManifestResponse(BaseModel):
    model_spec: str
    dax_files: List[str]
    visual_spec: str
    powerquery_files: List[str]


class TE3ScriptResponse(BaseModel):
    script_path: str


class LayoutResponse(BaseModel):
    layout_path: str
