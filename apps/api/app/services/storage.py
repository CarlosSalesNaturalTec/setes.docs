"""Adaptador de armazenamento de conteúdo binário (Épico 3, D4).

Interface pequena e comum a dois backends: **local** (filesystem, usado em
pytest/dev/E2E — os testes usam Postgres real, mas não GCP) e **GCS**
(produção, `google-cloud-storage` via ADC da SA do Cloud Run, sem chave
JSON). Selecionado por `Settings.documentos_storage_local`, mesmo padrão
dev/prod de `app/email/provider.py`. `remover` é idempotente em ambos os
backends — chave ausente é no-op — para sustentar a retomada da purga (D7).
"""

from __future__ import annotations

import abc
import io
import os
from pathlib import Path
from typing import BinaryIO

from app.config import Settings


class Storage(abc.ABC):
    @abc.abstractmethod
    def salvar(self, chave: str, conteudo: bytes, *, content_type: str) -> None: ...

    @abc.abstractmethod
    def abrir(self, chave: str) -> BinaryIO: ...

    @abc.abstractmethod
    def remover(self, chave: str) -> None: ...

    def url_assinada(self, chave: str, *, ttl_segundos: int) -> str:
        """Otimização futura (D5) — o MVP serve conteúdo por streaming autenticado."""
        raise NotImplementedError("url_assinada não é usada no MVP (D5) — ver streaming pela API")


class FilesystemStorage(Storage):
    """Backend local para pytest/dev/E2E — sem dependência do GCP."""

    def __init__(self, base_dir: str | Path) -> None:
        self._base_dir = Path(base_dir)

    def _caminho(self, chave: str) -> Path:
        return self._base_dir / chave

    def salvar(self, chave: str, conteudo: bytes, *, content_type: str) -> None:
        caminho = self._caminho(chave)
        caminho.parent.mkdir(parents=True, exist_ok=True)
        caminho.write_bytes(conteudo)

    def abrir(self, chave: str) -> BinaryIO:
        return self._caminho(chave).open("rb")

    def remover(self, chave: str) -> None:
        try:
            self._caminho(chave).unlink()
        except FileNotFoundError:
            pass  # idempotente (D7) — objeto já ausente não é erro


class GCSStorage(Storage):
    """Backend real (produção) — bucket regional `${project_id}-documentos`,
    acesso via ADC da SA do Cloud Run (sem chave JSON, D4)."""

    def __init__(self, bucket_name: str) -> None:
        from google.cloud import storage as gcs

        self._client = gcs.Client()
        self._bucket = self._client.bucket(bucket_name)

    def salvar(self, chave: str, conteudo: bytes, *, content_type: str) -> None:
        blob = self._bucket.blob(chave)
        blob.upload_from_file(io.BytesIO(conteudo), size=len(conteudo), content_type=content_type)

    def abrir(self, chave: str) -> BinaryIO:
        blob = self._bucket.blob(chave)
        return io.BytesIO(blob.download_as_bytes())

    def remover(self, chave: str) -> None:
        from google.cloud.exceptions import NotFound

        try:
            self._bucket.blob(chave).delete()
        except NotFound:
            pass  # idempotente (D7) — objeto já ausente não é erro

    def url_assinada(self, chave: str, *, ttl_segundos: int) -> str:
        from datetime import timedelta

        blob = self._bucket.blob(chave)
        return blob.generate_signed_url(version="v4", expiration=timedelta(seconds=ttl_segundos))


def get_storage(settings: Settings) -> Storage:
    """Seleciona o backend por config (D4)."""
    if settings.documentos_storage_local:
        os.makedirs(settings.documentos_storage_local_dir, exist_ok=True)
        return FilesystemStorage(settings.documentos_storage_local_dir)
    return GCSStorage(settings.documentos_bucket)
