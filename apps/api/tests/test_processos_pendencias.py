"""Testes das pendências herdadas (task 7.4 — obrigatório: histórico de atuação
+ visibilidade por unidade). US 1.4 Cen.2/3, US 1.5, US 8.1 Cen.3/4."""

from __future__ import annotations

from app.db.models import LogSeguranca, TipoEventoLog, Usuario
from tests.helpers_processo import (
    auth,
    login,
    servidor_com_setor,
    setor,
    tipo_processo,
    unidade,
    usuario,
)


def _cria(client, token, tipo, assunto="A", prazo=10):
    return client.post(
        "/processos",
        json={"assunto": assunto, "tipo_processo_id": str(tipo.id), "prazo_dias": prazo},
        headers=auth(token),
    ).json()


def test_acesso_direto_por_url_a_processo_de_outra_unidade_negado_e_logado(client, db):
    """US 1.4 Cen.2 — detalhe por URL de processo fora do escopo → 403 + log."""
    cofin, ajur = unidade(db, "COFIN"), unidade(db, "AJUR")
    tipo = tipo_processo(db)
    dono, _setor = servidor_com_setor(db, cofin, email="dono@ex.com")
    proc = _cria(client, login(client, "dono@ex.com"), tipo, "Sigiloso COFIN")

    usuario(db, unidade_id=ajur.id, email="curioso@ex.com")
    token_curioso = login(client, "curioso@ex.com")
    resp = client.get(f"/processos/{proc['id']}", headers=auth(token_curioso))
    assert resp.status_code == 403
    assert "não tem permissão para visualizar este processo" in resp.json()["detail"]

    logs = (
        db.query(LogSeguranca)
        .filter(LogSeguranca.tipo_evento == TipoEventoLog.ACESSO_NEGADO)
        .all()
    )
    assert any(log.contexto.get("processo_id") == proc["id"] for log in logs)


def test_meu_perfil_lista_processos_atuados(client, db):
    """US 1.5 Cen.1 — criador e responsável por tramitação aparecem em 'Meu Perfil'."""
    cofin, ajur = unidade(db, "COFIN"), unidade(db, "AJUR")
    tipo = tipo_processo(db)
    servidor_com_setor(db, cofin, email="atuante@ex.com")
    token = login(client, "atuante@ex.com")
    proc = _cria(client, token, tipo, "Meu processo")

    setor_ajur = setor(db, ajur, "Análise")
    serv_ajur = usuario(db, unidade_id=ajur.id, setor_id=setor_ajur.id, email="ajur-destino@ex.com")
    client.post(
        f"/processos/{proc['id']}/enviar",
        json={
            "unidade_destino_id": str(ajur.id),
            "setor_destino_id": str(setor_ajur.id),
            "servidor_destino_id": str(serv_ajur.id),
        },
        headers=auth(token),
    )

    resp = client.get("/usuarios/me/perfil", headers=auth(token))
    body = resp.json()
    assert len(body["processos"]) == 1
    item = body["processos"][0]
    assert item["numero"] == proc["numero"]
    assert item["assunto"] == "Meu processo"
    assert item["tipo_acao"] == "envio"


def test_meu_perfil_vazio_para_recem_cadastrado(client, db):
    cofin = unidade(db, "COFIN")
    usuario(db, unidade_id=cofin.id, email="novo@ex.com")
    token = login(client, "novo@ex.com")
    resp = client.get("/usuarios/me/perfil", headers=auth(token))
    body = resp.json()
    assert body["processos"] == []
    assert body["mensagem_processos"] == "Nenhum processo registrado"
    assert body["documentos_assinados"] == []


def test_servidor_transferido_mantem_historico_de_atuacao(client, db):
    """US 1.4 Cen.3 — atuação na unidade anterior permanece após transferência."""
    cofin, ajur, _dirad = unidade(db, "COFIN"), unidade(db, "AJUR"), unidade(db, "DIRAD")
    tipo = tipo_processo(db)
    serv, _setor = servidor_com_setor(db, cofin, email="movel@ex.com")
    token = login(client, "movel@ex.com")
    proc = _cria(client, token, tipo, "Antes da transferência")

    setor_ajur = setor(db, ajur, "Análise")
    serv_ajur = usuario(db, unidade_id=ajur.id, setor_id=setor_ajur.id, email="ajur-destino2@ex.com")
    client.post(
        f"/processos/{proc['id']}/enviar",
        json={
            "unidade_destino_id": str(ajur.id),
            "setor_destino_id": str(setor_ajur.id),
            "servidor_destino_id": str(serv_ajur.id),
        },
        headers=auth(token),
    )

    # Transfere o servidor para AJUR (processo já saiu da COFIN e está em AJUR).
    serv_db = db.get(Usuario, serv.id)
    serv_db.unidade_id = ajur.id
    db.commit()

    token2 = login(client, "movel@ex.com")
    resp = client.get("/usuarios/me/perfil", headers=auth(token2))
    numeros = [p["numero"] for p in resp.json()["processos"]]
    assert proc["numero"] in numeros  # histórico de atuação preservado


def test_desativacao_bloqueada_com_processo_em_andamento(client, db):
    from app.db.models import PerfilUsuario

    cofin = unidade(db, "COFIN")
    tipo = tipo_processo(db)
    servidor_com_setor(db, cofin, email="serv@ex.com")
    _cria(client, login(client, "serv@ex.com"), tipo, "Pendente")

    usuario(db, perfil=PerfilUsuario.ADMINISTRADOR, email="admin@ex.com")
    token_admin = login(client, "admin@ex.com")
    resp = client.post(f"/unidades/{cofin.id}/desativar", headers=auth(token_admin))
    assert resp.status_code == 422
    assert "1 processo(s) em andamento" in resp.json()["detail"]


def test_desativacao_liberada_sem_pendencias_desvincula_usuarios(client, db):
    from app.db.models import PerfilUsuario

    cofin = unidade(db, "COFIN")
    serv = usuario(db, unidade_id=cofin.id, email="serv2@ex.com")
    usuario(db, perfil=PerfilUsuario.ADMINISTRADOR, email="admin2@ex.com")
    token_admin = login(client, "admin2@ex.com")

    resp = client.post(f"/unidades/{cofin.id}/desativar", headers=auth(token_admin))
    assert resp.status_code == 200
    assert resp.json()["ativo"] is False
    db.refresh(serv)
    assert serv.unidade_id is None  # usuário desvinculado (Cen.4)
