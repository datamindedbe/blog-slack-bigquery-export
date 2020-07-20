# Slack export project

This project contains all the code needed to export slack messages (events) to BigQuery. It's made up of two core
 pipelines:
 
 1. Batch import of historical slack export as JSON files
    - ingest bucket
    - load function reacting to bucket events
 2. Streaming import based on the Slack Events API
    - Ingest function
    - ingest pubsub topic
    - load function

All infrastructure is defined as TF code in [infra](./infra). Unit tests are in the `test_...` files of each component. 


## Ingest
Taken inspration from [this video](https://fireship.io/lessons/how-to-build-a-slack-bot/)