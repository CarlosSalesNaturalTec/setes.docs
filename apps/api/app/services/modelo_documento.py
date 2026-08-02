"""Serviço de modelos de documento (change modelos-de-documento).

`sanitizar_html`/`renderizar_pdf` implementam D2/D3: a whitelist de tags é a
fronteira de segurança real, aplicada no backend tanto na gravação do modelo
quanto na geração do documento — a barra do editor do front é só conveniência
de uso. O restante do módulo é o catálogo do Administrador (D5/D6/D7): listar,
obter, criar, editar, desativar e reativar — **sem** caminho de exclusão
física, porque um modelo já usado é referenciado por `Documento.modelo_id`.
"""

from __future__ import annotations

import uuid
from html import escape
from html.parser import HTMLParser

from fpdf import FPDF
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import ModeloDocumento, TipoModeloDocumento, Usuario

MSG_MODELO_NAO_ENCONTRADO = "Modelo de documento não encontrado."
MSG_MODELO_INATIVO = "Este modelo não está disponível para uso."

# Whitelist estrita (D3) — qualquer tag ou atributo fora daqui é descartado
# silenciosamente, tanto na gravação do modelo quanto na geração do documento.
_TAGS_PERMITIDAS = {"p", "br", "b", "strong", "i", "em", "u", "ul", "ol", "li"}
_TAGS_AUTOFECHAVEIS = {"br"}
_ALIGN_VALORES_PERMITIDOS = {"left", "center", "right", "justify"}
# Conteúdo integralmente descartado (não só a marcação) — script/style/iframe
# carregam código/instruções, não texto do documento.
_TAGS_CONTEUDO_PERIGOSO = {"script", "style", "iframe", "object", "embed"}


class _SanitizadorHtml(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._saida: list[str] = []
        self._pilha_suprimida: list[str] = []

    def _suprimindo(self) -> bool:
        return bool(self._pilha_suprimida)

    def _atributos_permitidos(self, tag: str, attrs: list[tuple[str, str | None]]) -> str:
        if tag != "p":
            return ""
        for nome, valor in attrs:
            if nome == "align" and valor in _ALIGN_VALORES_PERMITIDOS:
                return f' align="{valor}"'
        return ""

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if self._suprimindo():
            if tag in _TAGS_CONTEUDO_PERIGOSO:
                self._pilha_suprimida.append(tag)
            return
        if tag in _TAGS_CONTEUDO_PERIGOSO:
            self._pilha_suprimida.append(tag)
            return
        if tag not in _TAGS_PERMITIDAS:
            return
        if tag in _TAGS_AUTOFECHAVEIS:
            self._saida.append(f"<{tag}>")
            return
        self._saida.append(f"<{tag}{self._atributos_permitidos(tag, attrs)}>")

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if self._suprimindo():
            return
        if tag in _TAGS_PERMITIDAS:
            self._saida.append(f"<{tag}>")

    def handle_endtag(self, tag: str) -> None:
        if self._pilha_suprimida and self._pilha_suprimida[-1] == tag:
            self._pilha_suprimida.pop()
            return
        if self._suprimindo():
            return
        if tag in _TAGS_PERMITIDAS and tag not in _TAGS_AUTOFECHAVEIS:
            self._saida.append(f"</{tag}>")

    def handle_data(self, data: str) -> None:
        if self._suprimindo():
            return
        self._saida.append(escape(data))

    def resultado(self) -> str:
        return "".join(self._saida)


def sanitizar_html(html: str) -> str:
    """Filtra `html` contra a whitelist estrita de tags/atributos (D3)."""
    sanitizador = _SanitizadorHtml()
    sanitizador.feed(html)
    sanitizador.close()
    return sanitizador.resultado()


def renderizar_pdf(html_sanitizado: str) -> bytes:
    """HTML sanitizado → bytes PDF via `fpdf2.write_html` (D2), preservando
    negrito, itálico, sublinhado, alinhamento e listas."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("helvetica", size=12)
    pdf.write_html(html_sanitizado)
    return bytes(pdf.output())


# --- Catálogo de modelos (D5, D6, D7) ----------------------------------------


def listar(db: Session, *, apenas_ativos: bool = False) -> list[ModeloDocumento]:
    query = select(ModeloDocumento)
    if apenas_ativos:
        query = query.where(ModeloDocumento.ativo.is_(True))
    return list(db.scalars(query.order_by(ModeloDocumento.nome)).all())


def obter(db: Session, modelo_id: uuid.UUID) -> ModeloDocumento:
    modelo = db.get(ModeloDocumento, modelo_id)
    if modelo is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=MSG_MODELO_NAO_ENCONTRADO
        )
    return modelo


def obter_ativo(db: Session, modelo_id: uuid.UUID) -> ModeloDocumento:
    """Usado na geração de documento (US — modelo inativo não pode originar
    documento): 404 se não existe, 422 se existe mas está desativado."""
    modelo = obter(db, modelo_id)
    if not modelo.ativo:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=MSG_MODELO_INATIVO
        )
    return modelo


def criar(
    db: Session,
    *,
    nome: str,
    categoria: str,
    tipo: TipoModeloDocumento,
    descricao: str | None,
    conteudo: str,
    criado_por: Usuario,
) -> ModeloDocumento:
    modelo = ModeloDocumento(
        nome=nome,
        categoria=categoria,
        tipo=tipo,
        descricao=descricao,
        conteudo=sanitizar_html(conteudo),
        ativo=True,
        criado_por_id=criado_por.id,
    )
    db.add(modelo)
    db.commit()
    db.refresh(modelo)
    return modelo


def editar(
    db: Session,
    *,
    modelo_id: uuid.UUID,
    nome: str | None,
    categoria: str | None,
    tipo: TipoModeloDocumento | None,
    descricao: str | None,
    conteudo: str | None,
) -> ModeloDocumento:
    modelo = obter(db, modelo_id)
    if nome is not None:
        modelo.nome = nome
    if categoria is not None:
        modelo.categoria = categoria
    if tipo is not None:
        modelo.tipo = tipo
    if descricao is not None:
        modelo.descricao = descricao
    if conteudo is not None:
        modelo.conteudo = sanitizar_html(conteudo)
    db.commit()
    db.refresh(modelo)
    return modelo


def desativar(db: Session, modelo_id: uuid.UUID) -> ModeloDocumento:
    """Nunca exclui — só desativa (D6): sai do catálogo de escolha, mas
    documentos já gerados a partir dele permanecem intactos e acessíveis."""
    modelo = obter(db, modelo_id)
    modelo.ativo = False
    db.commit()
    db.refresh(modelo)
    return modelo


def reativar(db: Session, modelo_id: uuid.UUID) -> ModeloDocumento:
    modelo = obter(db, modelo_id)
    modelo.ativo = True
    db.commit()
    db.refresh(modelo)
    return modelo
