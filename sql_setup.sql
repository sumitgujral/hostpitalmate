-- Drop the database if it already exists to ensure a clean start
DROP DATABASE IF EXISTS hospitalmate_db6;

-- Create the new database
CREATE DATABASE hospitalmate_db6;

-- Use the new database
USE hospitalmate_db6;

-- 1. Patient Management
CREATE TABLE IF NOT EXISTS patients (
    patient_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    dob DATE, 
    gender VARCHAR(10),
    address TEXT,
    phone VARCHAR(20)
);

-- 2. Doctor Management
CREATE TABLE IF NOT EXISTS doctors (
    doctor_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    qualification VARCHAR(255),
    specialization VARCHAR(255),
    phone VARCHAR(20)
);

-- 3. Staff Management
CREATE TABLE IF NOT EXISTS staff (
    staff_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    role VARCHAR(100),
    phone VARCHAR(20),
    address TEXT,
    salary DECIMAL(10, 2)
);

-- 4. Appointment Scheduling
CREATE TABLE IF NOT EXISTS appointments (
    appointment_id INT AUTO_INCREMENT PRIMARY KEY,
    patient_id INT NOT NULL,
    doctor_id INT NOT NULL,
    booked_date DATE NOT NULL,      
    appointment_date DATE NOT NULL, 
    appointment_note TEXT,          
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id) ON DELETE CASCADE,
    FOREIGN KEY (doctor_id) REFERENCES doctors(doctor_id) ON DELETE CASCADE
);

-- 5. Medical Records 
CREATE TABLE IF NOT EXISTS medical_records (
    record_id INT AUTO_INCREMENT PRIMARY KEY,
    patient_id INT NOT NULL,
    doctor_id INT NOT NULL,
    record_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    treatment TEXT,
    prescriptions TEXT,
    note TEXT,                      
    admit_date DATE,             
    release_date DATE,           
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id) ON DELETE CASCADE,
    FOREIGN KEY (doctor_id) REFERENCES doctors(doctor_id) ON DELETE CASCADE
);
