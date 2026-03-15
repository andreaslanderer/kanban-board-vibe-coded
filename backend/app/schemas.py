from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class UserOut(BaseModel):
    id: int
    email: str
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class DevLoginRequest(BaseModel):
    email: str


class CardBase(BaseModel):
    title: str
    description: Optional[str] = None


class CardCreate(CardBase):
    pass


class CardUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None


class CardMove(BaseModel):
    columnId: int
    position: int


class CardOut(CardBase):
    id: int
    column_id: int
    position: int

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class ColumnOut(BaseModel):
    id: int
    board_id: int
    title: str
    position: int
    cards: List[CardOut] = []

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class BoardOut(BaseModel):
    id: int
    user_id: int
    name: str
    columns: List[ColumnOut] = []

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class ColumnUpdate(BaseModel):
    title: str
