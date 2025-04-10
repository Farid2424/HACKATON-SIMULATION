-- Créer la base de données pour les utilisateurs
CREATE DATABASE IF NOT EXISTS user_db;
USE user_db;

-- Créer la table des médecins (doctors)
CREATE TABLE IF NOT EXISTS doctors (
    id VARCHAR(36) PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Créer la table des patients (patients)
CREATE TABLE IF NOT EXISTS patients (
    id VARCHAR(36) PRIMARY KEY,
    doctor_id VARCHAR(36) NOT NULL,
    name VARCHAR(255) NOT NULL,
    date_of_birth DATE NOT NULL,
    medical_record_number VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (doctor_id) REFERENCES doctors(id)
);

-- Créer la base de données pour les capteurs IoT
CREATE DATABASE IF NOT EXISTS iot_db;
USE iot_db;

-- Créer la table des données de capteurs (sensor_data)
CREATE TABLE IF NOT EXISTS sensor_data (
    id VARCHAR(36) PRIMARY KEY,
    patient_id VARCHAR(36) NOT NULL,
    sensor_type VARCHAR(50) NOT NULL,
    encrypted_value TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_patient_timestamp (patient_id, timestamp),
    FOREIGN KEY (patient_id) REFERENCES user_db.patients(id)
);

-- Créer la table des rapports d'analyse (analysis_reports)
CREATE TABLE IF NOT EXISTS analysis_reports (
    id VARCHAR(36) PRIMARY KEY,
    patient_id VARCHAR(36) NOT NULL,
    report_type VARCHAR(50) NOT NULL,
    encrypted_content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_patient_created (patient_id, created_at),
    FOREIGN KEY (patient_id) REFERENCES user_db.patients(id)
);