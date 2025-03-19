#!/bin/bash
export PYTHONPATH="./:$PYTHONPATH"
export PYTHONUNBUFFERED=1
export FLASK_APP=run.py
export FLASK_DEBUG=1

python run.py
