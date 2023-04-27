import mysql.connector

mydb = mysql.connector.connect(
    host="localhost",
    user="root",
    passwd="Uche_123",
)

my_cursor = mydb.cursor()

# my_cursor.execute("CREATE DATABASE ecommerce")

my_cursor.execute("SHOW DATABASES")
for db in my_cursor:
    print(db)