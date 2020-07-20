resource "google_bigquery_dataset" "events_dataset" {
  dataset_id                  = "slack_events"
  friendly_name               = "slack events"
  description                 = "A dataset containing all slack events from Data Minded"
  location                    = "EU"
}

resource "google_bigquery_table" "raw_events_table" {
  dataset_id = google_bigquery_dataset.events_dataset.dataset_id
  table_id   = "slack_raw_events"

  time_partitioning {
    type = "DAY"
    field = "ts"
  }

  # generated with https://pypi.org/project/bigquery-schema-generator/
  # on a merged JSON file of a few thousand messages to make sure we catch all properties as well as their documented
  # structure
  # in the pipeline, we convert the ts parameter to a date though for partitioning purposes
  schema = file("schema.json")

}

resource "google_bigquery_dataset" "slack_metadata" {
  dataset_id                  = "slack_metadata"
  friendly_name               = "slack metadata"
  description                 = "A dataset containing slack metadata such as users or channels"
  location                    = "EU"
}

resource "google_bigquery_table" "slack_channels" {
  dataset_id = google_bigquery_dataset.slack_metadata.dataset_id
  table_id   = "slack_channels"
}

resource "google_bigquery_table" "slack_users" {
  dataset_id = google_bigquery_dataset.slack_metadata.dataset_id
  table_id   = "slack_users"
}
