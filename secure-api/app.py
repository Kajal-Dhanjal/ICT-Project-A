from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
from auth import token_required, generate_token
from roles import roles
from models import db, Patient
from datetime import datetime

login_logs = []

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)
CORS(app)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/api/token/<username>")
def get_token(username):
    role = roles.get(username)
    if role:
        return jsonify({"token": generate_token(username, role)})
    return jsonify({"error": "Invalid user"}), 404

@app.route("/api/security/log", methods=["POST"])
@token_required()
def log_login():
    data = request.json
    timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    login_logs.append(f"{data['user']} logged in at {timestamp}")
    return jsonify({"message": "Logged"})

@app.route("/api/security/audit", methods=["GET"])
@token_required(role="admin")
def audit_logs():
    return jsonify({"logs": login_logs})

@app.route("/api/records", methods=["GET"])
@token_required()
def get_records():
    records = Patient.query.all()
    return jsonify([r.serialize() for r in records])

@app.route("/api/records", methods=["POST"])
@token_required(role="nurse")
def add_record():
    data = request.json
    patient = Patient(name=data["name"], condition=data["condition"])
    db.session.add(patient)
    db.session.commit()
    return jsonify({"message": "Patient added."}), 201

@app.route("/api/records/<int:id>", methods=["PUT"])
@token_required(role="nurse")
def update_record(id):
    data = request.json
    patient = Patient.query.get(id)
    if not patient:
        return jsonify({"error": "Patient not found"}), 404
    patient.name = data.get("name", patient.name)
    patient.condition = data.get("condition", patient.condition)
    db.session.commit()
    return jsonify({"message": "Patient updated."})

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
