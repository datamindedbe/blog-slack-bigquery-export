import base64
from unittest.mock import MagicMock

import pytest
from pytest import fixture

import main


# from main import handle_challenge, main

def test_main(fake_message, mock_bq):
    data = base64.b64encode(fake_message)
    result = main.main({'data': data}, None)
    assert mock_bq.insert_rows_json.call_count == 1
    pass


@fixture(autouse=True)
def mock_table_env(monkeypatch):
    monkeypatch.setattr(main, "BQ_DATASET", "slack_events")
    monkeypatch.setattr(main, "BQ_TABLE", "slack_raw_events")
    monkeypatch.setattr(main, "PROJECT_NAME", "slack-export-nonprod-1879")


@fixture()
def mock_bq(monkeypatch):
    monkeypatch.setattr(main, "BQ", MagicMock())
    main.BQ.insert_rows_json.return_value = []
    yield main.BQ


#@pytest.mark.skip
def test_run_from_local(fake_message):
    data = base64.b64encode(fake_message)
    main.main({'data': data}, None)


@fixture
def fake_message():
    return b'''
    {
  "token": "j5dzB8IU3eyInd9V4zjq2oVB",
  "team_id": "T051YCH9F",
  "api_app_id": "A016CFCGW94",
  "event": {
    "client_msg_id": "31a846a7-35c1-4056-bb1d-cac1affd231c",
    "type": "message",
    "text": ":grin:",
    "user": "UGALWDPJB",
    "ts": "1594070116.000600",
    "team": "T051YCH9F",
    "blocks": [
      {
        "type": "rich_text",
        "block_id": "b3DN",
        "elements": [
          {
            "type": "rich_text_section",
            "elements": [
              {
                "type": "emoji",
                "name": "grin"
              }
            ]
          }
        ]
      }
    ],
    "channel": "C016M323GDR",
    "event_ts": "1594070116.000600",
    "channel_type": "channel"
  },
  "type": "event_callback",
  "event_id": "Ev016TK3J3HA",
  "event_time": 1594070116,
  "authed_users": [
    "U016ZFB7X5F"
  ]
}
    '''
