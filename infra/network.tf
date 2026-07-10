# VPC/subnet + Private Service Access para Cloud SQL (task 3.1).
resource "google_compute_network" "vpc" {
  name                    = "setes-vpc"
  auto_create_subnetworks = false
  depends_on              = [google_project_service.enabled]
}

resource "google_compute_subnetwork" "subnet" {
  name          = "setes-subnet"
  ip_cidr_range = "10.10.0.0/24"
  region        = var.region
  network       = google_compute_network.vpc.id

  # Necessário para Direct VPC egress do Cloud Run (acesso privado ao Google/DB).
  private_ip_google_access = true
}

# Faixa reservada para o peering do Private Service Access (Cloud SQL IP privado).
resource "google_compute_global_address" "psa_range" {
  name          = "setes-psa-range"
  purpose       = "VPC_PEERING"
  address_type  = "INTERNAL"
  prefix_length = 16
  network       = google_compute_network.vpc.id
}

# Conexão de serviço privado: liga a VPC ao servicenetworking (onde o Cloud SQL
# aloca o IP privado da instância).
resource "google_service_networking_connection" "psa" {
  network                 = google_compute_network.vpc.id
  service                 = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [google_compute_global_address.psa_range.name]
}
