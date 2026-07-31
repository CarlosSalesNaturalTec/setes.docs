"""Serviço de documentos — anexar, listar, remover e purgar (Épico 3, fatia A).

`anexar` valida formato (extensão + sniffing do conteúdo real, US 3.1 Cen.2/2b),
calcula hash e desduplica o nome de exibição (D3) antes de gravar no storage e
no banco. `pode_remover`/`remover` implementam a regra de custódia (D1): a
remoção é permitida sse o processo está `Aberto`, ou `Em Tramitação` com o
último evento de movimentação sendo uma `devolucao` (ainda não redespachado a
partir desta custódia). `purgar_documentos_vencidos` é o passo do job diário
que fecha a retenção de 30 dias (D7) — GCS antes de DB, commit por documento.
"""

from __future__ import annotations

import hashlib
import os
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Documento, Processo, StatusProcesso, TipoEventoTramitacao, Tramitacao, Usuario
from app.services.storage import Storage

MSG_FORMATO_NAO_PERMITIDO = "Formato de arquivo não permitido"
MSG_TAMANHO_EXCEDIDO = "Arquivo excede o tamanho máximo de 20 MB"
MSG_ARQUIVO_VAZIO = "Não é possível anexar arquivo vazio. Selecione um arquivo com conteúdo."
MSG_REMOCAO_BLOQUEADA = "Não é possível remover documentos de um processo que já foi despachado"
MSG_DOCUMENTO_NAO_ENCONTRADO = "Documento não encontrado."

TAMANHO_MAXIMO_BYTES = 20 * 1024 * 1024
RETENCAO_DIAS = 30

# Extensão declarada -> MIME canônico esperado (US 3.1 Cen.1: PDF/DOC/DOCX/JPG/PNG).
_EXTENSAO_MIME: dict[str, str] = {
    "pdf": "application/pdf",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "png": "image/png",
    "doc": "application/msword",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}

_EVENTOS_MOVIMENTACAO = (TipoEventoTramitacao.ENVIO, TipoEventoTramitacao.DEVOLUCAO)


def _erro(codigo: int, detalhe: str) -> HTTPException:
    return HTTPException(status_code=codigo, detail=detalhe)


def _sniff_mime(conteudo: bytes) -> str | None:
    """Detecta o MIME real pela assinatura binária (sniffing) — não confia no
    Content-Type declarado pelo cliente nem só na extensão (US 3.1 Cen.2 /
    proteção contra MIME falsificado, design.md Riscos)."""
    if conteudo.startswith(b"%PDF-"):
        return "application/pdf"
    if conteudo.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if conteudo.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if conteudo.startswith(b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"):
        return "application/msword"
    if conteudo.startswith(b"PK\x03\x04"):
        return "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    return None


def _validar_formato_e_tamanho(nome_arquivo: str, conteudo: bytes) -> str:
    """Valida extensão + sniffing + tamanho; devolve o MIME canônico. Levanta
    HTTPException com a mensagem exata do PRD em qualquer rejeição — nada é
    gravado no bucket nem no banco antes desta validação passar."""
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


def _resolver_nome_exibicao(db: Session, *, processo_id: uuid.UUID, nome_original: str) -> str:
    """Sufixo `(n)` só quando colide com outro documento VISÍVEL do processo (D3)."""
    existentes = {
        d.nome_exibicao
        for d in db.scalars(
            select(Documento)
            .where(Documento.processo_id == processo_id)
            .where(Documento.removido_em.is_(None))
        ).all()
    }
    if nome_original not in existentes:
        return nome_original

    base, ext = os.path.splitext(nome_original)
    contador = 1
    while True:
        candidato = f"{base} ({contador}){ext}"
        if candidato not in existentes:
            return candidato
        contador += 1


def anexar(
    db: Session,
    *,
    processo: Processo,
    usuario: Usuario,
    storage: Storage,
    nome_arquivo: str,
    conteudo: bytes,
) -> Documento:
    """Anexa um documento ao processo (US 3.1 Cen.1/2/2b/5).

    A anexação NÃO gera evento de tramitação (D6) — a autoria vive em
    `anexado_por_id`/`anexado_em`.
    """
    tipo_conteudo = _validar_formato_e_tamanho(nome_arquivo, conteudo)

    hash_sha256 = hashlib.sha256(conteudo).hexdigest()
    nome_exibicao = _resolver_nome_exibicao(db, processo_id=processo.id, nome_original=nome_arquivo)
    objeto_chave = f"{processo.id}/{uuid.uuid4()}"

    storage.salvar(objeto_chave, conteudo, content_type=tipo_conteudo)

    documento = Documento(
        processo_id=processo.id,
        nome_original=nome_arquivo,
        nome_exibicao=nome_exibicao,
        objeto_chave=objeto_chave,
        tipo_conteudo=tipo_conteudo,
        tamanho_bytes=len(conteudo),
        hash_sha256=hash_sha256,
        anexado_por_id=usuario.id,
    )
    db.add(documento)
    db.commit()
    db.refresh(documento)
    return documento


def listar(db: Session, *, processo_id: uuid.UUID) -> list[Documento]:
    """Só documentos visíveis (`removido_em IS NULL`, US 3.1 Cen.3)."""
    return list(
        db.scalars(
            select(Documento)
            .where(Documento.processo_id == processo_id)
            .where(Documento.removido_em.is_(None))
            .order_by(Documento.anexado_em)
        ).all()
    )


def obter_visivel(db: Session, *, processo_id: uuid.UUID, documento_id: uuid.UUID) -> Documento:
    documento = db.scalars(
        select(Documento)
        .where(Documento.id == documento_id)
        .where(Documento.processo_id == processo_id)
        .where(Documento.removido_em.is_(None))
    ).first()
    if documento is None:
        raise _erro(status.HTTP_404_NOT_FOUND, MSG_DOCUMENTO_NAO_ENCONTRADO)
    return documento


def pode_remover(db: Session, *, processo: Processo) -> bool:
    """Regra de custódia (D1): permitido em `Aberto`; em `Em Tramitação` só se
    o último evento de movimentação (despacho/devolução) foi uma devolução —
    ou seja, o processo entrou na unidade atual por devolução e ainda não foi
    redespachado a partir desta custódia (Cen.3/4/4b/4c)."""
    if processo.status == StatusProcesso.ABERTO:
        return True
    if processo.status != StatusProcesso.EM_TRAMITACAO:
        return False

    ultimo_movimento = db.scalars(
        select(Tramitacao)
        .where(Tramitacao.processo_id == processo.id)
        .where(Tramitacao.tipo_evento.in_(_EVENTOS_MOVIMENTACAO))
        .order_by(Tramitacao.criado_em.desc())
    ).first()
    return ultimo_movimento is not None and ultimo_movimento.tipo_evento == TipoEventoTramitacao.DEVOLUCAO


def remover(db: Session, *, processo: Processo, documento: Documento, usuario: Usuario) -> Documento:
    """Soft-delete com retenção de 30 dias + evento imutável `remover_documento`
    (US 3.1 Cen.3, D6). Bloqueia conforme `pode_remover` (Cen.4/4b/4c)."""
    if not pode_remover(db, processo=processo):
        raise _erro(status.HTTP_409_CONFLICT, MSG_REMOCAO_BLOQUEADA)

    agora = datetime.now(timezone.utc)
    documento.removido_em = agora
    documento.removido_por_id = usuario.id
    documento.purgar_em = agora + timedelta(days=RETENCAO_DIAS)
    db.add(
        Tramitacao(
            processo_id=processo.id,
            tipo_evento=TipoEventoTramitacao.REMOVER_DOCUMENTO,
            unidade_origem_id=None,
            unidade_destino_id=None,
            responsavel_id=usuario.id,
            status_resultante=processo.status,
        )
    )
    db.commit()
    db.refresh(documento)
    return documento


def listar_removidos_em_retencao(db: Session, *, agora: datetime) -> list[Documento]:
    """Documentos em período de retenção (soft-deleted e ainda não purgados),
    cross-processo — a área é do Administrador (acesso irrestrito, D5), não
    filtrada por unidade. Restaurável ⇔ `removido_em IS NOT NULL AND
    purgar_em > agora` (D2); documento já purgado não existe mais (a purga faz
    DELETE), então simplesmente não aparece. Ordenado por data de remoção
    (US 8.7 Cen.1/2/3)."""
    return list(
        db.scalars(
            select(Documento)
            .where(Documento.removido_em.is_not(None))
            .where(Documento.purgar_em > agora)
            .order_by(Documento.removido_em)
        ).all()
    )


def restaurar(db: Session, *, documento: Documento, admin: Usuario) -> Documento:
    """Restaura um documento em retenção — inversa exata do soft-delete (US 8.7
    Cen.1, D1/D3/D4/D6). Recarrega o documento com o predicado de retenção
    **dentro da transação** (não confia no id vindo da listagem): se a purga do
    job diário apagou a linha entre o GET e o POST, o resultado é 404 limpo
    (US 8.7 Cen.2). Re-resolve `nome_exibicao` sobre os visíveis atuais para não
    colidir (D3), limpa os três campos de remoção e insere o evento imutável
    `restaurar_documento` (Admin responsável, unidades nulas, status atual —
    a restauração não altera a máquina de estados, D6). Não toca no storage
    (o objeto nunca saiu do bucket durante a retenção, D4)."""
    agora = datetime.now(timezone.utc)
    restauravel = db.scalars(
        select(Documento)
        .where(Documento.id == documento.id)
        .where(Documento.removido_em.is_not(None))
        .where(Documento.purgar_em > agora)
    ).first()
    if restauravel is None:
        raise _erro(status.HTTP_404_NOT_FOUND, MSG_DOCUMENTO_NAO_ENCONTRADO)

    processo = db.get(Processo, restauravel.processo_id)
    restauravel.nome_exibicao = _resolver_nome_exibicao(
        db, processo_id=restauravel.processo_id, nome_original=restauravel.nome_exibicao
    )
    restauravel.removido_em = None
    restauravel.removido_por_id = None
    restauravel.purgar_em = None
    db.add(
        Tramitacao(
            processo_id=restauravel.processo_id,
            tipo_evento=TipoEventoTramitacao.RESTAURAR_DOCUMENTO,
            unidade_origem_id=None,
            unidade_destino_id=None,
            responsavel_id=admin.id,
            status_resultante=processo.status,
        )
    )
    db.commit()
    db.refresh(restauravel)
    return restauravel


def purgar_documentos_vencidos(db: Session, *, agora: datetime, storage: Storage) -> int:
    """Purga física dos documentos vencidos (D7): remove o objeto do storage
    **antes** de deletar a linha, commit por documento (retomável). Seleção
    por estado atual garante idempotência — reexecução não encontra o que já
    foi purgado."""
    documentos = db.scalars(
        select(Documento)
        .where(Documento.removido_em.is_not(None))
        .where(Documento.purgar_em <= agora)
    ).all()

    total = 0
    for documento in documentos:
        storage.remover(documento.objeto_chave)
        db.delete(documento)
        db.commit()
        total += 1
    return total
