# Cloud SQL for PostgreSQL — SEM IP público, apenas IP privado (tasks 3.2, 3.3).
resource "google_sql_database_instance" "postgres" {
  name             = "setes-postgres"
  database_version = "POSTGRES_16"
  region           = var.region

  # Descarte integral autorizado para a migração de região (D1/D5,
  # docs/lgpd-transferencia-internacional-us-central1.md) — reativar após o apply em us-central1.
  deletion_protection = false

  depends_on = [google_service_networking_connection.psa]

  settings {
    tier              = var.db_tier
    edition           = "ENTERPRISE" # GCP passou a exigir isso p/ usar tier db-custom-* (não ENTERPRISE_PLUS)
    availability_type = "ZONAL"      # MVP; REGIONAL (HA) é upgrade futuro.
    disk_autoresize   = true

    ip_configuration {
      ipv4_enabled    = false # <- sem IP público (spec: acesso público negado)
      private_network = google_compute_network.vpc.id
    }

    database_flags {
      name  = "max_connections"
      value = tostring(var.db_max_connections)
    }

    backup_configuration {
      enabled = true
      # PITR desligado no MVP p/ economia (evita armazenamento contínuo de WAL);
      # RPO passa a ser de até 24h (só backup diário automatizado).
      # REATIVAR (=true) quando o sistema estiver estável e com alto volume de
      # dados em produção — dados de processos administrativos + LGPD justificam
      # RPO de minutos nesse momento.
      point_in_time_recovery_enabled = false
    }
  }
}

resource "google_sql_database" "app" {
  name     = "setes"
  instance = google_sql_database_instance.postgres.name
}

# Usuário de aplicação; senha vem do Secret Manager (task 3.3).
resource "google_sql_user" "app" {
  name     = "app"
  instance = google_sql_database_instance.postgres.name
  password = google_secret_manager_secret_version.db_password_v1.secret_data
}
