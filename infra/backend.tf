# State remoto em bucket GCS versionado (task 2.1).
# O bucket é criado FORA deste apply (bootstrap manual), pois o backend precisa
# existir antes do `terraform init`. Ver infra/README.md ("Bootstrap do state").
#
# Inicialização:
#   terraform init -backend-config=backend.hcl
# onde backend.hcl define: bucket = "<seu-bucket-de-state>"
terraform {
  backend "gcs" {
    prefix = "bootstrap-infraestrutura"
    # bucket é fornecido via -backend-config (backend.hcl) para não fixar o nome no VCS.
  }
}
