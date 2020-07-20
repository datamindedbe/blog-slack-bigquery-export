import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from google.api_core import retry
from google.cloud import bigquery
from google.cloud.bigquery import (
    TableReference,
    DatasetReference,
    LoadJob,
    job,
)

from flask import Response, Request

TOPIC = os.environ.get("INGEST_PUBSUB_TOPIC")
PROJECT_NAME = os.environ.get("PROJECT_NAME")
TOPIC_PATH = f"projects/{PROJECT_NAME}/topics/{TOPIC}"

BQ_DATASET = os.environ.get("BQ_DATASET")
BQ_TABLE = os.environ.get("BQ_TABLE")
BQ = bigquery.Client()

unwanted_keys = ["channel_type", "event_ts", "icons", "bot_profile", "attachments", "file", "files", "root", "blocks",
                 "room"]


# Heavy inspiration taken from
# https://github.com/GoogleCloudPlatform/solutions-gcs-bq-streaming-functions-python/blob/master/functions/streaming/main.py

def main(event, context):
    """Background Cloud Function to be triggered by Pub/Sub.
        Args:
             event (dict):  The dictionary with data specific to this type of
             event. The `data` field contains the PubsubMessage message. The
             `attributes` field will contain custom attributes if there are any.
             context (google.cloud.functions.Context): The Cloud Functions event
             metadata. The `event_id` field contains the Pub/Sub message ID. The
             `timestamp` field contains the publish time.
        """
    import base64

    if 'data' in event:
        row = base64.b64decode(event['data']).decode('utf-8')
        message = json.loads(row).get("event")
        message = process_message(message)
        stream_to_bq(message)
    else:
        raise Exception("missing data in event")


def stream_to_bq(row):
    ds = bigquery.dataset.DatasetReference(PROJECT_NAME, BQ_DATASET)
    table = bigquery.table.TableReference(ds, BQ_TABLE)
    errors = BQ.insert_rows_json(table,
                                 json_rows=[row],
                                 retry=retry.Retry(deadline=30))
    if errors != []:
        raise BigQueryError(errors)


def process_message(messages: Dict) -> Dict:
    messages = recursive_ts_conversion(messages)
    messages = clear_unwanted_keys(messages)
    return messages


def clear_unwanted_keys(msg: Dict) -> Dict:
    for k in unwanted_keys:
        if k in msg:
            del msg[k]
    return msg


def convert_ts_to_iso(ts) -> str:
    ts = ts.split(".")[0]  # get only second precision of ts
    return datetime.utcfromtimestamp(int(ts)).isoformat()


def recursive_ts_conversion(message: Dict) -> Dict:
    if not isinstance(message, dict):
        return message
    for k, v in message.items():
        if isinstance(v, dict):
            message[k] = recursive_ts_conversion(v)
        elif isinstance(v, list):
            message[k] = [recursive_ts_conversion(el) for el in v]
        elif k == "ts":
            message[k] = convert_ts_to_iso(v)
        else:
            # ignore other properties
            pass
    return message


class BigQueryError(Exception):
    '''Exception raised whenever a BigQuery error happened''' 

    def __init__(self, errors):
        super().__init__(self._format(errors))
        self.errors = errors

    def _format(self, errors):
        err = []
        for error in errors:
            err.extend(error['errors'])
        return json.dumps(err)
