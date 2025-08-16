import mysql.connector

# Database connection setup
conn = mysql.connector.connect(
    host='localhost',
    username='root',
    password='internet@123',
    database='sales_analytics'
)

# Ensure connection is working
try:
    my_cursor = conn.cursor()
    print("Connection successfully created")
except mysql.connector.Error as err:
    print(f"Error: {err}")
