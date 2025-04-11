-- Créer la base de données pour les utilisateurs
CREATE DATABASE IF NOT EXISTS user_database;

USE user_database;

CREATE TABLE IF NOT EXISTS patients (
    id VARCHAR(36) PRIMARY KEY,
    doctor_id VARCHAR(36) NOT NULL,
    name VARCHAR(255) NOT NULL,
    date_of_birth DATE NOT NULL,
    medical_record_number VARCHAR(50) NOT NULL
);




CREATE DATABASE IF NOT EXISTS iot_database;

USE iot_database;
-- Créer la table des rapports d'analyse (analysis_reports)
CREATE TABLE IF NOT EXISTS analysis_reports (
    id VARCHAR(36) PRIMARY KEY,
    patient_id VARCHAR(36) NOT NULL,
    report_type VARCHAR(50) NOT NULL,
    encrypted_content TEXT NOT NULL,
    created_at DATETIME NOT NULL,
    blood_pressure VARCHAR(50),
    heart_rate INT,
    gfr FLOAT,
    creatinine_level FLOAT,
    potassium_level FLOAT,
    sodium_level FLOAT,
    weight FLOAT,
    body_temperature FLOAT,
    spO2 FLOAT,
    urine_volume FLOAT,
    glucose_level FLOAT
);
-- Créer la table des données de capteurs (sensor_data)
CREATE TABLE IF NOT EXISTS sensor_data (
    id VARCHAR(36) PRIMARY KEY,
    patient_id VARCHAR(36) NOT NULL,
    sensor_type VARCHAR(50) NOT NULL,
    sensor_value FLOAT NOT NULL,
    timestamp DATETIME NOT NULL,
    blood_pressure VARCHAR(50),
    heart_rate INT,
    gfr FLOAT,
    creatinine_level FLOAT,
    potassium_level FLOAT,
    sodium_level FLOAT,
    weight FLOAT,
    body_temperature FLOAT,
    spO2 FLOAT,
    urine_volume FLOAT,
    glucose_level FLOAT
);

