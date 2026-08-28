
from pydantic import BaseModel


class ContextWindow(BaseModel):
    text: str

def build_context_window(text: str) -> ContextWindow:
    return ContextWindow(text=text)
