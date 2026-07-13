"""Teste de app/services/roteiros.py (D8)."""

from app.db.models import Roteiro, TipoProcesso
from app.services.roteiros import obter_roteiro_vigente


def test_obter_roteiro_vigente_retorna_apenas_o_marcado_vigente(db):
    tipo = TipoProcesso(nome="Licitação", ativo=True)
    db.add(tipo)
    db.flush()

    antigo = Roteiro(tipo_processo_id=tipo.id, vigente=False)
    atual = Roteiro(tipo_processo_id=tipo.id, vigente=True)
    db.add_all([antigo, atual])
    db.commit()

    encontrado = obter_roteiro_vigente(db, tipo.id)

    assert encontrado is not None
    assert encontrado.id == atual.id


def test_obter_roteiro_vigente_retorna_none_se_nenhum_vigente(db):
    tipo = TipoProcesso(nome="Sem Roteiro", ativo=True)
    db.add(tipo)
    db.commit()

    assert obter_roteiro_vigente(db, tipo.id) is None
