# Fila Cloud Tasks `emails` (task 7.1, D6).
# maxAttempts=1 -> sem retry após falha (US 5.2 Cen.3). Rate limit protege o SaaS.
resource "google_cloud_tasks_queue" "emails" {
  name     = "emails"
  location = var.region

  rate_limits {
    max_dispatches_per_second = 5
    max_concurrent_dispatches = 5
  }

  retry_config {
    max_attempts = 1 # <- sem novas tentativas automáticas
  }

  depends_on = [google_project_service.enabled]
}
