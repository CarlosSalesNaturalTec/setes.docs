"""Schema da caixa de entrada de desenvolvimento (Settings.dev_email_inbox)."""

from __future__ import annotations

from pydantic import BaseModel


class DevEmailItem(BaseModel):
    to: str
    subject: str
    body: str
    event_id: str
