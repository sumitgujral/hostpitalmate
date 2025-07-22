from flask import Flask, render_template, request, redirect, url_for, flash, session
from datetime import datetime, date
from db_manager import DatabaseManager
import pymysql
import pymysql.cursors
from functools import wraps
import os 
from dotenv import load_dotenv 

app = Flask(__name__)
app.secret_key = os.getenv("SECRETKEY_FOR_FLASK")
timeout = 10

load_dotenv()
DB_HOST = "hostpitalmate-hospitalmate.f.aivencloud.com"
DB_USER = "avnadmin"
DB_PASSWORD = os.getenv("AIVEN_DB_PASSWORD")
DB_NAME = "hospitalmate_db6"
DB_PORT = 21233
DB_CHARSET = "utf8mb4"


db_manager = DatabaseManager(
    host=DB_HOST,
    user=DB_USER,
    password=DB_PASSWORD,
    database=DB_NAME,
    port=DB_PORT,
    charset=DB_CHARSET,
    connect_timeout=timeout,
    read_timeout=timeout,
    write_timeout=timeout
)

if not db_manager.connect():
    print("FATAL: Could not connect to database. Exiting.")
    exit()

def _setup_database_tables():
    try:
        with open('sql_setup.sql', 'r') as f:
            sql_script = f.read()

        statements = [s.strip() for s in sql_script.split(';') if s.strip()]

        print("Attempting to set up database tables...")
        for statement in statements:
            if statement.upper().startswith('CREATE TABLE IF NOT EXISTS'):
                try:
                    db_manager.execute_query(statement)
                    print(f"Executed: {statement.split('(')[0].strip()}...")
                except pymysql.Error as e:
                    if e.args[0] == 1050:
                        print(f"Table already exists, skipping: {statement.split('(')[0].strip()}")
                    else:
                        print(f"Error executing SQL statement: {statement}\nError: {e}")
            elif statement.upper().startswith('DROP DATABASE') or \
                 statement.upper().startswith('CREATE DATABASE') or \
                 statement.upper().startswith('USE'):
                print(f"Skipping database management statement: {statement.split(' ')[0].strip()}...")
            else:
                try:
                    db_manager.execute_query(statement)
                    print(f"Executed other DDL: {statement.split(' ')[0].strip()}...")
                except pymysql.Error as e:
                    print(f"Error executing non-CREATE TABLE DDL: {statement}\nError: {e}")


        print("Database table setup complete (or tables already existed).")
    except FileNotFoundError:
        print("WARNING: sql_setup.sql not found. Database tables might not be created.")
    except Exception as e:
        print(f"An unexpected error occurred during database setup: {e}")

_setup_database_tables()

def parse_date_ddmmyyyy(date_str):
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, '%d-%m-%Y').date()
    except ValueError:
        return None

def format_date_ddmmyyyy(date_obj):
    if not date_obj:
        return ''
    return date_obj.strftime('%d-%m-%Y')

class PatientManager:
    def __init__(self, db_manager):
        self.db_manager = db_manager

    def add_patient(self, data):
        query = """INSERT INTO patients (name, dob, gender, address, phone)
                   VALUES (%s, %s, %s, %s, %s)"""
        params = (data['name'], data['dob'], data['gender'], data['address'],
                  data['phone'])
        try:
            return self.db_manager.execute_query(query, params)
        except Exception as e:
            print(f"Error adding patient: {e}")
            return False

    def get_patient(self, patient_id):
        query = "SELECT patient_id, name, dob, gender, address, phone FROM patients WHERE patient_id = %s"
        try:
            return self.db_manager.execute_query(query, (patient_id,), fetch_one=True)
        except Exception as e:
            print(f"Error getting patient: {e}")
            return None

    def get_all_patients(self):
        query = "SELECT patient_id, name, dob, gender, phone FROM patients ORDER BY patient_id DESC"
        try:
            return self.db_manager.execute_query(query, fetch_all=True)
        except Exception as e:
            print(f"Error getting all patients: {e}")
            return []

    def delete_patient(self, patient_id):
        query = "DELETE FROM patients WHERE patient_id = %s"
        try:
            return self.db_manager.execute_query(query, (patient_id,))
        except Exception as e:
            print(f"Error deleting patient: {e}")
            return False

class DoctorManager:
    def __init__(self, db_manager):
        self.db_manager = db_manager

    def add_doctor(self, data):
        query = """INSERT INTO doctors (name, qualification, specialization, phone)
                   VALUES (%s, %s, %s, %s)"""
        params = (data['name'], data['qualification'], data['specialization'],
                  data['phone'])
        try:
            return self.db_manager.execute_query(query, params)
        except Exception as e:
            print(f"Error adding doctor: {e}")
            return False

    def get_doctor(self, doctor_id):
        query = "SELECT doctor_id, name, qualification, specialization, phone FROM doctors WHERE doctor_id = %s"
        try:
            return self.db_manager.execute_query(query, (doctor_id,), fetch_one=True)
        except Exception as e:
            print(f"Error getting doctor: {e}")
            return None

    def get_all_doctors(self):
        query = "SELECT doctor_id, name, qualification, specialization, phone FROM doctors ORDER BY doctor_id DESC"
        try:
            return self.db_manager.execute_query(query, fetch_all=True)
        except Exception as e:
            print(f"Error getting all doctors: {e}")
            return []

    def delete_doctor(self, doctor_id):
        query = "DELETE FROM doctors WHERE doctor_id = %s"
        try:
            return self.db_manager.execute_query(query, (doctor_id,))
        except Exception as e:
            print(f"Error deleting doctor: {e}")
            return False

class StaffManager:
    def __init__(self, db_manager):
        self.db_manager = db_manager

    def add_staff(self, data):
        query = """INSERT INTO staff (name, role, phone, address, salary)
                   VALUES (%s, %s, %s, %s, %s)"""
        params = (data['name'], data['role'], data['phone'],
                  data['address'], data['salary'])
        try:
            return self.db_manager.execute_query(query, params)
        except Exception as e:
            print(f"Error adding staff: {e}")
            return False

    def get_staff_details(self, staff_id):
        query = "SELECT staff_id, name, role, phone, address, salary FROM staff WHERE staff_id = %s"
        try:
            return self.db_manager.execute_query(query, (staff_id,), fetch_one=True)
        except Exception as e:
            print(f"Error getting staff details: {e}")
            return None

    def get_all_staff(self):
        query = "SELECT staff_id, name, role, phone, salary FROM staff ORDER BY staff_id DESC"
        try:
            return self.db_manager.execute_query(query, fetch_all=True)
        except Exception as e:
            print(f"Error getting all staff: {e}")
            return []

    def delete_staff(self, staff_id):
        query = "DELETE FROM staff WHERE staff_id = %s"
        try:
            return self.db_manager.execute_query(query, (staff_id,))
        except Exception as e:
            print(f"Error deleting staff: {e}")
            return False

class AppointmentManager:
    def __init__(self, db_manager):
        self.db_manager = db_manager

    def book_appointment(self, patient_id, doctor_id, booked_date, appointment_date, appointment_note):
        query = """INSERT INTO appointments (patient_id, doctor_id, booked_date, appointment_date, appointment_note)
                   VALUES (%s, %s, %s, %s, %s)"""
        params = (patient_id, doctor_id, booked_date, appointment_date, appointment_note)
        try:
            return self.db_manager.execute_query(query, params)
        except Exception as e:
            print(f"Error booking appointment: {e}")
            return False

    def get_all_appointments(self):
        query = """SELECT a.appointment_id, p.name AS patient_name, d.name AS doctor_name,
                          a.booked_date, a.appointment_date, a.appointment_note, a.patient_id, a.doctor_id
                   FROM appointments a
                   JOIN patients p ON a.patient_id = p.patient_id
                   JOIN doctors d ON a.doctor_id = d.doctor_id
                   ORDER BY a.appointment_date DESC"""
        try:
            return self.db_manager.execute_query(query, fetch_all=True)
        except Exception as e:
            print(f"Error getting all appointments: {e}")
            return []

    def delete_appointment(self, appointment_id):
        query = "DELETE FROM appointments WHERE appointment_id = %s"
        try:
            return self.db_manager.execute_query(query, (appointment_id,))
        except Exception as e:
            print(f"Error deleting appointment: {e}")
            return False

class MedicalRecordManager:
    def __init__(self, db_manager):
        self.db_manager = db_manager

    def add_medical_record(self, patient_id, doctor_id, data):
        query = """INSERT INTO medical_records (patient_id, doctor_id, treatment, prescriptions, note, admit_date, release_date)
                   VALUES (%s, %s, %s, %s, %s, %s, %s)"""
        params = (patient_id, doctor_id, data['treatment'], data['prescriptions'],
                  data['note'], data['admit_date'], data['release_date'])
        try:
            return self.db_manager.execute_query(query, params)
        except Exception as e:
            print(f"Error adding medical record: {e}")
            return False

    def get_patient_medical_history(self, patient_id):
        query = """SELECT mr.record_id, mr.record_date, d.name AS doctor_name, mr.treatment, mr.prescriptions, mr.note, mr.admit_date, mr.release_date, mr.doctor_id
                   FROM medical_records mr
                   JOIN doctors d ON mr.doctor_id = d.doctor_id
                   WHERE mr.patient_id = %s
                   ORDER BY mr.record_date DESC"""
        try:
            return self.db_manager.execute_query(query, (patient_id,), fetch_all=True)
        except Exception as e:
            print(f"Error getting patient medical history: {e}")
            return []

    def get_medical_record(self, record_id):
        query = "SELECT * FROM medical_records WHERE record_id = %s"
        try:
            return self.db_manager.execute_query(query, (record_id,), fetch_one=True)
        except Exception as e:
            print(f"Error getting medical record: {e}")
            return None

    def delete_medical_record(self, record_id):
        query = "DELETE FROM medical_records WHERE record_id = %s"
        try:
            return self.db_manager.execute_query(query, (record_id,))
        except Exception as e:
            print(f"Error deleting medical record: {e}")
            return False

patient_manager = PatientManager(db_manager)
doctor_manager = DoctorManager(db_manager)
staff_manager = StaffManager(db_manager)
appointment_manager = AppointmentManager(db_manager)
medical_record_manager = MedicalRecordManager(db_manager)

VALID_USERNAME = "admin"
VALID_PASSWORD = "adminpass"

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            flash('Please log in to access this page.', 'info')
            return redirect(url_for('/'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username == VALID_USERNAME and password == VALID_PASSWORD:
            session['logged_in'] = True
            flash('Logged in successfully!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid credentials. Please try again.', 'error')
    return render_template('index.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/')
def index():
    if not session.get('logged_in'):
        return redirect(url_for('/'))
    return render_template('index.html')

@app.route('/patients', methods=['GET', 'POST'])
@login_required
def patients():
    if request.method == 'POST':
        name = request.form['name'].strip()
        dob_str = request.form['dob'].strip()
        gender = request.form['gender'].strip()
        address = request.form['address'].strip()
        phone = request.form['phone'].strip()
        dob = parse_date_ddmmyyyy(dob_str)
        if dob is None and dob_str:
            flash('Invalid DOB format. Please use DD-MM-YYYY.', 'error')
            return redirect(url_for('patients'))

        if not name or not phone:
            flash('Name and Phone are required.', 'error')
        else:
            data = {
                'name': name,
                'dob': dob,
                'gender': gender,
                'address': address,
                'phone': phone,
            }
            if patient_manager.add_patient(data):
                flash('Patient added successfully!', 'success')
            else:
                flash('Failed to add patient.', 'error')
        return redirect(url_for('patients'))

    patients_list = patient_manager.get_all_patients()
    if patients_list:
        for p in patients_list:
            p['dob'] = format_date_ddmmyyyy(p['dob'])
    return render_template('patients.html', patients=patients_list)

@app.route('/patients/delete/<int:patient_id>', methods=['POST'])
@login_required
def delete_patient(patient_id):
    if patient_manager.delete_patient(patient_id):
        flash('Patient deleted successfully!', 'success')
    else:
        flash('Failed to delete patient. Ensure no related appointments or medical records exist.', 'error')
    return redirect(url_for('patients'))

@app.route('/doctors', methods=['GET', 'POST'])
@login_required
def doctors():
    if request.method == 'POST':
        name = request.form['name'].strip()
        qualification = request.form['qualification'].strip()
        specialization = request.form['specialization'].strip()
        phone = request.form['phone'].strip()

        if not name or not specialization or not phone:
            flash('Name, Specialization, and Phone are required.', 'error')
        else:
            data = {
                'name': name,
                'qualification': qualification,
                'specialization': specialization,
                'phone': phone
            }
            if doctor_manager.add_doctor(data):
                flash('Doctor added successfully!', 'success')
            else:
                flash('Failed to add doctor.', 'error')
        return redirect(url_for('doctors'))

    doctors_list = doctor_manager.get_all_doctors()
    return render_template('doctors.html', doctors=doctors_list)

@app.route('/doctors/delete/<int:doctor_id>', methods=['POST'])
@login_required
def delete_doctor(doctor_id):
    if doctor_manager.delete_doctor(doctor_id):
        flash('Doctor deleted successfully!', 'success')
    else:
        flash('Failed to delete doctor. Ensure no related appointments or medical records exist.', 'error')
    return redirect(url_for('doctors'))

@app.route('/staff', methods=['GET', 'POST'])
@login_required
def staff():
    if request.method == 'POST':
        name = request.form['name'].strip()
        role = request.form['role'].strip()
        phone = request.form['phone'].strip()
        address = request.form['address'].strip()
        salary_str = request.form['salary'].strip()

        salary = None
        if salary_str:
            try:
                salary = float(salary_str)
            except ValueError:
                flash('Salary must be a number.', 'error')
                return redirect(url_for('staff'))

        if not name or not role or not phone:
            flash('Name, Role, and Phone are required.', 'error')
        else:
            data = {
                'name': name,
                'role': role,
                'phone': phone,
                'address': address,
                'salary': salary
            }
            if staff_manager.add_staff(data):
                flash('Staff added successfully!', 'success')
            else:
                flash('Failed to add staff.', 'error')
        return redirect(url_for('staff'))

    staff_list = staff_manager.get_all_staff()
    return render_template('staff.html', staff=staff_list)

@app.route('/staff/delete/<int:staff_id>', methods=['POST'])
@login_required
def delete_staff(staff_id):
    if staff_manager.delete_staff(staff_id):
        flash('Staff deleted successfully!', 'success')
    else:
        flash('Failed to delete staff.', 'error')
    return redirect(url_for('staff'))

@app.route('/appointments', methods=['GET', 'POST'])
@login_required
def appointments():
    if request.method == 'POST':
        patient_id_str = request.form['patient_id'].strip()
        doctor_id_str = request.form['doctor_id'].strip()
        booked_date_str = request.form['booked_date'].strip()
        appointment_date_str = request.form['appointment_date'].strip()
        appointment_note = request.form['appointment_note'].strip()

        if not (patient_id_str and doctor_id_str and booked_date_str and appointment_date_str):
            flash('All fields are required.', 'error')
            return redirect(url_for('appointments'))

        try:
            patient_id = int(patient_id_str)
            doctor_id = int(doctor_id_str)
            booked_date = parse_date_ddmmyyyy(booked_date_str)
            appointment_date = parse_date_ddmmyyyy(appointment_date_str)

            if booked_date is None or appointment_date is None:
                flash('Invalid date format. Please use DD-MM-YYYY.', 'error')
                return redirect(url_for('appointments'))

            if appointment_manager.book_appointment(patient_id, doctor_id, booked_date, appointment_date, appointment_note):
                flash('Appointment booked successfully!', 'success')
            else:
                flash('Failed to book appointment.', 'error')
        except ValueError:
            flash('Invalid Patient ID or Doctor ID.', 'error')
        return redirect(url_for('appointments'))

    appointments_list = appointment_manager.get_all_appointments()
    if appointments_list:
        for appt in appointments_list:
            appt['booked_date'] = format_date_ddmmyyyy(appt['booked_date'])
            appt['appointment_date'] = format_date_ddmmyyyy(appt['appointment_date'])

    patients_for_combo = patient_manager.get_all_patients()
    doctors_for_combo = doctor_manager.get_all_doctors()

    return render_template('appointments.html',
                           appointments=appointments_list,
                           patients=patients_for_combo,
                           doctors=doctors_for_combo)

@app.route('/appointments/delete/<int:appointment_id>', methods=['POST'])
@login_required
def delete_appointment(appointment_id):
    if appointment_manager.delete_appointment(appointment_id):
        flash('Appointment deleted successfully!', 'success')
    else:
        flash('Failed to delete appointment.', 'error')
    return redirect(url_for('appointments'))

@app.route('/medical_records', methods=['GET', 'POST'])
@login_required
def medical_records():
    if request.method == 'POST':
        patient_id_str = request.form['patient_id'].strip()
        doctor_id_str = request.form['doctor_id'].strip()
        treatment = request.form['treatment'].strip()
        prescriptions = request.form['prescriptions'].strip()
        note = request.form['note'].strip()
        admit_date_str = request.form['admit_date'].strip()
        release_date_str = request.form['release_date'].strip()

        if not (patient_id_str and doctor_id_str):
            flash('Patient and Doctor are required.', 'error')
            return redirect(url_for('medical_records'))

        try:
            patient_id = int(patient_id_str)
            doctor_id = int(doctor_id_str)
            admit_date = parse_date_ddmmyyyy(admit_date_str)
            release_date = parse_date_ddmmyyyy(release_date_str)

            if (admit_date_str and admit_date is None) or \
               (release_date_str and release_date is None):
                flash('Invalid date format. Please use DD-MM-YYYY.', 'error')
                return redirect(url_for('medical_records'))

            if not treatment and not prescriptions and not note:
                flash('At least one field required (Treatment, Prescriptions, or Note).', 'error')
                return redirect(url_for('medical_records'))

            data = {
                'treatment': treatment,
                'prescriptions': prescriptions,
                'note': note,
                'admit_date': admit_date,
                'release_date': release_date
            }
            if medical_record_manager.add_medical_record(patient_id, doctor_id, data):
                flash('Medical record added successfully!', 'success')
            else:
                flash('Failed to add medical record.', 'error')
        except ValueError:
            flash('Invalid Patient ID or Doctor ID.', 'error')
        return redirect(url_for('medical_records'))

    selected_patient_id = request.args.get('patient_id', type=int)
    medical_records_list = []
    current_patient_info = None

    if selected_patient_id:
        medical_records_list = medical_record_manager.get_patient_medical_history(selected_patient_id)
        if medical_records_list:
            for rec in medical_records_list:
                rec['admit_date'] = format_date_ddmmyyyy(rec['admit_date'])
                rec['release_date'] = format_date_ddmmyyyy(rec['release_date'])
                rec['record_date'] = rec['record_date'].strftime('%Y-%m-%d %H:%M:%S') 

        current_patient_info = patient_manager.get_patient(selected_patient_id)
    
    patients_for_combo = patient_manager.get_all_patients()
    doctors_for_combo = doctor_manager.get_all_doctors()

    return render_template('medical_records.html',
                           medical_records=medical_records_list,
                           patients=patients_for_combo,
                           doctors=doctors_for_combo,
                           current_patient_info=current_patient_info,
                           selected_patient_id=selected_patient_id)

@app.route('/medical_records/delete/<int:record_id>', methods=['POST'])
@login_required
def delete_medical_record(record_id):
    if medical_record_manager.delete_medical_record(record_id):
        flash('Medical record deleted successfully!', 'success')
    else:
        flash('Failed to delete medical record.', 'error')
    patient_id = request.form.get('patient_id')
    if patient_id:
        return redirect(url_for('medical_records', patient_id=patient_id))
    return redirect(url_for('medical_records'))


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
