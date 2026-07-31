"""Builders compartilhados dos testes de processo/workflow (Épico 2).

Change tramitacao-manual: processos nascem sem roteiro, atribuídos ao criador
(`setor_atual_id`/`servidor_atual_id`) — os builders abaixo refletem isso.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy.orm import Session

from app.db.models import (
    PerfilUsuario,
    Processo,
    Setor,
    StatusProcesso,
    StatusUsuario,
    TipoProcesso,
    Unidade,
    UnidadeGestor,
    Usuario,
)
from app.security.senha import hash_senha

SENHA = "SenhaForte1"

# CPF/CNPJ válidos (dígitos verificadores corretos) para os testes.
CPF_VALIDO = "529.982.247-25"
CPF_INVALIDO = "529.982.247-24"
CNPJ_VALIDO = "11.222.333/0001-81"
CNPJ_INVALIDO = "11.222.333/0001-80"


def unidade(db: Session, nome: str = "COFIN") -> Unidade:
    u = Unidade(nome=nome, sigla=nome[:5].upper(), ativo=True)
    db.add(u)
    db.commit()
    return u


def setor(db: Session, unidade_alvo: Unidade, nome: str = "Protocolo") -> Setor:
    # Sigla única por sufixo (D1: única *dentro* da unidade) — evita colisão
    # entre setores de nomes com prefixo igual (ex.: "Setor"/"Setor2") em
    # testes que criam vários setores na mesma unidade.
    sigla = f"{nome[:3].upper()}{uuid.uuid4().hex[:5].upper()}"
    s = Setor(unidade_id=unidade_alvo.id, nome=nome, sigla=sigla, ativo=True)
    db.add(s)
    db.commit()
    return s


def usuario(
    db: Session,
    *,
    perfil=PerfilUsuario.SERVIDOR,
    unidade_id=None,
    setor_id=None,
    email: str | None = None,
) -> Usuario:
    u = Usuario(
        nome="Fulano",
        email=email or f"{uuid.uuid4()}@example.com",
        senha_hash=hash_senha(SENHA),
        perfil=perfil,
        status=StatusUsuario.ATIVO,
        unidade_id=unidade_id,
        setor_id=setor_id,
    )
    db.add(u)
    db.commit()
    return u


def servidor_com_setor(
    db: Session, unidade_alvo: Unidade, *, nome_setor: str = "Protocolo", email: str | None = None
) -> tuple[Usuario, Setor]:
    """Atalho: cria (ou reaproveita) um setor da unidade e um Servidor nele —
    todo processo exige criador com setor vinculado (US 2.1 Cen. sem setor)."""
    s = setor(db, unidade_alvo, nome=nome_setor)
    u = usuario(db, unidade_id=unidade_alvo.id, setor_id=s.id, email=email)
    return u, s


def gestor_de(db: Session, *unidades: Unidade, email: str | None = None) -> Usuario:
    g = usuario(db, perfil=PerfilUsuario.GESTOR, email=email)
    for u in unidades:
        db.add(UnidadeGestor(gestor_id=g.id, unidade_id=u.id))
    db.commit()
    return g


def tipo_processo(db: Session, nome: str = "Licitação") -> TipoProcesso:
    tipo = TipoProcesso(nome=f"{nome}-{uuid.uuid4().hex[:6]}", ativo=True)
    db.add(tipo)
    db.commit()
    return tipo


# Alias — nome anterior citado por alguns testes; roteiro deixou de existir,
# então "com roteiro" e "sem roteiro" são hoje o mesmo tipo de processo.
tipo_com_roteiro = tipo_processo
tipo_sem_roteiro = tipo_processo


def processo_concluido(
    db: Session,
    *,
    unidade: Unidade,
    criador: Usuario,
    tipo: TipoProcesso,
    concluido_em: datetime,
    arquivar_em: datetime,
    status: StatusProcesso = StatusProcesso.CONCLUIDO,
) -> Processo:
    """Cria um processo diretamente já `Concluído`, com `arquivar_em` sob
    controle do teste (arquivamento não passa pelo fluxo HTTP de conclusão)."""
    processo = Processo(
        numero=f"2026/{uuid.uuid4().int % 999999:06d}",
        assunto="Processo de teste",
        tipo_processo_id=tipo.id,
        status=status,
        unidade_atual_id=unidade.id,
        unidade_origem_id=unidade.id,
        setor_atual_id=criador.setor_id,
        servidor_atual_id=criador.id,
        prazo_dias=30,
        prazo_em=date.today(),
        criado_por_id=criador.id,
        concluido_em=concluido_em,
        arquivar_em=arquivar_em,
    )
    db.add(processo)
    db.commit()
    return processo


def processo_ativo(
    db: Session,
    *,
    unidade: Unidade,
    criador: Usuario,
    tipo: TipoProcesso,
    prazo_em: date,
    status: StatusProcesso = StatusProcesso.EM_TRAMITACAO,
) -> Processo:
    """Cria um processo diretamente `Aberto`/`Em Tramitação` com `prazo_em` sob
    controle do teste (rotina de prazo não passa pelo fluxo HTTP de criação)."""
    processo = Processo(
        numero=f"2026/{uuid.uuid4().int % 999999:06d}",
        assunto="Processo de teste",
        tipo_processo_id=tipo.id,
        status=status,
        unidade_atual_id=unidade.id,
        unidade_origem_id=unidade.id,
        setor_atual_id=criador.setor_id,
        servidor_atual_id=criador.id,
        prazo_dias=30,
        prazo_em=prazo_em,
        criado_por_id=criador.id,
    )
    db.add(processo)
    db.commit()
    return processo


def enviar_para(
    client,
    db: Session,
    *,
    processo_id: str,
    token_origem: str,
    unidade_destino: Unidade,
    nome_setor: str = "Setor",
    email_destino: str | None = None,
    mensagem: str | None = "Segue",
) -> tuple:
    """Cria setor+servidor na `unidade_destino` e envia o processo para lá —
    atalho comum aos testes que precisam de um Envio válido antes de exercitar
    Devolução/Reatribuição/Conclusão. Retorna (resposta, servidor_destino, setor_destino)."""
    setor_destino = setor(db, unidade_destino, nome_setor)
    servidor_destino = usuario(
        db, unidade_id=unidade_destino.id, setor_id=setor_destino.id, email=email_destino
    )
    resp = client.post(
        f"/processos/{processo_id}/enviar",
        json={
            "unidade_destino_id": str(unidade_destino.id),
            "setor_destino_id": str(setor_destino.id),
            "servidor_destino_id": str(servidor_destino.id),
            "mensagem": mensagem,
        },
        headers=auth(token_origem),
    )
    return resp, servidor_destino, setor_destino


def login(client, email: str) -> str:
    resp = client.post("/auth/login", json={"email": email, "senha": SENHA})
    assert resp.status_code == 200, resp.text
    return resp.json()["token"]


def auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}
