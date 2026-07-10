# IAM — 6 service accounts de menor privilégio (tasks 5.1–5.4, D10).
# Nenhum papel primitivo (Owner/Editor). Bindings no NÍVEL DO RECURSO.

# ---------------------------------------------------------------------------
# 5.1 — Service accounts
# ---------------------------------------------------------------------------
locals {
  service_accounts = {
    sa-web           = "SSR do web; invoca a api via OIDC"
    sa-api           = "backend FastAPI"
    sa-jobs          = "Cloud Run Jobs (manutenção/anonimização)"
    sa-scheduler     = "Cloud Scheduler; apenas dispara os jobs"
    sa-tasks-invoker = "Cloud Tasks; OIDC p/ endpoint interno da api"
    sa-deploy        = "CI/CD via WIF; build+deploy"
  }
}

resource "google_service_account" "sa" {
  for_each     = local.service_accounts
  account_id   = each.key
  display_name = each.value
}

# Atalhos de membro (iam member string).
locals {
  m = { for k, sa in google_service_account.sa : k => "serviceAccount:${sa.email}" }
}

# ---------------------------------------------------------------------------
# 5.2 — sa-api
# ---------------------------------------------------------------------------
resource "google_project_iam_member" "api_cloudsql_client" {
  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = local.m["sa-api"]
}

# secretAccessor POR segredo (db, jwt, sendgrid) — não no projeto.
resource "google_secret_manager_secret_iam_member" "api_secrets" {
  for_each  = toset(["db-password", "jwt-signing-key", "sendgrid-api-key"])
  secret_id = google_secret_manager_secret.secrets[each.value].id
  role      = "roles/secretmanager.secretAccessor"
  member    = local.m["sa-api"]
}

# storage.objectUser no bucket (leitura+escrita, sem DELETE administrativo).
resource "google_storage_bucket_iam_member" "api_bucket" {
  bucket = google_storage_bucket.documentos.name
  role   = "roles/storage.objectUser"
  member = local.m["sa-api"]
}

# cloudtasks.enqueuer na fila emails.
resource "google_cloud_tasks_queue_iam_member" "api_enqueue" {
  location = var.region
  name     = google_cloud_tasks_queue.emails.name
  role     = "roles/cloudtasks.enqueuer"
  member   = local.m["sa-api"]
}

# a api gera tokens OIDC para as tasks assumirem a sa-tasks-invoker no enqueue.
resource "google_service_account_iam_member" "api_actas_tasks_invoker" {
  service_account_id = google_service_account.sa["sa-tasks-invoker"].name
  role               = "roles/iam.serviceAccountUser"
  member             = local.m["sa-api"]
}

# ---------------------------------------------------------------------------
# 5.3 — sa-jobs (precisa de DELETE no bucket; sem ingress)
# ---------------------------------------------------------------------------
resource "google_project_iam_member" "jobs_cloudsql_client" {
  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = local.m["sa-jobs"]
}

resource "google_secret_manager_secret_iam_member" "jobs_secrets" {
  for_each  = toset(["db-password", "sendgrid-api-key"])
  secret_id = google_secret_manager_secret.secrets[each.value].id
  role      = "roles/secretmanager.secretAccessor"
  member    = local.m["sa-jobs"]
}

# storage.objectAdmin: purga física de documentos soft-deleted > 30d exige DELETE.
resource "google_storage_bucket_iam_member" "jobs_bucket" {
  bucket = google_storage_bucket.documentos.name
  role   = "roles/storage.objectAdmin"
  member = local.m["sa-jobs"]
}

# ---------------------------------------------------------------------------
# 5.4 — sa-web, sa-scheduler, sa-tasks-invoker, sa-deploy
# ---------------------------------------------------------------------------
# sa-web -> run.invoker na api (chamada SSR OIDC).
resource "google_cloud_run_v2_service_iam_member" "web_invokes_api" {
  location = var.region
  name     = google_cloud_run_v2_service.api.name
  role     = "roles/run.invoker"
  member   = local.m["sa-web"]
}

# sa-tasks-invoker -> run.invoker na api (endpoint interno).
resource "google_cloud_run_v2_service_iam_member" "tasks_invokes_api" {
  location = var.region
  name     = google_cloud_run_v2_service.api.name
  role     = "roles/run.invoker"
  member   = local.m["sa-tasks-invoker"]
}

# sa-scheduler -> run.invoker NOS jobs (execução). Concedido por job em jobs_scheduler.tf.

# sa-deploy -> artifactregistry.writer, run.admin, iam.serviceAccountUser.
resource "google_project_iam_member" "deploy_ar_writer" {
  project = var.project_id
  role    = "roles/artifactregistry.writer"
  member  = local.m["sa-deploy"]
}

resource "google_project_iam_member" "deploy_run_admin" {
  project = var.project_id
  role    = "roles/run.admin"
  member  = local.m["sa-deploy"]
}

# Necessário para o deploy "agir como" as SAs de runtime (web/api/jobs).
resource "google_project_iam_member" "deploy_sa_user" {
  project = var.project_id
  role    = "roles/iam.serviceAccountUser"
  member  = local.m["sa-deploy"]
}
