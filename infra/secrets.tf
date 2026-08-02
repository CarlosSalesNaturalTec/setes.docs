# Secret Manager — 3 segredos com replicação user-managed fixada em var.region (task 4.2).
# replication.user_managed restringe a replicação a uma única região explícita (D4/D7),
# hoje us-central1 — escolha de custo, não requisito de residência; o padrão
# "automatic" replicaria globalmente.

locals {
  secret_ids = ["db-password", "jwt-signing-key", "sendgrid-api-key"]
}

resource "google_secret_manager_secret" "secrets" {
  for_each  = toset(local.secret_ids)
  secret_id = each.value

  replication {
    user_managed {
      replicas {
        location = var.region
      }
    }
  }

  depends_on = [google_project_service.enabled]
}

# Valores iniciais.
# db-password: gerado aqui e consumido pelo google_sql_user (task 3.3).
resource "random_password" "db_password" {
  length  = 32
  special = false
}

resource "google_secret_manager_secret_version" "db_password_v1" {
  secret      = google_secret_manager_secret.secrets["db-password"].id
  secret_data = random_password.db_password.result
}

# jwt-signing-key: gerado aqui (HS256 — D4).
resource "random_password" "jwt_key" {
  length  = 64
  special = false
}

resource "google_secret_manager_secret_version" "jwt_key_v1" {
  secret      = google_secret_manager_secret.secrets["jwt-signing-key"].id
  secret_data = random_password.jwt_key.result
}

# sendgrid-api-key: placeholder; o valor real é inserido manualmente/fora do VCS
# (o provedor definitivo é decidido na implementação — Open Question do design).
resource "google_secret_manager_secret_version" "sendgrid_key_v1" {
  secret      = google_secret_manager_secret.secrets["sendgrid-api-key"].id
  secret_data = "REPLACE_ME"

  lifecycle {
    ignore_changes = [secret_data] # não sobrescrever o valor real depois de inserido
  }
}
