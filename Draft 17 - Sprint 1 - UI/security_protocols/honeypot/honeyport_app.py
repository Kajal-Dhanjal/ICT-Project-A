from flask import Flask
from security_protocols.honeypot.honeypot_handler import honeypot

app = Flask(__name__, template_folder="hp_web_interfaces")
app.register_blueprint(honeypot)

if __name__ == "__main__":
    app.run(port=3000, debug=True)
