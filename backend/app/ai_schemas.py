from typing import List, Optional
from pydantic import BaseModel


class AICardUpdate(BaseModel):
    id: Optional[int] = None
    title: Optional[str] = None
    description: Optional[str] = None
    columnId: Optional[int] = None
    delete: Optional[bool] = None


class AIColumnUpdate(BaseModel):
    id: Optional[int] = None
    title: Optional[str] = None


class AIBoardUpdates(BaseModel):
    cards: Optional[List[AICardUpdate]] = None
    columns: Optional[List[AIColumnUpdate]] = None


class AIChatRequest(BaseModel):
    question: str


class AIChatResponse(BaseModel):
    response: str
    boardUpdates: Optional[AIBoardUpdates] = None
