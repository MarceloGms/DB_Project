from flask import Flask, jsonify, request
import logging
import psycopg2
import time
import jwt

app = Flask(__name__)
app.config['SECRET_KEY'] = 'abcd'

# connect to the db
def db_connection():
    db = psycopg2.connect(
        user='postgres',
        password='postgres',
        host='localhost',
        port='5432',
        database='musicfy')
    return db

def generate_token(user_id, user_type):
    payload = {
        'user_id': user_id,
        'user_type': user_type
    }
    token = jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')
    return token

def verify_token(token):
    try:
        payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return None  
    except jwt.InvalidTokenError:
        return None  


@app.route('/dbproj/register', methods=['POST'])
def register_consumer():
    app.logger.info("###              DEMO: POST /register              ###")
    payload = request.get_json()

    con = db_connection()
    cur = con.cursor()

    app.logger.debug(f'payload: {payload}')

    cur.execute("begin transaction")
    
    # verify if username already exists
    cur.execute("""SELECT username
                     FROM person 
                    WHERE username = %s""", (payload["username"],))
    rows = cur.fetchall()

    if len(rows) != 0:
        con.close()
        result = "Error: username already exists"
        return jsonify(result)
    
    # insert consumer data
    else: 
        statement = """INSERT INTO person(username, password, email, name, birthdate) 
                       VALUES (%s, %s, %s, %s, %s)"""
        values = (payload["username"], payload["password"], payload["email"], payload["name"], payload["birthdate"])

        try:   
            cur.execute(statement, values)
   
            cur.execute("""SELECT id
                            FROM person 
                            WHERE username = %s""", (payload["username"],))
            consumer_id = cur.fetchone()
            consumer_id = consumer_id[0]

            cur.execute("""INSERT INTO consumer (person_id)
               VALUES (%s)""", (consumer_id,))
            
            result = f'Account created with id: {consumer_id}'

            cur.execute("commit")
            app.logger.info("---- new consumer registered  ----")
        except (Exception, psycopg2.DatabaseError) as error:
            app.logger.error(error)
            result = f'Error: {error}'
            cur.execute("rollback")

        finally:
            if con is not None:
                con.close()

        return jsonify(result)
    
@app.route('/dbproj/login', methods=['POST'])
def login():
    app.logger.info("###              DEMO: POST /login              ###")
    payload = request.get_json()

    con = db_connection()
    cur = con.cursor()

    app.logger.debug(f'payload: {payload}')

    cur.execute("begin transaction")

    # verify if the table is empty
    cur.execute("""SELECT EXISTS (SELECT 1 FROM person WHERE username = %s)""", (payload["username"],))
    person_exists = cur.fetchone()[0]

    if not person_exists:
        con.close()
        result = "Error: username does not exist"
        return jsonify(result)

    # verify if the user exists
    cur.execute("""SELECT id, password
                    FROM person
                    WHERE username = %s""", (payload["username"],))
    row = cur.fetchone()

    if row is None:
        con.close()
        result = "Error: username does not exist"
        return jsonify(result)

    user_id, stored_password = row

    # verify password
    if payload["password"] != stored_password:
        con.close()
        result = "Error: invalid password"
        return jsonify(result)
    
    # verify the user type
    cur.execute("""SELECT person_id, 'consumer' AS type
               FROM consumer
               WHERE person_id = %s""", (user_id,))
    row = cur.fetchone()

    if row is None:
        cur.execute("""SELECT person_id, 'artist' AS type
                    FROM artist
                    WHERE person_id = %s""", (user_id,))
        row = cur.fetchone()

        if row is None:
            cur.execute("""SELECT person_id, 'administrator' AS type
                        FROM administrator
                        WHERE person_id = %s""", (user_id,))
            row = cur.fetchone()

    if row is None:
        con.close()
        result = "Error: user type not found"
        return jsonify(result)

    user_id, user_type = row

    #generate a token
    token = generate_token(user_id, user_type)
    result = "Logged in"
    
    cur.execute("commit")
    app.logger.info(f"---- {user_type} logged in  ----")
    con.close()
    
    return jsonify(result)

@app.route('/dbproj/add_artist', methods=['POST'])
def add_artist():
    # admin verification
    token = request.headers.get('Authorization')
    if not token:
        result = "Error: missing token"
        return jsonify(result)

    token = token.split('Bearer ')[-1]

    payload = verify_token(token)
    if not payload:
        result = "Error: invalid token or token expired"
        return jsonify(result)

    user_type = payload['user_type']

    if user_type != 'admin':
        result = "Error: only admins can add artists"
        return jsonify(result)
    
    app.logger.info("###              DEMO: POST /add_artist              ###")
    payload = request.get_json()
    app.logger.debug(f'payload: {payload}')

    con = db_connection()
    cur = con.cursor()

    cur.execute("begin transaction")
    
    # verify if username already exists
    cur.execute("""SELECT username
                     FROM person 
                    WHERE username = %s""", (payload["username"],))
    rows = cur.fetchall()

    if len(rows) != 0:
        con.close()
        result = "Error: username already exists"
        return jsonify(result)
    
    # insert artist data
    else: 
        statement = """INSERT INTO artist(artistic_name, person_username, person_password, person_email, person_name, person_birthdate) 
                       VALUES (%s, %s, %s, %s, %s, %s)"""
        values = (payload["artistic_name"], payload["username"], payload["password"], payload["email"], payload["name"], payload["birthdate"])

        try:   
            cur.execute(statement, values)
   
            cur.execute("""SELECT person_id
                            FROM consumer 
                            WHERE person_username = %s""", (payload["username"],))
            rows = cur.fetchall()
            result = f'Account created with id: {rows[0][0]}'
            cur.execute("commit")
            app.logger.info("---- new consumer registered  ----")
        except (Exception, psycopg2.DatabaseError) as error:
            app.logger.error(error)
            result = f'Error: {error}'
            cur.execute("rollback")

        finally:
            if con is not None:
                con.close()

        return jsonify(result)

@app.route('/dbproj/song', methods=['POST'])
def add_song():
    # artist verification
    token = request.headers.get('Authorization')
    if not token:
        result = "Error: missing token"
        return jsonify(result)

    token = token.split('Bearer ')[-1]

    payload = verify_token(token)
    if not payload:
        result = "Error: invalid token or token expired"
        return jsonify(result)

    user_type = payload['user_type']

    if user_type != 'artist':
        result = "Error: only artists can add songs"
        return jsonify(result)

    app.logger.info("###              DEMO: POST /song              ###")
    payload = request.get_json()
    app.logger.debug(f'payload: {payload}')

    # song insertion
 

    result = "Song added successfully"
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
