"""Modelos Pydantic expostos no contrato OpenAPI (geram os tipos TS)."""

from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field


class HealthResponse(BaseModel):
    status: str = Field(examples=["ok"])
    service: str = Field(examples=["api"])


class EmailTaskPayload(BaseModel):
    """Corpo da tarefa enfileirada no Cloud Tasks e entregue ao endpoint interno."""

    to: EmailStr
    subject: str
    body: str
    # Chave de idempotência do evento de origem (usada como task name no enqueue).
    event_id: str


class AckResponse(BaseModel):
    status: str = Field(examples=["acked"])
