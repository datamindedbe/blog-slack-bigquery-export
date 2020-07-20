#!/usr/bin/env bash
export BQ_DATASET=slack_events
export PROJECT_NAME=slack-export-nonprod-1879
export BQ_TABLE=slack_raw_events
python main.py
