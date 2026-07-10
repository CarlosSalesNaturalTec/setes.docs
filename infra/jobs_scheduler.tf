# Cloud Run Jobs + Cloud Scheduler (tasks 8.1, 8.2, 8.3, D5).
# Infra e contrato apenas — a lógica de negócio vem em changes futuros.

locals {
  jobs = {
    job-manutencao-diaria = {
      command  = ["python", "-m", "app.jobs.entrypoint"]
      schedule = "0 3 * * *" # diário 03:00
    }
    job-anonimizacao-lgpd = {
      command  = ["python", "-m", "app.jobs.entrypoint"] # placeholder; entrypoint próprio virá depois
      schedule = "0 4 1 1,4,7,10 *"                      # trimestral (1º dia de jan/abr/jul/out, 04:00)
    }
  }
  scheduler_timezone = "America/Bahia"
}

resource "google_cloud_run_v2_job" "jobs" {
  for_each = local.jobs
  name     = each.key
  location = var.region

  template {
    template {
      service_account = google_service_account.sa["sa-jobs"].email

      # Direct VPC egress -> IP privado do Cloud SQL.
      vpc_access {
        network_interfaces {
          network    = google_compute_network.vpc.id
          subnetwork = google_compute_subnetwork.subnet.id
        }
        egress = "PRIVATE_RANGES_ONLY"
      }

      containers {
        image   = local.placeholder_image # substituída pelo pipeline
        command = each.value.command

        env {
          name = "DATABASE_URL"
          value_source {
            secret_key_ref {
              secret  = google_secret_manager_secret.secrets["db-password"].secret_id
              version = "latest"
            }
          }
        }
        env {
          name = "SENDGRID_API_KEY"
          value_source {
            secret_key_ref {
              secret  = google_secret_manager_secret.secrets["sendgrid-api-key"].secret_id
              version = "latest"
            }
          }
        }
        env {
          name  = "GCP_PROJECT_ID"
          value = var.project_id
        }
      }
    }
  }

  lifecycle {
    ignore_changes = [
      template[0].template[0].containers[0].image,
    ]
  }

  depends_on = [
    google_secret_manager_secret_iam_member.jobs_secrets,
    google_service_networking_connection.psa,
  ]
}

# sa-scheduler -> permissão de EXECUÇÃO em cada job (e nada mais).
# roles/run.invoker no job permite disparar RunJob. Só a sa-scheduler recebe;
# qualquer outra identidade é negada (spec: disparo por identidade não autorizada).
resource "google_cloud_run_v2_job_iam_member" "scheduler_runs_jobs" {
  for_each = google_cloud_run_v2_job.jobs
  location = var.region
  name     = each.value.name
  role     = "roles/run.invoker"
  member   = local.m["sa-scheduler"]
}

# Cloud Scheduler dispara cada job via API Admin do Cloud Run, autenticando com OIDC.
resource "google_cloud_scheduler_job" "triggers" {
  for_each  = local.jobs
  name      = "trigger-${each.key}"
  region    = var.region
  schedule  = each.value.schedule
  time_zone = local.scheduler_timezone

  http_target {
    http_method = "POST"
    uri         = "https://${var.region}-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/${var.project_id}/jobs/${each.key}:run"

    oauth_token {
      service_account_email = google_service_account.sa["sa-scheduler"].email
    }
  }

  depends_on = [google_cloud_run_v2_job.jobs]
}
