from flask import Flask, render_template, request, redirect, url_for, flash
from datetime import datetime, date
from db_manager import DatabaseManager

app = Flask(__name__)
app.secret_key = 'a_very_secret_key_for_flask_messages_change_this_in_production' # IMPORTANT: Change this!

db_manager = DatabaseManager("localhost", "root", "7206", "hospitalmate_db6")

# Ensure database connection is established at app startup
if not db_manager.connect():
    print("FATAL: Could not connect to database. Exiting.")
    exit()

# --- Helper Functions for Date Conversion ---
def parse_date_ddmmyyyy(date_str):
    """Parses DD-MM-YYYY string to datetime.date object."""
    if not date_str:
        return None
    return datetime.strptime(date_str, '%d-%m-%Y').date()


def format_date_ddmmyyyy(date_obj):
    """Formats datetime.date object to DD-MM-YYYY string."""
    if not date_obj:
        return ''
    return date_obj.strftime('%d-%m-%Y')

# --- Module Manager Classes (Backend Logic) ---

class PatientManager:
    def __init__(self, db_manager):
        self.db_manager = db_manager

    def add_patient(self, data):
        query = """INSERT INTO patients (name, dob, gender, address, phone)
                   VALUES (%s, %s, %s, %s, %s)"""
        params = (data['name'], data['dob'], data['gender'], data['address'],
                  data['phone'])
        return self.db_manager.execute_query(query, params)

    def get_patient(self, patient_id):
        query = "SELECT patient_id, name, dob, gender, address, phone FROM patients WHERE patient_id = %s"
        return self.db_manager.execute_query(query, (patient_id,), fetch_one=True)

    def get_all_patients(self):
        query = "SELECT patient_id, name, dob, gender, phone FROM patients ORDER BY patient_id DESC"
        return self.db_manager.execute_query(query, fetch_all=True)

    def delete_patient(self, patient_id):
        query = "DELETE FROM patients WHERE patient_id = %s"
        return self.db_manager.execute_query(query, (patient_id,))

class DoctorManager:
    def __init__(self, db_manager):
        self.db_manager = db_manager

    def add_doctor(self, data):
        query = """INSERT INTO doctors (name, qualification, specialization, phone)
                   VALUES (%s, %s, %s, %s)"""
        params = (data['name'], data['qualification'], data['specialization'],
                  data['phone'])
        return self.db_manager.execute_query(query, params)

    def get_doctor(self, doctor_id):
        query = "SELECT doctor_id, name, qualification, specialization, phone FROM doctors WHERE doctor_id = %s"
        return self.db_manager.execute_query(query, (doctor_id,), fetch_one=True)

    def get_all_doctors(self):
        query = "SELECT doctor_id, name, qualification, specialization, phone FROM doctors ORDER BY doctor_id DESC"
        return self.db_manager.execute_query(query, fetch_all=True)

    def delete_doctor(self, doctor_id):
        query = "DELETE FROM doctors WHERE doctor_id = %s"
        return self.db_manager.execute_query(query, (doctor_id,))

class StaffManager:
    def __init__(self, db_manager):
        self.db_manager = db_manager

    def add_staff(self, data):
        query = """INSERT INTO staff (name, role, phone, address, salary)
                   VALUES (%s, %s, %s, %s, %s)"""
        params = (data['name'], data['role'], data['phone'],
                  data['address'], data['salary'])
        return self.db_manager.execute_query(query, params)

    def get_staff_details(self, staff_id):
        query = "SELECT staff_id, name, role, phone, address, salary FROM staff WHERE staff_id = %s"
        return self.db_manager.execute_query(query, (staff_id,), fetch_one=True)

    def get_all_staff(self):
        query = "SELECT staff_id, name, role, phone, salary FROM staff ORDER BY staff_id DESC"
        return self.db_manager.execute_query(query, fetch_all=True)

    def delete_staff(self, staff_id):
        query = "DELETE FROM staff WHERE staff_id = %s"
        return self.db_manager.execute_query(query, (staff_id,))

class AppointmentManager:
    def __init__(self, db_manager):
        self.db_manager = db_manager

    def book_appointment(self, patient_id, doctor_id, booked_date, appointment_date, appointment_note):
        query = """INSERT INTO appointments (patient_id, doctor_id, booked_date, appointment_date, appointment_note)
                   VALUES (%s, %s, %s, %s, %s)"""
        params = (patient_id, doctor_id, booked_date, appointment_date, appointment_note)
        return self.db_manager.execute_query(query, params)

    def get_all_appointments(self):
        query = """SELECT a.appointment_id, p.name AS patient_name, d.name AS doctor_name,
                          a.booked_date, a.appointment_date, a.appointment_note, a.patient_id, a.doctor_id
                   FROM appointments a
                   JOIN patients p ON a.patient_id = p.patient_id
                   JOIN doctors d ON a.doctor_id = d.doctor_id
                   ORDER BY a.appointment_date DESC"""
        return self.db_manager.execute_query(query, fetch_all=True)

    def delete_appointment(self, appointment_id):
        query = "DELETE FROM appointments WHERE appointment_id = %s"
        return self.db_manager.execute_query(query, (appointment_id,))

class MedicalRecordManager:
    def __init__(self, db_manager):
        self.db_manager = db_manager

    def add_medical_record(self, patient_id, doctor_id, data):
        query = """INSERT INTO medical_records (patient_id, doctor_id, treatment, prescriptions, note, admit_date, release_date)
                   VALUES (%s, %s, %s, %s, %s, %s, %s)"""
        params = (patient_id, doctor_id, data['treatment'], data['prescriptions'],
                  data['note'], data['admit_date'], data['release_date'])
        return self.db_manager.execute_query(query, params)

    def get_patient_medical_history(self, patient_id):
        query = """SELECT mr.record_id, mr.record_date, d.name AS doctor_name, mr.treatment, mr.prescriptions, mr.note, mr.admit_date, mr.release_date, mr.doctor_id
                   FROM medical_records mr
                   JOIN doctors d ON mr.doctor_id = d.doctor_id
                   WHERE mr.patient_id = %s
                   ORDER BY mr.record_date DESC"""
        return self.db_manager.execute_query(query, (patient_id,), fetch_all=True)

    def get_medical_record(self, record_id):
        query = "SELECT * FROM medical_records WHERE record_id = %s"
        return self.db_manager.execute_query(query, (record_id,), fetch_one=True)

    def delete_medical_record(self, record_id):
        query = "DELETE FROM medical_records WHERE record_id = %s"
        return self.db_manager.execute_query(query, (record_id,))


# --- Initialize Managers ---
patient_manager = PatientManager(db_manager)
doctor_manager = DoctorManager(db_manager)
staff_manager = StaffManager(db_manager)
appointment_manager = AppointmentManager(db_manager)
medical_record_manager = MedicalRecordManager(db_manager)


# --- Flask Routes ---

@app.route('/')
def index():
    """Home page/dashboard."""
    return render_template('index.html')

@app.route('/patients', methods=['GET', 'POST'])
def patients():
    """Handles patient listing and adding."""
    if request.method == 'POST':
        name = request.form['name'].strip()
        dob_str = request.form['dob'].strip()
        gender = request.form['gender'].strip()
        address = request.form['address'].strip()
        phone = request.form['phone'].strip()
         # Still expecting this from form, but not in DB

        dob = parse_date_ddmmyyyy(dob_str)
        if dob is None and dob_str: # If DOB was provided but invalid
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
                # 'emergency_contact_name': emergency_contact_name # Removed from DB schema, so don't pass
            }
            if patient_manager.add_patient(data):
                flash('Patient added successfully!', 'success')
            else:
                flash('Failed to add patient.', 'error')
        return redirect(url_for('patients'))

    patients_list = patient_manager.get_all_patients()
    # Format DOB for display
    if patients_list:
        for p in patients_list:
            p['dob'] = format_date_ddmmyyyy(p['dob'])
    return render_template('patients.html', patients=patients_list)

@app.route('/patients/delete/<int:patient_id>', methods=['POST'])
def delete_patient(patient_id):
    """Handles patient deletion."""
    if patient_manager.delete_patient(patient_id):
        flash('Patient deleted successfully!', 'success')
    else:
        flash('Failed to delete patient. Ensure no related appointments or medical records exist.', 'error')
    return redirect(url_for('patients'))

@app.route('/doctors', methods=['GET', 'POST'])
def doctors():
    """Handles doctor listing and adding."""
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
def delete_doctor(doctor_id):
    """Handles doctor deletion."""
    if doctor_manager.delete_doctor(doctor_id):
        flash('Doctor deleted successfully!', 'success')
    else:
        flash('Failed to delete doctor. Ensure no related appointments or medical records exist.', 'error')
    return redirect(url_for('doctors'))

@app.route('/staff', methods=['GET', 'POST'])
def staff():
    """Handles staff listing and adding."""
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
def delete_staff(staff_id):
    """Handles staff deletion."""
    if staff_manager.delete_staff(staff_id):
        flash('Staff deleted successfully!', 'success')
    else:
        flash('Failed to delete staff.', 'error')
    return redirect(url_for('staff'))

@app.route('/appointments', methods=['GET', 'POST'])
def appointments():
    """Handles appointment listing and booking."""
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
    # Format dates for display
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
def delete_appointment(appointment_id):
    """Handles appointment deletion."""
    if appointment_manager.delete_appointment(appointment_id):
        flash('Appointment deleted successfully!', 'success')
    else:
        flash('Failed to delete appointment.', 'error')
    return redirect(url_for('appointments'))

@app.route('/medical_records', methods=['GET', 'POST'])
def medical_records():
    """Handles medical record listing and adding."""
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

    # Display medical records for a selected patient (if any)
    selected_patient_id = request.args.get('patient_id', type=int)
    medical_records_list = []
    current_patient_info = None

    if selected_patient_id:
        medical_records_list = medical_record_manager.get_patient_medical_history(selected_patient_id)
        # Format dates for display
        if medical_records_list:
            for rec in medical_records_list:
                rec['admit_date'] = format_date_ddmmyyyy(rec['admit_date'])
                rec['release_date'] = format_date_ddmmyyyy(rec['release_date'])
                # record_date is DATETIME, keep full timestamp for now
                rec['record_date'] = rec['record_date'].strftime('%Y-%m-%d %H:%M:%S') 

        current_patient_info = patient_manager.get_patient(selected_patient_id)
    
    patients_for_combo = patient_manager.get_all_patients()
    doctors_for_combo = doctor_manager.get_all_doctors()

    return render_template('medical_records.html',
                           medical_records=medical_records_list,
                           patients=patients_for_combo,
                           doctors=doctors_for_combo,
                           current_patient_info=current_patient_info, # Pass patient object
                           selected_patient_id=selected_patient_id)

@app.route('/medical_records/delete/<int:record_id>', methods=['POST'])
def delete_medical_record(record_id):
    """Handles medical record deletion."""
    if medical_record_manager.delete_medical_record(record_id):
        flash('Medical record deleted successfully!', 'success')
    else:
        flash('Failed to delete medical record.', 'error')
    # Redirect back to medical records, with the same patient selected if possible
    patient_id = request.form.get('patient_id') # Get patient_id from hidden input on form
    if patient_id:
        return redirect(url_for('medical_records', patient_id=patient_id))
    return redirect(url_for('medical_records'))


if __name__ == '__main__':
    app.run(debug="true") 
