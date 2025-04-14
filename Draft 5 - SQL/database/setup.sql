-- database/setup.sql

CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY,
    full_name TEXT,
    email TEXT UNIQUE,
    role TEXT
);

CREATE TABLE IF NOT EXISTS residents (
    resident_id TEXT PRIMARY KEY,
    full_name TEXT,
    room TEXT
);

CREATE TABLE IF NOT EXISTS assignments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    staff_id TEXT,
    resident_id TEXT,
    access TEXT
);

CREATE TABLE IF NOT EXISTS care_plans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    resident_id TEXT,
    timestamp TEXT,
    assessment TEXT,
    diagnosis TEXT,
    goals TEXT,
    interventions TEXT,
    evaluation TEXT,
    filename TEXT
);

CREATE TABLE IF NOT EXISTS vitals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    resident_id TEXT,
    bp TEXT,
    temp TEXT,
    hr TEXT,
    timestamp TEXT
);

CREATE TABLE IF NOT EXISTS medications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    resident_id TEXT,
    name TEXT,
    dose TEXT,
    time TEXT,
    route TEXT,
    timestamp TEXT
);

CREATE TABLE IF NOT EXISTS files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    resident_id TEXT,
    filename TEXT,
    timestamp TEXT
);
