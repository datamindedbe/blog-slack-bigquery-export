import json
import logging
import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

from google.cloud import bigquery, storage
from google.cloud.bigquery import (
    TableReference,
    DatasetReference,
    LoadJob,
    job,
)

PROJECT_NAME = os.environ.get("PROJECT_NAME")
BQ_DATASET = os.environ.get("BQ_DATASET")
BQ_TABLE = os.environ.get("BQ_TABLE")
BQ = lambda: bigquery.Client()
CS = lambda: storage.Client()


def main(data, context):
    """Background Cloud Function to be triggered by Cloud Storage.
       This generic function logs relevant data when a file is changed.

    Args:
        data (dict): The Cloud Functions event payload.
        context (google.cloud.functions.Context): Metadata of triggering event.
    Returns:
        None; the output is written to Stackdriver Logging
    """
    channel, messages = load_file(**data)
    messages = process_messages(messages, channel)
    path = write_dicts_to_json_file(messages)
    write_to_table_from_json_file(path)


def assign_channel(messages: List[Dict], channel: str) -> List[Dict]:
    for message in messages:
        message["channel"] = channel
    return messages


def process_messages(messages: List[Dict], channel: str)-> List[Dict]:
    messages = parse_ts(messages)
    messages = clear_unwanted_keys(messages)
    messages = assign_channel(messages, channel)
    return messages


def clear_unwanted_keys(messages):
    unwanted_keys = ["icons", "bot_profile", "attachments", "file", "files", "root", "blocks", "room"]

    def clear_from_keys(msg):
        for k in unwanted_keys:
            if k in msg:
                del msg[k]
        return msg

    return [clear_from_keys(msg) for msg in messages]


def get_channel_from_blob_name(name) -> str:
    return name.split("/")[-2]


def load_file(bucket, name, **kwargs) -> Tuple[str, List[Dict]]:
    blob = CS().get_bucket(bucket).blob(name)
    channel = get_channel_from_blob_name(name)

    return (channel, json.loads(blob.download_as_string()))


def parse_ts(messages: List[Dict]) -> List[Dict]:
    return [recursive_ts_conversion(msg) for msg in messages]


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



def write_dicts_to_json_file(records) -> Path:
    tmpfd, tmppath = tempfile.mkstemp(suffix=".json")
    os.close(tmpfd)
    print(tmppath)
    with open(tmppath, "w") as f:
        for record in records:
            f.write(f"{json.dumps(record)}\n")
    return Path(tmppath)


def write_to_table_from_json_file(path: Path) -> LoadJob:
    table = TableReference(DatasetReference(PROJECT_NAME, BQ_DATASET), BQ_TABLE)
    bq = BQ()
    job_config = job.LoadJobConfig()
    # job_config.autodetect = True
    job_config.source_format = job.SourceFormat.NEWLINE_DELIMITED_JSON
    job_config.write_disposition = job.WriteDisposition.WRITE_APPEND
    job_config.create_disposition = job.CreateDisposition.CREATE_NEVER

    try:
        with path.open("rb") as f:
            load_job: LoadJob = bq.load_table_from_file(
                f, destination=table, job_config=job_config
            )
            load_job.result()
        os.remove(str(path))
        logging.info(f"{load_job.job_id} completed at {load_job.ended}")
    except Exception as ex:
        logging.info(f"{load_job.job_id} crashed with {load_job.errors}")

    return load_job


# ----- used for local testing -----

def main_local():
    with open("test/sample_messages.json") as f:
        messages = json.load(f)
    messages = process_messages(messages)
    path = write_dicts_to_json_file(messages)
    write_to_table_from_json_file(path)


if __name__ == "__main__":
    logging.getLogger().setLevel(logging.INFO)
    main_local()
