# Artifact Registry para as imagens web/api (task 6.1). Regional (var.region).
resource "google_artifact_registry_repository" "images" {
  location      = var.region
  repository_id = "setes-images"
  format        = "DOCKER"
  description   = "Imagens de contêiner do SETES.DOCS (web/api/jobs)."

  depends_on = [google_project_service.enabled]
}
