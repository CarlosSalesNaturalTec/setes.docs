"""Sanitização de HTML e renderização de PDF do modelo de documento (task 2.3
— obrigatório: segurança). Change modelos-de-documento, design.md D2/D3."""

from __future__ import annotations

from app.services import modelo_documento as servico
from app.services.documento import _sniff_mime, _validar_formato_e_tamanho


def test_tags_permitidas_sao_preservadas():
    html = (
        '<p align="center"><b>Requerimento</b></p>'
        "<p>Prezado <i>Fulano</i>, <u>bom dia</u>.</p>"
        "<ul><li>Item um</li><li>Item dois</li></ul>"
        "<ol><li>Passo um</li></ol>"
        "Texto solto<br>com quebra"
    )

    saida = servico.sanitizar_html(html)

    assert '<p align="center"><b>Requerimento</b></p>' in saida
    assert "<i>Fulano</i>" in saida
    assert "<u>bom dia</u>" in saida
    assert "<ul><li>Item um</li><li>Item dois</li></ul>" in saida
    assert "<ol><li>Passo um</li></ol>" in saida
    assert "<br>" in saida


def test_script_e_removido_com_conteudo():
    html = "<p>Antes</p><script>alert('xss')</script><p>Depois</p>"

    saida = servico.sanitizar_html(html)

    assert "<script" not in saida
    assert "alert" not in saida
    assert "<p>Antes</p>" in saida
    assert "<p>Depois</p>" in saida


def test_atributos_de_evento_sao_removidos():
    html = '<p onclick="roubarDados()" onmouseover="x()">Texto</p>'

    saida = servico.sanitizar_html(html)

    assert "onclick" not in saida
    assert "onmouseover" not in saida
    assert "<p>Texto</p>" in saida


def test_style_e_iframe_sao_removidos():
    html = '<p style="color:red">Texto</p><iframe src="javascript:alert(1)"></iframe>'

    saida = servico.sanitizar_html(html)

    assert "style" not in saida
    assert "<iframe" not in saida
    assert "javascript" not in saida
    assert "<p>Texto</p>" in saida


def test_tag_fora_da_whitelist_e_removida_mas_texto_permanece():
    html = '<div class="destaque"><span>Texto dentro</span></div>'

    saida = servico.sanitizar_html(html)

    assert "<div" not in saida
    assert "<span" not in saida
    assert "Texto dentro" in saida


def test_align_so_aceita_valores_reconhecidos():
    html = '<p align="center">A</p><p align="javascript:alert(1)">B</p>'

    saida = servico.sanitizar_html(html)

    assert '<p align="center">A</p>' in saida
    assert "javascript" not in saida
    assert "<p>B</p>" in saida


def test_renderizar_pdf_produz_bytes_com_assinatura_pdf():
    html_sanitizado = servico.sanitizar_html(
        '<p align="center"><b>Requerimento</b></p><p>Acentuação: á é í ó ú ç ã õ</p>'
    )

    pdf_bytes = servico.renderizar_pdf(html_sanitizado)

    assert pdf_bytes.startswith(b"%PDF")


def test_pdf_gerado_passa_na_validacao_e_sniffing_de_documento_service():
    html_sanitizado = servico.sanitizar_html("<p>Conteúdo do modelo preenchido</p>")
    pdf_bytes = servico.renderizar_pdf(html_sanitizado)

    tipo_conteudo = _validar_formato_e_tamanho("documento-gerado.pdf", pdf_bytes)

    assert tipo_conteudo == "application/pdf"
    assert _sniff_mime(pdf_bytes) == "application/pdf"
