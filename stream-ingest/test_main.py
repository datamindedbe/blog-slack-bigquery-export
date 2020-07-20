import json
from unittest.mock import MagicMock, call

from flask import Flask
from pytest import fixture

import main
#from main import handle_challenge, main


def test_handle_challenge(app: Flask):
    data = {
        "token": "Jhj5dZrVaK7ZwHHjRyZWjbDl",
        "challenge": "3eZbrw1aBm2rZgRNFdxV2595E9CY3gmdALWMmHkvFXO7tYXAYM8P",
        "type": "url_verification",
    }
    with app.test_request_context(json=data) as context:
        assert context.request.json is not None
        response = main.handle_challenge(context.request)
        print(response)
        assert response is not None
        assert response.json.get("challenge") == data["challenge"]

def test_calls_pubsub(app: Flask, mock_publisher):
    data = {"foo": "bar"}
    with app.test_request_context(json=data) as context:
        main.main(context.request)
        assert mock_publisher.publish.call_count == 1
        assert call('projects/None/topics/None', str.encode(json.dumps(data))) == mock_publisher.publish.call_args


@fixture(autouse=True)
def mock_publisher(monkeypatch):
    import main
    monkeypatch.setattr(main, 'pubsub_publisher', MagicMock())
    assert isinstance(main.pubsub_publisher, MagicMock)
    return main.pubsub_publisher


@fixture()
def app():
    app = Flask(__name__)
    return app
