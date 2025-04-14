# security_protocols/database/db_handler.py

from datetime import datetime

# Simulated in-memory storage
care_plans_db = {}
vitals_db = {}
medications_db = {}
files_db = {}

def get_resident_by_id(resident_id):
    # Simulated resident lookup
    return {"id": resident_id, "full_name": "John", "room": "101"}

def get_care_plans(resident_id):
    return care_plans_db.get(resident_id, [])

def get_vitals(resident_id):
    return vitals_db.get(resident_id, [])

def get_medications(resident_id):
    return medications_db.get(resident_id, [])

def get_files(resident_id):
    return files_db.get(resident_id, [])

def save_care_entry(resident_id, assessment, diagnosis, goals, interventions, evaluation, filename=None):
    entry = {
        "id": len(care_plans_db.get(resident_id, [])) + 1,
        "timestamp": datetime.now(),
        "assessment": assessment,
        "diagnosis": diagnosis,
        "goals": goals,
        "interventions": interventions,
        "evaluation": evaluation,
        "filename": filename
    }
    care_plans_db.setdefault(resident_id, []).append(entry)

    if filename:
        files_db.setdefault(resident_id, []).append({
            "filename": filename,
            "timestamp": datetime.now()
        })

def save_vitals(resident_id, bp, temp, hr):
    vitals_db.setdefault(resident_id, []).append({
        "bp": bp,
        "temp": temp,
        "hr": hr,
        "timestamp": datetime.now()
    })

def save_medication(resident_id, name, dose, time, route):
    medications_db.setdefault(resident_id, []).append({
        "name": name,
        "dose": dose,
        "time": time,
        "route": route,
        "timestamp": datetime.now()
    })
