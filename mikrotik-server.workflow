name = "mikrotik-server"
entrypoint = "bash"
persistent = true
onBoot = true

[nix]
channel = "stable-23_05"

[deployment]
deploymentTarget = "cloudrun"
run = ["bash", "mikrotik-server.sh"]

[env]
PYTHONPATH = "."
PYTHONUNBUFFERED = "1"

[languages]
python = "python3"