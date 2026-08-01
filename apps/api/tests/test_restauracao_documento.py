"""Testes obrigatórios do change `restauracao-documento` (US 8.7) — histórico de
tramitação imutável e dado pessoal em anexo: evento imutável `restaurar_documento`,
acesso negado a não-Administrador, re-resolução de nome na restauração e
restauração independente do status do processo (D1)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from fastapi import HTTPException

from app.db.models import (
    PerfilUsuario,
    Processo,
    StatusProcesso,
    TipoEventoTramitacao,
    Tramitacao,
)
from app.services import documento as documento_service
from app.services.storage import FilesystemStorage
from tests.helpers_processo import (
    auth,
    login,
    processo_concluido,
    servidor_com_setor,
    tipo_processo,
    unidade,
    usuario,
)

PDF = b"%PDF-1.4\n1 0 obj\n<< >>\nendobj\n%%EOF"


def _storage(tmp_path):
    return FilesystemStorage(tmp_path)


def _processo_aberto(client, db):
    cofin = unidade(db, "COFIN")
    tipo = tipo_processo(db)
    criador, _setor_criador = servidor_com_setor(db, cofin, email=f"criador-{cofin.id}@ex.com")
    token = login(client, criador.email)
    resp = client.post(
        "/processos",
        json={"assunto": "Doc", "tipo_processo_id": str(tipo.id), "prazo_dias": 10},
        headers=auth(token),
    )
    assert resp.status_code == 201, resp.text
    return db.get(Processo, resp.json()["id"]), criador, cofin, tipo


def _admin(db, sufixo="") -> object:
    return usuario(db, perfil=PerfilUsuario.ADMINISTRADOR, email=f"admin{sufixo}@ex.com")


def _anexar_e_remover(db, *, processo, criador, storage, nome="a.pdf"):
    documento = documento_service.anexar(
        db, processo=processo, usuario=criador, storage=storage, nome_arquivo=nome, conteudo=PDF
    )
    return documento_service.remover(db, processo=processo, documento=documento, usuario=criador)


# --- 2.1 — listar_removidos_em_retencao -------------------------------------


def test_listar_removidos_retorna_so_em_retencao(client, db, tmp_path):
    processo, criador, _cofin, _tipo = _processo_aberto(client, db)
    storage = _storage(tmp_path)
    agora = datetime.now(timezone.utc)

    em_retencao = _anexar_e_remover(db, processo=processo, criador=criador, storage=storage, nome="retido.pdf")
    purgavel = _anexar_e_remover(db, processo=processo, criador=criador, storage=storage, nome="purgavel.pdf")
    visivel = documento_service.anexar(
        db, processo=processo, usuario=criador, storage=storage, nome_arquivo="visivel.pdf", conteudo=PDF
    )
    # purgavel já venceu (purgar_em <= agora); ainda existe a linha mas não deve listar.
    purgavel.purgar_em = agora - timedelta(days=1)
    db.commit()

    removidos = documento_service.listar_removidos_em_retencao(db, agora=agora)

    assert [d.id for d in removidos] == [em_retencao.id]
    ids = {d.id for d in removidos}
    assert purgavel.id not in ids
    assert visivel.id not in ids


# --- 4.1 — evento imutável restaurar_documento ------------------------------


def test_restaurar_gera_evento_imutavel_e_volta_visivel(client, db, tmp_path):
    processo, criador, _cofin, _tipo = _processo_aberto(client, db)
    storage = _storage(tmp_path)
    admin = _admin(db, "-imut")
    documento = _anexar_e_remover(db, processo=processo, criador=criador, storage=storage)
    assert documento_service.listar(db, processo_id=processo.id) == []

    restaurado = documento_service.restaurar(db, documento=documento, admin=admin)

    assert restaurado.removido_em is None
    assert restaurado.removido_por_id is None
    assert restaurado.purgar_em is None
    visiveis = documento_service.listar(db, processo_id=processo.id)
    assert [d.id for d in visiveis] == [documento.id]

    eventos = db.query(Tramitacao).filter(Tramitacao.processo_id == processo.id).all()
    restauracoes = [e for e in eventos if e.tipo_evento == TipoEventoTramitacao.RESTAURAR_DOCUMENTO]
    assert len(restauracoes) == 1
    evento = restauracoes[0]
    assert evento.responsavel_id == admin.id
    assert evento.unidade_origem_id is None
    assert evento.unidade_destino_id is None
    assert evento.status_resultante == processo.status


def test_restaurar_documento_purgado_retorna_404(client, db, tmp_path):
    processo, criador, _cofin, _tipo = _processo_aberto(client, db)
    storage = _storage(tmp_path)
    admin = _admin(db, "-purg")
    documento = _anexar_e_remover(db, processo=processo, criador=criador, storage=storage)
    # simula purga: purgar_em já venceu → não restaurável (D2)
    documento.purgar_em = datetime.now(timezone.utc) - timedelta(days=1)
    db.commit()

    with pytest.raises(HTTPException) as exc:
        documento_service.restaurar(db, documento=documento, admin=admin)
    assert exc.value.status_code == 404


# --- 4.3 — re-resolução de nome na restauração ------------------------------


def test_restaurar_re_resolve_nome_em_colisao(client, db, tmp_path):
    processo, criador, _cofin, _tipo = _processo_aberto(client, db)
    storage = _storage(tmp_path)
    admin = _admin(db, "-nome")

    removido = _anexar_e_remover(db, processo=processo, criador=criador, storage=storage, nome="parecer.pdf")
    # durante a ausência, outro "parecer.pdf" visível passou a existir
    visivel = documento_service.anexar(
        db, processo=processo, usuario=criador, storage=storage, nome_arquivo="parecer.pdf", conteudo=PDF
    )
    assert visivel.nome_exibicao == "parecer.pdf"

    restaurado = documento_service.restaurar(db, documento=removido, admin=admin)

    assert restaurado.nome_exibicao == "parecer (1).pdf"
    visiveis = documento_service.listar(db, processo_id=processo.id)
    nomes = {d.nome_exibicao for d in visiveis}
    assert nomes == {"parecer.pdf", "parecer (1).pdf"}
    assert len(visiveis) == 2


# --- 4.4 — restauração independente do status (D1) --------------------------


def test_restaurar_em_processo_arquivado_nao_altera_status(client, db, tmp_path):
    cofin = unidade(db, "COFIN")
    tipo = tipo_processo(db)
    criador, _setor_criador = servidor_com_setor(db, cofin, email=f"arq-{cofin.id}@ex.com")
    admin = _admin(db, "-arq")
    storage = _storage(tmp_path)

    processo = processo_concluido(
        db,
        unidade=cofin,
        criador=criador,
        tipo=tipo,
        concluido_em=datetime.now(timezone.utc) - timedelta(days=60),
        arquivar_em=datetime.now(timezone.utc) - timedelta(days=1),
        status=StatusProcesso.ARQUIVADO,
    )
    # anexa e remove diretamente (remover valida custódia; aqui manipulamos o estado)
    documento = documento_service.anexar(
        db, processo=processo, usuario=criador, storage=storage, nome_arquivo="a.pdf", conteudo=PDF
    )
    agora = datetime.now(timezone.utc)
    documento.removido_em = agora
    documento.removido_por_id = criador.id
    documento.purgar_em = agora + timedelta(days=30)
    db.commit()

    restaurado = documento_service.restaurar(db, documento=documento, admin=admin)

    db.refresh(processo)
    assert processo.status == StatusProcesso.ARQUIVADO
    assert restaurado.removido_em is None
    assert [d.id for d in documento_service.listar(db, processo_id=processo.id)] == [documento.id]
    evento = (
        db.query(Tramitacao)
        .filter(Tramitacao.processo_id == processo.id)
        .filter(Tramitacao.tipo_evento == TipoEventoTramitacao.RESTAURAR_DOCUMENTO)
        .one()
    )
    assert evento.status_resultante == StatusProcesso.ARQUIVADO


# --- 3.1 / 3.2 / 4.2 — endpoints e acesso negado ----------------------------


def test_endpoint_lista_e_restaura_admin(client, db, tmp_path):
    processo, criador, _cofin, _tipo = _processo_aberto(client, db)
    storage = _storage(tmp_path)
    admin = _admin(db, "-ep")
    documento = _anexar_e_remover(db, processo=processo, criador=criador, storage=storage, nome="ep.pdf")
    token_admin = login(client, admin.email)

    # lista
    resp = client.get("/admin/documentos-removidos", headers=auth(token_admin))
    assert resp.status_code == 200, resp.text
    itens = resp.json()["items"]
    assert len(itens) == 1
    item = itens[0]
    assert item["id"] == str(documento.id)
    assert item["nome_exibicao"] == "ep.pdf"
    assert item["processo_numero"] == processo.numero
    assert item["processo_assunto"] == processo.assunto
    assert item["removido_por_id"] == str(criador.id)

    # restaura
    resp = client.post(
        f"/admin/documentos-removidos/{documento.id}/restaurar", headers=auth(token_admin)
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["id"] == str(documento.id)

    # some da lista de removidos
    resp = client.get("/admin/documentos-removidos", headers=auth(token_admin))
    assert resp.json()["items"] == []


def test_endpoint_restaurar_purgado_ou_inexistente_404(client, db, tmp_path):
    _processo, _criador, _cofin, _tipo = _processo_aberto(client, db)
    admin = _admin(db, "-404")
    token_admin = login(client, admin.email)
    import uuid as _uuid

    resp = client.post(
        f"/admin/documentos-removidos/{_uuid.uuid4()}/restaurar", headers=auth(token_admin)
    )
    assert resp.status_code == 404


# Auditor ainda não existe no enum PerfilUsuario (persona futura do PRD); os
# perfis não-Admin implementados hoje são Servidor e Gestor. Qualquer não-Admin
# é barrado por `require_perfil(ADMINISTRADOR)`.
@pytest.mark.parametrize("perfil", [PerfilUsuario.SERVIDOR, PerfilUsuario.GESTOR])
def test_acesso_negado_nao_admin_lista_e_restaura(client, db, tmp_path, perfil):
    processo, criador, cofin, _tipo = _processo_aberto(client, db)
    storage = _storage(tmp_path)
    documento = _anexar_e_remover(db, processo=processo, criador=criador, storage=storage, nome="neg.pdf")
    nao_admin = usuario(db, perfil=perfil, unidade_id=cofin.id, email=f"naoadmin-{perfil.value}@ex.com")
    token = login(client, nao_admin.email)

    resp_lista = client.get("/admin/documentos-removidos", headers=auth(token))
    assert resp_lista.status_code == 403

    resp_rest = client.post(
        f"/admin/documentos-removidos/{documento.id}/restaurar", headers=auth(token)
    )
    assert resp_rest.status_code == 403
