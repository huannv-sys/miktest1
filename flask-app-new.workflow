run = ["python3", "simple_flask_server.py"]
language = "python3"
entrypoint = "simple_flask_server.py"
persistent = true
onBoot = true
name = "flask-app-new"

[env]
PYTHONPATH = "."
PYTHONUNBUFFERED = "1"