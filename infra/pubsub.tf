
resource "google_pubsub_topic" "ingest_message" {
  name = "ingest.message"
}

//resource "google_pubsub_subscription" "ingest_processing_subscription" {
//  name = "${google_pubsub_topic.ingest_queue.name}.processing.subscription"
//  topic = google_pubsub_topic.ingest_queue.name
//}

# ---- channel_created
resource "google_pubsub_topic" "ingest_channel_created" {
  name = "ingest.channel_created"
}

//resource "google_pubsub_subscription" "ingest_processing_subscription" {
//  name = "${google_pubsub_topic.ingest_queue.name}.processing.subscription"
//  topic = google_pubsub_topic.ingest_queue.name
//}
# ---- batch load

resource "google_pubsub_topic" "batch_dlq" {
  name = "batch.dlq"
}

resource "google_pubsub_subscription" "dlq_processing" {
  name = "${google_pubsub_topic.batch_dlq.name}.processing.subscription"
  topic = google_pubsub_topic.batch_dlq.name
}
