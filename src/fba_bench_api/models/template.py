from typing import List, Dict, Any

from pydantic import BaseModel, Field, ConfigDict


class Template(BaseModel):
    """Model representing a single template from YAML config files."""
    name: str = Field(..., description="Name of the template file")
    path: str = Field(..., description="Relative path to the template file")
    content: str = Field(..., description="Raw YAML content as string")
    parsed: Dict[str, Any] = Field(default_factory=dict, description="Parsed YAML object")
    size: int = Field(..., ge=0, description="File size in bytes")
    modified: str = Field(..., description="Last modified timestamp in ISO 8601 format")

    model_config = ConfigDict(extra="forbid")


class TemplateResponse(BaseModel):
    """Response model for the templates endpoint."""
    templates: List[Template] = Field(..., description="List of template objects")

    model_config = ConfigDict(extra="forbid")