import psycopg2
import time

var = 1
con = psycopg2.connect("dbname='postgres' user='postgres'")   
cur = con.cursor()
cur.execute("CREATE TABLE test(Time VARCHAR(30))")

while var == 1 :
    cur.execute("INSERT INTO test VALUES(now())")
    con.commit()
    time.sleep(120)