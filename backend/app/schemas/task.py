import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    input: str = Field(min_length=1)


class TaskStepRead(BaseModel):
    id: uuid.UUID
    name: str
    status: str
    result: dict[str, object] | None

    model_config = ConfigDict(from_attributes=True)


class TaskRead(BaseModel):
    id: uuid.UUID
    title: str
    input: str = Field(validation_alias="input_text", serialization_alias="input")
    status: str
    created_at: datetime
    updated_at: datetime
    steps: list[TaskStepRead] = []

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class TaskListRead(BaseModel):
    items: list[TaskRead]
    total: int
