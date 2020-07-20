resource "google_storage_bucket" "deployment_config" {
  bucket_policy_only = true
  force_destroy      = true
  name               = "deployment-config-${local.project}"
  requester_pays     = false
  storage_class      = "STANDARD"
}

resource "google_storage_bucket" "batch_import" {
  bucket_policy_only = true
  force_destroy      = true
  name               = "batch-import-${local.project}"
  requester_pays     = false
  storage_class      = "STANDARD"
}

resource "google_storage_bucket" "datastudio" {
  bucket_policy_only = true
  force_destroy      = true
  name               = "data-studio-import-${local.project}"
  requester_pays     = false
  storage_class      = "STANDARD"
}
