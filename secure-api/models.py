from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Patient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    condition = db.Column(db.String(100))

    def serialize(self):
        return {
            "id": self.id,
            "name": self.name,
            "condition": self.condition
        }
