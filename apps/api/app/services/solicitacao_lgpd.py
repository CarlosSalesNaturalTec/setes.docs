"""Canal público de solicitação LGPD e fila administrativa (Épico 10 — US
10.1/10.2). Validação de campos/documento e persistência da `solicitacao_lgpd`;
o efeito irreversível de anonimização em si vive em `services/lgpd.py`
(D1 — serviço único compartilhado com a rotina automática)."""

from __future__ import annotations

import os
import uuid
from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.db.models import Processo, SolicitacaoLgpd, StatusSolicitacaoLgpd, TipoSolicitacaoLgpd, Usuario
from app.services.documento_fiscal import normalizar_documento, validar_cpf
from app.services.lgpd import anonimizar_interessados
from app.services.protocolo_lgpd import gerar_protocolo
from app.services.storage import Storage

MSG_CAMPOS_OBRIGATORIOS = "Preencha todos os campos obrigatórios"
MSG_CPF_INVALIDO = "CPF inválido — verifique o número informado"
MSG_PROCESSO_NAO_ENCONTRADO = (
    "Nenhum processo encontrado com o número informado. Verifique o número e tente novamente."
)
MSG_FORMATO_NAO_PERMITIDO = (
    "Formato de arquivo não permitido. Anexe documento de identificação nos formatos PDF, JPG ou PNG."
)
MSG_ARQUIVO_VAZIO = "Não é possível anexar arquivo vazio. Selecione um arquivo com conteúdo."
MSG_TAMANHO_EXCEDIDO = "Arquivo excede o tamanho máximo de 20 MB"
MSG_JUSTIFICATIVA_OBRIGATORIA = "Justificativa é obrigatória para rejeitar a solicitação."
MSG_SOLICITACAO_NAO_ENCONTRADA = "Solicitação LGPD não encontrada."
MSG_ESTADO_TERMINAL = "Esta solicitação já está em estado terminal e não pode ser alterada."

TAMANHO_MAXIMO_BYTES = 20 * 1024 * 1024

_ESTADOS_TRANSICIONAVEIS = (StatusSolicitacaoLgpd.PENDENTE, StatusSolicitacaoLgpd.EM_ANALISE)

# Formatos aceitos (D6) — mais restrito que os anexos de processo (sem DOC/DOCX).
_EXTENSAO_MIME: dict[str, str] = {
    "pdf": "application/pdf",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "png": "image/png",
}


def _erro(codigo: int, detalhe: str) -> HTTPException:
    return HTTPException(status_code=codigo, detail=detalhe)


def _sniff_mime(conteudo: bytes) -> str | None:
    if conteudo.startswith(b"%PDF-"):
        return "application/pdf"
    if conteudo.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if conteudo.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    return None


def _validar_documento(nome_arquivo: str, conteudo: bytes) -> str:
    if len(conteudo) == 0:
        raise _erro(status.HTTP_422_UNPROCESSABLE_CONTENT, MSG_ARQUIVO_VAZIO)
    if len(conteudo) > TAMANHO_MAXIMO_BYTES:
        raise _erro(status.HTTP_422_UNPROCESSABLE_CONTENT, MSG_TAMANHO_EXCEDIDO)

    extensao = os.path.splitext(nome_arquivo)[1].lower().lstrip(".")
    mime_esperado = _EXTENSAO_MIME.get(extensao)
    if mime_esperado is None:
        raise _erro(status.HTTP_422_UNPROCESSABLE_CONTENT, MSG_FORMATO_NAO_PERMITIDO)

    mime_real = _sniff_mime(conteudo)
    if mime_real is None or mime_real != mime_esperado:
        raise _erro(status.HTTP_422_UNPROCESSABLE_CONTENT, MSG_FORMATO_NAO_PERMITIDO)

    return mime_real


def criar_solicitacao(
    db: Session,
    *,
    storage: Storage,
    numero_processo: str,
    nome: str,
    cpf: str,
    email: str,
    tipo: str,
    nome_arquivo: str,
    conteudo: bytes,
) -> SolicitacaoLgpd:
    """US 10.1 Cen.1/2/3/3b/4 — valida campos, documento e processo antes de
    gravar. Nenhum efeito colateral (storage/banco) antes da validação passar."""
    if not all(v.strip() for v in (numero_processo, nome, cpf, email, tipo)):
        raise _erro(status.HTTP_422_UNPROCESSABLE_CONTENT, MSG_CAMPOS_OBRIGATORIOS)

    if not validar_cpf(cpf):
        raise _erro(status.HTTP_422_UNPROCESSABLE_CONTENT, MSG_CPF_INVALIDO)

    processo = db.query(Processo).filter(Processo.numero == numero_processo.strip()).first()
    if processo is None:
        raise _erro(status.HTTP_404_NOT_FOUND, MSG_PROCESSO_NAO_ENCONTRADO)

    tipo_conteudo = _validar_documento(nome_arquivo, conteudo)

    objeto_chave = f"solicitacoes/{uuid.uuid4()}"
    storage.salvar(objeto_chave, conteudo, content_type=tipo_conteudo)

    protocolo = gerar_protocolo(db)
    solicitacao = SolicitacaoLgpd(
        protocolo=protocolo,
        processo_id=processo.id,
        nome_solicitante=nome.strip(),
        cpf_solicitante=normalizar_documento(cpf),
        email_solicitante=email.strip(),
        tipo=TipoSolicitacaoLgpd(tipo),
        documento_identificacao_chave=objeto_chave,
    )
    db.add(solicitacao)
    db.commit()
    db.refresh(solicitacao)
    return solicitacao


def listar(db: Session, *, status_filtro: str | None = None) -> list[SolicitacaoLgpd]:
    """US 10.2 Cen.1 — fila administrativa, mais recente primeiro."""
    query = db.query(SolicitacaoLgpd)
    if status_filtro is not None:
        query = query.filter(SolicitacaoLgpd.status == StatusSolicitacaoLgpd(status_filtro))
    return query.order_by(SolicitacaoLgpd.criado_em.desc()).all()


def obter(db: Session, solicitacao_id: uuid.UUID) -> SolicitacaoLgpd:
    solicitacao = db.get(SolicitacaoLgpd, solicitacao_id)
    if solicitacao is None:
        raise _erro(status.HTTP_404_NOT_FOUND, MSG_SOLICITACAO_NAO_ENCONTRADA)
    return solicitacao


def atender(db: Session, *, solicitacao: SolicitacaoLgpd, admin: Usuario, agora: datetime) -> SolicitacaoLgpd:
    """US 10.2 Cen.2 — dispara a anonimização (D1, mesmo serviço da rotina
    automática) e marca a solicitação como atendida."""
    if solicitacao.status not in _ESTADOS_TRANSICIONAVEIS:
        raise _erro(status.HTTP_409_CONFLICT, MSG_ESTADO_TERMINAL)

    processo = db.get(Processo, solicitacao.processo_id)
    anonimizar_interessados(
        db, processo, agora=agora, origem="manual", solicitacao_lgpd_id=solicitacao.id
    )

    solicitacao.status = StatusSolicitacaoLgpd.ATENDIDA
    solicitacao.atendido_em = agora
    solicitacao.atendido_por_id = admin.id
    db.commit()
    db.refresh(solicitacao)
    return solicitacao


def rejeitar(
    db: Session, *, solicitacao: SolicitacaoLgpd, admin: Usuario, justificativa: str, agora: datetime
) -> SolicitacaoLgpd:
    """US 10.2 Cen.3/3b — exige justificativa não vazia; transição final."""
    if solicitacao.status not in _ESTADOS_TRANSICIONAVEIS:
        raise _erro(status.HTTP_409_CONFLICT, MSG_ESTADO_TERMINAL)
    if not justificativa.strip():
        raise _erro(status.HTTP_422_UNPROCESSABLE_CONTENT, MSG_JUSTIFICATIVA_OBRIGATORIA)

    solicitacao.status = StatusSolicitacaoLgpd.REJEITADA
    solicitacao.justificativa_rejeicao = justificativa.strip()
    solicitacao.atendido_em = agora
    solicitacao.atendido_por_id = admin.id
    db.commit()
    db.refresh(solicitacao)
    return solicitacao
