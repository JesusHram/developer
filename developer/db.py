import pymysql

def getConnection():
    return pymysql.connect(
        host='52.12.110.149',
        user='newvirus',
        password='3d462a1b271d-4fc4-4c2748f0-9422-fb9f2f3d137d81bd',
        db='admin_zaroprod',
        port=3306,
        charset='latin1',
        cursorclass=pymysql.cursors.DictCursor
    )
    
def query_db(query):
    conn = getConnection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(query)
            # Conversión EXTRA de tipos para Reflex
            rows = []
            for row in cursor.fetchall():
                clean_row = {}
                for key, value in row.items():
                    if isinstance(value, (int, float)):
                        clean_row[key] = str(value)  # Enteros a string
                    elif isinstance(value, (bytes, bytearray)):
                        clean_row[key] = value.decode('latin1').strip()
                    elif value is None:
                        clean_row[key] = ""
                    else:
                        clean_row[key] = str(value).strip()
                rows.append(clean_row)
            return rows
    finally:
        conn.close()