"""Testes de geração de notificação interna nos eventos de tramitação
(task 2.5, Épico 5 — obrigatório: histórico de tramitação). US 5.1, 5.3,
change tramitacao-manual (D8 — destinatário único, e os dois tipos novos de
notificação do fluxo de Reatribuição)."""

from __future__ import annotations

from app.db.models import Notificacao, TipoNotificacao
from tests.helpers_processo import auth, enviar_para, login, servidor_com_setor, setor, tipo_processo, unidade, usuario

ASSUNTO = "Licitação de equipamentos"


def _criar_processo(client, db, tipo, unidade_criacao, *, email=None):
    serv, _setor = servidor_com_setor(db, unidade_criacao, email=email)
    token = login(client, serv.email)
    resp = client.post(
        "/processos",
        json={"assunto": ASSUNTO, "tipo_processo_id": str(tipo.id), "prazo_dias": 10},
        headers=auth(token),
    )
    assert resp.status_code == 201, resp.text
    return resp.json(), serv, token


def test_envio_notifica_apenas_o_servidor_de_destino(client, db):
    """D8 — destinatário único, não mais fan-out para toda a unidade (US 5.1)."""
    cofin, ajur = unidade(db, "COFIN"), unidade(db, "AJUR")
    tipo = tipo_processo(db)
    proc, _serv, token = _criar_processo(client, db, tipo, cofin)

    setor_ajur = setor(db, ajur, "Análise")
    serv_ajur_destino = usuario(db, unidade_id=ajur.id, setor_id=setor_ajur.id, email="destino@ex.com")
    usuario(db, unidade_id=ajur.id, setor_id=setor_ajur.id, email="outro-servidor-ajur@ex.com")

    resp = client.post(
        f"/processos/{proc['id']}/enviar",
        json={
            "unidade_destino_id": str(ajur.id),
            "setor_destino_id": str(setor_ajur.id),
            "servidor_destino_id": str(serv_ajur_destino.id),
        },
        headers=auth(token),
    )
    assert resp.status_code == 200, resp.text

    notificacoes = (
        db.query(Notificacao)
        .filter(
            Notificacao.processo_id == proc["id"],
            Notificacao.tipo == TipoNotificacao.NOVO_PROCESSO,
        )
        .all()
    )
    assert {n.usuario_id for n in notificacoes} == {serv_ajur_destino.id}
    notificacao = notificacoes[0]
    assert notificacao.lida_em is None
    assert notificacao.unidade_id == ajur.id
    assert notificacao.unidade_origem_id == cofin.id
    assert notificacao.numero_processo == proc["numero"]
    assert notificacao.assunto == ASSUNTO


def test_conclusao_notifica_apenas_o_criador(client, db):
    """MODIFIED: destinatário passa a ser o servidor criador, não a unidade inteira (US 5.3)."""
    cofin, ajur = unidade(db, "COFIN"), unidade(db, "AJUR")
    tipo = tipo_processo(db)
    proc, serv_criador, token = _criar_processo(client, db, tipo, cofin)
    _resp, serv_ajur, _setor = enviar_para(
        client, db, processo_id=proc["id"], token_origem=token, unidade_destino=ajur
    )
    token_ajur = login(client, serv_ajur.email)

    resp = client.post(f"/processos/{proc['id']}/concluir", json={}, headers=auth(token_ajur))
    assert resp.status_code == 200, resp.text

    notificacoes = (
        db.query(Notificacao)
        .filter(
            Notificacao.processo_id == proc["id"], Notificacao.tipo == TipoNotificacao.CONCLUIDO
        )
        .all()
    )
    assert {n.usuario_id for n in notificacoes} == {serv_criador.id}
    assert notificacoes[0].unidade_id == ajur.id


def test_conclusao_pelo_proprio_criador_nao_gera_notificacao(client, db):
    cofin = unidade(db, "COFIN")
    tipo = tipo_processo(db)
    proc, _serv_criador, token = _criar_processo(client, db, tipo, cofin)

    resp = client.post(f"/processos/{proc['id']}/concluir", json={}, headers=auth(token))
    assert resp.status_code == 200, resp.text

    total = (
        db.query(Notificacao)
        .filter(
            Notificacao.processo_id == proc["id"], Notificacao.tipo == TipoNotificacao.CONCLUIDO
        )
        .count()
    )
    assert total == 0


def test_reatribuicao_notifica_destino_e_remetente_original(client, db):
    """D8 — REATRIBUIDO_PARA_VOCE ao destino, DESTINO_CORRIGIDO ao remetente original."""
    cofin, ajur = unidade(db, "COFIN"), unidade(db, "AJUR")
    tipo = tipo_processo(db)
    proc, serv_a, token_a = _criar_processo(client, db, tipo, cofin, email="a@ex.com")
    _resp, serv_b, setor_ajur = enviar_para(
        client, db, processo_id=proc["id"], token_origem=token_a, unidade_destino=ajur,
        email_destino="b@ex.com",
    )
    serv_c = usuario(db, unidade_id=ajur.id, setor_id=setor_ajur.id, email="c@ex.com")

    token_b = login(client, serv_b.email)
    resp = client.post(
        f"/processos/{proc['id']}/reatribuir",
        json={
            "setor_destino_id": str(setor_ajur.id),
            "servidor_destino_id": str(serv_c.id),
            "justificativa": "Destino errado",
        },
        headers=auth(token_b),
    )
    assert resp.status_code == 200, resp.text

    para_c = (
        db.query(Notificacao)
        .filter(
            Notificacao.processo_id == proc["id"],
            Notificacao.tipo == TipoNotificacao.REATRIBUIDO_PARA_VOCE,
        )
        .all()
    )
    assert {n.usuario_id for n in para_c} == {serv_c.id}
    assert para_c[0].justificativa == "Destino errado"

    para_a = (
        db.query(Notificacao)
        .filter(
            Notificacao.processo_id == proc["id"],
            Notificacao.tipo == TipoNotificacao.DESTINO_CORRIGIDO,
        )
        .all()
    )
    assert {n.usuario_id for n in para_a} == {serv_a.id}
    assert serv_c.nome in para_a[0].justificativa


def test_reatribuicao_pelo_proprio_remetente_nao_notifica_a_si_mesmo(client, db):
    """"Autor da correção não é notificado de si mesmo": A enviou a B por
    engano e o próprio A reatribui de B para C — A não recebe DESTINO_CORRIGIDO.

    A permanece na mesma unidade do processo (Envio não exige mudar de
    unidade) — autorização por unidade (D6, inalterada) continua satisfeita.
    """
    cofin = unidade(db, "COFIN")
    tipo = tipo_processo(db)
    proc, serv_a, token_a = _criar_processo(client, db, tipo, cofin, email="a2@ex.com")
    setor_b = setor(db, cofin, "SetorB")
    serv_b = usuario(db, unidade_id=cofin.id, setor_id=setor_b.id, email="b2@ex.com")
    serv_c = usuario(db, unidade_id=cofin.id, setor_id=setor_b.id, email="c2@ex.com")
    client.post(
        f"/processos/{proc['id']}/enviar",
        json={
            "unidade_destino_id": str(cofin.id),
            "setor_destino_id": str(setor_b.id),
            "servidor_destino_id": str(serv_b.id),
        },
        headers=auth(token_a),
    )

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

    destino_corrigido = (
        db.query(Notificacao)
        .filter(
            Notificacao.processo_id == proc["id"],
            Notificacao.tipo == TipoNotificacao.DESTINO_CORRIGIDO,
        )
        .count()
    )
    assert destino_corrigido == 0


def test_reatribuicao_sem_remetente_original_nao_gera_aviso_de_correcao(client, db):
    """Processo ainda com o criador (nunca tramitou) reatribuído pelo próprio
    criador — não há remetente original a notificar."""
    cofin = unidade(db, "COFIN")
    tipo = tipo_processo(db)
    proc, serv_a, token_a = _criar_processo(client, db, tipo, cofin, email="a3@ex.com")
    setor_a_id = serv_a.setor_id
    serv_c = usuario(db, unidade_id=cofin.id, setor_id=setor_a_id, email="c3@ex.com")

    resp = client.post(
        f"/processos/{proc['id']}/reatribuir",
        json={
            "setor_destino_id": str(setor_a_id),
            "servidor_destino_id": str(serv_c.id),
            "justificativa": "Correção direta",
        },
        headers=auth(token_a),
    )
    assert resp.status_code == 200, resp.text

    destino_corrigido = (
        db.query(Notificacao)
        .filter(
            Notificacao.processo_id == proc["id"],
            Notificacao.tipo == TipoNotificacao.DESTINO_CORRIGIDO,
        )
        .count()
    )
    assert destino_corrigido == 0
    para_c = (
        db.query(Notificacao)
        .filter(
            Notificacao.processo_id == proc["id"],
            Notificacao.tipo == TipoNotificacao.REATRIBUIDO_PARA_VOCE,
        )
        .all()
    )
    assert {n.usuario_id for n in para_c} == {serv_c.id}
