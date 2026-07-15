"""Teste do serviço de documentos (tasks 2.2 e 3.x — obrigatório: histórico de
tramitação imutável, dado pessoal em anexo). US 3.1 Cen.1/2/2b/3/4/4b/4c/5."""

from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone

import pytest
from fastapi import HTTPException

from app.db.models import Documento, Processo, StatusProcesso, TipoEventoTramitacao, Tramitacao
from app.services import documento as documento_service
from app.services.storage import FilesystemStorage
from tests.helpers_processo import auth, login, processo_concluido, tipo_com_roteiro, unidade, usuario

PDF = b"%PDF-1.4\n1 0 obj\n<< >>\nendobj\n%%EOF"
DOCX = b"PK\x03\x04" + b"\x00" * 20
EXE_DISFARCADO_DE_PDF = b"MZ\x90\x00\x03\x00\x00\x00" + b"\x00" * 20


def _storage(tmp_path):
    return FilesystemStorage(tmp_path)


def _criar_processo(client, token, tipo):
    resp = client.post(
        "/processos",
        json={"assunto": "Doc", "tipo_processo_id": str(tipo.id), "prazo_dias": 10},
        headers=auth(token),
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def _processo_aberto(client, db):
    cofin = unidade(db, "COFIN")
    tipo = tipo_com_roteiro(db, cofin, unidade(db, "AJUR"))
    criador = usuario(db, unidade_id=cofin.id, email=f"criador-{cofin.id}@ex.com")
    token = login(client, criador.email)
    proc = _criar_processo(client, token, tipo)
    return db.get(Processo, proc["id"]), criador, cofin, tipo


# --- anexar (3.1, 3.2, 3.3) -------------------------------------------------


def test_anexa_documento_com_sucesso(client, db, tmp_path):
    processo, criador, _cofin, _tipo = _processo_aberto(client, db)

    documento = documento_service.anexar(
        db,
        processo=processo,
        usuario=criador,
        storage=_storage(tmp_path),
        nome_arquivo="parecer.pdf",
        conteudo=PDF,
    )

    assert documento.nome_exibicao == "parecer.pdf"
    assert documento.nome_original == "parecer.pdf"
    assert documento.tipo_conteudo == "application/pdf"
    assert documento.tamanho_bytes == len(PDF)
    assert documento.hash_sha256 == hashlib.sha256(PDF).hexdigest()
    assert documento.anexado_por_id == criador.id
    assert documento.removido_em is None
    # Objeto gravado no storage sob chave própria (não o nome do arquivo).
    with (tmp_path / documento.objeto_chave).open("rb") as f:
        assert f.read() == PDF
    # Anexação não gera evento de tramitação (D6).
    assert db.query(Tramitacao).filter(Tramitacao.processo_id == processo.id).count() == 0


def test_rejeita_formato_nao_permitido_extensao(client, db, tmp_path):
    processo, criador, _cofin, _tipo = _processo_aberto(client, db)

    with pytest.raises(HTTPException) as exc:
        documento_service.anexar(
            db, processo=processo, usuario=criador, storage=_storage(tmp_path),
            nome_arquivo="virus.exe", conteudo=EXE_DISFARCADO_DE_PDF,
        )
    assert exc.value.status_code == 422
    assert exc.value.detail == documento_service.MSG_FORMATO_NAO_PERMITIDO
    assert db.query(Documento).filter(Documento.processo_id == processo.id).count() == 0


def test_rejeita_mime_falsificado_extensao_pdf_conteudo_exe(client, db, tmp_path):
    """US 3.1 Cen.2 + design.md (proteção contra MIME falsificado)."""
    processo, criador, _cofin, _tipo = _processo_aberto(client, db)

    with pytest.raises(HTTPException) as exc:
        documento_service.anexar(
            db, processo=processo, usuario=criador, storage=_storage(tmp_path),
            nome_arquivo="disfarcado.pdf", conteudo=EXE_DISFARCADO_DE_PDF,
        )
    assert exc.value.status_code == 422
    assert exc.value.detail == documento_service.MSG_FORMATO_NAO_PERMITIDO
    assert db.query(Documento).filter(Documento.processo_id == processo.id).count() == 0


def test_rejeita_tamanho_excedido(client, db, tmp_path):
    processo, criador, _cofin, _tipo = _processo_aberto(client, db)
    conteudo_grande = PDF + b"\x00" * documento_service.TAMANHO_MAXIMO_BYTES

    with pytest.raises(HTTPException) as exc:
        documento_service.anexar(
            db, processo=processo, usuario=criador, storage=_storage(tmp_path),
            nome_arquivo="grande.pdf", conteudo=conteudo_grande,
        )
    assert exc.value.status_code == 422
    assert exc.value.detail == documento_service.MSG_TAMANHO_EXCEDIDO
    assert db.query(Documento).filter(Documento.processo_id == processo.id).count() == 0


def test_rejeita_arquivo_vazio(client, db, tmp_path):
    processo, criador, _cofin, _tipo = _processo_aberto(client, db)

    with pytest.raises(HTTPException) as exc:
        documento_service.anexar(
            db, processo=processo, usuario=criador, storage=_storage(tmp_path),
            nome_arquivo="vazio.pdf", conteudo=b"",
        )
    assert exc.value.status_code == 422
    assert exc.value.detail == documento_service.MSG_ARQUIVO_VAZIO
    assert db.query(Documento).filter(Documento.processo_id == processo.id).count() == 0


def test_nome_duplicado_e_renomeado_nao_sobrescreve(client, db, tmp_path):
    processo, criador, _cofin, _tipo = _processo_aberto(client, db)
    storage = _storage(tmp_path)

    d1 = documento_service.anexar(
        db, processo=processo, usuario=criador, storage=storage,
        nome_arquivo="parecer.pdf", conteudo=PDF,
    )
    d2 = documento_service.anexar(
        db, processo=processo, usuario=criador, storage=storage,
        nome_arquivo="parecer.pdf", conteudo=PDF,
    )
    d3 = documento_service.anexar(
        db, processo=processo, usuario=criador, storage=storage,
        nome_arquivo="parecer.pdf", conteudo=PDF,
    )

    assert d1.nome_exibicao == "parecer.pdf"
    assert d2.nome_exibicao == "parecer (1).pdf"
    assert d3.nome_exibicao == "parecer (2).pdf"
    assert len({d1.objeto_chave, d2.objeto_chave, d3.objeto_chave}) == 3
    visiveis = documento_service.listar(db, processo_id=processo.id)
    assert {d.nome_exibicao for d in visiveis} == {
        "parecer.pdf", "parecer (1).pdf", "parecer (2).pdf",
    }


# --- listar (3.4) ------------------------------------------------------------


def test_listar_retorna_so_visiveis(client, db, tmp_path):
    processo, criador, _cofin, _tipo = _processo_aberto(client, db)
    storage = _storage(tmp_path)
    visivel = documento_service.anexar(
        db, processo=processo, usuario=criador, storage=storage,
        nome_arquivo="a.pdf", conteudo=PDF,
    )
    removido = documento_service.anexar(
        db, processo=processo, usuario=criador, storage=storage,
        nome_arquivo="b.docx", conteudo=DOCX,
    )
    documento_service.remover(db, processo=processo, documento=removido, usuario=criador)

    visiveis = documento_service.listar(db, processo_id=processo.id)

    assert [d.id for d in visiveis] == [visivel.id]


# --- pode_remover / custódia (3.5, D1) ---------------------------------------


def test_pode_remover_processo_aberto(client, db):
    processo, _criador, _cofin, _tipo = _processo_aberto(client, db)
    assert documento_service.pode_remover(db, processo=processo) is True


def test_pode_remover_bloqueia_apos_despacho(client, db):
    processo, criador, cofin, tipo = _processo_aberto(client, db)
    token = login(client, criador.email)
    client.post(f"/processos/{processo.id}/despachar", json={}, headers=auth(token))
    db.refresh(processo)

    assert processo.status == StatusProcesso.EM_TRAMITACAO
    assert documento_service.pode_remover(db, processo=processo) is False


def test_pode_remover_permite_apos_devolucao(client, db):
    processo, criador, cofin, tipo = _processo_aberto(client, db)
    token = login(client, criador.email)
    client.post(f"/processos/{processo.id}/despachar", json={}, headers=auth(token))
    db.refresh(processo)
    ajur_id = processo.unidade_atual_id
    servidor_ajur = usuario(db, unidade_id=ajur_id, email=f"ajur-{processo.id}@ex.com")
    token_ajur = login(client, servidor_ajur.email)
    client.post(
        f"/processos/{processo.id}/devolver",
        json={"motivo": "correcao_dados"},
        headers=auth(token_ajur),
    )
    db.refresh(processo)

    assert processo.status == StatusProcesso.EM_TRAMITACAO
    assert documento_service.pode_remover(db, processo=processo) is True


def test_pode_remover_bloqueia_apos_redespacho_pos_devolucao(client, db):
    processo, criador, cofin, tipo = _processo_aberto(client, db)
    token = login(client, criador.email)
    client.post(f"/processos/{processo.id}/despachar", json={}, headers=auth(token))
    db.refresh(processo)
    servidor_ajur = usuario(db, unidade_id=processo.unidade_atual_id, email=f"ajur2-{processo.id}@ex.com")
    token_ajur = login(client, servidor_ajur.email)
    client.post(
        f"/processos/{processo.id}/devolver",
        json={"motivo": "correcao_dados"},
        headers=auth(token_ajur),
    )
    db.refresh(processo)
    client.post(f"/processos/{processo.id}/despachar", json={}, headers=auth(token))
    db.refresh(processo)

    assert processo.status == StatusProcesso.EM_TRAMITACAO
    assert documento_service.pode_remover(db, processo=processo) is False


def test_pode_remover_bloqueia_processo_concluido(client, db):
    cofin = unidade(db, "COFIN")
    tipo = tipo_com_roteiro(db, cofin)
    criador = usuario(db, unidade_id=cofin.id, email=f"concl-{cofin.id}@ex.com")

    processo = processo_concluido(
        db, unidade=cofin, criador=criador, tipo=tipo,
        concluido_em=datetime.now(timezone.utc),
        arquivar_em=datetime.now(timezone.utc) + timedelta(days=30),
        status=StatusProcesso.CONCLUIDO,
    )
    assert documento_service.pode_remover(db, processo=processo) is False


def test_pode_remover_bloqueia_processo_arquivado(client, db):
    cofin = unidade(db, "COFIN")
    tipo = tipo_com_roteiro(db, cofin)
    criador = usuario(db, unidade_id=cofin.id, email=f"arq-{cofin.id}@ex.com")

    processo = processo_concluido(
        db, unidade=cofin, criador=criador, tipo=tipo,
        concluido_em=datetime.now(timezone.utc) - timedelta(days=60),
        arquivar_em=datetime.now(timezone.utc) - timedelta(days=1),
        status=StatusProcesso.ARQUIVADO,
    )
    assert documento_service.pode_remover(db, processo=processo) is False


# --- remover / soft-delete + evento imutável (3.6) ---------------------------


def test_remover_soft_deleta_e_gera_evento_imutavel(client, db, tmp_path):
    processo, criador, _cofin, _tipo = _processo_aberto(client, db)
    storage = _storage(tmp_path)
    documento = documento_service.anexar(
        db, processo=processo, usuario=criador, storage=storage,
        nome_arquivo="a.pdf", conteudo=PDF,
    )

    resultado = documento_service.remover(db, processo=processo, documento=documento, usuario=criador)

    assert resultado.removido_em is not None
    assert resultado.removido_por_id == criador.id
    assert resultado.purgar_em == resultado.removido_em + timedelta(days=30)
    assert documento_service.listar(db, processo_id=processo.id) == []

    eventos = db.query(Tramitacao).filter(Tramitacao.processo_id == processo.id).all()
    remocoes = [e for e in eventos if e.tipo_evento == TipoEventoTramitacao.REMOVER_DOCUMENTO]
    assert len(remocoes) == 1
    evento = remocoes[0]
    assert evento.responsavel_id == criador.id
    assert evento.unidade_origem_id is None
    assert evento.unidade_destino_id is None
    assert evento.status_resultante == processo.status


def test_remover_bloqueado_apos_despacho(client, db, tmp_path):
    processo, criador, _cofin, _tipo = _processo_aberto(client, db)
    storage = _storage(tmp_path)
    documento = documento_service.anexar(
        db, processo=processo, usuario=criador, storage=storage,
        nome_arquivo="a.pdf", conteudo=PDF,
    )
    token = login(client, criador.email)
    client.post(f"/processos/{processo.id}/despachar", json={}, headers=auth(token))
    db.refresh(processo)

    with pytest.raises(HTTPException) as exc:
        documento_service.remover(db, processo=processo, documento=documento, usuario=criador)
    assert exc.value.status_code == 409
    assert exc.value.detail == documento_service.MSG_REMOCAO_BLOQUEADA
    assert documento_service.listar(db, processo_id=processo.id) == [documento]


# --- purga física (6.1, 6.2, D7) ---------------------------------------------


def test_purga_remove_so_vencidos(client, db, tmp_path):
    processo, criador, _cofin, _tipo = _processo_aberto(client, db)
    storage = _storage(tmp_path)
    agora = datetime.now(timezone.utc)

    vencido = documento_service.anexar(
        db, processo=processo, usuario=criador, storage=storage,
        nome_arquivo="vencido.pdf", conteudo=PDF,
    )
    dentro_prazo = documento_service.anexar(
        db, processo=processo, usuario=criador, storage=storage,
        nome_arquivo="recente.pdf", conteudo=PDF,
    )
    vencido.removido_em = agora - timedelta(days=31)
    vencido.purgar_em = agora - timedelta(days=1)
    vencido.removido_por_id = criador.id
    dentro_prazo.removido_em = agora - timedelta(days=1)
    dentro_prazo.purgar_em = agora + timedelta(days=29)
    dentro_prazo.removido_por_id = criador.id
    db.commit()

    total = documento_service.purgar_documentos_vencidos(db, agora=agora, storage=storage)

    assert total == 1
    assert db.get(Documento, vencido.id) is None
    assert db.get(Documento, dentro_prazo.id) is not None
    assert not (tmp_path / vencido.objeto_chave).exists()
    assert (tmp_path / dentro_prazo.objeto_chave).exists()


def test_purga_e_idempotente_e_reexecucao_e_no_op(client, db, tmp_path):
    processo, criador, _cofin, _tipo = _processo_aberto(client, db)
    storage = _storage(tmp_path)
    agora = datetime.now(timezone.utc)

    vencido = documento_service.anexar(
        db, processo=processo, usuario=criador, storage=storage,
        nome_arquivo="vencido.pdf", conteudo=PDF,
    )
    vencido.removido_em = agora - timedelta(days=40)
    vencido.purgar_em = agora - timedelta(days=10)
    vencido.removido_por_id = criador.id
    db.commit()

    primeira = documento_service.purgar_documentos_vencidos(db, agora=agora, storage=storage)
    segunda = documento_service.purgar_documentos_vencidos(db, agora=agora, storage=storage)

    assert primeira == 1
    assert segunda == 0  # reexecução não encontra o que já foi purgado
