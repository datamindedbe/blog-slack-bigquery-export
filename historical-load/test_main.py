import json
from unittest.mock import MagicMock

from pytest import fixture

import main


def test_get_channel_from_blob_name():
    name = main.get_channel_from_blob_name("root/channel/2015-05-01.json")
    assert name == "channel"
    name = main.get_channel_from_blob_name("asdf/root/moo/2015-05-01.json")
    assert name == "moo"
    name = main.get_channel_from_blob_name("root/d/2015-05-01.json")
    assert name == "d"


def test_load_file(mocked_gcs, test_file):
    event = {
        "bucket": "batch-import-slack-export-nonprod-1879",
        "name": "google-cloud/2020-06-24.json",
        "foo": "bar",
    }
    # when calling the GCS API, we expect data to come back in a certain way
    channel, data = main.load_file(**event)
    assert data is not None
    assert len(data) == 4  # messages that day


def test_clear_unwanted_keys():
    input = {
        "keep": "foo",
        "icons": "foo",
        "bot_profile": "foo",
        "attachments": "foo",
        "file": "foo",
        "files": "foo",
        "root": "foo",
        "blocks": "foo"
    }
    output = main.clear_unwanted_keys([input])[0]

    assert "keep" in output
    assert "icons" not in output
    assert "bot_profile" not in output
    assert "attachments" not in output
    assert "file" not in output


def test_recursive_ts_conversion():
    input = """
{
    "ts": "1590101824.000000",
    "one": {
        "user": "U34QP5ZHN",
        "ts": "1590101824.000000"
    },
    "list": [{
        "user": "U34QP5ZHN",
        "ts": "1590101824.000000"
    }],
    "one": {
        "two": {
            "ts": "1590101824.000000"
        }
    }
}
"""
    result = main.recursive_ts_conversion(json.loads(input))
    result_json = json.dumps(result)
    assert (
            result_json
            == '{"ts": "2020-05-21T22:57:04", "one": {"two": {"ts": "2020-05-21T22:57:04"}}, "list": [{"user": "U34QP5ZHN", "ts": "2020-05-21T22:57:04"}]}'
    )


@fixture()
def test_table_env(monkeypatch):
    monkeypatch.setattr(main, "BQ_DATASET", "slack_events")
    monkeypatch.setattr(main, "BQ_TABLE", "slack_raw_events")
    monkeypatch.setattr(main, "PROJECT_NAME", "slack-export-nonprod-1879")


@fixture()
def mocked_gcs(test_file, monkeypatch):
    with monkeypatch.context() as ctx:
        mm = MagicMock()
        monkeypatch.setattr(main, "CS", mm)
        mm.return_value.get_bucket.return_value.blob.return_value.download_as_string.return_value = (
            test_file
        )
        yield mm


@fixture
def test_file():
    with open("test/sample_messages.json") as f:
        yield f.read()
