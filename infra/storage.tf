# Bucket único de documentos (task 4.1).
# uniform bucket-level access + versionamento + soft-delete nativo. Sem binding
# público (spec: leitura pública negada / rede de segurança).
resource "google_storage_bucket" "documentos" {
  name     = "${var.project_id}-documentos"
  location = var.region # regional, dentro do Brasil
  project  = var.project_id

  uniform_bucket_level_access = true
  public_access_prevention    = "enforced" # bloqueia allUsers/allAuthenticatedUsers

  versioning {
    enabled = true
  }

  # Soft-delete nativo do Cloud Storage: retém objeto deletado por 30 dias como
  # rede de segurança contra exclusão acidental de INFRAESTRUTURA (D3). Não é a
  # regra de negócio de soft-delete de documentos (essa é do job diário via banco).
  soft_delete_policy {
    retention_duration_seconds = 2592000 # 30 dias
  }

  depends_on = [google_project_service.enabled]
}
