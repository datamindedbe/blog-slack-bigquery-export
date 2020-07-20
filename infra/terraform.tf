provider "google" {
  project     = local.project
  region      = "europe-west1"
}
provider "google-beta" {
  project     = local.project
  region      = "europe-west1"
}

locals {
  project = "slack-export-nonprod-1879"
  region  = "europe-west1"
}

//uncomment after initial apply
terraform {
  backend "gcs" {
    bucket = "deployment-config-slack-export-nonprod-1879"
    prefix = "infrastructure/terraform/state.tfstate"
  }
}


