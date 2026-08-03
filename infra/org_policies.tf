# Org policies de governança (tasks 2.3 e 2.4) — DESABILITADAS no MVP.
#
# constraints/gcp.resourceLocations e constraints/iam.disableServiceAccountKeyCreation
# exigem o papel roles/orgpolicy.policyAdmin, que só pode ser vinculado no nível de
# Organização/Pasta — nunca diretamente num projeto. O projeto `setes-docs` foi criado
# direto sob uma conta pessoal, sem Organização GCP (Cloud Identity/Workspace) por trás,
# então não existe recurso onde conceder esse papel. Confirmado via terraform apply e
# `gcloud org-policies set-policy` (erro: "Permission 'orgpolicy.policies.create' denied").
# Consequência prática para a migração de região (change migracao-regiao-us-central1,
# D2): não há policy ativa de localização a afrouxar — o `terraform apply` em
# us-central1 nunca esteve bloqueado por isso.
#
# Mitigações parciais já em vigor sem depender de org policy:
# - Cloud SQL: ipv4_enabled=false já bloqueia IP público diretamente (cloudsql.tf).
# - Storage: public_access_prevention=enforced já bloqueia acesso público (storage.tf).
# - Secret Manager: replicação user-managed já fixada em var.region (secrets.tf).
# - Todos os recursos são criados manualmente só em var.region (nenhum módulo usa
#   outra região) — a trava aqui é de processo/revisão, não de policy automática;
#   a região em si passou a ser escolha de custo, não de residência (D4).
#
# Revisitar se o projeto for movido para dentro de uma Organização GCP.

# resource "google_project_organization_policy" "resource_locations" {
#   project    = var.project_id
#   constraint = "constraints/gcp.resourceLocations"
#
#   list_policy {
#     allow {
#       values = [
#         "in:southamerica-east1-locations",
#       ]
#     }
#   }
#
#   depends_on = [google_project_service.enabled]
# }
#
# resource "google_project_organization_policy" "disable_sa_keys" {
#   project    = var.project_id
#   constraint = "constraints/iam.disableServiceAccountKeyCreation"
#
#   boolean_policy {
#     enforced = true
#   }
#
#   depends_on = [google_project_service.enabled]
# }
