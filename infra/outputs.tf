output "api_url" {
  description = "URL do serviço Cloud Run api."
  value       = google_cloud_run_v2_service.api.uri
}

output "web_url" {
  description = "URL do serviço Cloud Run web."
  value       = google_cloud_run_v2_service.web.uri
}

output "artifact_registry" {
  description = "Caminho base do Artifact Registry para as imagens."
  value       = local.image_base
}

output "cloudsql_connection_name" {
  description = "Connection name da instância Cloud SQL."
  value       = google_sql_database_instance.postgres.connection_name
}

output "cloudsql_private_ip" {
  description = "IP privado da instância Cloud SQL."
  value       = google_sql_database_instance.postgres.private_ip_address
}

output "documentos_bucket" {
  description = "Nome do bucket de documentos."
  value       = google_storage_bucket.documentos.name
}

output "emails_queue" {
  description = "Fila Cloud Tasks de e-mails."
  value       = google_cloud_tasks_queue.emails.id
}

output "wif_provider" {
  description = "Nome do WIF provider (usar no google-github-actions/auth)."
  value       = google_iam_workload_identity_pool_provider.github.name
}

output "sa_deploy_email" {
  description = "E-mail da service account de deploy (assumida via WIF)."
  value       = google_service_account.sa["sa-deploy"].email
}

output "service_account_emails" {
  description = "E-mails de todas as service accounts."
  value       = { for k, sa in google_service_account.sa : k => sa.email }
}
