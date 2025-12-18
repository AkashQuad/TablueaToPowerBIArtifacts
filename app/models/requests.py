from pydantic import BaseModel
from typing import Optional
from typing import Dict, Any

class TableauUploadRequest(BaseModel):
    report_id: Optional[str] = None


class ArtifactGenerationRequest(BaseModel):
    report_id: str


class TableauParseResponse(BaseModel):
    report_id: str
    parsed_meta_path: str


class SourceConfigRequest(BaseModel):
    report_id: str
    source_type: str
    source_config: Dict[str, Any]


class TE3ScriptRequest(BaseModel):
    model_spec_path: str
    template_path: str


class LayoutGenerationRequest(BaseModel):
    visual_spec_path: str
    dataset_name: str
