from typing import List, Optional
from pydantic import BaseModel

class AIChatRequest(BaseModel):
    question: str
    conversationHistory: Optional[List[dict]] = None

class AIChatResponse(BaseModel):
    response: str
    boardUpdates: Optional[dict] = None
