"""Testes de tramitação manual — Envio, Devolução, Reatribuição e Conclusão
(task 5.4 — obrigatório: histórico de tramitação). US 2.2, 2.2b, US 1.4 Cen.2,
change tramitacao-manual (design.md D1-D9)."""

from __future__ import annotations

from app.db.models import (
    LogSeguranca,
    PerfilUsuario,
    Processo,
    StatusProcesso,
    TipoEventoLog,
    TipoEventoTramitacao,
    Tramitacao,
)
from tests.helpers_processo import (
    auth,
    gestor_de,
    login,
    servidor_com_setor,
    setor,
    tipo_processo,
    unidade,
    usuario,
)


def _criar_processo(client, servidor, token, tipo):
    resp = client.post(
        "/processos",
        json={"assunto": "Fluxo", "tipo_processo_id": str(tipo.id), "prazo_dias": 10},
        headers=auth(token),
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def _enviar(client, proc_id, token, *, unidade_id, setor_id, servidor_id, mensagem="Segue"):
    return client.post(
        f"/processos/{proc_id}/enviar",
        json={
            "unidade_destino_id": str(unidade_id),
            "setor_destino_id": str(setor_id),
            "servidor_destino_id": str(servidor_id),
            "mensagem": mensagem,
        },
        headers=auth(token),
    )


# --- Envio -------------------------------------------------------------


def test_envio_com_destino_valido(client, db):
    cofin, ajur = unidade(db, "COFIN"), unidade(db, "AJUR")
    tipo = tipo_processo(db)
    serv_a, _setor_a = servidor_com_setor(db, cofin, nome_setor="Protocolo")
    setor_analise = setor(db, ajur, "Análise")
    serv_b = usuario(db, unidade_id=ajur.id, setor_id=setor_analise.id, email="maria@ex.com")
    token_a = login(client, serv_a.email)

    proc = _criar_processo(client, serv_a, token_a, tipo)
    resp = _enviar(
        client,
        proc["id"],
        token_a,
        unidade_id=ajur.id,
        setor_id=setor_analise.id,
        servidor_id=serv_b.id,
        mensagem="Segue para parecer jurídico",
    )

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["status"] == "em_tramitacao"
    assert body["unidade_atual_id"] == str(ajur.id)
    assert body["setor_atual_id"] == str(setor_analise.id)
    assert body["servidor_atual_id"] == str(serv_b.id)

    evento = db.query(Tramitacao).filter(Tramitacao.processo_id == proc["id"]).one()
    assert evento.tipo_evento == TipoEventoTramitacao.ENVIO
    assert evento.unidade_origem_id == cofin.id
    assert evento.unidade_destino_id == ajur.id
    assert evento.servidor_destino_id == serv_b.id
    assert evento.mensagem == "Segue para parecer jurídico"


def test_envio_para_si_mesmo_e_rejeitado(client, db):
    cofin = unidade(db, "COFIN")
    tipo = tipo_processo(db)
    serv_a, setor_a = servidor_com_setor(db, cofin)
    token_a = login(client, serv_a.email)
    proc = _criar_processo(client, serv_a, token_a, tipo)

    resp = _enviar(
        client, proc["id"], token_a, unidade_id=cofin.id, setor_id=setor_a.id, servidor_id=serv_a.id
    )
    assert resp.status_code == 422
    assert "diferente do responsável atual" in resp.json()["detail"]


def test_envio_setor_fora_da_unidade_e_rejeitado(client, db):
    cofin, ajur = unidade(db, "COFIN"), unidade(db, "AJUR")
    tipo = tipo_processo(db)
    serv_a, _ = servidor_com_setor(db, cofin)
    setor_cofin_2 = setor(db, cofin, "Financeiro")
    token_a = login(client, serv_a.email)
    proc = _criar_processo(client, serv_a, token_a, tipo)

    outro_servidor = usuario(db, unidade_id=cofin.id, setor_id=setor_cofin_2.id, email="x@ex.com")
    resp = _enviar(
        client,
        proc["id"],
        token_a,
        unidade_id=ajur.id,  # unidade destino = AJUR
        setor_id=setor_cofin_2.id,  # mas setor é da COFIN
        servidor_id=outro_servidor.id,
    )
    assert resp.status_code == 422


def test_envio_servidor_inativo_nao_e_destino_valido(client, db):
    cofin, ajur = unidade(db, "COFIN"), unidade(db, "AJUR")
    tipo = tipo_processo(db)
    serv_a, _ = servidor_com_setor(db, cofin)
    setor_ajur = setor(db, ajur, "Análise")
    inativo = usuario(db, unidade_id=ajur.id, setor_id=setor_ajur.id, email="inativo@ex.com")
    from app.db.models import StatusUsuario

    inativo.status = StatusUsuario.INATIVO
    db.commit()
    token_a = login(client, serv_a.email)
    proc = _criar_processo(client, serv_a, token_a, tipo)

    resp = _enviar(
        client, proc["id"], token_a, unidade_id=ajur.id, setor_id=setor_ajur.id, servidor_id=inativo.id
    )
    assert resp.status_code == 422


def test_envio_por_quem_nao_e_responsavel_atual_acesso_negado(client, db):
    cofin, ajur = unidade(db, "COFIN"), unidade(db, "AJUR")
    tipo = tipo_processo(db)
    serv_a, _ = servidor_com_setor(db, cofin)
    serv_d, _ = servidor_com_setor(db, cofin, nome_setor="Financeiro", email="d@ex.com")
    setor_ajur = setor(db, ajur, "Análise")
    serv_b = usuario(db, unidade_id=ajur.id, setor_id=setor_ajur.id, email="b@ex.com")
    token_a = login(client, serv_a.email)
    proc = _criar_processo(client, serv_a, token_a, tipo)

    token_d = login(client, serv_d.email)
    resp = _enviar(
        client, proc["id"], token_d, unidade_id=ajur.id, setor_id=setor_ajur.id, servidor_id=serv_b.id
    )
    assert resp.status_code == 403
    logs = db.query(LogSeguranca).filter(LogSeguranca.tipo_evento == TipoEventoLog.ACESSO_NEGADO).all()
    assert len(logs) >= 1


# --- Devolução -----------------------------------------------------------


def test_devolucao_retorna_ao_remetente_correto(client, db):
    cofin, ajur = unidade(db, "COFIN"), unidade(db, "AJUR")
    tipo = tipo_processo(db)
    serv_a, setor_a = servidor_com_setor(db, cofin)
    setor_ajur = setor(db, ajur, "Análise")
    serv_b = usuario(db, unidade_id=ajur.id, setor_id=setor_ajur.id, email="b@ex.com")
    token_a = login(client, serv_a.email)
    proc = _criar_processo(client, serv_a, token_a, tipo)
    _enviar(client, proc["id"], token_a, unidade_id=ajur.id, setor_id=setor_ajur.id, servidor_id=serv_b.id)

    token_b = login(client, serv_b.email)
    resp = client.post(
        f"/processos/{proc['id']}/devolver",
        json={"motivo": "documentacao_insuficiente", "justificativa": "Faltam anexos"},
        headers=auth(token_b),
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["unidade_atual_id"] == str(cofin.id)
    assert body["setor_atual_id"] == str(setor_a.id)
    assert body["servidor_atual_id"] == str(serv_a.id)
    assert body["status"] == "em_tramitacao"

    evento = (
        db.query(Tramitacao).filter(Tramitacao.tipo_evento == TipoEventoTramitacao.DEVOLUCAO).one()
    )
    assert evento.unidade_destino_id == cofin.id
    assert evento.servidor_destino_id == serv_a.id
    assert evento.justificativa == "Faltam anexos"


def test_devolucao_sem_remetente_anterior_e_bloqueada(client, db):
    cofin = unidade(db, "COFIN")
    tipo = tipo_processo(db)
    serv_a, _ = servidor_com_setor(db, cofin)
    token_a = login(client, serv_a.email)
    proc = _criar_processo(client, serv_a, token_a, tipo)

    resp = client.post(
        f"/processos/{proc['id']}/devolver",
        json={"motivo": "correcao_dados"},
        headers=auth(token_a),
    )
    assert resp.status_code == 409
    assert "remetente anterior" in resp.json()["detail"]


def test_devolucao_sem_motivo_e_rejeitada(client, db):
    cofin, ajur = unidade(db, "COFIN"), unidade(db, "AJUR")
    tipo = tipo_processo(db)
    serv_a, _ = servidor_com_setor(db, cofin)
    setor_ajur = setor(db, ajur, "Análise")
    serv_b = usuario(db, unidade_id=ajur.id, setor_id=setor_ajur.id, email="b@ex.com")
    token_a = login(client, serv_a.email)
    proc = _criar_processo(client, serv_a, token_a, tipo)
    _enviar(client, proc["id"], token_a, unidade_id=ajur.id, setor_id=setor_ajur.id, servidor_id=serv_b.id)

    token_b = login(client, serv_b.email)
    resp = client.post(f"/processos/{proc['id']}/devolver", json={}, headers=auth(token_b))
    assert resp.status_code == 422
    assert "Selecione um motivo para a devolução" in resp.text


# --- Reatribuição --------------------------------------------------------


def test_reatribuicao_preserva_status_e_prazo(client, db):
    cofin = unidade(db, "COFIN")
    tipo = tipo_processo(db)
    serv_a, setor_a = servidor_com_setor(db, cofin)
    setor_protocolo = setor(db, cofin, "Financas")
    serv_c = usuario(db, unidade_id=cofin.id, setor_id=setor_protocolo.id, email="joao@ex.com")
    token_a = login(client, serv_a.email)
    proc = _criar_processo(client, serv_a, token_a, tipo)
    prazo_em_antes = proc["prazo_em"]

    resp = client.post(
        f"/processos/{proc['id']}/reatribuir",
        json={
            "setor_destino_id": str(setor_protocolo.id),
            "servidor_destino_id": str(serv_c.id),
            "justificativa": "Atribuído por engano",
        },
        headers=auth(token_a),
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["status"] == "aberto"  # status inalterado (D4)
    assert body["prazo_em"] == prazo_em_antes  # prazo inalterado (D9)
    assert body["setor_atual_id"] == str(setor_protocolo.id)
    assert body["servidor_atual_id"] == str(serv_c.id)
    assert body["unidade_atual_id"] == str(cofin.id)

    evento = (
        db.query(Tramitacao).filter(Tramitacao.tipo_evento == TipoEventoTramitacao.REATRIBUICAO).one()
    )
    assert evento.status_resultante == StatusProcesso.ABERTO
    assert evento.servidor_origem_id == serv_a.id
    assert evento.servidor_destino_id == serv_c.id


def test_reatribuicao_para_outra_unidade_e_rejeitada(client, db):
    cofin, ajur = unidade(db, "COFIN"), unidade(db, "AJUR")
    tipo = tipo_processo(db)
    serv_a, _ = servidor_com_setor(db, cofin)
    setor_ajur = setor(db, ajur, "Análise")
    serv_b = usuario(db, unidade_id=ajur.id, setor_id=setor_ajur.id, email="b@ex.com")
    token_a = login(client, serv_a.email)
    proc = _criar_processo(client, serv_a, token_a, tipo)

    resp = client.post(
        f"/processos/{proc['id']}/reatribuir",
        json={
            "setor_destino_id": str(setor_ajur.id),
            "servidor_destino_id": str(serv_b.id),
            "justificativa": "Errado",
        },
        headers=auth(token_a),
    )
    assert resp.status_code == 422
    assert "não muda de unidade" in resp.json()["detail"]


def test_reatribuicao_para_mesmo_servidor_e_rejeitada(client, db):
    cofin = unidade(db, "COFIN")
    tipo = tipo_processo(db)
    serv_a, setor_a = servidor_com_setor(db, cofin)
    token_a = login(client, serv_a.email)
    proc = _criar_processo(client, serv_a, token_a, tipo)

    resp = client.post(
        f"/processos/{proc['id']}/reatribuir",
        json={
            "setor_destino_id": str(setor_a.id),
            "servidor_destino_id": str(serv_a.id),
            "justificativa": "Errado",
        },
        headers=auth(token_a),
    )
    assert resp.status_code == 422
    assert "diferente do responsável atual" in resp.json()["detail"]


def test_reatribuicao_sem_justificativa_e_rejeitada(client, db):
    cofin = unidade(db, "COFIN")
    tipo = tipo_processo(db)
    serv_a, _ = servidor_com_setor(db, cofin)
    setor_protocolo = setor(db, cofin, "Financas")
    serv_c = usuario(db, unidade_id=cofin.id, setor_id=setor_protocolo.id, email="c@ex.com")
    token_a = login(client, serv_a.email)
    proc = _criar_processo(client, serv_a, token_a, tipo)

    resp = client.post(
        f"/processos/{proc['id']}/reatribuir",
        json={"setor_destino_id": str(setor_protocolo.id), "servidor_destino_id": str(serv_c.id)},
        headers=auth(token_a),
    )
    assert resp.status_code == 422
    assert "justificativa" in resp.json()["detail"].lower()


def test_reatribuicao_por_servidor_sem_papel_e_negada(client, db):
    cofin, ajur = unidade(db, "COFIN"), unidade(db, "AJUR")
    tipo = tipo_processo(db)
    serv_a, _ = servidor_com_setor(db, cofin)
    setor_ajur = setor(db, ajur, "Análise")
    serv_b = usuario(db, unidade_id=ajur.id, setor_id=setor_ajur.id, email="b@ex.com")
    token_a = login(client, serv_a.email)
    proc = _criar_processo(client, serv_a, token_a, tipo)
    _enviar(client, proc["id"], token_a, unidade_id=ajur.id, setor_id=setor_ajur.id, servidor_id=serv_b.id)

    # Servidor D, da mesma unidade (AJUR) do processo, mas sem nenhum dos
    # três papéis (não é atual, não é remetente, não é gestor).
    serv_d = usuario(db, unidade_id=ajur.id, setor_id=setor_ajur.id, email="d@ex.com")
    token_d = login(client, serv_d.email)

    resp = client.post(
        f"/processos/{proc['id']}/reatribuir",
        json={
            "setor_destino_id": str(setor_ajur.id),
            "servidor_destino_id": str(serv_d.id),
            "justificativa": "Tentativa indevida",
        },
        headers=auth(token_d),
    )
    assert resp.status_code == 403
    logs = db.query(LogSeguranca).filter(LogSeguranca.tipo_evento == TipoEventoLog.ACESSO_NEGADO).all()
    assert len(logs) >= 1


def test_reatribuicao_remetente_da_ultima_tramitacao_pode_reatribuir(client, db):
    """"Remetente que errou o destino corrige": A enviou para B por engano,
    correto era C — A (que não é mais o responsável) pode reatribuir.

    A permanece na mesma unidade do processo (Envio não exige mudar de
    unidade) — autorização por unidade (D6, inalterada) continua sendo
    satisfeita; o que muda é o papel dentro dela (D5).
    """
    cofin = unidade(db, "COFIN")
    tipo = tipo_processo(db)
    serv_a, _setor_a = servidor_com_setor(db, cofin, nome_setor="Protocolo")
    setor_b = setor(db, cofin, "Analise")
    serv_b = usuario(db, unidade_id=cofin.id, setor_id=setor_b.id, email="b@ex.com")
    serv_c = usuario(db, unidade_id=cofin.id, setor_id=setor_b.id, email="c@ex.com")
    token_a = login(client, serv_a.email)
    proc = _criar_processo(client, serv_a, token_a, tipo)
    _enviar(client, proc["id"], token_a, unidade_id=cofin.id, setor_id=setor_b.id, servidor_id=serv_b.id)

    resp = client.post(
        f"/processos/{proc['id']}/reatribuir",
        json={
            "setor_destino_id": str(setor_b.id),
            "servidor_destino_id": str(serv_c.id),
            "justificativa": "Era para C",
        },
        headers=auth(token_a),
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["servidor_atual_id"] == str(serv_c.id)


def test_reatribuicao_gestor_da_unidade_pode_reatribuir_e_nao_e_detentor(client, db):
    cofin, ajur = unidade(db, "COFIN"), unidade(db, "AJUR")
    tipo = tipo_processo(db)
    serv_a, _ = servidor_com_setor(db, cofin)
    setor_ajur = setor(db, ajur, "Análise")
    serv_b = usuario(db, unidade_id=ajur.id, setor_id=setor_ajur.id, email="b@ex.com")
    serv_c = usuario(db, unidade_id=ajur.id, setor_id=setor_ajur.id, email="c@ex.com")
    gestor = gestor_de(db, ajur, email="gestor@ex.com")
    token_a = login(client, serv_a.email)
    proc = _criar_processo(client, serv_a, token_a, tipo)
    _enviar(client, proc["id"], token_a, unidade_id=ajur.id, setor_id=setor_ajur.id, servidor_id=serv_b.id)

    token_gestor = login(client, gestor.email)
    resp = client.post(
        f"/processos/{proc['id']}/reatribuir",
        json={
            "setor_destino_id": str(setor_ajur.id),
            "servidor_destino_id": str(serv_c.id),
            "justificativa": "Correção pelo gestor",
        },
        headers=auth(token_gestor),
    )
    assert resp.status_code == 200, resp.text

    evento = (
        db.query(Tramitacao).filter(Tramitacao.tipo_evento == TipoEventoTramitacao.REATRIBUICAO).one()
    )
    assert evento.responsavel_id == gestor.id
    assert evento.servidor_origem_id == serv_b.id
    assert evento.servidor_destino_id == serv_c.id
    # O gestor nunca aparece como detentor (origem/destino) — só como responsável (D6).
    assert gestor.id not in (evento.servidor_origem_id, evento.servidor_destino_id)


def test_reatribuicao_em_processo_concluido_e_bloqueada(client, db):
    cofin = unidade(db, "COFIN")
    tipo = tipo_processo(db)
    serv_a, setor_a = servidor_com_setor(db, cofin)
    serv_c = usuario(db, unidade_id=cofin.id, setor_id=setor_a.id, email="c@ex.com")
    token_a = login(client, serv_a.email)
    proc = _criar_processo(client, serv_a, token_a, tipo)
    client.post(f"/processos/{proc['id']}/concluir", json={}, headers=auth(token_a))

    resp = client.post(
        f"/processos/{proc['id']}/reatribuir",
        json={
            "setor_destino_id": str(setor_a.id),
            "servidor_destino_id": str(serv_c.id),
            "justificativa": "Tarde demais",
        },
        headers=auth(token_a),
    )
    assert resp.status_code == 409


# --- Conclusão -------------------------------------------------------------


def test_conclusao_a_partir_de_aberto(client, db):
    cofin = unidade(db, "COFIN")
    tipo = tipo_processo(db)
    serv_a, _ = servidor_com_setor(db, cofin)
    token_a = login(client, serv_a.email)
    proc = _criar_processo(client, serv_a, token_a, tipo)

    resp = client.post(f"/processos/{proc['id']}/concluir", json={}, headers=auth(token_a))
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "concluido"
    processo = db.get(Processo, proc["id"])
    assert processo.concluido_em is not None
    assert processo.arquivar_em is not None


def test_conclusao_a_partir_de_em_tramitacao(client, db):
    cofin, ajur = unidade(db, "COFIN"), unidade(db, "AJUR")
    tipo = tipo_processo(db)
    serv_a, _ = servidor_com_setor(db, cofin)
    setor_ajur = setor(db, ajur, "Análise")
    serv_b = usuario(db, unidade_id=ajur.id, setor_id=setor_ajur.id, email="b@ex.com")
    token_a = login(client, serv_a.email)
    proc = _criar_processo(client, serv_a, token_a, tipo)
    _enviar(client, proc["id"], token_a, unidade_id=ajur.id, setor_id=setor_ajur.id, servidor_id=serv_b.id)

    token_b = login(client, serv_b.email)
    resp = client.post(f"/processos/{proc['id']}/concluir", json={}, headers=auth(token_b))
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "concluido"


def test_conclusao_por_quem_nao_e_responsavel_nem_gestor_acesso_negado(client, db):
    cofin = unidade(db, "COFIN")
    tipo = tipo_processo(db)
    serv_a, setor_a = servidor_com_setor(db, cofin)
    serv_d = usuario(db, unidade_id=cofin.id, setor_id=setor_a.id, email="d@ex.com")
    token_a = login(client, serv_a.email)
    proc = _criar_processo(client, serv_a, token_a, tipo)

    token_d = login(client, serv_d.email)
    resp = client.post(f"/processos/{proc['id']}/concluir", json={}, headers=auth(token_d))
    assert resp.status_code == 403
    logs = db.query(LogSeguranca).filter(LogSeguranca.tipo_evento == TipoEventoLog.ACESSO_NEGADO).all()
    assert len(logs) >= 1


# --- Autorização por unidade / histórico -----------------------------------


def test_servidor_de_outra_unidade_nao_envia_e_loga(client, db):
    cofin, ajur = unidade(db, "COFIN"), unidade(db, "AJUR")
    tipo = tipo_processo(db)
    serv_a, _ = servidor_com_setor(db, cofin)
    token_a = login(client, serv_a.email)
    proc = _criar_processo(client, serv_a, token_a, tipo)

    # Servidor de AJUR tenta agir sobre processo que está na COFIN (fora do escopo de unidade).
    intruso, setor_ajur = servidor_com_setor(db, ajur, email="intruso@ex.com")
    token_intruso = login(client, intruso.email)
    resp = _enviar(
        client,
        proc["id"],
        token_intruso,
        unidade_id=ajur.id,
        setor_id=setor_ajur.id,
        servidor_id=intruso.id,
    )
    assert resp.status_code == 403
    logs = db.query(LogSeguranca).filter(LogSeguranca.tipo_evento == TipoEventoLog.ACESSO_NEGADO).all()
    assert len(logs) >= 1


def test_historico_e_append_only_apos_multiplas_transicoes(client, db):
    """Imutabilidade: cada transição é um novo INSERT; eventos anteriores não mudam."""
    cofin, ajur, dirad = unidade(db, "COFIN"), unidade(db, "AJUR"), unidade(db, "DIRAD")
    tipo = tipo_processo(db)
    serv_a, _ = servidor_com_setor(db, cofin)
    setor_ajur = setor(db, ajur, "Análise")
    serv_b = usuario(db, unidade_id=ajur.id, setor_id=setor_ajur.id, email="b@ex.com")
    setor_dirad = setor(db, dirad, "Julgamento")
    serv_c = usuario(db, unidade_id=dirad.id, setor_id=setor_dirad.id, email="c@ex.com")
    token_a = login(client, serv_a.email)
    proc = _criar_processo(client, serv_a, token_a, tipo)

    _enviar(client, proc["id"], token_a, unidade_id=ajur.id, setor_id=setor_ajur.id, servidor_id=serv_b.id)
    primeiro = db.query(Tramitacao).filter(Tramitacao.processo_id == proc["id"]).one()
    id_primeiro, criado_primeiro = primeiro.id, primeiro.criado_em

    token_b = login(client, serv_b.email)
    _enviar(client, proc["id"], token_b, unidade_id=dirad.id, setor_id=setor_dirad.id, servidor_id=serv_c.id)

    eventos = (
        db.query(Tramitacao)
        .filter(Tramitacao.processo_id == proc["id"])
        .order_by(Tramitacao.criado_em)
        .all()
    )
    assert len(eventos) == 2
    # O primeiro evento permanece inalterado.
    assert eventos[0].id == id_primeiro
    assert eventos[0].criado_em == criado_primeiro
