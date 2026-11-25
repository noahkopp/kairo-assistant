#!/bin/bash
# Kairo's tool command (see kairo_tool.py). Runs from anywhere.
cd "$(dirname "$0")" && exec .venv/bin/python kairo_tool.py "$@"
