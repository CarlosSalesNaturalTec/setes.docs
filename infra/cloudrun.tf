# Cloud Run — serviços api e web (tasks 6.2, 6.3, 6.4).
#
# Nota: a imagem inicial usa um placeholder público; o deploy real de cada revisão
# é feito pelo pipeline (gcloud run deploy). ignore_changes no image evita que o
# Terraform reverta a imagem publicada pelo CD.

locals {
  # Placeholder até o primeiro deploy do pipeline.
  placeholder_image = "us-docker.pkg.dev/cloudrun/container/hello"
  image_base        = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.images.repository_id}"
}

# ---------------------------------------------------------------------------
# api — min-instances=1, concurrency=80, Direct VPC egress, secrets como env var
# ---------------------------------------------------------------------------
resource "google_cloud_run_v2_service" "api" {
  name     = "api"
  location = var.region

  # Só a rede interna + o web/tasks (via IAM) chamam a api; sem acesso público direto.
  ingress = "INGRESS_TRAFFIC_INTERNAL_LOAD_BALANCER"

  template {
    service_account = google_service_account.sa["sa-api"].email

    scaling {
      min_instance_count = 1 # instância aquecida (spec: API aquecida)
      max_instance_count = var.api_max_instances
    }

    max_instance_request_concurrency = 80

    # Direct VPC egress para a subnet -> IP privado do Cloud SQL (D2).
    vpc_access {
      network_interfaces {
        network    = google_compute_network.vpc.id
        subnetwork = google_compute_subnetwork.subnet.id
      }
      egress = "PRIVATE_RANGES_ONLY"
    }

    containers {
      image = local.placeholder_image

      ports {
        container_port = 8080
      }

      # Pool de conexões (task 6.4): instâncias × pool < max_connections.
      env {
        name  = "DB_POOL_SIZE"
        value = tostring(var.api_pool_size)
      }
      env {
        name  = "DB_MAX_OVERFLOW"
        value = "0"
      }
      env {
        name  = "GCP_PROJECT_ID"
        value = var.project_id
      }
      env {
        name  = "TASKS_INVOKER_SA_EMAIL"
        value = google_service_account.sa["sa-tasks-invoker"].email
      }
      env {
        name  = "EMAIL_FROM"
        value = var.email_provider_from
      }

      # Segredos injetados como env var apontando para `latest` (D4).
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
        name = "JWT_SIGNING_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.secrets["jwt-signing-key"].secret_id
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

      startup_probe {
        http_get {
          path = "/health"
        }
        initial_delay_seconds = 5
        period_seconds        = 5
        failure_threshold     = 6
      }
    }
  }

  lifecycle {
    ignore_changes = [
      template[0].containers[0].image, # imagem gerida pelo pipeline
    ]
  }

  depends_on = [
    google_secret_manager_secret_iam_member.api_secrets,
    google_service_networking_connection.psa,
  ]
}

# ---------------------------------------------------------------------------
# web — min-instances configurável (0–1), público
# ---------------------------------------------------------------------------
resource "google_cloud_run_v2_service" "web" {
  name     = "web"
  location = var.region

  ingress = "INGRESS_TRAFFIC_ALL"

  template {
    service_account = google_service_account.sa["sa-web"].email

    scaling {
      min_instance_count = 0
      max_instance_count = 5
    }

    containers {
      image = local.placeholder_image
      ports {
        container_port = 8080
      }
      env {
        name  = "API_BASE_URL"
        value = google_cloud_run_v2_service.api.uri
      }
      startup_probe {
        http_get {
          path = "/api/health"
        }
        initial_delay_seconds = 5
        period_seconds        = 5
        failure_threshold     = 6
      }
    }
  }

  lifecycle {
    ignore_changes = [
      template[0].containers[0].image,
    ]
  }
}

# web é público (usuários acessam o front). O acesso à api é restrito por IAM.
resource "google_cloud_run_v2_service_iam_member" "web_public" {
  location = var.region
  name     = google_cloud_run_v2_service.web.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}
