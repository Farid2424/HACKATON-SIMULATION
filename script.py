import mysql.connector
from faker import Faker
import uuid
import random
from datetime import datetime
import os
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import pad, unpad
import base64

# Configuration des bases de données
user_db_config = {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "",
    "database": "user_database"
}

iot_db_config = {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "",
    "database": "iot_database"
}

# Connexion aux bases de données
user_db = mysql.connector.connect(**user_db_config)
iot_db = mysql.connector.connect(**iot_db_config)

cursor_user = user_db.cursor()
cursor_iot = iot_db.cursor()

# Initialisation de Faker
fake = Faker()

# Remplacer par l'ID réel du docteur
DOCTOR_ID = "exemple-doctor-id-uuid"

# Générer ou charger une clé AES-256 pour le chiffrement
def load_or_generate_aes_key():
    key_file = 'aes_key.bin'
    if os.path.exists(key_file):
        with open(key_file, 'rb') as f:
            key = f.read()
    else:
        # Si la clé n'existe pas, générer une nouvelle clé
        key = get_random_bytes(32)
        with open(key_file, 'wb') as f:
            f.write(key)
    return key

# Fonction pour chiffrer avec AES-256-CBC
def encrypt_data(data, key):
    cipher = AES.new(key, AES.MODE_CBC)
    ct_bytes = cipher.encrypt(pad(data.encode(), AES.block_size))
    iv = base64.b64encode(cipher.iv).decode('utf-8')
    ct = base64.b64encode(ct_bytes).decode('utf-8')
    return iv + ct  # On concatène l'IV et le texte chiffré

# Fonction pour déchiffrer avec AES-256-CBC
def decrypt_data(encrypted_data, key):
    try:
        # Extraire l'IV (24 premiers caractères de la base64) et le texte chiffré
        iv = base64.b64decode(encrypted_data[:24])  # L'IV est de 16 octets
        ct = base64.b64decode(encrypted_data[24:])  # Le reste est le texte chiffré

        cipher = AES.new(key, AES.MODE_CBC, iv)
        
        # Déchiffrement des données
        decrypted_data = unpad(cipher.decrypt(ct), AES.block_size).decode('utf-8')
        
        return decrypted_data
    except ValueError as e:
        print(f"Erreur de padding lors du déchiffrement: {str(e)}")
        return None
    except Exception as e:
        print(f"Erreur générale lors du déchiffrement: {str(e)}")
        return None

# Créer un dossier pour stocker les rapports localement
output_dir = "rapports_chiffres"
os.makedirs(output_dir, exist_ok=True)

# Fonction pour récupérer les patients avec leurs rapports et données de capteurs
def get_patients_with_reports_and_sensors():
    cursor_user.execute("SELECT id, name FROM patients WHERE doctor_id = %s", (DOCTOR_ID,))
    patients = cursor_user.fetchall()
    patients_list = []

    for patient in patients:
        patient_id, name = patient
        cursor_iot.execute("""
            SELECT id, report_type FROM analysis_reports WHERE patient_id = %s
        """, (patient_id,))
        reports = cursor_iot.fetchall()

        cursor_iot.execute("""
            SELECT id, sensor_type, sensor_value, timestamp FROM sensor_data WHERE patient_id = %s
        """, (patient_id,))
        sensor_data = cursor_iot.fetchall()
        
        # Si le patient a des rapports
        if reports or sensor_data:
            patient_reports = []
            for report in reports:
                report_id, report_type = report
                patient_reports.append({
                    'report_id': report_id,
                    'report_type': report_type
                })

            patient_sensor_data = []
            for sensor in sensor_data:
                sensor_id, sensor_type, sensor_value, timestamp = sensor
                patient_sensor_data.append({
                    'sensor_id': sensor_id,
                    'sensor_type': sensor_type,
                    'sensor_value': sensor_value,
                    'timestamp': timestamp
                })

            patients_list.append({
                'patient_id': patient_id,
                'name': name,
                'reports': patient_reports,
                'sensor_data': patient_sensor_data
            })

    return patients_list

# Demander à l'utilisateur quel patient et rapport il souhaite télécharger
def ask_for_report_selection(patients_with_reports_and_sensors):
    print("Liste des patients avec leurs rapports et données de capteurs disponibles :")
    for idx, patient in enumerate(patients_with_reports_and_sensors, 1):
        print(f"{idx}. {patient['name']}")
    
    patient_choice = int(input("Choisissez un patient en entrant son numéro : "))
    selected_patient = patients_with_reports_and_sensors[patient_choice - 1]

    print(f"Vous avez sélectionné : {selected_patient['name']}")
    print("Liste des rapports disponibles :")
    
    for idx, report in enumerate(selected_patient['reports'], 1):
        print(f"{idx}. {report['report_type']} (ID: {report['report_id']})")
    
    report_choice = int(input("Choisissez un rapport en entrant son numéro : "))
    selected_report = selected_patient['reports'][report_choice - 1]

    return selected_patient['patient_id'], selected_report['report_id'], selected_patient['sensor_data']

# Fonction pour générer des données de test
def generate_patient_data():
    nombre_de_patients = 10  # Nombre de patients à générer
    aes_key = load_or_generate_aes_key()  # Charger ou générer la clé AES

    for _ in range(nombre_de_patients):
        # Générer des données de patients et les insérer dans la base
        patient_id = str(uuid.uuid4())
        name = fake.name()
        dob = fake.date_of_birth(minimum_age=18, maximum_age=90).strftime('%Y-%m-%d')
        mrn = f"MRN-{random.randint(100000, 999999)}"

        cursor_user.execute("""
            INSERT INTO patients (id, doctor_id, name, date_of_birth, medical_record_number)
            VALUES (%s, %s, %s, %s, %s)
        """, (patient_id, DOCTOR_ID, name, dob, mrn))

        print(f"[✓] Patient {name} ajouté.")

        # Insérer des rapports d'analyse
        for _ in range(random.randint(1, 3)):  # Entre 1 et 3 rapports
            report_id = str(uuid.uuid4())
            report_type = random.choice(["diagnosis", "treatment", "follow-up"])
            content = fake.text(max_nb_chars=200)
            created_at = fake.date_this_year(before_today=True, after_today=False).strftime('%Y-%m-%d %H:%M:%S')

            # Générer des valeurs aléatoires pour les nouvelles colonnes
            blood_pressure = f"{random.randint(110, 130)}/{random.randint(70, 90)}"
            heart_rate = random.randint(60, 100)
            gfr = round(random.uniform(60.0, 120.0), 2)
            creatinine_level = round(random.uniform(0.5, 1.5), 2)
            potassium_level = round(random.uniform(3.5, 5.0), 2)
            sodium_level = round(random.uniform(135.0, 145.0), 2)
            weight = round(random.uniform(50.0, 90.0), 2)
            body_temperature = round(random.uniform(36.5, 37.5), 2)
            spO2 = round(random.uniform(95.0, 100.0), 2)
            urine_volume = round(random.uniform(800.0, 2000.0), 2)
            glucose_level = round(random.uniform(70.0, 130.0), 2)

            encrypted_content = encrypt_data(content, aes_key)
            
            cursor_iot.execute("""
                INSERT INTO analysis_reports 
                (id, patient_id, report_type, encrypted_content, created_at, blood_pressure, heart_rate, gfr,
                creatinine_level, potassium_level, sodium_level, weight, body_temperature, spO2, urine_volume, glucose_level)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (report_id, patient_id, report_type, encrypted_content, created_at, blood_pressure, heart_rate, gfr,
                  creatinine_level, potassium_level, sodium_level, weight, body_temperature, spO2, urine_volume, glucose_level))

            print(f"[✓] Rapport d'analyse {report_type} pour {name} ajouté.")

            # Insérer des données de capteurs
            for sensor_type in ["ECG", "SpO2", "Température", "Poids"]:
                sensor_value = random.uniform(0, 100) if sensor_type != "Poids" else round(random.uniform(50.0, 90.0), 2)
                timestamp = fake.date_this_year(before_today=True, after_today=False).strftime('%Y-%m-%d %H:%M:%S')
                id=str(uuid.uuid4())
                cursor_iot.execute("""
                    INSERT INTO sensor_data 
                    ( id, patient_id, sensor_type, sensor_value, timestamp, blood_pressure, heart_rate, gfr, 
                    creatinine_level, potassium_level, sodium_level, weight, body_temperature, spO2, urine_volume, glucose_level)
                    VALUES ( %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (id, patient_id, sensor_type, sensor_value, timestamp, blood_pressure, heart_rate, gfr,
                      creatinine_level, potassium_level, sodium_level, weight, body_temperature, spO2, urine_volume, glucose_level))

            print(f"[✓] Données de capteur pour {name} ajoutées.")

    # Commit et fermeture de la connexion
    user_db.commit()
    iot_db.commit()

def insert_sensor_data():
    sensor_id = str(uuid.uuid4())  # Générer un UUID pour chaque sensor_data
    patient_id = 'patient123'  # Exemple d'ID patient

    # Exemple de valeurs de capteurs
    sensor_type = 'ECG'
    sensor_value = 72.5
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    blood_pressure = '120/80'
    heart_rate = 75
    gfr = 90.0
    creatinine_level = 0.8
    potassium_level = 4.0
    sodium_level = 135.0
    weight = 70.5
    body_temperature = 36.7
    spO2 = 98.0
    urine_volume = 1500.0
    glucose_level = 100.0

    # Vérifie les noms de colonnes dans ta base de données
    cursor_iot.execute(""" 
        INSERT INTO sensor_data (id, patient_id, sensor_type, sensor_value, timestamp, blood_pressure, heart_rate, gfr, 
        creatinine_level, potassium_level, sodium_level, weight, body_temperature, spO2, urine_volume, glucose_level)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (sensor_id, patient_id, sensor_type, sensor_value, timestamp, blood_pressure, heart_rate, gfr,
          creatinine_level, potassium_level, sodium_level, weight, body_temperature, spO2, urine_volume, glucose_level))

    print(f"[✓] Données de capteur pour le patient {patient_id} insérées.")

# Demander à l'utilisateur de télécharger un rapport
aes_key = load_or_generate_aes_key()  # Charger ou générer la clé AES

action = input("Que voulez-vous faire ?\n1. Générer des données\n2. Télécharger un rapport\nEntrez 1 ou 2 : ")

if action == "1":
    generate_patient_data()
elif action == "2":
    patients_with_reports_and_sensors = get_patients_with_reports_and_sensors()
    patient_id, report_id, sensor_data = ask_for_report_selection(patients_with_reports_and_sensors)

    # Récupérer les données de l'analyse avec les nouvelles colonnes
    cursor_iot.execute("""
        SELECT blood_pressure, heart_rate, gfr, creatinine_level, potassium_level, sodium_level,
               weight, body_temperature, spO2, urine_volume, glucose_level
        FROM analysis_reports WHERE id = %s
    """, (report_id,))
    report_data = cursor_iot.fetchone()

    # Ajouter les nouvelles données de santé au rapport
    report_text = f"Rapport d'Analyse ID: {report_id}\n"
    report_text += f"Pression Artérielle: {report_data[0]}\n"
    report_text += f"Fréquence Cardiaque: {report_data[1]} bpm\n"
    report_text += f"Taux de Filtration Glomérulaire: {report_data[2]} mL/min\n"
    report_text += f"Niveau de Créatinine: {report_data[3]} mg/dL\n"
    report_text += f"Niveau de Potassium: {report_data[4]} mmol/L\n"
    report_text += f"Niveau de Sodium: {report_data[5]} mmol/L\n"
    report_text += f"Poids: {report_data[6]} kg\n"
    report_text += f"Température Corporelle: {report_data[7]} °C\n"
    report_text += f"Saturation en Oxygène: {report_data[8]}%\n"
    report_text += f"Volume Urinaire: {report_data[9]} mL\n"
    report_text += f"Glycémie: {report_data[10]} mg/dL\n"

    # Enregistrer dans le fichier
    filename = f"{output_dir}/{__name__}_rapport.txt"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(report_text)

    print(f"Le rapport a été téléchargé et sauvegardé sous {filename}")

# Fermer les curseurs et les connexions
cursor_user.close()
cursor_iot.close()
user_db.close()
iot_db.close()