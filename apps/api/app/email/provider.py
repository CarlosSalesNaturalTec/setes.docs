"""Cliente do provedor SaaS de e-mail (SendGrid/Mailgun — D6).

`send_email` levanta `EmailDeliveryError` em qualquer falha de entrega. Quem
chama (o endpoint interno) captura, registra em log e faz ACK — a fila usa
`maxAttempts=1`, então não há redespacho (US 5.2 Cen.3).
"""

from __future__ import annotations

from dataclasses import dataclass


class EmailDeliveryError(RuntimeError):
    """Falha ao entregar o e-mail ao provedor SaaS."""


@dataclass(frozen=True)
class EmailMessage:
    to: str
    subject: str
    body: str


def send_email(message: EmailMessage, *, api_key: str, sender: str) -> None:
    """Envia o e-mail via provedor SaaS.

    Implementação real (chamada HTTP ao SendGrid/Mailgun) entra num change de
    negócio. No bootstrap, valida a config e levanta em falta de credencial —
    o suficiente para o contrato de falha do endpoint ser exercido nos testes.
    """
    if not api_key:
        raise EmailDeliveryError("SENDGRID_API_KEY ausente — envio não configurado.")

    import httpx

    try:
        resp = httpx.post(
            "https://api.sendgrid.com/v3/mail/send",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "personalizations": [{"to": [{"email": message.to}]}],
                "from": {"email": sender},
                "subject": message.subject,
                "content": [{"type": "text/plain", "value": message.body}],
            },
            timeout=10.0,
        )
    except httpx.HTTPError as exc:  # rede/timeout
        raise EmailDeliveryError(f"Falha de rede ao contatar o provedor: {exc}") from exc

    if resp.status_code >= 400:
        raise EmailDeliveryError(
            f"Provedor recusou o envio: HTTP {resp.status_code} {resp.text[:200]}"
        )
