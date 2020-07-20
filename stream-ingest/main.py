import hashlib
import hmac
import json
import logging
import os
from time import time, sleep
from traceback import print_exc, format_exc
from typing import Dict

from flask import Response, Request, jsonify
from flask import request
from google.cloud import pubsub_v1

TOPIC = os.environ.get("INGEST_PUBSUB_TOPIC")
PROJECT_NAME = os.environ.get("INGEST_PUBSUB_PROJECT")
TOPIC_PATH = f"projects/{PROJECT_NAME}/topics/{TOPIC}"
SLACK_SIGNING_SECRET = os.environ.get("SLACK_SIGNING_SECRET")

pubsub_publisher = pubsub_v1.PublisherClient()


# see https://issuetracker.google.com/issues/155215191
# if errors occur, it's a bitch!
def main(request: Request) -> Response:
    if request.json and request.json.get("challenge"):
        return handle_challenge(request)
    if SLACK_SIGNING_SECRET is not None and not verify_message(request):
        logging.error(request.body)
        logging.error(request.headers)
        return jsonify({"error": "signature invalid"}, status=403)
    return handle_message_body(request.json)


def handle_challenge(request: Request) -> Response:
    challenge = request.json.get("challenge")
    logging.info(f"handling challenge with {challenge}")
    return jsonify({"challenge": challenge})


def handle_message_body(data: Dict):
    try:
        pubsub_publisher.publish(TOPIC_PATH, str.encode(json.dumps(data)))
        return Response(status=200)
    except Exception as e:
        return jsonify({"error": e}, status=500)


def verify_message(request: Request) -> bool:
    # taken from slackeventsapi library. See their server.py
    # Each request comes with request timestamp and request signature
    # emit an error if the timestamp is out of range
    try:
        req_timestamp = request.headers.get("X-Slack-Request-Timestamp")
        if abs(time() - int(req_timestamp)) > 60 * 5:
            raise Exception("bad timestamp")
        # Verify the request signature using the app's signing secret
        # emit an error if the signature can't be verified
        req_signature = request.headers.get("X-Slack-Signature")
        return verify_signature(req_timestamp, req_signature)
    except Exception as e:
        logging.warning(e)
        logging.warning(format_exc())
        return False


def verify_signature(timestamp, signature):
    """
    Taken from slackeventsapi library
    :param timestamp:
    :param signature:
    :return:
    """
    req = str.encode("v0:" + str(timestamp) + ":") + request.get_data()
    request_hash = (
        "v0="
        + hmac.new(str.encode(SLACK_SIGNING_SECRET), req, hashlib.sha256).hexdigest()
    )
    return hmac.compare_digest(request_hash, signature)
