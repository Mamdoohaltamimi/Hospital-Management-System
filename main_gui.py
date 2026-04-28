import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import customtkinter as ctk
from PIL import Image, ImageTk
import os
import re
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from datetime import datetime
from fpdf import FPDF

# --- Database Integration ---
try:
    from database import cursor, conn
    
    def run_migrations():
        # 1. Patients Table Update
        try:
            cursor.execute("SHOW COLUMNS FROM patients LIKE 'assigned_doctor_id'")
            if not cursor.fetchone():
                cursor.execute("ALTER TABLE patients ADD COLUMN assigned_doctor_id VARCHAR(50)")
                conn.commit()
        except: pass

        # 2. Appointments Table
        try:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS appointments (
                    appointment_id VARCHAR(50) PRIMARY KEY,
                    patient_id VARCHAR(50),
                    doctor_id VARCHAR(50),
                    appointment_date DATE,
                    appointment_time TIME,
                    status VARCHAR(50)
                )
            """)
            conn.commit()
        except: pass

        # 3. Activity Logs Table
        try:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS activity_logs (
                    log_id INTEGER PRIMARY KEY AUTO_INCREMENT,
                    action_type VARCHAR(100),
                    details TEXT,
                    timestamp DATETIME
                )
            """)
            conn.commit()
        except: pass

    run_migrations()

except ImportError:
    class MockCursor:
        def execute(self, query, params=None): pass
        def fetchall(self): return []
        def fetchone(self): return (0,)
        @property
        def rowcount(self): return 1
    class MockConn:
        def commit(self): pass
    cursor = MockCursor()
    conn = MockConn()

# --- Appearance Settings ---
ctk.set_appearance_mode("Light")
ctk.set_default_color_theme("blue")

class PDFReport(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 15)
        self.cell(0, 10, 'MEDICORE HOSPITAL - OFFICIAL REPORT', 0, 1, 'C')
        self.set_font('Arial', 'I', 10)
        self.cell(0, 10, f'Generated on: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', 0, 1, 'R')
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

class HospitalGUI(ctk.CTkToplevel):
    def __init__(self, root=None):
        super().__init__(root)

        self.title("Hospital Management System")
        self.geometry("1540x850")
        self.lift()
        self.focus_force()
        
        self.cursor = cursor
        self.conn = conn
        self.search_var = tk.StringVar()
        self.current_view = "Dashboard"

        self.vcmd_numeric = (self.register(self.validate_numeric), '%P')
        self.vcmd_alpha = (self.register(self.validate_alpha), '%P')

        # Main Grid Config
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.create_sidebar()
        
        self.main_container = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.main_container.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.main_container.grid_columnconfigure(0, weight=1)
        self.main_container.grid_rowconfigure(1, weight=1)

        self.header_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        
        self.title_label = ctk.CTkLabel(self.header_frame, text="Dashboard Overview", font=ctk.CTkFont(size=28, weight="bold"))
        self.title_label.pack(side="left")

        self.search_entry = ctk.CTkEntry(self.header_frame, placeholder_text="Search in current page...", width=350, textvariable=self.search_var)
        self.search_entry.pack(side="right", padx=10)
        self.search_btn = ctk.CTkButton(self.header_frame, text="Search", width=100, command=self.execute_search)
        self.search_btn.pack(side="right")

        self.content_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.content_frame.grid(row=1, column=0, sticky="nsew")
        self.content_frame.grid_columnconfigure(0, weight=1)
        self.content_frame.grid_rowconfigure(0, weight=1)

        self.show_dashboard_view()
        if root: root.withdraw()

    def validate_numeric(self, P): return P == "" or P.isdigit()
    def validate_alpha(self, P): return P == "" or all(c.isalpha() or c.isspace() for c in P)

    def create_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=240, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(10, weight=1)

        self.logo = ctk.CTkLabel(self.sidebar, text="MEDICORE\nSYSTEM", font=ctk.CTkFont(size=22, weight="bold"), text_color="#1f6aa5")
        self.logo.grid(row=0, column=0, padx=20, pady=(30, 40))

        self.create_nav_btn("Dashboard", self.show_dashboard_view, row=1)
        self.create_nav_btn("Patient Management", self.show_patient_view, row=2)
        self.create_nav_btn("Doctor Management", self.show_doctor_view, row=3)
        self.create_nav_btn("Appointments", self.show_appointment_view, row=4)
        self.create_nav_btn("Activity Logs", self.show_logs_view, row=5)
        self.create_nav_btn("Billing & Invoices", self.show_billing_view, row=6)
        self.create_nav_btn("About System", self.show_about_box, row=7)
        
        self.mode_menu = ctk.CTkOptionMenu(self.sidebar, values=["Light", "Dark", "System"], command=lambda m: ctk.set_appearance_mode(m))
        self.mode_menu.grid(row=12, column=0, padx=20, pady=(5, 10))
        
        self.exit_btn = ctk.CTkButton(self.sidebar, text="Exit Application", command=self.quit_app, fg_color="#d32f2f", hover_color="#b71c1c", height=40)
        self.exit_btn.grid(row=13, column=0, padx=20, pady=(10, 20), sticky="ew")

    def create_nav_btn(self, text, command, row):
        btn = ctk.CTkButton(self.sidebar, text=text, command=command, height=45, fg_color="transparent", text_color=("gray10", "gray90"), hover_color=("gray70", "gray30"), anchor="w", font=ctk.CTkFont(size=14))
        btn.grid(row=row, column=0, padx=15, pady=5, sticky="ew")
        return btn

    def clear_content(self):
        for widget in self.content_frame.winfo_children(): widget.destroy()

    # --- VIEW: DASHBOARD ---
    def show_dashboard_view(self):
        self.current_view = "Dashboard"
        self.clear_content()
        self.title_label.configure(text="Dashboard Overview")
        self.search_var.set("") # Clear search on view change
        
        dash_container = ctk.CTkScrollableFrame(self.content_frame, fg_color="transparent")
        dash_container.grid(row=0, column=0, sticky="nsew")
        dash_container.grid_columnconfigure((0,1,2), weight=1)
        dash_container.grid_rowconfigure(2, weight=1)

        self.create_stat_card(dash_container, "Total Patients", str(self.get_count("patients")), "#e3f2fd", "#1976d2", 0)
        self.create_stat_card(dash_container, "Active Doctors", str(self.get_count("doctors")), "#f1f8e9", "#388e3c", 1)
        self.create_stat_card(dash_container, "Today's Appointments", str(self.get_count("appointments", f"WHERE appointment_date = '{datetime.now().date()}'")), "#fff3e0", "#f57c00", 2)

        charts_frame = ctk.CTkFrame(dash_container, corner_radius=15)
        charts_frame.grid(row=1, column=0, columnspan=3, sticky="nsew", pady=20, padx=5)
        charts_frame.grid_columnconfigure((0, 1), weight=1)
        self.create_disease_chart(charts_frame, 0)
        self.create_gender_chart(charts_frame, 1)

        table_frame = ctk.CTkFrame(dash_container, corner_radius=15)
        table_frame.grid(row=2, column=0, columnspan=3, sticky="nsew", pady=(0, 20), padx=5)
        table_frame.grid_columnconfigure(0, weight=1)
        table_frame.grid_rowconfigure(1, weight=1)
        ctk.CTkLabel(table_frame, text="Recent Patient Admissions", font=ctk.CTkFont(size=18, weight="bold")).grid(row=0, column=0, sticky="w", padx=20, pady=15)
        self.create_data_table(table_frame, ["ID", "Name", "Age", "Gender", "Disease"], row=1)
        self.refresh_table("patients")

    def create_disease_chart(self, parent, col):
        try:
            self.cursor.execute("SELECT disease, COUNT(*) FROM patients GROUP BY disease")
            data = self.cursor.fetchall()
            if not data: return
            fig, ax = plt.subplots(figsize=(5, 4), dpi=100)
            ax.pie([d[1] for d in data], labels=[d[0] for d in data], autopct='%1.1f%%', startangle=140, colors=plt.cm.Paired.colors)
            ax.set_title("Disease Distribution")
            canvas = FigureCanvasTkAgg(fig, master=parent)
            canvas.draw()
            canvas.get_tk_widget().grid(row=1, column=col, padx=10, pady=10, sticky="nsew")
        except: pass

    def create_gender_chart(self, parent, col):
        try:
            self.cursor.execute("SELECT gender, COUNT(*) FROM patients GROUP BY gender")
            data = self.cursor.fetchall()
            if not data: return
            fig, ax = plt.subplots(figsize=(5, 4), dpi=100)
            ax.bar([d[0] for d in data], [d[1] for d in data], color=['#1976d2', '#e91e63', '#9c27b0'])
            ax.set_title("Patient Gender Ratio")
            canvas = FigureCanvasTkAgg(fig, master=parent)
            canvas.draw()
            canvas.get_tk_widget().grid(row=1, column=col, padx=10, pady=10, sticky="nsew")
        except: pass

    def get_count(self, table, condition=""):
        try:
            self.cursor.execute(f"SELECT COUNT(*) FROM {table} {condition}")
            res = self.cursor.fetchone()
            return res[0] if res else 0
        except: return 0

    def create_stat_card(self, parent, title, value, bg, fg, col):
        card = ctk.CTkFrame(parent, height=120, fg_color=bg, corner_radius=15)
        card.grid(row=0, column=col, padx=10, pady=10, sticky="nsew")
        ctk.CTkLabel(card, text=title, font=ctk.CTkFont(size=14), text_color=fg).pack(pady=(20, 0))
        ctk.CTkLabel(card, text=value, font=ctk.CTkFont(size=28, weight="bold"), text_color=fg).pack(pady=(5, 20))

    # --- VIEW: PATIENT MANAGEMENT ---
    def show_patient_view(self):
        self.current_view = "Patients"
        self.clear_content()
        self.title_label.configure(text="Patient Management")
        self.search_var.set("")
        
        main_split = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        main_split.grid(row=0, column=0, sticky="nsew")
        main_split.grid_columnconfigure(0, weight=1); main_split.grid_columnconfigure(1, weight=3)
        main_split.grid_rowconfigure(0, weight=1)
        
        form_card = ctk.CTkScrollableFrame(main_split, corner_radius=15, label_text="Patient Registration")
        form_card.grid(row=0, column=0, padx=(0, 10), sticky="nsew")
        
        next_id = self.generate_auto_id("patients", "patient_id", "P")
        ctk.CTkLabel(form_card, text=f"Next ID: {next_id}", font=ctk.CTkFont(weight="bold")).pack(pady=10)
        self.p_id_val = next_id
        self.p_name = self.create_form_entry(form_card, "Full Name", self.vcmd_alpha)
        self.p_age = self.create_form_entry(form_card, "Age", self.vcmd_numeric)
        self.p_gender = ctk.CTkComboBox(form_card, values=["Male", "Female", "Other"], width=250); self.p_gender.pack(pady=5)
        self.p_disease = ctk.CTkComboBox(form_card, values=["Fever", "Flu", "Covid-19", "Diabetes", "Injury", "Other"], width=250); self.p_disease.pack(pady=5)
        self.p_doctor = ctk.CTkComboBox(form_card, values=self.get_list("doctors"), width=250); self.p_doctor.pack(pady=5)
        
        ctk.CTkButton(form_card, text="Register Patient", command=self.submit_patient).pack(pady=10)
        ctk.CTkButton(form_card, text="Delete Selected", fg_color="#d32f2f", command=self.delete_patient).pack(pady=5)
        
        ctk.CTkLabel(form_card, text="Export Data:", font=ctk.CTkFont(size=12, weight="bold")).pack(pady=(15, 0))
        self.p_export_format = ctk.CTkOptionMenu(form_card, values=["Excel (.xlsx)", "PDF (.pdf)"], width=200)
        self.p_export_format.pack(pady=5)
        ctk.CTkButton(form_card, text="Export Now", fg_color="#2e7d32", command=lambda: self.unified_export("patients", ["ID", "Name", "Age", "Gender", "Disease", "Doctor ID"], self.p_export_format.get())).pack(pady=5)

        table_card = ctk.CTkFrame(main_split, corner_radius=15)
        table_card.grid(row=0, column=1, sticky="nsew")
        table_card.grid_rowconfigure(0, weight=1); table_card.grid_columnconfigure(0, weight=1)
        self.create_data_table(table_card, ["ID", "Name", "Age", "Gender", "Disease", "Doctor ID"], row=0)
        self.refresh_table("patients")

    # --- VIEW: DOCTOR MANAGEMENT ---
    def show_doctor_view(self):
        self.current_view = "Doctors"
        self.clear_content()
        self.title_label.configure(text="Doctor Management")
        self.search_var.set("")
        
        main_split = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        main_split.grid(row=0, column=0, sticky="nsew")
        main_split.grid_columnconfigure(0, weight=1); main_split.grid_columnconfigure(1, weight=3)
        main_split.grid_rowconfigure(0, weight=1)
        
        form_card = ctk.CTkScrollableFrame(main_split, corner_radius=15, label_text="Doctor Registration")
        form_card.grid(row=0, column=0, padx=(0, 10), sticky="nsew")
        
        next_id = self.generate_auto_id("doctors", "doctor_id", "D")
        ctk.CTkLabel(form_card, text=f"Next ID: {next_id}", font=ctk.CTkFont(weight="bold")).pack(pady=10)
        self.d_id_val = next_id
        self.d_name = self.create_form_entry(form_card, "Full Name", self.vcmd_alpha)
        self.d_age = self.create_form_entry(form_card, "Age", self.vcmd_numeric)
        self.d_gender = ctk.CTkComboBox(form_card, values=["Male", "Female", "Other"], width=250); self.d_gender.pack(pady=5)
        self.d_spec = ctk.CTkComboBox(form_card, values=["Cardiology", "Neurology", "Pediatrics", "Orthopedics", "Surgery", "Other"], width=250); self.d_spec.pack(pady=5)
        
        ctk.CTkButton(form_card, text="Register Doctor", command=self.submit_doctor).pack(pady=10)
        ctk.CTkButton(form_card, text="Delete Selected", fg_color="#d32f2f", command=self.delete_doctor).pack(pady=5)
        
        ctk.CTkLabel(form_card, text="Export Data:", font=ctk.CTkFont(size=12, weight="bold")).pack(pady=(15, 0))
        self.d_export_format = ctk.CTkOptionMenu(form_card, values=["Excel (.xlsx)", "PDF (.pdf)"], width=200)
        self.d_export_format.pack(pady=5)
        ctk.CTkButton(form_card, text="Export Now", fg_color="#2e7d32", command=lambda: self.unified_export("doctors", ["ID", "Name", "Age", "Gender", "Specialization"], self.d_export_format.get())).pack(pady=5)

        table_card = ctk.CTkFrame(main_split, corner_radius=15)
        table_card.grid(row=0, column=1, sticky="nsew")
        table_card.grid_rowconfigure(0, weight=1); table_card.grid_columnconfigure(0, weight=1)
        self.create_data_table(table_card, ["ID", "Name", "Age", "Gender", "Specialization"], row=0)
        self.refresh_table("doctors")

    # --- VIEW: APPOINTMENTS ---
    def show_appointment_view(self):
        self.current_view = "Appointments"
        self.clear_content()
        self.title_label.configure(text="Appointment Scheduling")
        self.search_var.set("")
        
        main_split = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        main_split.grid(row=0, column=0, sticky="nsew")
        main_split.grid_columnconfigure(0, weight=1); main_split.grid_columnconfigure(1, weight=3)
        main_split.grid_rowconfigure(0, weight=1)
        
        form_card = ctk.CTkScrollableFrame(main_split, corner_radius=15, label_text="Book Appointment")
        form_card.grid(row=0, column=0, padx=(0, 10), sticky="nsew")
        
        next_id = self.generate_auto_id("appointments", "appointment_id", "A")
        ctk.CTkLabel(form_card, text=f"Next ID: {next_id}", font=ctk.CTkFont(weight="bold")).pack(pady=10)
        self.a_id_val = next_id
        self.a_patient = ctk.CTkComboBox(form_card, values=self.get_list("patients"), width=250); self.a_patient.pack(pady=5)
        self.a_doctor = ctk.CTkComboBox(form_card, values=self.get_list("doctors"), width=250); self.a_doctor.pack(pady=5)
        self.a_date = self.create_form_entry(form_card, "Date (YYYY-MM-DD)")
        self.a_date.insert(0, str(datetime.now().date()))
        self.a_time = self.create_form_entry(form_card, "Time (HH:MM)")
        self.a_time.insert(0, "10:00")
        self.a_status = ctk.CTkComboBox(form_card, values=["Scheduled", "Completed", "Cancelled"], width=250); self.a_status.pack(pady=5)
        
        ctk.CTkButton(form_card, text="Book Appointment", command=self.submit_appointment).pack(pady=10)
        ctk.CTkButton(form_card, text="Delete Selected", fg_color="#d32f2f", command=self.delete_appointment).pack(pady=5)
        
        ctk.CTkLabel(form_card, text="Export Data:", font=ctk.CTkFont(size=12, weight="bold")).pack(pady=(15, 0))
        self.a_export_format = ctk.CTkOptionMenu(form_card, values=["Excel (.xlsx)", "PDF (.pdf)"], width=200)
        self.a_export_format.pack(pady=5)
        ctk.CTkButton(form_card, text="Export Now", fg_color="#2e7d32", command=lambda: self.unified_export("appointments", ["ID", "Patient ID", "Doctor ID", "Date", "Time", "Status"], self.a_export_format.get())).pack(pady=5)

        table_card = ctk.CTkFrame(main_split, corner_radius=15)
        table_card.grid(row=0, column=1, sticky="nsew")
        table_card.grid_rowconfigure(0, weight=1); table_card.grid_columnconfigure(0, weight=1)
        self.create_data_table(table_card, ["ID", "Patient ID", "Doctor ID", "Date", "Time", "Status"], row=0)
        self.refresh_table("appointments")

    # --- VIEW: ACTIVITY LOGS ---
    def show_logs_view(self):
        self.current_view = "Logs"
        self.clear_content()
        self.title_label.configure(text="System Activity Logs")
        self.search_var.set("")
        
        logs_frame = ctk.CTkFrame(self.content_frame, corner_radius=15)
        logs_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        logs_frame.grid_columnconfigure(0, weight=1)
        logs_frame.grid_rowconfigure(1, weight=1)
        
        ctk.CTkLabel(logs_frame, text="Recent System Actions", font=ctk.CTkFont(size=18, weight="bold")).grid(row=0, column=0, sticky="w", padx=20, pady=15)
        
        self.create_data_table(logs_frame, ["Log ID", "Action Type", "Details", "Timestamp"], row=1)
        self.refresh_table("activity_logs")
        
        ctk.CTkButton(logs_frame, text="Clear All Logs", fg_color="#d32f2f", command=self.clear_logs_logic).grid(row=2, column=0, pady=20)

    # --- VIEW: BILLING ---
    def show_billing_view(self):
        self.current_view = "Billing"
        self.clear_content()
        self.title_label.configure(text="Billing & Invoices")
        self.search_var.set("")
        
        bill_frame = ctk.CTkFrame(self.content_frame, corner_radius=15)
        bill_frame.grid(row=0, column=0, padx=50, pady=20, sticky="nsew")
        bill_frame.grid_columnconfigure((0,1), weight=1)
        bill_frame.grid_rowconfigure(0, weight=1)
        
        input_area = ctk.CTkFrame(bill_frame, fg_color="transparent")
        input_area.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        self.bill_pid = self.create_form_entry(input_area, "Patient ID")
        self.bill_days = self.create_form_entry(input_area, "Days Admitted")
        self.bill_rate = self.create_form_entry(input_area, "Daily Rate ($)")
        ctk.CTkButton(input_area, text="Calculate & Preview", command=self.calculate_bill, width=250, height=45).pack(pady=30)

        preview_area = ctk.CTkFrame(bill_frame, fg_color="#f5f5f5", corner_radius=10)
        preview_area.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        self.bill_text = tk.Text(preview_area, font=("Consolas", 12), bg="#f5f5f5", fg="black", bd=0, padx=20, pady=20)
        self.bill_text.pack(fill="both", expand=True)
        ctk.CTkButton(preview_area, text="Save as PDF Invoice", fg_color="#c62828", command=self.save_pdf_invoice).pack(pady=20)

    # --- LOGIC HELPERS ---
    def log_activity(self, action, details):
        try:
            self.cursor.execute("INSERT INTO activity_logs (action_type, details, timestamp) VALUES (%s, %s, %s)", (action, details, datetime.now()))
            self.conn.commit()
        except: pass

    def clear_logs_logic(self):
        if messagebox.askyesno("Confirm", "Clear all activity logs?"):
            try:
                self.cursor.execute("DELETE FROM activity_logs")
                self.conn.commit(); self.show_logs_view()
            except: pass

    def unified_export(self, table, headers, format_choice):
        if "Excel" in format_choice: self.export_to_excel(table)
        else: self.export_to_pdf(table, headers)
        self.log_activity("Export Data", f"Exported {table} as {format_choice}")

    def create_form_entry(self, parent, label, vcmd=None):
        ctk.CTkLabel(parent, text=f"{label}:").pack(pady=(10,0), anchor="w", padx=25)
        entry = ctk.CTkEntry(parent, placeholder_text=label, width=250, height=35, validate="key" if vcmd else None, validatecommand=vcmd)
        entry.pack(pady=5); return entry

    def get_list(self, table):
        try:
            self.cursor.execute(f"SELECT {table[:-1]}_id, name FROM {table}")
            rows = self.cursor.fetchall()
            return [f"{r[0]} - {r[1]}" for r in rows] if rows else ["None Available"]
        except: return ["None Available"]

    def generate_auto_id(self, table, id_col, prefix):
        try:
            self.cursor.execute(f"SELECT {id_col} FROM {table}")
            all_ids = [re.findall(r'\d+', str(r[0])) for r in self.cursor.fetchall()]
            nums = {int(n[0]) for n in all_ids if n}
            next_num = 1
            while next_num in nums: next_num += 1
            return f"{prefix}{str(next_num).zfill(3)}"
        except: return f"{prefix}001"

    def refresh_table(self, table):
        for item in self.tree.get_children(): self.tree.delete(item)
        try:
            self.cursor.execute(f"SELECT * FROM {table} ORDER BY 1 DESC" if table == "activity_logs" else f"SELECT * FROM {table}")
            for row in self.cursor.fetchall(): self.tree.insert("", "end", values=row)
        except: pass

    def create_data_table(self, parent, columns, row):
        style = ttk.Style(); style.theme_use("default")
        style.configure("Treeview", rowheight=40, font=("Segoe UI", 11))
        self.tree = ttk.Treeview(parent, columns=columns, show="headings")
        for col in columns: self.tree.heading(col, text=col); self.tree.column(col, width=150, anchor="center")
        self.tree.grid(row=row, column=0, sticky="nsew", padx=10, pady=10)
        
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.grid(row=row, column=1, sticky="ns")
        
        parent.grid_rowconfigure(row, weight=1); parent.grid_columnconfigure(0, weight=1)

    def submit_patient(self):
        doc_id = self.p_doctor.get().split(" - ")[0] if " - " in self.p_doctor.get() else ""
        try:
            self.cursor.execute("INSERT INTO patients VALUES (%s, %s, %s, %s, %s, %s)", (self.p_id_val, self.p_name.get(), self.p_age.get(), self.p_gender.get(), self.p_disease.get(), doc_id))
            self.conn.commit(); self.log_activity("Add Patient", f"Registered patient {self.p_name.get()} ({self.p_id_val})")
            messagebox.showinfo("Success", "Patient registered!"); self.show_patient_view()
        except Exception as e: messagebox.showerror("Error", str(e))

    def submit_doctor(self):
        try:
            self.cursor.execute("INSERT INTO doctors VALUES (%s, %s, %s, %s, %s)", (self.d_id_val, self.d_name.get(), self.d_age.get(), self.d_gender.get(), self.d_spec.get()))
            self.conn.commit(); self.log_activity("Add Doctor", f"Registered doctor {self.d_name.get()} ({self.d_id_val})")
            messagebox.showinfo("Success", "Doctor registered!"); self.show_doctor_view()
        except Exception as e: messagebox.showerror("Error", str(e))

    def submit_appointment(self):
        p_id = self.a_patient.get().split(" - ")[0] if " - " in self.a_patient.get() else ""
        d_id = self.a_doctor.get().split(" - ")[0] if " - " in self.a_doctor.get() else ""
        try:
            self.cursor.execute("INSERT INTO appointments VALUES (%s, %s, %s, %s, %s, %s)", (self.a_id_val, p_id, d_id, self.a_date.get(), self.a_time.get(), self.a_status.get()))
            self.conn.commit(); self.log_activity("Book Appointment", f"Booked appointment {self.a_id_val} for patient {p_id}")
            messagebox.showinfo("Success", "Appointment booked!"); self.show_appointment_view()
        except Exception as e: messagebox.showerror("Error", str(e))

    def delete_logic(self, table, id_col, refresh_func):
        sel = self.tree.selection()
        if not sel: return
        val = self.tree.item(sel[0])['values'][0]
        if messagebox.askyesno("Confirm", f"Delete {val}?"):
            try:
                self.cursor.execute(f"DELETE FROM {table} WHERE {id_col} = %s", (val,))
                self.conn.commit(); self.log_activity("Delete Record", f"Deleted {val} from {table}")
                refresh_func()
            except: pass

    def delete_patient(self): self.delete_logic("patients", "patient_id", self.show_patient_view)
    def delete_doctor(self): self.delete_logic("doctors", "doctor_id", self.show_doctor_view)
    def delete_appointment(self): self.delete_logic("appointments", "appointment_id", self.show_appointment_view)

    def calculate_bill(self):
        try:
            total = int(self.bill_days.get()) * int(self.bill_rate.get())
            self.bill_text.delete("1.0", tk.END)
            self.bill_text.insert(tk.END, f"\n      MEDICORE HOSPITAL\n      ------------------\n\n Patient ID:    {self.bill_pid.get()}\n Total Amount:  ${total}\n Status:        PENDING\n")
            self.log_activity("Generate Bill", f"Calculated bill for patient {self.bill_pid.get()}")
        except: messagebox.showerror("Error", "Invalid input")

    def save_pdf_invoice(self):
        content = self.bill_text.get("1.0", tk.END).strip()
        if not content: return
        path = filedialog.asksaveasfilename(defaultextension=".pdf")
        if path:
            pdf = PDFReport(); pdf.add_page(); pdf.set_font("Courier", size=12)
            for line in content.split('\n'): pdf.cell(0, 10, line, 0, 1)
            pdf.output(path); self.log_activity("Save Invoice", f"Saved PDF invoice for patient {self.bill_pid.get()}")
            messagebox.showinfo("Success", "PDF Invoice Saved!")

    def export_to_excel(self, table):
        try:
            self.cursor.execute(f"SELECT * FROM {table}")
            df = pd.DataFrame(self.cursor.fetchall())
            path = filedialog.asksaveasfilename(defaultextension=".xlsx")
            if path: df.to_excel(path, index=False); messagebox.showinfo("Success", "Exported!")
        except: pass

    def export_to_pdf(self, table, headers):
        try:
            self.cursor.execute(f"SELECT * FROM {table}")
            rows = self.cursor.fetchall()
            if not rows: return
            path = filedialog.asksaveasfilename(defaultextension=".pdf")
            if path:
                pdf = PDFReport(); pdf.add_page(); pdf.set_font("Arial", 'B', 10)
                col_width = pdf.epw / len(headers)
                for h in headers: pdf.cell(col_width, 10, h, 1)
                pdf.ln(); pdf.set_font("Arial", size=9)
                for row in rows:
                    for item in row: pdf.cell(col_width, 10, str(item), 1)
                    pdf.ln()
                pdf.output(path); messagebox.showinfo("Success", "PDF Report Exported!")
        except Exception as e: messagebox.showerror("Error", str(e))

    def execute_search(self):
        q = self.search_var.get().strip()
        view = self.current_view.lower()
        
        # Mapping view names to database tables and searchable columns
        search_map = {
            "dashboard": ("patients", ["patient_id", "name", "disease"]),
            "patients": ("patients", ["patient_id", "name", "gender", "disease", "assigned_doctor_id"]),
            "doctors": ("doctors", ["doctor_id", "name", "gender", "specialization"]),
            "appointments": ("appointments", ["appointment_id", "patient_id", "doctor_id", "status"]),
            "logs": ("activity_logs", ["log_id", "action_type", "details"])
        }
        
        if view not in search_map: return
        table, columns = search_map[view]
        
        if not q: self.refresh_table(table); return
        
        try:
            # Build dynamic query to search across all relevant columns
            where_clause = " OR ".join([f"{col} LIKE %s" for col in columns])
            query = f"SELECT * FROM {table} WHERE {where_clause}"
            params = [f"%{q}%"] * len(columns)
            
            self.cursor.execute(query, tuple(params))
            for item in self.tree.get_children(): self.tree.delete(item)
            for row in self.cursor.fetchall(): self.tree.insert("", "end", values=row)
        except Exception as e:
            messagebox.showerror("Search Error", str(e))

    def show_about_box(self): messagebox.showinfo("About",  "Hospital Management System \n Developed by: Mamdooh Altamimi")
    def quit_app(self): self.quit(); os._exit(0)

if __name__ == "__main__":
    root = tk.Tk()
    app = HospitalGUI(root)
    root.mainloop()