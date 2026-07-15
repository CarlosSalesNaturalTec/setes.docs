"""Congelamento de `arquivar_em` na conclusão — não-retroatividade (task 2.2,
US 2.5 Cen.2)."""

from __future__ import annotations

from datetime import timedelta

from app.db.models import Processo, SistemaConfig
from tests.helpers_processo import auth, login, tipo_com_roteiro, unidade, usuario


def _criar_e_concluir(client, db, tipo, unidade_criacao):
    serv = usuario(db, unidade_id=unidade_criacao.id, email=f"criador-{unidade_criacao.sigla}@ex.com")
    token = login(client, serv.email)
    resp = client.post(
        "/processos",
        json={"assunto": "Fluxo", "tipo_processo_id": str(tipo.id), "prazo_dias": 10},
        headers=auth(token),
    )
    assert resp.status_code == 201, resp.text
    proc_id = resp.json()["id"]

    resp_conclui = client.post(
        f"/processos/{proc_id}/despachar", json={"confirmar": True}, headers=auth(token)
    )
    assert resp_conclui.status_code == 200, resp_conclui.text
    return proc_id


def test_arquivar_em_congelado_com_prazo_vigente_na_conclusao(client, db):
    cofin = unidade(db, "COFIN")
    tipo = tipo_com_roteiro(db, cofin)  # roteiro de unidade única
    proc_id = _criar_e_concluir(client, db, tipo, cofin)

    processo = db.get(Processo, proc_id)
    assert processo.arquivar_em is not None
    assert processo.concluido_em is not None
    assert processo.arquivar_em == processo.concluido_em + timedelta(days=30)  # default


def test_alteracao_do_prazo_global_nao_afeta_processo_ja_concluido(client, db):
    cofin = unidade(db, "COFIN")
    tipo = tipo_com_roteiro(db, cofin)
    proc_id = _criar_e_concluir(client, db, tipo, cofin)

    processo = db.get(Processo, proc_id)
    arquivar_em_original = processo.arquivar_em
    assert arquivar_em_original == processo.concluido_em + timedelta(days=30)

    # Administrador altera o prazo global de 30 para 15 dias.
    config = db.get(SistemaConfig, 1)
    config.prazo_arquivamento_dias = 15
    db.commit()

    # O processo já concluído mantém o prazo de 30 dias vigente na sua conclusão.
    db.refresh(processo)
    assert processo.arquivar_em == arquivar_em_original

    # Uma conclusão nova, após a alteração, já usa o novo prazo (15 dias).
    ajur = unidade(db, "AJUR")
    tipo2 = tipo_com_roteiro(db, ajur)
    proc_id_2 = _criar_e_concluir(client, db, tipo2, ajur)
    processo2 = db.get(Processo, proc_id_2)
    assert processo2.arquivar_em == processo2.concluido_em + timedelta(days=15)
