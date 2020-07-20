resource "google_cloudfunctions_function" "stream_load" {
  name        = "stream_load"
  description = "load slack events raw JSON into BigQuery"
  runtime     = "python37"
  region      = local.region
  timeout     = 540

  service_account_email = google_service_account.stream_load_service_account.email
  depends_on = [google_project_iam_member.stream_load_function_roles]
  available_memory_mb   = 256
  source_archive_bucket = google_storage_bucket.deployment_config.name
  source_archive_object = google_storage_bucket_object.stream_load_zip.name
  entry_point = "main"
  event_trigger {
    event_type = "google.pubsub.topic.publish"
    resource = google_pubsub_topic.ingest_message.id # 'projects/foo/topic/bar' notation
  }
  environment_variables = {
    INGEST_PUBSUB_TOPIC = google_pubsub_topic.ingest_message.name
    PROJECT_NAME = local.project
    BQ_DATASET = google_bigquery_dataset.events_dataset.dataset_id
    BQ_TABLE = google_bigquery_table.raw_events_table.table_id
  }
}


data "archive_file" "stream_load_zip" {
  type        = "zip"
  source_dir  = "${path.module}/../stream-load"
  output_path = local.stream_load_zip_path
  excludes = [".pytest_cache/**"]
}

locals {
  stream_load_zip_path = "${path.module}/../artifacts/stream_load.zip"
}


resource "google_storage_bucket_object" "stream_load_zip" {
  source = local.stream_load_zip_path
  bucket = google_storage_bucket.deployment_config.name
  name   = "stream-load-${data.archive_file.stream_load_zip.output_md5}.zip"

  # archive must exist first
  depends_on = [data.archive_file.stream_load_zip]
}

# --- service account ----
resource "google_service_account" "stream_load_service_account" {
  project      = local.project
  account_id   = "stream-load-function"
}

# Bind roles to service account
resource "google_project_iam_member" "stream_load_function_roles" {
  for_each = toset([
    "roles/storage.objectAdmin",   # running the job
    "roles/logging.logWriter", # writing logs (to stackdriver),
    "roles/bigquery.dataEditor" #should be more fine-grained but ... meh
  ])

  role    = each.value
  member  = "serviceAccount:${google_service_account.stream_load_service_account.email}"
  project = local.project
}

