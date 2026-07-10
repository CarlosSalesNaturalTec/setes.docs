# Org policies de governança (tasks 2.3 e 2.4).
# Aplicadas no NÍVEL DO PROJETO (project-level org policy). Requer papel
# roles/orgpolicy.policyAdmin no projeto (ou na org).

# 2.3 — Trava a região: nenhum recurso pode ser criado fora do Brasil.
# in:southamerica-east1-locations é o "value group" que engloba a região e
# suas zonas. Multirregião/global legítimos (ex.: Artifact Registry global) são
# adicionados ao allow abaixo se necessário (mitigação do risco no design).
resource "google_project_organization_policy" "resource_locations" {
  project    = var.project_id
  constraint = "constraints/gcp.resourceLocations"

  list_policy {
    allow {
      values = [
        "in:southamerica-east1-locations",
      ]
    }
  }

  depends_on = [google_project_service.enabled]
}

# 2.4 — Proíbe a criação de chaves JSON de service account (força WIF).
resource "google_project_organization_policy" "disable_sa_keys" {
  project    = var.project_id
  constraint = "constraints/iam.disableServiceAccountKeyCreation"

  boolean_policy {
    enforced = true
  }

  depends_on = [google_project_service.enabled]
}
