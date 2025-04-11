import os
import sqlite3
import tkinter as tk
from tkinter import messagebox
from tkinter import filedialog
from tkinter import scrolledtext
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from base64 import b64encode, b64decode
from Crypto.Random import get_random_bytes
import random
from faker import Faker
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

# AES
def load_or_generate_aes_key():
    key_file = "aes_key.bin"
    if os.path.exists(key_file):
        with open(key_file, "rb") as f:
            return f.read()
    else:
        key = get_random_bytes(32)
        with open(key_file, "wb") as f:
            f.write(key)
        return key

def encrypt_data(data, key):
    iv = get_random_bytes(16)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    ciphertext = cipher.encrypt(pad(data.encode(), AES.block_size))
    return b64encode(iv + ciphertext).decode()

def decrypt_data(data, key):
    raw = b64decode(data)
    iv = raw[:16]
    ciphertext = raw[16:]
    cipher = AES.new(key, AES.MODE_CBC, iv)
    return unpad(cipher.decrypt(ciphertext), AES.block_size).decode()

# Connexion SQLite
db = sqlite3.connect('patient_db.sqlite')
cursor = db.cursor()
db_iot = sqlite3.connect('iot_data.sqlite')
cursor_iot = db_iot.cursor()

# Créer les tables si elles n'existent pas
cursor.execute("""
CREATE TABLE IF NOT EXISTS patients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nom TEXT,
    age INTEGER,
    email TEXT
)
""")
db.commit()

cursor_iot.execute("""
CREATE TABLE IF NOT EXISTS analysis_reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id INTEGER,
    blood_pressure TEXT,
    heart_rate TEXT,
    gfr TEXT,
    creatinine_level TEXT,
    potassium_level TEXT,
    sodium_level TEXT,
    weight TEXT,
    body_temperature TEXT,
    spO2 TEXT,
    urine_volume TEXT,
    glucose_level TEXT,
    FOREIGN KEY(patient_id) REFERENCES patients(id)
)
""")
db_iot.commit()

# Générer données chiffrées
def generate_patient_data():
    fake = Faker()
    aes_key = load_or_generate_aes_key()

    for _ in range(5):
        nom = fake.name()
        age = random.randint(20, 80)
        email = fake.email()

        cursor.execute("INSERT INTO patients (nom, age, email) VALUES (?, ?, ?)", (nom, age, email))
        db.commit()
        patient_id = cursor.lastrowid

        for _ in range(2):
            data = {
                "blood_pressure": f"{random.randint(100, 140)}/{random.randint(60, 90)}",
                "heart_rate": str(random.randint(60, 100)),
                "gfr": str(random.randint(60, 120)),
                "creatinine_level": str(round(random.uniform(0.5, 1.5), 2)),
                "potassium_level": str(round(random.uniform(3.5, 5.0), 2)),
                "sodium_level": str(round(random.uniform(135, 145), 2)),
                "weight": str(round(random.uniform(50, 100), 2)),
                "body_temperature": str(round(random.uniform(36.0, 38.0), 2)),
                "spO2": str(random.randint(95, 100)),
                "urine_volume": str(round(random.uniform(0.5, 2.0), 2)),
                "glucose_level": str(round(random.uniform(70, 140), 2)),
            }

            encrypted_data = {k: encrypt_data(v, aes_key) for k, v in data.items()}
            cursor_iot.execute("""
                INSERT INTO analysis_reports (
                    patient_id, blood_pressure, heart_rate, gfr, creatinine_level, potassium_level,
                    sodium_level, weight, body_temperature, spO2, urine_volume, glucose_level
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (patient_id, *encrypted_data.values()))
            db_iot.commit()

# Récupérer patients et rapports
def get_patients_with_reports_and_sensors():
    cursor.execute("SELECT id, nom FROM patients")
    patients = cursor.fetchall()
    data = {}
    for patient_id, nom in patients:
        cursor_iot.execute("SELECT id FROM analysis_reports WHERE patient_id = ?", (patient_id,))
        reports = [r[0] for r in cursor_iot.fetchall()]
        data[(patient_id, nom)] = reports
    return data

# Générer fichier PDF
def save_report_as_pdf(filename, report_text):
    c = canvas.Canvas(filename, pagesize=letter)
    width, height = letter
    y = height - 50
    for line in report_text.splitlines():
        c.drawString(50, y, line)
        y -= 15
    c.save()

# Interface graphique
def interface_graphique():
    root = tk.Tk()
    root.title("Système de gestion de patients")
    root.geometry("600x600")

    aes_key = load_or_generate_aes_key()
    patients_data = get_patients_with_reports_and_sensors()

    # Définir selected_patient et selected_report ici
    selected_patient = tk.StringVar(root)
    selected_report = tk.StringVar(root)

    label_title = tk.Label(root, text="Système de gestion de patients", font=("Helvetica", 16))
    label_title.pack(pady=10)

    def lancer_generation():
        generate_patient_data()
        messagebox.showinfo("Succès", "Les données ont été générées avec succès.")
        root.destroy()
        interface_graphique()

    def update_reports(*args):
        patient_key = selected_patient.get()
        if patient_key:
            pid = int(patient_key.split(" - ")[0])
            reports = patients_data.get((pid, patient_key.split(" - ")[1]), [])
            selected_report.set("")  # Réinitialiser la sélection du rapport
            menu = report_menu["menu"]
            menu.delete(0, "end")
            for rid in reports:
                menu.add_command(label=str(rid), command=lambda v=rid: selected_report.set(v))

    
    def lancer_telechargement():
        try:
            if not selected_patient.get() or not selected_report.get():
                messagebox.showwarning("Sélection requise", "Veuillez sélectionner un patient et un rapport.")
                return

            patient_id = int(selected_patient.get().split(" - ")[0])
            report_id = int(selected_report.get())

            print(f"Patient ID: {patient_id}, Report ID: {report_id}")  # Afficher les IDs pour le débogage

            cursor_iot.execute(""" 
                SELECT blood_pressure, heart_rate, gfr, creatinine_level, potassium_level, sodium_level,
                    weight, body_temperature, spO2, urine_volume, glucose_level 
                FROM analysis_reports WHERE id = %s AND patient_id = %s
            """, (report_id, patient_id))  # Exécution de la requête

            report_data = cursor_iot.fetchone()

            if not report_data:
                messagebox.showwarning("Erreur", "Aucun rapport trouvé pour ce patient.")
                return

            decrypted = [decrypt_data(field, aes_key) for field in report_data]

            report_text = f"Rapport d'Analyse ID: {report_id}\n"
            labels = [
                "Pression Artérielle", "Fréquence Cardiaque", "Taux de Filtration Glomérulaire",
                "Niveau de Créatinine", "Niveau de Potassium", "Niveau de Sodium", "Poids",
                "Température Corporelle", "Saturation en Oxygène", "Volume Urinaire", "Glycémie"
            ]
            for label, value in zip(labels, decrypted):
                report_text += f"{label}: {value}\n"

            output_dir = "output"
            os.makedirs(output_dir, exist_ok=True)
            txt_file = os.path.join(output_dir, f"{report_id}_rapport.txt")
            with open(txt_file, "w", encoding="utf-8") as f:
                f.write(report_text)

            pdf_file = os.path.join(output_dir, f"{report_id}_rapport.pdf")
            save_report_as_pdf(pdf_file, report_text)

            text_display.delete("1.0", tk.END)
            text_display.insert(tk.END, report_text)

            messagebox.showinfo("Téléchargement réussi", f"Rapport enregistré :\n{txt_file}\n{pdf_file}")
        except Exception as e:
            messagebox.showerror("Erreur", f"Une erreur est survenue : {str(e)}")
            print(f"Erreur : {str(e)}")  # Afficher l'erreur dans la console pour débogage
    # Bouton générer
    btn_generate = tk.Button(root, text="Générer des données", command=lancer_generation, width=30, height=2)
    btn_generate.pack(pady=10)

    # Menu patient
    label_patient = tk.Label(root, text="Sélectionnez un patient :", font=("Helvetica", 12))
    label_patient.pack(pady=5)

    if patients_data:
        patient_names = [f"{pid} - {nom}" for (pid, nom) in patients_data.keys()]
        selected_patient.set(patient_names[0])  # Par défaut, sélectionne le premier patient

        patient_menu = tk.OptionMenu(root, selected_patient, *patient_names)
        patient_menu.pack()

    # Menu rapport
    label_report = tk.Label(root, text="Sélectionnez un rapport :", font=("Helvetica", 12))
    label_report.pack(pady=5)

    report_menu = tk.OptionMenu(root, selected_report, "")  # Lier selected_report
    report_menu.pack()

    selected_patient.trace("w", update_reports)

    # Bouton télécharger
    btn_download = tk.Button(root, text="Télécharger le rapport sélectionné", command=lancer_telechargement, width=30, height=2)
    btn_download.pack(pady=20)

    # Zone d'affichage
    text_display = scrolledtext.ScrolledText(root, width=70, height=15)
    text_display.pack(pady=10)

    if patients_data:
        update_reports()

    root.mainloop()

# Lancer l'interface
interface_graphique()