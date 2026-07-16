"""Serviço transacional de processo e workflow (Épico 2).

Reúne a criação (US 2.1), o despacho (US 2.2) e a devolução (US 2.2b). Cada
operação roda numa única transação e, quando move o processo, insere um evento
imutável em `tramitacao` na mesma transação (D4). A autorização por unidade é
aplicada pelo router (`require_acesso_unidade`) antes de chamar despacho/devolução.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.db.models import (
    MotivoDevolucao,
    Notificacao,
    Processo,
    ProcessoInteressado,
    SistemaConfig,
    StatusProcesso,
    TipoDocumentoInteressado,
    TipoEventoTramitacao,
    TipoNotificacao,
    TipoParticipacaoInteressado,
    TipoProcesso,
    Tramitacao,
    Usuario,
)
from app.schemas.processo import CriarProcessoRequest, DevolverRequest, InteressadoInput
from app.services import notificacao as notificacao_service
from app.services.documento_fiscal import normalizar_documento, validar_cnpj, validar_cpf
from app.services.numero_processo import alocar_numero
from app.services.processo_estado import validar_transicao
from app.services.roteiro_snapshot import (
    RoteiroInvalido,
    etapas_do_roteiro,
    etapa_anterior,
    is_primeira,
    is_ultima,
    proxima_etapa,
    validar_roteiro_para_criacao,
)
from app.services.roteiros import obter_roteiro_vigente

MSG_SEM_UNIDADE = "Servidor não está vinculado a nenhuma unidade."
MSG_TIPO_INEXISTENTE = "Tipo de processo não encontrado."
MSG_CPF_INVALIDO = "CPF inválido — verifique o número informado"
MSG_CNPJ_INVALIDO = "CNPJ inválido — verifique o número informado"
MSG_TIPO_DOC_OBRIGATORIO = "Informe o tipo de documento (CPF ou CNPJ) do interessado."
MSG_MOTIVO_OBRIGATORIO = "Selecione um motivo para a devolução"
MSG_DEVOLUCAO_NA_ORIGEM = (
    "Não é possível devolver um processo que está na unidade de origem do roteiro"
)


def _erro(codigo: int, detalhe: str) -> HTTPException:
    return HTTPException(status_code=codigo, detail=detalhe)


def _validar_interessado(item: InteressadoInput) -> tuple[str | None, TipoDocumentoInteressado | None]:
    """Valida documento (se informado) e devolve (documento_normalizado, tipo_documento)."""
    if item.documento is None or item.documento.strip() == "":
        return None, None
    if item.tipo_documento is None:
        raise _erro(status.HTTP_422_UNPROCESSABLE_CONTENT, MSG_TIPO_DOC_OBRIGATORIO)
    if item.tipo_documento == "cpf":
        if not validar_cpf(item.documento):
            raise _erro(status.HTTP_422_UNPROCESSABLE_CONTENT, MSG_CPF_INVALIDO)
        return normalizar_documento(item.documento), TipoDocumentoInteressado.CPF
    if not validar_cnpj(item.documento):
        raise _erro(status.HTTP_422_UNPROCESSABLE_CONTENT, MSG_CNPJ_INVALIDO)
    return normalizar_documento(item.documento), TipoDocumentoInteressado.CNPJ


def criar_processo(db: Session, *, criador: Usuario, payload: CriarProcessoRequest) -> Processo:
    """Cria o processo com número único, snapshot de roteiro e interessados (US 2.1)."""
    if criador.unidade_id is None:
        raise _erro(status.HTTP_422_UNPROCESSABLE_CONTENT, MSG_SEM_UNIDADE)

    try:
        tipo_id = uuid.UUID(payload.tipo_processo_id)
    except ValueError as exc:
        raise _erro(status.HTTP_422_UNPROCESSABLE_CONTENT, MSG_TIPO_INEXISTENTE) from exc

    tipo = db.get(TipoProcesso, tipo_id)
    if tipo is None:
        raise _erro(status.HTTP_422_UNPROCESSABLE_CONTENT, MSG_TIPO_INEXISTENTE)

    roteiro = obter_roteiro_vigente(db, tipo_id)
    try:
        etapas = etapas_do_roteiro(db, roteiro.id) if roteiro else []
        validar_roteiro_para_criacao(roteiro, etapas)
    except RoteiroInvalido as exc:
        # US 2.1 Cen.3c — tipo sem roteiro configurado.
        raise _erro(status.HTTP_422_UNPROCESSABLE_CONTENT, str(exc)) from exc

    # Valida todos os interessados antes de qualquer escrita (falha sem efeito colateral).
    interessados_norm = [(item, *_validar_interessado(item)) for item in payload.interessados]

    hoje = date.today()
    numero = alocar_numero(db, hoje.year)

    processo = Processo(
        numero=numero,
        assunto=payload.assunto,
        tipo_processo_id=tipo_id,
        roteiro_id=roteiro.id,
        status=StatusProcesso.ABERTO,
        unidade_atual_id=criador.unidade_id,
        unidade_origem_id=criador.unidade_id,
        ordem_atual=0,  # índice posicional na 1ª etapa do snapshot (D3)
        prazo_dias=payload.prazo_dias,
        prazo_em=hoje + timedelta(days=payload.prazo_dias),
        criado_por_id=criador.id,
    )
    db.add(processo)
    db.flush()  # materializa processo.id para os interessados

    for item, documento, tipo_doc in interessados_norm:
        db.add(
            ProcessoInteressado(
                processo_id=processo.id,
                nome=item.nome,
                documento=documento,
                tipo_documento=tipo_doc,
                tipo_participacao=(
                    TipoParticipacaoInteressado(item.tipo_participacao)
                    if item.tipo_participacao
                    else None
                ),
            )
        )

    db.commit()
    db.refresh(processo)
    return processo


def despachar(
    db: Session, *, processo: Processo, responsavel: Usuario, confirmar: bool
) -> tuple[Processo, list[Notificacao]]:
    """Despacha para a próxima etapa; na última, conclui (com confirmação). US 2.2.

    Retorna também as notificações internas geradas (US 5.1/5.3) — inseridas na
    mesma transação do evento de tramitação (D1, design.md
    `notificacoes-e-alertas`) — para o router enfileirar os e-mails correspondentes
    após o commit.
    """
    etapas = etapas_do_roteiro(db, processo.roteiro_id)

    if is_ultima(etapas, processo.ordem_atual):
        if not confirmar:
            # US 2.2 Cen.2/4 — pede confirmação de conclusão; Cen.3: cancelar não altera nada.
            if len(etapas) == 1:
                prompt = (
                    "Esta é a unidade de origem e destino final do roteiro. "
                    "Deseja concluir o processo?"
                )
            else:
                prompt = "Este é o destino final do roteiro. Deseja concluir o processo?"
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=prompt)

        origem_id = processo.unidade_atual_id
        validar_transicao(processo.status, StatusProcesso.CONCLUIDO)
        processo.status = StatusProcesso.CONCLUIDO
        processo.concluido_em = datetime.now(timezone.utc)
        # Congelamento do prazo de arquivamento (US 2.5 Cen.2, D1): o prazo
        # vigente em sistema_config é lido e fixado como instante absoluto —
        # alterações futuras do parâmetro global não retroagem sobre este processo.
        config = db.get(SistemaConfig, 1)
        processo.arquivar_em = processo.concluido_em + timedelta(days=config.prazo_arquivamento_dias)
        db.add(
            Tramitacao(
                processo_id=processo.id,
                tipo_evento=TipoEventoTramitacao.CONCLUSAO,
                unidade_origem_id=origem_id,
                unidade_destino_id=None,
                responsavel_id=responsavel.id,
                status_resultante=StatusProcesso.CONCLUIDO,
            )
        )
        notificacoes = notificacao_service.gerar_notificacoes(
            db, tipo=TipoNotificacao.CONCLUIDO, processo=processo, unidade_id=origem_id
        )
        db.commit()
        db.refresh(processo)
        return processo, notificacoes

    prox = proxima_etapa(etapas, processo.ordem_atual)
    assert prox is not None  # garantido por not is_ultima
    origem_id = processo.unidade_atual_id
    validar_transicao(processo.status, StatusProcesso.EM_TRAMITACAO)
    processo.status = StatusProcesso.EM_TRAMITACAO
    processo.ordem_atual += 1
    processo.unidade_atual_id = prox.unidade_id
    db.add(
        Tramitacao(
            processo_id=processo.id,
            tipo_evento=TipoEventoTramitacao.DESPACHO,
            unidade_origem_id=origem_id,
            unidade_destino_id=prox.unidade_id,
            responsavel_id=responsavel.id,
            status_resultante=StatusProcesso.EM_TRAMITACAO,
        )
    )
    notificacoes = notificacao_service.gerar_notificacoes(
        db,
        tipo=TipoNotificacao.NOVO_PROCESSO,
        processo=processo,
        unidade_id=prox.unidade_id,
        unidade_origem_id=origem_id,
    )
    db.commit()
    db.refresh(processo)
    return processo, notificacoes


def devolver(
    db: Session, *, processo: Processo, responsavel: Usuario, payload: DevolverRequest
) -> Processo:
    """Devolve para a etapa anterior, com motivo obrigatório. US 2.2b."""
    if not payload.motivo:
        raise _erro(status.HTTP_422_UNPROCESSABLE_CONTENT, MSG_MOTIVO_OBRIGATORIO)
    try:
        motivo = MotivoDevolucao(payload.motivo)
    except ValueError as exc:
        raise _erro(status.HTTP_422_UNPROCESSABLE_CONTENT, MSG_MOTIVO_OBRIGATORIO) from exc

    etapas = etapas_do_roteiro(db, processo.roteiro_id)
    if is_primeira(etapas, processo.ordem_atual):
        # US 2.2b Cen.2 — bloqueio na primeira unidade do roteiro.
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=MSG_DEVOLUCAO_NA_ORIGEM)

    ant = etapa_anterior(etapas, processo.ordem_atual)
    assert ant is not None  # garantido por not is_primeira
    origem_id = processo.unidade_atual_id
    validar_transicao(processo.status, StatusProcesso.EM_TRAMITACAO)
    processo.status = StatusProcesso.EM_TRAMITACAO
    processo.ordem_atual -= 1
    processo.unidade_atual_id = ant.unidade_id
    db.add(
        Tramitacao(
            processo_id=processo.id,
            tipo_evento=TipoEventoTramitacao.DEVOLUCAO,
            unidade_origem_id=origem_id,
            unidade_destino_id=ant.unidade_id,
            responsavel_id=responsavel.id,
            status_resultante=StatusProcesso.EM_TRAMITACAO,
            motivo=motivo,
            justificativa=payload.justificativa,
        )
    )
    db.commit()
    db.refresh(processo)
    return processo
