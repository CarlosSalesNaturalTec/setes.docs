variable "project_id" {
  type        = string
  description = "ID do projeto GCP único de produção do SETES.DOCS."
}

variable "org_id" {
  type        = string
  description = "ID da organização GCP (necessário para as org policies de governança)."
  default     = ""
}

variable "region" {
  type        = string
  description = "Região única de todos os recursos regionais (residência de dados no Brasil)."
  default     = "southamerica-east1"
}

variable "github_repository" {
  type        = string
  description = "Repositório GitHub autorizado no WIF, no formato 'org/repo'."
}

variable "db_tier" {
  type        = string
  description = "Tier da instância Cloud SQL (MVP: pequena)."
  default     = "db-custom-2-4096"
}

variable "db_max_connections" {
  type        = number
  description = "max_connections configurado na instância Cloud SQL (teto de conexões)."
  default     = 100
}

variable "api_max_instances" {
  type        = number
  description = "Teto de instâncias do Cloud Run api. instâncias × pool_size deve ficar < db_max_connections."
  default     = 10
}

variable "api_pool_size" {
  type        = number
  description = "Tamanho do pool de conexões por instância da api (deve casar com DB_POOL_SIZE do app)."
  default     = 5
}

variable "email_provider_from" {
  type        = string
  description = "Endereço remetente dos e-mails transacionais."
  default     = "no-reply@setes.docs"
}
