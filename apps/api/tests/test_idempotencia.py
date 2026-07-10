"""Prova o contrato de idempotência das rotinas (task 8.4, spec rotinas-agendadas)."""

from datetime import datetime, timedelta

from app.jobs.manutencao_diaria import (
    Historico,
    Processo,
    StatusProcesso,
    arquivar_processos,
)

AGORA = datetime(2026, 7, 9, 3, 0, 0)


def _cenario():
    return [
        # vencido: deve arquivar
        Processo(id="p1", status=StatusProcesso.CONCLUIDO, arquivar_a_partir_de=AGORA - timedelta(days=1)),
        # ainda não vencido: não toca
        Processo(id="p2", status=StatusProcesso.CONCLUIDO, arquivar_a_partir_de=AGORA + timedelta(days=1)),
        # já arquivado: guard impede reprocesso
        Processo(id="p3", status=StatusProcesso.ARQUIVADO, arquivar_a_partir_de=AGORA - timedelta(days=10)),
    ]


def test_execucao_repetida_nao_duplica_efeito():
    processos = _cenario()
    hist = Historico()

    n1 = arquivar_processos(processos, hist, agora=AGORA)
    n2 = arquivar_processos(processos, hist, agora=AGORA)  # reexecução sobre o mesmo estado

    assert n1 == 1  # só p1
    assert n2 == 0  # nada reentra
    # Exatamente 1 evento de histórico — sem duplicação.
    assert len(hist.eventos) == 1
    assert hist.eventos[0].processo_id == "p1"
    assert processos[0].status == StatusProcesso.ARQUIVADO


def test_retomada_apos_execucao_perdida_captura_tudo_que_venceu():
    # Rotina não rodou por 3 dias; ao voltar, agora>data de vários vencidos.
    processos = [
        Processo(id="a", status=StatusProcesso.CONCLUIDO, arquivar_a_partir_de=AGORA - timedelta(days=3)),
        Processo(id="b", status=StatusProcesso.CONCLUIDO, arquivar_a_partir_de=AGORA - timedelta(days=2)),
        Processo(id="c", status=StatusProcesso.CONCLUIDO, arquivar_a_partir_de=AGORA - timedelta(days=1)),
    ]
    hist = Historico()
    n = arquivar_processos(processos, hist, agora=AGORA)
    # Todos os vencidos durante a indisponibilidade são capturados nesta execução.
    assert n == 3
    assert len(hist.eventos) == 3
    assert all(p.status == StatusProcesso.ARQUIVADO for p in processos)


def test_selecao_e_funcao_do_estado_atual_nao_do_intervalo():
    # Mesmo estado, dois "agora" diferentes -> resultado depende do estado, não da data da última run.
    processos = _cenario()
    hist = Historico()
    # roda "amanhã": p2 agora venceu também
    amanha = AGORA + timedelta(days=2)
    n = arquivar_processos(processos, hist, agora=amanha)
    assert n == 2  # p1 e p2 (p3 já arquivado)
