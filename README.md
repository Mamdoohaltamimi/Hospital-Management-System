# Hospital Management System – OOP Project (Python + MySQL)


## Project Overview

This project has evolved from a basic Python Tkinter GUI into a comprehensive,Hospital Management System. It features a modern, intuitive interface built with CustomTkinter, designed to streamline patient, doctor, and appointment management, alongside robust billing, analytics, and activity logging capabilities.

It combines ***Object-Oriented Programming***, a CustomTkinter GUI, and **MySQL** integration. It enables users to manage patient data, doctor assignments, billing, and user authentication through a clean, modular architecture.

---

## Key Features

**Modern Pro Dashboard:** A sleek, professional user interface built with CustomTkinter, offering both Light and Dark modes.

**Patient Management:** Efficient registration, viewing, and deletion of patient records. Includes smart ID generation and character-only name validation.

**Doctor Management:** Comprehensive management of medical staff, with smart ID generation and character-only name validation.

**Appointment Scheduling:** A dedicated module for booking, tracking, and managing patient appointments with specific doctors, including status updates.

**Real-time Analytics:** An interactive dashboard featuring live statistics (Total Patients, Active Doctors, Today's Appointments) and visual charts (Disease Distribution, Patient Gender Ratio) for quick insights.

**Unified Data Export:** Seamlessly export patient, doctor, and appointment data to either Excel (.xlsx) for data analysis or PDF (.pdf) for professional reports.

**Professional PDF Invoicing:** Generate and save detailed patient invoices as professional PDF documents.

**Activity Logs:** A robust logging system that tracks all major actions (additions, deletions, exports) within the system, enhancing security and accountability.

**Smart ID Generation:** Automatic, gap-filling ID assignment (e.g., P001, D001, A001) ensuring unique and sequential IDs even after deletions.

**Input Validation:** Strict validation for input fields (e.g., names accept only characters, age accepts only numbers) to maintain data integrity.

**Database Auto-Migration:** Automatically creates missing tables and columns (like assigned_doctor_id) upon first run, ensuring smooth setup.

**Context-Aware Search:** A dynamic search bar that filters data specifically within the currently active management view (Patients, Doctors, Appointments, Logs).

**Login Authentication System:** Secure user authentication to access the system.

---

##  Tech Stack

- **Language:** Python  
- **GUI:** Tkinter & CustomTkinter  
- **Interface:** CLI and GUI  
- **Database:** MySQL (`hospital_db`)
- **Data Handling:** Pandas, Openpyxl
- **Charting:** Matplotlib
- **PDF Generation:** FPDF2
- **Design Pattern:** Object-Oriented Programming  

---

## Project Structure
```
Hospital-Management/
├── main.py         # CLI version
├── main_gui.py     # GUI interface
├── login.py        # Login window with GUI
├── database.py     # MySQL DB connection
├── model/          # OOP-based entity classes
│ ├── person.py
│ ├── patient.py
│ ├── doctor.py
│ └── billing.py
└── .venv/          # Optional virtual environment
```
---

## Setup Instructions

### 1.  Clone the Repository :

```bash
git clone https://github.com/Mamdoohaltamimi/Hospital-Management-System.git
cd Hospital-Management
```

### 2.  (Optional) Create a Virtual Environment :

```
python -m venv .venv
source .venv/bin/activate  # For Windows: .venv\Scripts\activate
```
### 3.  Install Required Libraries :

```
pip install customtkinter mysql-connector-python pandas openpyxl matplotlib fpdf2

```
### 4. Set Up MySQL Database :

- Ensure your MySQL server is running.
- Open Database.txt and execute its SQL statements in your MySQL client (e.g., phpMyAdmin,XAMPP, MySQL Workbench, or terminal).
- This will create the hospital_db database and necessary tables.

### 5.  Run the Application :
Run the GUI version:
```
python login.py
```
Run the CLI version:
```
python main.py
```

###  Sample Credentials :

- Username: admin
- Password: 1234
(You can customize this in login.py)


## Class Diagram :
The following diagram shows the relationships between core classes in the Hospital Management System for CLI version :

<img src="images/class_diagram.png" alt="Class Diagram" width="400"/>

### Concepts Demonstrated :

- Object-Oriented Programming (Inheritance, Encapsulation, Composition)
- GUI development with CustomTkinter
- Integration of MySQL with Python using mysql-connector-python
- Functional separation between logic, database, and interface
- CLI and GUI support for managing hospital operations
- Data visualization with Matplotlib
- Professional report generation with FPDF2 and Pandas

### Authors :

- [Mamdooh Altamimi]

### References :

- Tkinter used for building the graphical user interface in Python.
- MySQL used as the backend database system.
- Python MySQL Connector for integrating Python with MySQL.
- Object-Oriented Programming (OOP) concepts used to structure classes like Patient, Doctor, and Billing.
- Project developed as part of Object-Oriented Programming coursework at NCBA&E.
