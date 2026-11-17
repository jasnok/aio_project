"""여행 MCP 공통 스키마 규칙."""

from pydantic import BaseModel, ConfigDict


class StrictInputModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class StrictOutputModel(BaseModel):
    model_config = ConfigDict(extra="forbid")
