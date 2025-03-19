name = "flask-app"
entrypoint = "bash"
run = ["bash", "flask-server.sh"]
persistent = true
onBoot = true