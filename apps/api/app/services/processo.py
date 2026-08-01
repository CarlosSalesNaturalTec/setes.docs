"""Serviço transacional de processo e tramitação manual (Épico 2).

Change tramitacao-manual: substitui o despacho roteirizado por três ações com
destino explícito — Envio, Devolução e Reatribuição — e a conclusão vira ação
própria. Cada operação roda numa única transação e, quando move o processo,
insere um evento imutável em `tramitacao` na mesma transação (D4). A
autorização por unidade é aplicada pelo router (`require_acesso_unidade`)
*antes* de chamar qualquer ação; a guarda de papel por ação (D5) é aplicada
aqui, depois dela.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.db.models import (
    MotivoDevolucao,
    Notificacao,
    PerfilUsuario,
    Processo,
    ProcessoInteressado,
    Setor,
    SistemaConfig,
    StatusProcesso,
    StatusUsuario,
    TipoDocumentoInteressado,
    TipoEventoTramitacao,
    TipoNotificacao,
    TipoParticipacaoInteressado,
    TipoProcesso,
    Tramitacao,
    Unidade,
    UnidadeGestor,
    Usuario,
)
from app.schemas.processo import (
    CriarProcessoRequest,
    DevolverRequest,
    EnviarRequest,
    InteressadoInput,
    ReatribuirRequest,
)
from app.security.autorizacao import registrar_acesso_negado
from app.services import notificacao as notificacao_service
from app.services.documento_fiscal import normalizar_documento, validar_cnpj, validar_cpf
from app.services.numero_processo import alocar_numero
from app.services.processo_estado import validar_transicao

MSG_SEM_UNIDADE = "Servidor não está vinculado a nenhuma unidade."
MSG_SEM_SETOR = "Você precisa estar vinculado a um setor para criar um processo."
MSG_TIPO_INEXISTENTE = "Tipo de processo não encontrado."
MSG_CPF_INVALIDO = "CPF inválido — verifique o número informado"
MSG_CNPJ_INVALIDO = "CNPJ inválido — verifique o número informado"
MSG_TIPO_DOC_OBRIGATORIO = "Informe o tipo de documento (CPF ou CNPJ) do interessado."
MSG_MOTIVO_OBRIGATORIO = "Selecione um motivo para a devolução"
MSG_DESTINO_INVALIDO = "Destino inválido."
MSG_UNIDADE_DESTINO_INVALIDA = "Unidade de destino inválida."
MSG_SETOR_FORA_DA_UNIDADE = "O setor informado não pertence à unidade de destino."
MSG_SERVIDOR_INVALIDO = "Servidor de destino inválido, inativo ou fora do setor informado."
MSG_DESTINO_MESMO_SERVIDOR = "O destino deve ser um servidor diferente do responsável atual."
MSG_SEM_REMETENTE_ANTERIOR = "Não há remetente anterior para o qual devolver este processo."
MSG_REATRIBUICAO_MUDA_UNIDADE = (
    "A reatribuição não muda de unidade — quando a unidade estiver errada, utilize Devolução."
)
MSG_JUSTIFICATIVA_OBRIGATORIA = "Informe a justificativa da reatribuição."
MSG_REATRIBUICAO_FINALIZADO = "Reatribuição só se aplica a processos em andamento."
MSG_ACAO_RESTRITA_SERVIDOR_ATUAL = (
    "Acesso negado — apenas o servidor responsável atual pode realizar esta ação."
)
MSG_ACESSO_NEGADO_REATRIBUIR = "Acesso negado — você não tem permissão para reatribuir este processo."
MSG_ACESSO_NEGADO_CONCLUIR = "Acesso negado — você não tem permissão para concluir este processo."

_EM_ANDAMENTO = (StatusProcesso.ABERTO, StatusProcesso.EM_TRAMITACAO)
_EVENTOS_ATRIBUICAO = (TipoEventoTramitacao.ENVIO, TipoEventoTramitacao.REATRIBUICAO)


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
    """Cria o processo com número único, sem roteiro (US 2.1, D1).

    Nasce atribuído ao próprio criador (`servidor_atual_id`/`setor_atual_id`),
    de modo que apareça na área de trabalho dele antes de qualquer tramitação.
    """
    if criador.unidade_id is None:
        raise _erro(status.HTTP_422_UNPROCESSABLE_CONTENT, MSG_SEM_UNIDADE)
    if criador.setor_id is None:
        raise _erro(status.HTTP_422_UNPROCESSABLE_CONTENT, MSG_SEM_SETOR)

    try:
        tipo_id = uuid.UUID(payload.tipo_processo_id)
    except ValueError as exc:
        raise _erro(status.HTTP_422_UNPROCESSABLE_CONTENT, MSG_TIPO_INEXISTENTE) from exc

    tipo = db.get(TipoProcesso, tipo_id)
    if tipo is None or not tipo.ativo:
        raise _erro(status.HTTP_422_UNPROCESSABLE_CONTENT, MSG_TIPO_INEXISTENTE)

    # Valida todos os interessados antes de qualquer escrita (falha sem efeito colateral).
    interessados_norm = [(item, *_validar_interessado(item)) for item in payload.interessados]

    hoje = date.today()
    numero = alocar_numero(db, hoje.year)

    processo = Processo(
        numero=numero,
        assunto=payload.assunto,
        tipo_processo_id=tipo_id,
        status=StatusProcesso.ABERTO,
        unidade_atual_id=criador.unidade_id,
        unidade_origem_id=criador.unidade_id,
        setor_atual_id=criador.setor_id,
        servidor_atual_id=criador.id,
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


def _e_gestor_da_unidade(db: Session, *, usuario: Usuario, unidade_id: uuid.UUID) -> bool:
    if usuario.perfil != PerfilUsuario.GESTOR:
        return False
    return (
        db.query(UnidadeGestor)
        .filter(UnidadeGestor.gestor_id == usuario.id, UnidadeGestor.unidade_id == unidade_id)
        .first()
        is not None
    )


def _ultimo_evento_atribuicao(db: Session, processo: Processo) -> Tramitacao | None:
    """Último evento de Envio/Reatribuição que trouxe o processo ao detentor
    atual (D3) — usado tanto para resolver o destino da Devolução quanto para
    identificar o "remetente" no papel de Reatribuir (D5) e o remetente
    original a notificar (D8)."""
    return (
        db.query(Tramitacao)
        .filter(
            Tramitacao.processo_id == processo.id,
            Tramitacao.tipo_evento.in_(_EVENTOS_ATRIBUICAO),
            Tramitacao.servidor_destino_id == processo.servidor_atual_id,
        )
        .order_by(Tramitacao.criado_em.desc())
        .first()
    )


def _exigir_servidor_atual(
    db: Session, *, processo: Processo, usuario: Usuario, rota: str, acao: str
) -> None:
    if usuario.id == processo.servidor_atual_id:
        return
    registrar_acesso_negado(
        db, usuario=usuario, rota=rota, contexto={"processo_id": str(processo.id), "acao": acao}
    )
    raise _erro(status.HTTP_403_FORBIDDEN, MSG_ACAO_RESTRITA_SERVIDOR_ATUAL)


def _exigir_papel_reatribuir(db: Session, *, processo: Processo, usuario: Usuario, rota: str) -> None:
    if usuario.id == processo.servidor_atual_id:
        return
    evento = _ultimo_evento_atribuicao(db, processo)
    if evento is not None and evento.responsavel_id == usuario.id:
        return
    if _e_gestor_da_unidade(db, usuario=usuario, unidade_id=processo.unidade_atual_id):
        return
    registrar_acesso_negado(
        db,
        usuario=usuario,
        rota=rota,
        contexto={"processo_id": str(processo.id), "acao": "reatribuir"},
    )
    raise _erro(status.HTTP_403_FORBIDDEN, MSG_ACESSO_NEGADO_REATRIBUIR)


def _exigir_papel_concluir(db: Session, *, processo: Processo, usuario: Usuario, rota: str) -> None:
    if usuario.id == processo.servidor_atual_id:
        return
    if _e_gestor_da_unidade(db, usuario=usuario, unidade_id=processo.unidade_atual_id):
        return
    registrar_acesso_negado(
        db, usuario=usuario, rota=rota, contexto={"processo_id": str(processo.id), "acao": "concluir"}
    )
    raise _erro(status.HTTP_403_FORBIDDEN, MSG_ACESSO_NEGADO_CONCLUIR)


def _resolver_setor_servidor_destino(
    db: Session, *, unidade_destino_id: uuid.UUID, setor_destino_id: uuid.UUID, servidor_destino_id: uuid.UUID
) -> tuple[Setor, Usuario]:
    setor = db.get(Setor, setor_destino_id)
    if setor is None or setor.unidade_id != unidade_destino_id:
        raise _erro(status.HTTP_422_UNPROCESSABLE_CONTENT, MSG_SETOR_FORA_DA_UNIDADE)

    servidor_destino = db.get(Usuario, servidor_destino_id)
    if (
        servidor_destino is None
        or servidor_destino.setor_id != setor_destino_id
        or servidor_destino.status != StatusUsuario.ATIVO
    ):
        raise _erro(status.HTTP_422_UNPROCESSABLE_CONTENT, MSG_SERVIDOR_INVALIDO)

    return setor, servidor_destino


def enviar(
    db: Session, *, processo: Processo, responsavel: Usuario, payload: EnviarRequest, rota: str
) -> tuple[Processo, list[Notificacao]]:
    """Envio com destino explícito — unidade, setor e servidor (D2, US 2.2)."""
    _exigir_servidor_atual(db, processo=processo, usuario=responsavel, rota=rota, acao="enviar")

    try:
        unidade_destino_id = uuid.UUID(payload.unidade_destino_id)
        setor_destino_id = uuid.UUID(payload.setor_destino_id)
        servidor_destino_id = uuid.UUID(payload.servidor_destino_id)
    except ValueError as exc:
        raise _erro(status.HTTP_422_UNPROCESSABLE_CONTENT, MSG_DESTINO_INVALIDO) from exc

    if servidor_destino_id == processo.servidor_atual_id:
        raise _erro(status.HTTP_422_UNPROCESSABLE_CONTENT, MSG_DESTINO_MESMO_SERVIDOR)

    unidade_destino = db.get(Unidade, unidade_destino_id)
    if unidade_destino is None or not unidade_destino.ativo:
        raise _erro(status.HTTP_422_UNPROCESSABLE_CONTENT, MSG_UNIDADE_DESTINO_INVALIDA)

    _resolver_setor_servidor_destino(
        db,
        unidade_destino_id=unidade_destino_id,
        setor_destino_id=setor_destino_id,
        servidor_destino_id=servidor_destino_id,
    )

    origem_unidade_id = processo.unidade_atual_id
    origem_setor_id = processo.setor_atual_id
    origem_servidor_id = processo.servidor_atual_id

    validar_transicao(processo.status, StatusProcesso.EM_TRAMITACAO)
    processo.status = StatusProcesso.EM_TRAMITACAO
    processo.unidade_atual_id = unidade_destino_id
    processo.setor_atual_id = setor_destino_id
    processo.servidor_atual_id = servidor_destino_id

    db.add(
        Tramitacao(
            processo_id=processo.id,
            tipo_evento=TipoEventoTramitacao.ENVIO,
            unidade_origem_id=origem_unidade_id,
            unidade_destino_id=unidade_destino_id,
            setor_origem_id=origem_setor_id,
            setor_destino_id=setor_destino_id,
            servidor_origem_id=origem_servidor_id,
            servidor_destino_id=servidor_destino_id,
            responsavel_id=responsavel.id,
            status_resultante=StatusProcesso.EM_TRAMITACAO,
            mensagem=payload.mensagem,
        )
    )
    notificacoes = notificacao_service.gerar_notificacoes(
        db,
        tipo=TipoNotificacao.NOVO_PROCESSO,
        processo=processo,
        usuario_id=servidor_destino_id,
        unidade_id=unidade_destino_id,
        unidade_origem_id=origem_unidade_id,
    )
    db.commit()
    db.refresh(processo)
    return processo, notificacoes


def devolver(
    db: Session, *, processo: Processo, responsavel: Usuario, payload: DevolverRequest, rota: str
) -> Processo:
    """Devolve ao remetente anterior, resolvido do histórico (D3, US 2.2b)."""
    _exigir_servidor_atual(db, processo=processo, usuario=responsavel, rota=rota, acao="devolver")

    if not payload.motivo:
        raise _erro(status.HTTP_422_UNPROCESSABLE_CONTENT, MSG_MOTIVO_OBRIGATORIO)
    try:
        motivo = MotivoDevolucao(payload.motivo)
    except ValueError as exc:
        raise _erro(status.HTTP_422_UNPROCESSABLE_CONTENT, MSG_MOTIVO_OBRIGATORIO) from exc

    evento_anterior = _ultimo_evento_atribuicao(db, processo)
    if evento_anterior is None:
        raise _erro(status.HTTP_409_CONFLICT, MSG_SEM_REMETENTE_ANTERIOR)

    origem_unidade_id = processo.unidade_atual_id
    origem_setor_id = processo.setor_atual_id
    origem_servidor_id = processo.servidor_atual_id

    destino_unidade_id = evento_anterior.unidade_origem_id
    destino_setor_id = evento_anterior.setor_origem_id
    destino_servidor_id = evento_anterior.servidor_origem_id

    validar_transicao(processo.status, StatusProcesso.EM_TRAMITACAO)
    processo.status = StatusProcesso.EM_TRAMITACAO
    processo.unidade_atual_id = destino_unidade_id
    processo.setor_atual_id = destino_setor_id
    processo.servidor_atual_id = destino_servidor_id

    db.add(
        Tramitacao(
            processo_id=processo.id,
            tipo_evento=TipoEventoTramitacao.DEVOLUCAO,
            unidade_origem_id=origem_unidade_id,
            unidade_destino_id=destino_unidade_id,
            setor_origem_id=origem_setor_id,
            setor_destino_id=destino_setor_id,
            servidor_origem_id=origem_servidor_id,
            servidor_destino_id=destino_servidor_id,
            responsavel_id=responsavel.id,
            status_resultante=StatusProcesso.EM_TRAMITACAO,
            motivo=motivo,
            justificativa=payload.justificativa,
        )
    )
    db.commit()
    db.refresh(processo)
    return processo


def reatribuir(
    db: Session, *, processo: Processo, responsavel: Usuario, payload: ReatribuirRequest, rota: str
) -> tuple[Processo, list[Notificacao]]:
    """Corrige atribuição indevida: mesma unidade, setor livre, servidor
    obrigatoriamente diferente; ortogonal ao status (D2, D4, D9)."""
    _exigir_papel_reatribuir(db, processo=processo, usuario=responsavel, rota=rota)

    if processo.status not in _EM_ANDAMENTO:
        raise _erro(status.HTTP_409_CONFLICT, MSG_REATRIBUICAO_FINALIZADO)

    if not payload.justificativa or not payload.justificativa.strip():
        raise _erro(status.HTTP_422_UNPROCESSABLE_CONTENT, MSG_JUSTIFICATIVA_OBRIGATORIA)

    try:
        setor_destino_id = uuid.UUID(payload.setor_destino_id)
        servidor_destino_id = uuid.UUID(payload.servidor_destino_id)
    except ValueError as exc:
        raise _erro(status.HTTP_422_UNPROCESSABLE_CONTENT, MSG_DESTINO_INVALIDO) from exc

    if servidor_destino_id == processo.servidor_atual_id:
        raise _erro(status.HTTP_422_UNPROCESSABLE_CONTENT, MSG_DESTINO_MESMO_SERVIDOR)

    setor = db.get(Setor, setor_destino_id)
    if setor is None or setor.unidade_id != processo.unidade_atual_id:
        raise _erro(status.HTTP_422_UNPROCESSABLE_CONTENT, MSG_REATRIBUICAO_MUDA_UNIDADE)

    servidor_destino = db.get(Usuario, servidor_destino_id)
    if (
        servidor_destino is None
        or servidor_destino.setor_id != setor_destino_id
        or servidor_destino.status != StatusUsuario.ATIVO
    ):
        raise _erro(status.HTTP_422_UNPROCESSABLE_CONTENT, MSG_SERVIDOR_INVALIDO)

    unidade_atual_id = processo.unidade_atual_id
    origem_setor_id = processo.setor_atual_id
    origem_servidor_id = processo.servidor_atual_id

    # Remetente original (D8): quem enviou o processo ao detentor "errado"
    # atual — resolvido ANTES de mover `servidor_atual_id` (D3/D6).
    evento_anterior = _ultimo_evento_atribuicao(db, processo)
    remetente_original_id = evento_anterior.responsavel_id if evento_anterior else None

    processo.setor_atual_id = setor_destino_id
    processo.servidor_atual_id = servidor_destino_id
    # status_resultante = status corrente, SEM validar_transicao (D4) — self-loop.

    db.add(
        Tramitacao(
            processo_id=processo.id,
            tipo_evento=TipoEventoTramitacao.REATRIBUICAO,
            unidade_origem_id=unidade_atual_id,
            unidade_destino_id=unidade_atual_id,
            setor_origem_id=origem_setor_id,
            setor_destino_id=setor_destino_id,
            servidor_origem_id=origem_servidor_id,
            servidor_destino_id=servidor_destino_id,
            responsavel_id=responsavel.id,
            status_resultante=processo.status,
            justificativa=payload.justificativa,
        )
    )

    notificacoes = notificacao_service.gerar_notificacoes(
        db,
        tipo=TipoNotificacao.REATRIBUIDO_PARA_VOCE,
        processo=processo,
        usuario_id=servidor_destino_id,
        unidade_id=unidade_atual_id,
        justificativa=payload.justificativa,
    )
    # D8 — omitida quando o remetente original é o próprio autor da correção,
    # ou quando não há remetente identificável (processo nunca tramitou).
    if remetente_original_id and remetente_original_id != responsavel.id:
        notificacoes += notificacao_service.gerar_notificacoes(
            db,
            tipo=TipoNotificacao.DESTINO_CORRIGIDO,
            processo=processo,
            usuario_id=remetente_original_id,
            unidade_id=unidade_atual_id,
            justificativa=f"Reatribuído para {servidor_destino.nome}.",
        )

    db.commit()
    db.refresh(processo)
    return processo, notificacoes


def concluir(
    db: Session, *, processo: Processo, responsavel: Usuario, rota: str
) -> tuple[Processo, list[Notificacao]]:
    """Conclusão como ação própria (US 2.2 Cen.2/3/4, US 2.5)."""
    _exigir_papel_concluir(db, processo=processo, usuario=responsavel, rota=rota)

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
            setor_origem_id=processo.setor_atual_id,
            setor_destino_id=None,
            servidor_origem_id=processo.servidor_atual_id,
            servidor_destino_id=None,
            responsavel_id=responsavel.id,
            status_resultante=StatusProcesso.CONCLUIDO,
        )
    )

    notificacoes: list[Notificacao] = []
    if processo.criado_por_id != responsavel.id:
        notificacoes = notificacao_service.gerar_notificacoes(
            db,
            tipo=TipoNotificacao.CONCLUIDO,
            processo=processo,
            usuario_id=processo.criado_por_id,
            unidade_id=origem_id,
        )
    db.commit()
    db.refresh(processo)
    return processo, notificacoes
