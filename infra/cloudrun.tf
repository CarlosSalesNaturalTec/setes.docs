# Cloud Run — serviços api e web (tasks 6.2, 6.3, 6.4).
#
# Nota: a imagem inicial usa um placeholder público; o deploy real de cada revisão
# é feito pelo pipeline (gcloud run deploy). ignore_changes no image evita que o
# Terraform reverta a imagem publicada pelo CD.

locals {
  # Placeholder até o primeiro deploy do pipeline.
  placeholder_image = "us-docker.pkg.dev/cloudrun/container/hello"
  image_base        = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.images.repository_id}"
  # Audience OIDC dos endpoints internos (task 7.2). PRECISA ser a URL canônica
  # do próprio serviço `api` -- o Cloud Run, no nível de plataforma (antes do
  # request chegar no container), já exige que o `aud` do token OIDC bata com
  # essa URL para autorizar a invocação (serviço não é --allow-unauthenticated);
  # uma string customizada é rejeitada ali, antes até de app/security/oidc.py
  # rodar. Não dá pra referenciar `google_cloud_run_v2_service.api.uri` aqui
  # (self-reference), então fixamos o valor observado via `terraform output
  # api_url` -- estável entre applies (hash determinístico por projeto/serviço/
  # região). Se o serviço for recriado do zero, atualizar este valor.
  oidc_audience = "https://api-2j5ojmtaiq-rj.a.run.app"
  # Origem pública do `web`, usada pela api para autorizar CORS (browser chama
  # a api diretamente -- expor-api-e-configurar-api-url-web). Mesma razão de
  # `oidc_audience` acima: referenciar `google_cloud_run_v2_service.web.uri`
  # aqui criaria dependência circular (web já referencia `api.uri` em
  # API_BASE_URL), então fixamos o valor observado via `terraform output
  # web_url` -- estável entre applies. Se o serviço `web` for recriado do
  # zero, atualizar este valor junto com `oidc_audience`.
  web_url = "https://web-2j5ojmtaiq-rj.a.run.app"
}

# ---------------------------------------------------------------------------
# api — min-instances=0 (MVP: custo zero em ocioso), concurrency=80,
# Direct VPC egress, secrets como env var
# ---------------------------------------------------------------------------
resource "google_cloud_run_v2_service" "api" {
  name     = "api"
  location = var.region

  # Descarte integral autorizado para a migração de região (D1/D5).
  deletion_protection = false

  # Browser do usuário chama a api diretamente; autorização real fica na aplicação
  # (JWT próprio) -- ver google_cloud_run_v2_service_iam_member.api_public abaixo.
  ingress = "INGRESS_TRAFFIC_ALL"

  template {
    service_account = google_service_account.sa["sa-api"].email

    scaling {
      min_instance_count = 0 # MVP: sem instância aquecida (custo zero em ocioso)
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
      # Audience esperada no token OIDC do endpoint /internal/tasks/* (task 7.2).
      # String fixa, não a URL do serviço (evita self-reference no Terraform e
      # fica estável mesmo se a URL do Cloud Run mudar). Quem enfileira a tarefa
      # no Cloud Tasks deve setar o mesmo valor em oidc_token.audience.
      env {
        name  = "OIDC_AUDIENCE"
        value = local.oidc_audience
      }
      env {
        name  = "EMAIL_FROM"
        value = var.email_provider_from
      }
      # Base dos links enviados por e-mail (primeiro acesso, recuperação de
      # senha, reset por Admin, link direto para processo). SEM isso a app cai
      # no default `http://localhost:3000` (app/config.py) e todos os links de
      # e-mail saem quebrados em produção. Aponta para o próprio serviço `web`.
      env {
        name  = "FRONTEND_BASE_URL"
        value = local.web_url
      }
      # Browser do usuário (origem do `web`) chama a api diretamente -- sem essa
      # allow-list, o browser recebe "Disallowed CORS origin" mesmo com o
      # ingress público (app/config.py:75 default é só localhost:3000).
      env {
        name  = "CORS_ALLOWED_ORIGINS"
        value = local.web_url
      }

      # Conexão com o Cloud SQL: peças simples + senha do secret (D4). A app monta
      # a URL completa (app/config.py) — DATABASE_URL sozinho não existe, pois o
      # secret db-password guarda só a senha, não uma URL de conexão.
      env {
        name  = "DB_HOST"
        value = google_sql_database_instance.postgres.private_ip_address
      }
      env {
        name  = "DB_PORT"
        value = "5432"
      }
      env {
        name  = "DB_USER"
        value = google_sql_user.app.name
      }
      env {
        name  = "DB_NAME"
        value = google_sql_database.app.name
      }
      env {
        name = "DB_PASSWORD"
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

# api é chamada diretamente pelo browser do usuário (sem BFF/proxy). Isso é o
# análogo do --allow-unauthenticated: remove a exigência de token OIDC/IAM do
# Cloud Run, mas não abre mão de nenhuma autorização de negócio -- essa
# continua inteiramente na aplicação (JWT, require_perfil/require_acesso_unidade,
# rate limiting slowapi, log_seguranca de acesso negado).
resource "google_cloud_run_v2_service_iam_member" "api_public" {
  location = var.region
  name     = google_cloud_run_v2_service.api.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# ---------------------------------------------------------------------------
# web — min-instances configurável (0–1), público
# ---------------------------------------------------------------------------
resource "google_cloud_run_v2_service" "web" {
  name     = "web"
  location = var.region

  # Descarte integral autorizado para a migração de região (D1/D5).
  deletion_protection = false

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
