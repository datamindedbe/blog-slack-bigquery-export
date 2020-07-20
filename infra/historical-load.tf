resource "google_cloudfunctions_function" "historical_load" {
  name        = "historical_load"
  description = "load slack events raw JSON into BigQuery"
  runtime     = "python37"
  region      = local.region
  timeout     = 540

  service_account_email = google_service_account.historical_load_service_account.email
  depends_on = [google_project_iam_member.historical_load_function_roles]
  available_memory_mb   = 256
  source_archive_bucket = google_storage_bucket.deployment_config.name
  source_archive_object = google_storage_bucket_object.historical_load_zip.name
  entry_point = "main"
  event_trigger {
    event_type = "google.storage.object.finalize"
    resource = google_storage_bucket.batch_import.name
  }
  environment_variables = {
    BQ_DATASET = google_bigquery_dataset.events_dataset.dataset_id
    PROJECT_NAME = local.project
    BQ_TABLE = google_bigquery_table.raw_events_table.table_id
  }
}


data "archive_file" "historical_load_zip" {
  type        = "zip"
  source_dir  = "${path.module}/../historical-load"
  output_path = local.historical_load_zip_path
  excludes = [".pytest_cache/**"]
}

locals {
  historical_load_zip_path = "${path.module}/../artifacts/historical_load.zip"
}


resource "google_storage_bucket_object" "historical_load_zip" {
  source = local.historical_load_zip_path
  bucket = google_storage_bucket.deployment_config.name
  name   = "historical-load-${data.archive_file.historical_load_zip.output_md5}.zip"

  # archive must exist first
  depends_on = [data.archive_file.historical_load_zip]
}

# --- service account ----
resource "google_service_account" "historical_load_service_account" {
  project      = local.project
  account_id   = "historical-load-function"
}

# Bind roles to service account
resource "google_project_iam_member" "historical_load_function_roles" {
  for_each = toset([
    "roles/logging.logWriter", # writing logs (to stackdriver),
    "roles/bigquery.dataEditor", #should be more fine-grained but ... meh,
  ])

  role    = each.value
  member  = "serviceAccount:${google_service_account.historical_load_service_account.email}"
  project = local.project
}

resource "google_project_iam_member" "historical_load_custom_role_binding" {
  role = google_project_iam_custom_role.historical_load_custom_role.name
  member  = "serviceAccount:${google_service_account.historical_load_service_account.email}"
}

resource "google_project_iam_custom_role" "historical_load_custom_role" {
  role_id     = replace("${google_service_account.historical_load_service_account.account_id}-role", "-", "_")
  title       = ""
  description = ""
  permissions = ["storage.buckets.get", "storage.objects.get", "storage.objects.list", "bigquery.jobs.create"]
}
