import mysql.connector

def check_table_structure():
    try:
        db = mysql.connector.connect(
            host="dbs.spskladno.cz",  
            user="student14",  
            password="spsnet",  
            database="vyuka14"  
        )
        cursor = db.cursor()
        cursor.execute("DESCRIBE betlandia_users;")
        columns = cursor.fetchall()
        
        print("📌 Struktura tabulky 'betlandia_users':")
        for column in columns:
            print(column)

        cursor.close()
        db.close()
    except mysql.connector.Error as err:
        print(f"❌ Chyba při kontrole struktury tabulky: {err}")

check_table_structure()
