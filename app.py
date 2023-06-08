from flask import Flask, jsonify, request
import logging
import psycopg2
import time

app = Flask(__name__)

# connect to the db
def db_connection():
    db = psycopg2.connect(
        user='postgres',
        password='postgres',
        host='localhost',
        port='5432',
        database='musicfy')
    return db

@app.route('/dbproj/consumer', methods=['POST'])
def register_consumer():
    app.logger.info("###              DEMO: POST /consumer              ###")
    payload = request.get_json()

    con = db_connection()
    cur = con.cursor()

    app.logger.debug(f'payload: {payload}')

    cur.execute("begin transaction")
    cur.execute("""SELECT person_username
                     FROM consumer 
                    WHERE person_username = %s""", (payload["username"],))
    rows = cur.fetchall()

    if len(rows) != 0:
        con.close()
        result = "Error: username already exists!"
        return jsonify(result)
    
    else: 
        statement = """INSERT INTO consumer(person_username, person_password, person_email, person_name, person_birthdate) 
                       VALUES (%s, %s, %s, %s, %s)"""
        values = (payload["username"], payload["password"], payload["email"], payload["name"], payload["birthdate"])

        try:   
            cur.execute(statement, values)
   
            cur.execute("""SELECT person_id
                            FROM consumer 
                            WHERE person_username = %s""", (payload["username"],))
            rows = cur.fetchall()
            result = f'id: {rows[0][0]}'
            cur.execute("commit")
            app.logger.info("---- new consumer registered  ----")
        except (Exception, psycopg2.DatabaseError) as error:
            app.logger.error(error)
            result = f'Error: {error}!'
            cur.execute("rollback")

        finally:
            if con is not None:
                con.close()

        return jsonify(result)
    
if __name__ == "__main__":
    # Set up the logging
    logging.basicConfig(filename="log_file.log")
    app.logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)

    # create formatter
    formatter = logging.Formatter('%(asctime)s [%(levelname)s]:  %(message)s',
                                  '%H:%M:%S')
    
    ch.setFormatter(formatter)
    app.logger.addHandler(ch)

    time.sleep(1)

    app.logger.info("\n---------------------------------------------------------------\n" +
                    "API v1.0 online: http://localhost:5000/dbproj/\n\n")
    
    app.run(host="localhost", port="5000", debug=True, threaded=True)
