[workflow]
name = "Flask App"
description = "Run the Flask server for MikroTik Monitor"
command = "python app.py"
always = false
persistent = true
[workflow.port]
from = 5000
to = 80