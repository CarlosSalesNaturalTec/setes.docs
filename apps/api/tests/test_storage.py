"""Teste do adaptador de armazenamento (Épico 3, D4) — backend local e seleção."""

from __future__ import annotations

import pytest

from app.config import Settings
from app.services.storage import FilesystemStorage, GCSStorage, get_storage


def test_filesystem_storage_salva_abre_remove(tmp_path):
    storage = FilesystemStorage(tmp_path)

    storage.salvar("proc-1/abc", b"conteudo", content_type="application/pdf")
    with storage.abrir("proc-1/abc") as stream:
        assert stream.read() == b"conteudo"

    storage.remover("proc-1/abc")
    with pytest.raises(FileNotFoundError):
        storage.abrir("proc-1/abc")


def test_filesystem_storage_remover_e_idempotente(tmp_path):
    storage = FilesystemStorage(tmp_path)
    storage.remover("nunca-existiu")  # não lança (D7)


def test_get_storage_seleciona_backend_local_por_default(tmp_path):
    settings = Settings(DOCUMENTOS_STORAGE_LOCAL_DIR=str(tmp_path))
    assert isinstance(get_storage(settings), FilesystemStorage)


def test_get_storage_seleciona_backend_gcs_quando_local_desabilitado(monkeypatch):
    monkeypatch.setattr(
        "app.services.storage.GCSStorage.__init__", lambda self, bucket_name: None
    )
    settings = Settings(DOCUMENTOS_STORAGE_LOCAL=False, DOCUMENTOS_BUCKET="meu-bucket")
    assert isinstance(get_storage(settings), GCSStorage)
