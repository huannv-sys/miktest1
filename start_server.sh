#!/bin/bash
export PYTHONPATH="."
export FLASK_APP="run.py"
export FLASK_DEBUG=1

# Khởi động Flask với Gunicorn
gunicorn -b 0.0.0.0:5000 run:app