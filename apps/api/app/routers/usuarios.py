"""Gestão de usuários, reset de senha administrativo e "Meu Perfil"
(seções 6.2, 7, 10 de tasks.md)."""

from __future__ import annotations

import re
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.db.models import (
    LogSeguranca,
    PerfilUsuario,
    StatusUsuario,
    TipoEventoLog,
    TipoTokenAutenticacao,
    Unidade,
    UnidadeGestor,
    Usuario,
)
from app.db.session import get_db
from app.email.provider import EmailMessage
from app.email.queue import config_from_settings, enqueue_email_seguro
from app.schemas.auth import MensagemResponse
from app.schemas.usuarios import (
    AtualizarMeuPerfilRequest,
    CadastroUsuarioRequest,
    ListaUsuariosResponse,
    MeuPerfilResponse,
    TransferirUnidadeRequest,
    UnidadesGeridasRequest,
    UsuarioResponse,
)
from app.security.autorizacao import (
    get_current_user,
    registrar_acesso_negado,
    require_perfil,
    tem_acesso_a_unidade,
)
from app.security.senha import hash_senha_inutilizavel
from app.services import processo_consulta
from app.services.tokens import gerar_token
from app.services.usuarios import validar_vinculo_setor

router = APIRouter(tags=["usuarios"])

MSG_USUARIO_INATIVO_RESET = (
    "Não é possível resetar a senha de um usuário inativo. Reative o usuário antes de prosseguir."
)
MSG_NOME_OBRIGATORIO = "Nome é obrigatório"
MSG_EMAIL_FORMATO_INVALIDO = "Formato de e-mail inválido — informe um endereço de e-mail válido"
MSG_EMAIL_DUPLICADO = "E-mail já cadastrado no sistema"
MSG_UNIDADE_INVALIDA = "Unidade inválida ou inativa — selecione uma unidade ativa"
MSG_PERFIL_NAO_PERMITIDO_GESTOR = (
    "Você não tem permissão para atribuir este perfil. Apenas o Administrador pode "
    "cadastrar Gestores e Administradores."
)
MSG_UNIDADE_NAO_GERENCIADA = "Você não tem permissão para cadastrar usuários nesta unidade"
MSG_TRANSFERENCIA_APENAS_SERVIDOR = "Esta operação se aplica apenas a usuários com perfil Servidor."
MSG_USUARIO_NAO_ENCONTRADO = "Usuário não encontrado."
MSG_USUARIO_JA_INATIVO = "Usuário já está inativo"


def _msg_processos_pendentes(quantidade: int) -> str:
    return (
        f"Este usuário possui {quantidade} processo(s) em andamento. "
        "Reatribua os processos antes de desativar."
    )

_EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


@router.post("/admin/usuarios/{usuario_id}/resetar-senha", response_model=MensagemResponse)
def resetar_senha_admin(
    usuario_id: uuid.UUID,
    admin: Annotated[Usuario, Depends(require_perfil(PerfilUsuario.ADMINISTRADOR))],
    db: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> MensagemResponse:
    """PRD US 1.10 — invalida a senha atual, envia link de redefinição, audita."""
    alvo = db.get(Usuario, usuario_id)
    if alvo is None or alvo.status != StatusUsuario.ATIVO:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=MSG_USUARIO_INATIVO_RESET
        )

    alvo.senha_hash = hash_senha_inutilizavel()  # invalida a senha atual
    db.add(
        LogSeguranca(
            usuario_id=alvo.id,
            tipo_evento=TipoEventoLog.RESET_SENHA_ADMIN,
            contexto={"administrador_id": str(admin.id)},
        )
    )
    db.commit()

    gerado = gerar_token(db, usuario_id=alvo.id, tipo=TipoTokenAutenticacao.RECUPERACAO_SENHA)
    db.commit()

    link = f"{settings.frontend_base_url}/redefinir-senha/{gerado.valor}"
    enqueue_email_seguro(
        EmailMessage(
            to=alvo.email,
            subject="SETES.DOCS — redefinição de senha solicitada pelo Administrador",
            body=(
                f"Olá {alvo.nome}, o Administrador solicitou a redefinição da sua senha. "
                f"Use o link a seguir (válido por 2 horas): {link}"
            ),
        ),
        event_id=f"reset-admin:{gerado.token_id}",
        config=config_from_settings(settings),
    )

    return MensagemResponse(mensagem="Link de redefinição enviado ao usuário.")


@router.post("/usuarios", response_model=UsuarioResponse, status_code=status.HTTP_201_CREATED)
def cadastrar_usuario(
    payload: CadastroUsuarioRequest,
    usuario_atual: Annotated[Usuario, Depends(require_perfil(PerfilUsuario.ADMINISTRADOR, PerfilUsuario.GESTOR))],
    db: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> UsuarioResponse:
    """PRD US 1.1 (Administrador) e US 1.2 (Gestor, restrito à própria unidade/perfil Servidor)."""
    unidade_id = uuid.UUID(payload.unidade_id) if payload.unidade_id else None

    if usuario_atual.perfil == PerfilUsuario.GESTOR:
        if payload.perfil != "servidor":
            registrar_acesso_negado(
                db, usuario=usuario_atual, rota="/usuarios", contexto={"perfil_solicitado": payload.perfil}
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail=MSG_PERFIL_NAO_PERMITIDO_GESTOR
            )
        if unidade_id is None or not tem_acesso_a_unidade(db, usuario=usuario_atual, unidade_id=unidade_id):
            registrar_acesso_negado(
                db,
                usuario=usuario_atual,
                rota="/usuarios",
                contexto={"unidade_solicitada": str(unidade_id) if unidade_id else None},
            )
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=MSG_UNIDADE_NAO_GERENCIADA)

    if not payload.nome.strip():
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=MSG_NOME_OBRIGATORIO)

    if not _EMAIL_REGEX.match(payload.email):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=MSG_EMAIL_FORMATO_INVALIDO
        )

    if db.query(Usuario).filter(Usuario.email == payload.email).first() is not None:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=MSG_EMAIL_DUPLICADO)

    if unidade_id is not None:
        unidade = db.get(Unidade, unidade_id)
        if unidade is None or not unidade.ativo:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=MSG_UNIDADE_INVALIDA
            )

    perfil = PerfilUsuario(payload.perfil)
    setor_id = uuid.UUID(payload.setor_id) if payload.setor_id else None
    validar_vinculo_setor(db, perfil=perfil, unidade_id=unidade_id, setor_id=setor_id)

    novo = Usuario(
        nome=payload.nome.strip(),
        email=payload.email,
        senha_hash=hash_senha_inutilizavel(),
        perfil=perfil,
        status=StatusUsuario.PENDENTE_PRIMEIRO_ACESSO,
        unidade_id=unidade_id,
        setor_id=setor_id,
        telefone=payload.telefone,
        cargo=payload.cargo,
        chefia_direta=payload.chefia_direta,
    )
    db.add(novo)
    db.commit()

    gerado = gerar_token(db, usuario_id=novo.id, tipo=TipoTokenAutenticacao.PRIMEIRO_ACESSO)
    db.commit()

    link = f"{settings.frontend_base_url}/primeiro-acesso/{gerado.valor}"
    enqueue_email_seguro(
        EmailMessage(
            to=novo.email,
            subject="SETES.DOCS — bem-vindo(a)! Ative sua conta",
            body=(
                f"Olá {novo.nome}, você foi cadastrado(a) no SETES.DOCS. Ative sua conta pelo "
                f"link a seguir (válido por 48 horas): {link}"
            ),
        ),
        event_id=f"primeiro-acesso:{gerado.token_id}",
        config=config_from_settings(settings),
    )

    return UsuarioResponse.de(novo)


@router.patch("/usuarios/{usuario_id}/unidade", response_model=UsuarioResponse)
def transferir_unidade(
    usuario_id: uuid.UUID,
    payload: TransferirUnidadeRequest,
    _admin: Annotated[Usuario, Depends(require_perfil(PerfilUsuario.ADMINISTRADOR))],
    db: Annotated[Session, Depends(get_db)],
) -> UsuarioResponse:
    """US 8.6 — vínculo 1:1 Servidor↔unidade. O PATCH sempre *substitui* o
    vínculo (nunca adiciona), então o cenário de "vínculo duplo" (Cen.2) é
    estruturalmente impossível: não existe operação que preserve o vínculo
    anterior e crie um segundo — `unidade_id` é uma FK escalar.
    """
    alvo = db.get(Usuario, usuario_id)
    if alvo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado.")
    if alvo.perfil != PerfilUsuario.SERVIDOR:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=MSG_TRANSFERENCIA_APENAS_SERVIDOR
        )

    nova_unidade_id = uuid.UUID(payload.unidade_id)
    unidade = db.get(Unidade, nova_unidade_id)
    if unidade is None or not unidade.ativo:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=MSG_UNIDADE_INVALIDA)

    # A coerência setor↔unidade vale para toda escrita, inclusive aqui (D2):
    # omitir `setor_id` mantém o setor atual, que pertence à unidade antiga e
    # por isso é rejeitado — transferir exige escolher um setor da nova unidade.
    novo_setor_id = uuid.UUID(payload.setor_id) if payload.setor_id else alvo.setor_id
    validar_vinculo_setor(
        db, perfil=alvo.perfil, unidade_id=nova_unidade_id, setor_id=novo_setor_id
    )

    alvo.unidade_id = nova_unidade_id
    alvo.setor_id = novo_setor_id
    db.commit()

    return UsuarioResponse.de(alvo)


@router.get("/usuarios/{usuario_id}/unidades-geridas", response_model=list[str])
def obter_unidades_geridas(
    usuario_id: uuid.UUID,
    _admin: Annotated[Usuario, Depends(require_perfil(PerfilUsuario.ADMINISTRADOR))],
    db: Annotated[Session, Depends(get_db)],
) -> list[str]:
    vinculos = db.query(UnidadeGestor.unidade_id).filter(UnidadeGestor.gestor_id == usuario_id).all()
    return [str(v[0]) for v in vinculos]


@router.put("/usuarios/{usuario_id}/unidades-geridas", response_model=list[str])
def definir_unidades_geridas(
    usuario_id: uuid.UUID,
    payload: UnidadesGeridasRequest,
    _admin: Annotated[Usuario, Depends(require_perfil(PerfilUsuario.ADMINISTRADOR))],
    db: Annotated[Session, Depends(get_db)],
) -> list[str]:
    """US 8.6b — conjunto de unidades geridas por um Gestor (N:N)."""
    alvo = db.get(Usuario, usuario_id)
    if alvo is None or alvo.perfil != PerfilUsuario.GESTOR:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Unidades geridas só podem ser definidas para usuários com perfil Gestor.",
        )

    unidade_ids = {uuid.UUID(u) for u in payload.unidade_ids}
    encontradas = db.query(Unidade.id).filter(Unidade.id.in_(unidade_ids)).all()
    if len(encontradas) != len(unidade_ids):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=MSG_UNIDADE_INVALIDA)

    db.query(UnidadeGestor).filter(UnidadeGestor.gestor_id == alvo.id).delete()
    for unidade_id in unidade_ids:
        db.add(UnidadeGestor(gestor_id=alvo.id, unidade_id=unidade_id))
    db.commit()

    return [str(u) for u in unidade_ids]


@router.get("/usuarios", response_model=ListaUsuariosResponse)
def listar_usuarios(
    usuario_atual: Annotated[Usuario, Depends(require_perfil(PerfilUsuario.ADMINISTRADOR, PerfilUsuario.GESTOR))],
    db: Annotated[Session, Depends(get_db)],
    page: int = 1,
    page_size: int = 20,
    nome: str | None = None,
) -> ListaUsuariosResponse:
    """Administrador lista todos; Gestor só lista usuários das unidades que gerencia.

    `nome` filtra por fragmento, insensível a maiúsculas/minúsculas, no backend
    (D5) — o filtro restringe o conjunto exibido, nunca amplia o escopo de
    autorização já aplicado acima.
    """
    query = db.query(Usuario)
    if usuario_atual.perfil == PerfilUsuario.GESTOR:
        unidades_geridas = (
            db.query(UnidadeGestor.unidade_id).filter(UnidadeGestor.gestor_id == usuario_atual.id)
        )
        query = query.filter(Usuario.unidade_id.in_(unidades_geridas))

    if nome and nome.strip():
        query = query.filter(Usuario.nome.ilike(f"%{nome.strip()}%"))

    total = query.count()
    itens = query.order_by(Usuario.nome).offset((page - 1) * page_size).limit(page_size).all()

    return ListaUsuariosResponse(
        items=[UsuarioResponse.de(u) for u in itens], total=total, page=page, page_size=page_size
    )


@router.post("/usuarios/{usuario_id}/permissao-auditoria", response_model=UsuarioResponse)
def conceder_permissao_auditoria(
    usuario_id: uuid.UUID,
    admin: Annotated[Usuario, Depends(require_perfil(PerfilUsuario.ADMINISTRADOR))],
    db: Annotated[Session, Depends(get_db)],
) -> UsuarioResponse:
    """US 8.3 Cen.1 — concede, ortogonal ao `perfil`; idempotente (só loga em
    transição real, D3/D4)."""
    alvo = db.get(Usuario, usuario_id)
    if alvo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=MSG_USUARIO_NAO_ENCONTRADO)

    if not alvo.pode_auditar:
        alvo.pode_auditar = True
        db.add(
            LogSeguranca(
                usuario_id=alvo.id,
                tipo_evento=TipoEventoLog.PERMISSAO_AUDITORIA_CONCEDIDA,
                contexto={"administrador_id": str(admin.id)},
            )
        )
        db.commit()

    return UsuarioResponse.de(alvo)


@router.delete("/usuarios/{usuario_id}/permissao-auditoria", response_model=UsuarioResponse)
def revogar_permissao_auditoria(
    usuario_id: uuid.UUID,
    admin: Annotated[Usuario, Depends(require_perfil(PerfilUsuario.ADMINISTRADOR))],
    db: Annotated[Session, Depends(get_db)],
) -> UsuarioResponse:
    """US 8.3 Cen.2 — revoga sem "lembrar" perfil anterior; idempotente (D3/D4)."""
    alvo = db.get(Usuario, usuario_id)
    if alvo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=MSG_USUARIO_NAO_ENCONTRADO)

    if alvo.pode_auditar:
        alvo.pode_auditar = False
        db.add(
            LogSeguranca(
                usuario_id=alvo.id,
                tipo_evento=TipoEventoLog.PERMISSAO_AUDITORIA_REVOGADA,
                contexto={"administrador_id": str(admin.id)},
            )
        )
        db.commit()

    return UsuarioResponse.de(alvo)


@router.post("/usuarios/{usuario_id}/desativar", response_model=UsuarioResponse)
def desativar_usuario(
    usuario_id: uuid.UUID,
    admin: Annotated[Usuario, Depends(require_perfil(PerfilUsuario.ADMINISTRADOR))],
    db: Annotated[Session, Depends(get_db)],
) -> UsuarioResponse:
    """US 8.4 — desativa com a guarda de processos em andamento sob
    responsabilidade (D2); idempotente (D4)."""
    alvo = db.get(Usuario, usuario_id)
    if alvo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=MSG_USUARIO_NAO_ENCONTRADO)

    if alvo.status == StatusUsuario.INATIVO:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=MSG_USUARIO_JA_INATIVO
        )

    quantidade = processo_consulta.contar_processos_sob_responsabilidade(db, alvo)
    if quantidade > 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=_msg_processos_pendentes(quantidade),
        )

    alvo.status = StatusUsuario.INATIVO
    db.add(
        LogSeguranca(
            usuario_id=alvo.id,
            tipo_evento=TipoEventoLog.USUARIO_DESATIVADO,
            contexto={"administrador_id": str(admin.id)},
        )
    )
    db.commit()

    return UsuarioResponse.de(alvo)


@router.get("/usuarios/me/perfil", response_model=MeuPerfilResponse)
def meu_perfil(
    usuario_atual: Annotated[Usuario, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> MeuPerfilResponse:
    """US 1.5 — sempre os dados do próprio token (`get_current_user`); não há
    parâmetro de ID manipulável, então não existe rota que permita ver o
    perfil de terceiros (US 1.5 Cen.2 / task 10.2). A lista de processos atuados
    (Cen.1) acompanha o usuário mesmo após transferência (US 1.4 Cen.3)."""
    return _meu_perfil_response(db, usuario_atual)


@router.patch("/usuarios/me/perfil", response_model=MeuPerfilResponse)
def atualizar_meu_perfil(
    payload: AtualizarMeuPerfilRequest,
    usuario_atual: Annotated[Usuario, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> MeuPerfilResponse:
    """US 1.5 — auto-serviço do próprio nome (task 2.2) e dos dados funcionais
    (setor, telefone, cargo, chefia direta); e-mail, perfil e unidade permanecem
    sob gestão exclusiva do Administrador. O setor continua validado contra a
    unidade do próprio usuário (D2)."""
    informados = payload.model_fields_set  # PATCH parcial: o que não veio não é tocado
    if "setor_id" in informados:
        setor_id = uuid.UUID(payload.setor_id) if payload.setor_id else None
        validar_vinculo_setor(
            db,
            perfil=usuario_atual.perfil,
            unidade_id=usuario_atual.unidade_id,
            setor_id=setor_id,
        )
        usuario_atual.setor_id = setor_id

    usuario_atual.nome = payload.nome.strip()
    for campo in ("telefone", "cargo", "chefia_direta"):
        if campo in informados:
            setattr(usuario_atual, campo, getattr(payload, campo))
    db.commit()
    db.refresh(usuario_atual)

    return _meu_perfil_response(db, usuario_atual)


def _meu_perfil_response(db: Session, usuario: Usuario) -> MeuPerfilResponse:
    """US 1.5 — monta a resposta com os nomes de unidade/setor resolvidos: o
    catálogo de setores é restrito ao Administrador, então o próprio usuário
    não conseguiria traduzir os ids para exibição."""
    processos = processo_consulta.processos_atuados(db, usuario)
    return MeuPerfilResponse(
        usuario=UsuarioResponse.de(usuario),
        unidade_nome=usuario.unidade.nome if usuario.unidade else None,
        setor_nome=usuario.setor.nome if usuario.setor else None,
        processos=processos,
        mensagem_processos=(
            "Nenhum processo registrado" if not processos else ""
        ),
    )
