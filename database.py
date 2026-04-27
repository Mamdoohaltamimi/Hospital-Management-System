import mysql.connector

# This handles the connection to your XAMPP MySQL
try:
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="", # Default XAMPP password is empty
        database="hospital"
    )
    cursor = conn.cursor()
    print("Database connected successfully!")
except mysql.connector.Error as err:
    print(f"Error: {err}")