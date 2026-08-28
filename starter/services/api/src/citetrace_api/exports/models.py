from pydantic import BaseModel

class ExportRequest(BaseModel):
    format: str = "json"
