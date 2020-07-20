resource "google_cloudfunctions_function" "ingest" {
  name        = "ingest"
  description = "ingest endpoint for slack events API"
  runtime     = "python37"
  region      = local.region
  timeout     = 540

  service_account_email = google_service_account.ingest_service_account.email
  depends_on = [google_project_iam_member.ingest_function_roles]
  available_memory_mb   = 256
  source_archive_bucket = google_storage_bucket.deployment_config.name
  source_archive_object = google_storage_bucket_object.ingest_zip.name
  entry_point = "main"
  trigger_http = true
  environment_variables = {
    INGEST_PUBSUB_TOPIC = google_pubsub_topic.ingest_message.name
    INGEST_PUBSUB_PROJECT = local.project
    SLACK_SIGNING_SECRET = var.slack_signing_secret
  }
}

variable "slack_signing_secret" {}

output "ingest_endpoint" {
  value = google_cloudfunctions_function.ingest.https_trigger_url
}

data "archive_file" "ingest_zip" {
  type        = "zip"
  source_dir  = "${path.module}/../stream-ingest"
  output_path = local.ingest_zip_path
  excludes = [".pytest_cache/**"]
}

locals {
  ingest_zip_path = "${path.module}/../artifacts/ingest.zip"
}


resource "google_storage_bucket_object" "ingest_zip" {
  source = local.ingest_zip_path
  bucket = google_storage_bucket.deployment_config.name
  name   = "ingest-${data.archive_file.ingest_zip.output_md5}.zip"

  # archive must exist first
  depends_on = [data.archive_file.ingest_zip]
}

# --- service account ----
resource "google_service_account" "ingest_service_account" {
  project      = local.project
  account_id   = "ingest-function"
}

# Bind roles to service account
resource "google_project_iam_member" "ingest_function_roles" {
  for_each = toset([
    "roles/storage.objectAdmin",   # running the job
    "roles/pubsub.publisher",    # storing and fetching heatmaps
    "roles/logging.logWriter", # writing logs (to stackdriver),
  ])

  role    = each.value
  member  = "serviceAccount:${google_service_account.ingest_service_account.email}"
  project = local.project
}

resource "google_cloudfunctions_function_iam_binding" "function_invokers" {
  members = ["allUsers"]
  role = "roles/cloudfunctions.invoker"
  cloud_function = google_cloudfunctions_function.ingest.name
  region = local.region
  project = local.project
}
