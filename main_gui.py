import tkinter as tk
from tkinter import ttk, messagebox
import customtkinter as ctk
from PIL import Image, ImageTk
import os
import re

# --- Database Integration ---
try:
    from database import cursor, conn
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

class HospitalGUI(ctk.CTkToplevel):
    """
    Optimized Hospital Management System GUI.
    Features: Character-only Name validation, Numeric-only Age, and Gap-filling Auto-ID.
    """
    def __init__(self, root=None):
        super().__init__(root)

        # Window Setup
        self.title("Hospital Management System - Pro Dashboard")
        self.geometry("1540x850")
        
        # Ensure it stays on top and gets focus
        self.lift()
        self.focus_force()
        
        # Database
        self.cursor = cursor
        self.conn = conn

        # State Variables
        self.search_var = tk.StringVar()
        self.current_view = "Dashboard"

        # Register Validation Commands
        self.vcmd_numeric = (self.register(self.validate_numeric), '%P')
        self.vcmd_alpha = (self.register(self.validate_alpha), '%P')

        # Layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Sidebar
        self.create_sidebar()
        
        # Main Container
        self.main_container = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.main_container.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.main_container.grid_columnconfigure(0, weight=1)
        self.main_container.grid_rowconfigure(1, weight=1)

        # Top Header
        self.header_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        
        self.title_label = ctk.CTkLabel(self.header_frame, text="Dashboard Overview", font=ctk.CTkFont(size=28, weight="bold"))
        self.title_label.pack(side="left")

        self.search_entry = ctk.CTkEntry(self.header_frame, placeholder_text="Search by Name or ID...", width=350, textvariable=self.search_var)
        self.search_entry.pack(side="right", padx=10)
        self.search_btn = ctk.CTkButton(self.header_frame, text="Search", width=100, command=self.execute_search)
        self.search_btn.pack(side="right")

        # Content Area
        self.content_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.content_frame.grid(row=1, column=0, sticky="nsew")
        self.content_frame.grid_columnconfigure(0, weight=1)
        self.content_frame.grid_rowconfigure(0, weight=1)

        # Initialize Views
        self.show_dashboard_view()
        
        # Handle the login root window if it exists
        if root:
            root.withdraw()

    def validate_numeric(self, P):
        """Validation function to allow only numbers."""
        if P == "" or P.isdigit():
            return True
        return False

    def validate_alpha(self, P):
        """Validation function to allow only letters and spaces."""
        if P == "" or all(c.isalpha() or c.isspace() for c in P):
            return True
        return False

    def create_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=240, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(10, weight=1)

        # Logo
        self.logo = ctk.CTkLabel(self.sidebar, text="MEDICORE\nSYSTEM", font=ctk.CTkFont(size=22, weight="bold"), text_color="#1f6aa5")
        self.logo.grid(row=0, column=0, padx=20, pady=(30, 40))

        # Nav Buttons
        self.nav_dashboard = self.create_nav_btn("Dashboard", self.show_dashboard_view, row=1)
        self.nav_patients = self.create_nav_btn("Patient Management", self.show_patient_view, row=2)
        self.nav_doctors = self.create_nav_btn("Doctor Management", self.show_doctor_view, row=3)
        self.nav_billing = self.create_nav_btn("Billing & Invoices", self.show_billing_view, row=4)
        
        # New Buttons: About and Exit
        self.nav_about = self.create_nav_btn("About System", self.show_about_box, row=5)
        
        # Settings and Exit at bottom
        self.mode_label = ctk.CTkLabel(self.sidebar, text="Theme Mode:", font=ctk.CTkFont(size=12))
        self.mode_label.grid(row=11, column=0, padx=20, pady=(10, 0), sticky="w")
        self.mode_menu = ctk.CTkOptionMenu(self.sidebar, values=["Light", "Dark", "System"], command=lambda m: ctk.set_appearance_mode(m))
        self.mode_menu.grid(row=12, column=0, padx=20, pady=(5, 10))
        
        self.exit_btn = ctk.CTkButton(self.sidebar, text="Exit Application", command=self.quit_app, fg_color="#d32f2f", hover_color="#b71c1c", height=40)
        self.exit_btn.grid(row=13, column=0, padx=20, pady=(10, 20), sticky="ew")

    def create_nav_btn(self, text, command, row):
        btn = ctk.CTkButton(self.sidebar, text=text, command=command, height=45, fg_color="transparent", text_color=("gray10", "gray90"), hover_color=("gray70", "gray30"), anchor="w", font=ctk.CTkFont(size=14))
        btn.grid(row=row, column=0, padx=15, pady=5, sticky="ew")
        return btn

    def clear_content(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()

    # --- VIEW: DASHBOARD ---
    def show_dashboard_view(self):
        self.current_view = "Dashboard"
        self.clear_content()
        self.title_label.configure(text="Dashboard Overview")
        
        dash_container = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        dash_container.grid(row=0, column=0, sticky="nsew")
        dash_container.grid_columnconfigure((0,1,2), weight=1)
        dash_container.grid_rowconfigure(1, weight=1)

        # Fetch Real Data for Stats
        total_patients = self.get_count("patients")
        total_doctors = self.get_count("doctors")
        pending_tasks = self.get_count("patients", "WHERE assigned_doctor_id IS NULL")

        # Stats Cards with Real Data
        self.create_stat_card(dash_container, "Total Patients", str(total_patients), "#e3f2fd", "#1976d2", 0)
        self.create_stat_card(dash_container, "Active Doctors", str(total_doctors), "#f1f8e9", "#388e3c", 1)
        self.create_stat_card(dash_container, "Unassigned Patients", str(pending_tasks), "#fff3e0", "#f57c00", 2)

        # Recent Activity Table (Large)
        table_frame = ctk.CTkFrame(dash_container, corner_radius=15)
        table_frame.grid(row=1, column=0, columnspan=3, sticky="nsew", pady=(20, 0), padx=5)
        table_frame.grid_columnconfigure(0, weight=1)
        table_frame.grid_rowconfigure(1, weight=1)
        
        ctk.CTkLabel(table_frame, text="Recent Patient Admissions", font=ctk.CTkFont(size=18, weight="bold")).grid(row=0, column=0, sticky="w", padx=20, pady=15)
        
        self.create_data_table(table_frame, ["ID", "Name", "Age", "Gender", "Disease"], row=1)
        self.refresh_patient_table()

    def get_count(self, table, condition=""):
        try:
            self.cursor.execute(f"SELECT COUNT(*) FROM {table} {condition}")
            result = self.cursor.fetchone()
            return result[0] if result else 0
        except:
            return 0

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
        
        main_split = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        main_split.grid(row=0, column=0, sticky="nsew")
        main_split.grid_columnconfigure(0, weight=1) # Form on Left (1x)
        main_split.grid_columnconfigure(1, weight=3) # Table on Right (3x)
        main_split.grid_rowconfigure(0, weight=1)

        # Left: Compact Form
        form_card = ctk.CTkScrollableFrame(main_split, corner_radius=15, label_text="Patient Registration")
        form_card.grid(row=0, column=0, padx=(0, 10), pady=0, sticky="nsew")
        
        # Auto-ID Display
        next_id = self.generate_auto_id("patients", "patient_id", "P")
        self.p_id_display = ctk.CTkLabel(form_card, text=f"Next ID: {next_id}", font=ctk.CTkFont(size=14, weight="bold"), text_color="#1f6aa5")
        self.p_id_display.pack(pady=(10, 5))
        self.p_id_val = next_id # Store for submission
        
        # Name Input with Character Validation
        ctk.CTkLabel(form_card, text="Full Name:", font=ctk.CTkFont(size=12)).pack(pady=(10, 0), anchor="w", padx=25)
        self.p_name = ctk.CTkEntry(form_card, placeholder_text="Letters only", width=250, height=35, validate="key", validatecommand=self.vcmd_alpha)
        self.p_name.pack(pady=5)
        
        # Age Input with Numeric Validation
        ctk.CTkLabel(form_card, text="Age:", font=ctk.CTkFont(size=12)).pack(pady=(10, 0), anchor="w", padx=25)
        self.p_age = ctk.CTkEntry(form_card, placeholder_text="Numbers only", width=250, height=35, validate="key", validatecommand=self.vcmd_numeric)
        self.p_age.pack(pady=5)
        
        ctk.CTkLabel(form_card, text="Gender:", font=ctk.CTkFont(size=12)).pack(pady=(10, 0), anchor="w", padx=25)
        self.p_gender = ctk.CTkComboBox(form_card, values=["Male", "Female", "Other"], width=250)
        self.p_gender.pack(pady=5)
        
        ctk.CTkLabel(form_card, text="Disease:", font=ctk.CTkFont(size=12)).pack(pady=(10, 0), anchor="w", padx=25)
        self.p_disease = ctk.CTkComboBox(form_card, values=["Fever", "Flu", "Covid-19", "Diabetes", "Injury", "Other"], width=250)
        self.p_disease.pack(pady=5)
        
        ctk.CTkButton(form_card, text="Register Patient", command=self.submit_patient_logic, width=200, height=40).pack(pady=20)
        ctk.CTkButton(form_card, text="Delete Selected", fg_color="#d32f2f", hover_color="#b71c1c", command=self.delete_patient_logic, width=200).pack(pady=5)

        # Right: Large Table
        table_card = ctk.CTkFrame(main_split, corner_radius=15)
        table_card.grid(row=0, column=1, padx=0, pady=0, sticky="nsew")
        table_card.grid_columnconfigure(0, weight=1)
        table_card.grid_rowconfigure(0, weight=1)
        
        self.create_data_table(table_card, ["ID", "Name", "Age", "Gender", "Disease", "Doctor ID"], row=0)
        self.refresh_patient_table()

    # --- VIEW: DOCTOR MANAGEMENT ---
    def show_doctor_view(self):
        self.current_view = "Doctors"
        self.clear_content()
        self.title_label.configure(text="Doctor Management")
        
        main_split = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        main_split.grid(row=0, column=0, sticky="nsew")
        main_split.grid_columnconfigure(0, weight=1) # Form on Left (1x)
        main_split.grid_columnconfigure(1, weight=3) # Table on Right (3x)
        main_split.grid_rowconfigure(0, weight=1)

        # Left: Compact Form
        form_card = ctk.CTkScrollableFrame(main_split, corner_radius=15, label_text="Doctor Registration")
        form_card.grid(row=0, column=0, padx=(0, 10), pady=0, sticky="nsew")
        
        # Auto-ID Display
        next_id = self.generate_auto_id("doctors", "doctor_id", "D")
        self.d_id_display = ctk.CTkLabel(form_card, text=f"Next ID: {next_id}", font=ctk.CTkFont(size=14, weight="bold"), text_color="#1f6aa5")
        self.d_id_display.pack(pady=(10, 5))
        self.d_id_val = next_id # Store for submission
        
        # Name Input with Character Validation
        ctk.CTkLabel(form_card, text="Full Name:", font=ctk.CTkFont(size=12)).pack(pady=(10, 0), anchor="w", padx=25)
        self.d_name = ctk.CTkEntry(form_card, placeholder_text="Letters only", width=250, height=35, validate="key", validatecommand=self.vcmd_alpha)
        self.d_name.pack(pady=5)
        
        # Age Input with Numeric Validation
        ctk.CTkLabel(form_card, text="Age:", font=ctk.CTkFont(size=12)).pack(pady=(10, 0), anchor="w", padx=25)
        self.d_age = ctk.CTkEntry(form_card, placeholder_text="Numbers only", width=250, height=35, validate="key", validatecommand=self.vcmd_numeric)
        self.d_age.pack(pady=5)
        
        ctk.CTkLabel(form_card, text="Gender:", font=ctk.CTkFont(size=12)).pack(pady=(10, 0), anchor="w", padx=25)
        self.d_gender = ctk.CTkComboBox(form_card, values=["Male", "Female", "Other"], width=250)
        self.d_gender.pack(pady=5)
        
        ctk.CTkLabel(form_card, text="Specialization:", font=ctk.CTkFont(size=12)).pack(pady=(10, 0), anchor="w", padx=25)
        self.d_spec = ctk.CTkComboBox(form_card, values=["Cardiology", "Neurology", "Pediatrics", "Orthopedics", "General Surgery", "Dermatology", "Other"], width=250)
        self.d_spec.pack(pady=5)
        
        ctk.CTkButton(form_card, text="Register Doctor", command=self.submit_doctor_logic, width=200, height=40).pack(pady=20)
        ctk.CTkButton(form_card, text="Delete Selected", fg_color="#d32f2f", hover_color="#b71c1c", command=self.delete_doctor_logic, width=200).pack(pady=5)

        # Right: Large Table
        table_card = ctk.CTkFrame(main_split, corner_radius=15)
        table_card.grid(row=0, column=1, padx=0, pady=0, sticky="nsew")
        table_card.grid_columnconfigure(0, weight=1)
        table_card.grid_rowconfigure(0, weight=1)
        
        self.create_data_table(table_card, ["ID", "Name", "Age", "Gender", "Specialization"], row=0)
        self.refresh_doctor_table()

    # --- VIEW: BILLING ---
    def show_billing_view(self):
        self.current_view = "Billing"
        self.clear_content()
        self.title_label.configure(text="Billing & Invoices")
        
        bill_frame = ctk.CTkFrame(self.content_frame, corner_radius=15)
        bill_frame.grid(row=0, column=0, padx=50, pady=20, sticky="nsew")
        bill_frame.grid_columnconfigure(0, weight=1)
        bill_frame.grid_columnconfigure(1, weight=1)
        bill_frame.grid_rowconfigure(0, weight=1)

        # Left: Inputs
        input_area = ctk.CTkFrame(bill_frame, fg_color="transparent")
        input_area.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        
        ctk.CTkLabel(input_area, text="Generate Invoice", font=ctk.CTkFont(size=20, weight="bold")).pack(pady=20)
        self.bill_pid = self.create_input(input_area, "Patient ID")
        self.bill_days = self.create_input(input_area, "Days Admitted")
        self.bill_rate = self.create_input(input_area, "Daily Rate ($)")
        
        ctk.CTkButton(input_area, text="Calculate & Preview", command=self.calculate_bill_logic, width=250, height=45).pack(pady=30)

        # Right: Preview
        preview_area = ctk.CTkFrame(bill_frame, fg_color="#f5f5f5", corner_radius=10)
        preview_area.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        
        ctk.CTkLabel(preview_area, text="Invoice Preview", font=ctk.CTkFont(size=14, weight="bold"), text_color="black").pack(pady=10)
        self.bill_text = tk.Text(preview_area, font=("Consolas", 12), bg="#f5f5f5", fg="black", bd=0, padx=20, pady=20)
        self.bill_text.pack(fill="both", expand=True)
        
        ctk.CTkButton(preview_area, text="Print Invoice", fg_color="#2e7d32", hover_color="#1b5e20", width=200).pack(pady=20)

    # --- HELPERS ---
    def create_input(self, parent, placeholder):
        entry = ctk.CTkEntry(parent, placeholder_text=placeholder, width=250, height=35)
        entry.pack(pady=10)
        return entry

    def create_data_table(self, parent, columns, row):
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", background="#ffffff", foreground="#333333", rowheight=40, fieldbackground="#ffffff", borderwidth=0, font=("Segoe UI", 11))
        style.map("Treeview", background=[('selected', '#1f6aa5')])
        style.configure("Treeview.Heading", background="#f0f0f0", font=("Segoe UI", 12, "bold"), borderwidth=0)

        self.tree = ttk.Treeview(parent, columns=columns, show="headings")
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=150, anchor="center")
        
        self.tree.grid(row=row, column=0, sticky="nsew", padx=10, pady=10)
        
        # Scrollbar
        sb = ctk.CTkScrollbar(parent, orientation="vertical", command=self.tree.yview)
        sb.grid(row=row, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=sb.set)

    def generate_auto_id(self, table, id_col, prefix):
        try:
            # Explicitly check if table is empty first
            self.cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = self.cursor.fetchone()[0]
            if count == 0:
                return f"{prefix}001"

            # If not empty, find the first available gap
            self.cursor.execute(f"SELECT {id_col} FROM {table}")
            all_ids = self.cursor.fetchall()
            
            existing_nums = set()
            for row in all_ids:
                nums = re.findall(r'\d+', str(row[0]))
                if nums:
                    existing_nums.add(int(nums[0]))
            
            next_num = 1
            while next_num in existing_nums:
                next_num += 1
            
            return f"{prefix}{str(next_num).zfill(3)}"
        except Exception as e:
            print(f"ID Gen Error: {e}")
            return f"{prefix}001"

    def show_about_box(self):
        messagebox.showinfo("About System", "Hospital Management System\nVersion 2.0 (Modern Edition)\n\nDeveloped for professional medical administration.\n© 2026 All Rights Reserved.")

    def quit_app(self):
        if messagebox.askokcancel("Exit", "Are you sure you want to exit the application?"):
            self.quit()
            os._exit(0)

    # --- SEARCH LOGIC ---
    def execute_search(self):
        query = self.search_var.get().strip()
        if not query:
            # If search is empty, refresh current view
            if self.current_view == "Patients" or self.current_view == "Dashboard": self.refresh_patient_table()
            elif self.current_view == "Doctors": self.refresh_doctor_table()
            return

        try:
            if self.current_view == "Patients" or self.current_view == "Dashboard":
                sql = "SELECT * FROM patients WHERE name LIKE %s OR patient_id LIKE %s"
                self.cursor.execute(sql, (f"%{query}%", f"%{query}%"))
                rows = self.cursor.fetchall()
                self.update_tree(rows)
            elif self.current_view == "Doctors":
                sql = "SELECT * FROM doctors WHERE name LIKE %s OR doctor_id LIKE %s"
                self.cursor.execute(sql, (f"%{query}%", f"%{query}%"))
                rows = self.cursor.fetchall()
                self.update_tree(rows)
        except Exception as e:
            messagebox.showerror("Search Error", str(e))

    def update_tree(self, rows):
        for item in self.tree.get_children(): self.tree.delete(item)
        for row in rows: self.tree.insert("", "end", values=row)

    # --- ORIGINAL LOGIC INTEGRATION ---
    def refresh_patient_table(self):
        for item in self.tree.get_children(): self.tree.delete(item)
        try:
            self.cursor.execute("SELECT * FROM patients")
            for row in self.cursor.fetchall(): self.tree.insert("", "end", values=row)
        except: pass

    def refresh_doctor_table(self):
        for item in self.tree.get_children(): self.tree.delete(item)
        try:
            self.cursor.execute("SELECT * FROM doctors")
            for row in self.cursor.fetchall(): self.tree.insert("", "end", values=row)
        except: pass

    def submit_patient_logic(self):
        pid = self.p_id_val
        name = self.p_name.get()
        age = self.p_age.get()
        if not name:
            messagebox.showerror("Error", "Patient Name is required!")
            return
        if not age:
            messagebox.showerror("Error", "Age is required!")
            return
        try:
            query = "INSERT INTO patients (patient_id, name, age, gender, disease) VALUES (%s, %s, %s, %s, %s)"
            values = (pid, name, age, self.p_gender.get(), self.p_disease.get())
            self.cursor.execute(query, values)
            self.conn.commit()
            messagebox.showinfo("Success", f"Patient {pid} registered successfully")
            self.show_patient_view() # Refresh to update ID
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def submit_doctor_logic(self):
        did = self.d_id_val
        name = self.d_name.get()
        age = self.d_age.get()
        if not name:
            messagebox.showerror("Error", "Doctor Name is required!")
            return
        if not age:
            messagebox.showerror("Error", "Age is required!")
            return
        try:
            query = "INSERT INTO doctors (doctor_id, name, age, gender, specialization) VALUES (%s, %s, %s, %s, %s)"
            values = (did, name, age, self.d_gender.get(), self.d_spec.get())
            self.cursor.execute(query, values)
            self.conn.commit()
            messagebox.showinfo("Success", f"Doctor {did} registered successfully")
            self.show_doctor_view() # Refresh to update ID
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def delete_patient_logic(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a patient to delete")
            return
        pid = self.tree.item(selected[0])['values'][0]
        if messagebox.askyesno("Confirm", f"Are you sure you want to delete Patient ID {pid}?"):
            try:
                self.cursor.execute("DELETE FROM patients WHERE patient_id = %s", (pid,))
                self.conn.commit()
                messagebox.showinfo("Deleted", f"Patient {pid} removed")
                self.show_patient_view()
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def delete_doctor_logic(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a doctor to delete")
            return
        did = self.tree.item(selected[0])['values'][0]
        if messagebox.askyesno("Confirm", f"Are you sure you want to delete Doctor ID {did}?"):
            try:
                self.cursor.execute("DELETE FROM doctors WHERE doctor_id = %s", (did,))
                self.conn.commit()
                messagebox.showinfo("Deleted", f"Doctor {did} removed")
                self.show_doctor_view()
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def calculate_bill_logic(self):
        try:
            pid = self.bill_pid.get()
            days = int(self.bill_days.get())
            rate = int(self.bill_rate.get())
            total = days * rate
            
            self.bill_text.delete("1.0", tk.END)
            self.bill_text.insert(tk.END, f"\n      MEDICORE HOSPITAL\n")
            self.bill_text.insert(tk.END, f"      ------------------\n\n")
            self.bill_text.insert(tk.END, f" Patient ID:    {pid}\n")
            self.bill_text.insert(tk.END, f" Days Admitted: {days}\n")
            self.bill_text.insert(tk.END, f" Daily Rate:    ${rate}\n")
            self.bill_text.insert(tk.END, f" ------------------------\n")
            self.bill_text.insert(tk.END, f" TOTAL AMOUNT:  ${total}\n\n")
            self.bill_text.insert(tk.END, f" Status:        PENDING\n")
        except Exception as e:
            messagebox.showerror("Error", "Please enter valid numeric values")

if __name__ == "__main__":
    root = tk.Tk()
    app = HospitalGUI(root)
    root.mainloop()