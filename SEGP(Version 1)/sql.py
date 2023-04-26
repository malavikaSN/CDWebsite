import mysql.connector
import time



def InsertRecords(id,color,TimeStamp):

    cnx = mysql.connector.connect(user='root',database='turtle')
    cursor = cnx.cursor()

    cursor.execute('''CREATE TABLE IF NOT EXISTS colour_changes
                 (colour_change VARCHAR(20),
                  time_changed DATETIME,
                  bounding_box_id INTEGER NOT NULL PRIMARY KEY)''')
    cnx.commit()

    cursor.execute("SELECT colour_change FROM colour_changes WHERE bounding_box_id = %s",(id,))
    
    dbcolor = cursor.fetchone()
    
    if(dbcolor == None):

        cursor.execute("INSERT INTO colour_changes (colour_change, time_changed, bounding_box_id) VALUES (%s, %s, %s)",(color,TimeStamp,id))
        f = open("log.txt", "a")
        f.write(f"[{TimeStamp}] - Sensor {id} changed to {color}\n")
        f.close()

    elif(dbcolor[0] != color):

        cursor.execute("UPDATE colour_changes SET colour_change  = %s , time_changed = %s WHERE bounding_box_id = %s",(color,TimeStamp,id))
        f = open("log.txt", "a")
        f.write(f"[{TimeStamp}] - Sensor {id} changed to {color}\n")
        f.close()
    
    else:

        return

    cnx.commit()
    cursor.close()
    cnx.close()

def SelectRecords(search_query,search_column):

    cnx = mysql.connector.connect(user='root',database='turtle')
    cursor = cnx.cursor()

    cursor.execute('''CREATE TABLE IF NOT EXISTS colour_changes
                 (colour_change VARCHAR(20),
                  time_changed DATETIME,
                  bounding_box_id INTEGER NOT NULL PRIMARY KEY)''')
    cnx.commit()

    if(search_column == 'bounding_box_id'):
        cursor.execute("SELECT * FROM colour_changes WHERE bounding_box_id = %s",(search_query,))
    elif(search_column == 'colour_change'): 
        cursor.execute("SELECT * FROM colour_changes WHERE colour_change LIKE %s",("%"+search_query+"%",))
    elif(search_column == 'time_changed'):
        cursor.execute("SELECT * FROM colour_changes WHERE time_changed LIKE %s",("%"+search_query+"%",))

    results = cursor.fetchall()

    print(results)

    cursor.close()
    cnx.close()

    return results