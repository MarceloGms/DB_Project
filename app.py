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


@app.route('/dbproj/user', methods=['POST'])
def register():
    app.logger.info("###              DEMO: POST /user              ###")
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
        result = {
            "status": 400,
            "errors": "Username already exists",
            "results": None
        }
        return jsonify(result), 400
    
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
            
            result = {
                "status": 200,
                "errors": None,
                "results": consumer_id
            }

            cur.execute("commit")
            app.logger.info("---- new consumer registered  ----")
        except (Exception, psycopg2.DatabaseError) as error:
            app.logger.error(error)
            result = {
                "status": 500,
                "errors": "Internal Server Error",
                "results": None
            }
            cur.execute("rollback")

        finally:
            if con is not None:
                con.close()

        return jsonify(result)
    
@app.route('/dbproj/user', methods=['PUT'])
def login():
    app.logger.info("###              DEMO: PUT /user              ###")
    payload = request.get_json()

    con = db_connection()
    cur = con.cursor()

    app.logger.debug(f'payload: {payload}')

    cur.execute("begin transaction")

    try:
        # verify if the table is empty
        cur.execute("""SELECT EXISTS (SELECT 1 FROM person WHERE username = %s)""", (payload["username"],))
        person_exists = cur.fetchone()[0]

        if not person_exists:
            con.close()
            response = {
                "status": 400,
                "errors": "Username does not exist",
                "results": None
            }
            return jsonify(response), 400

        # verify if the user exists
        cur.execute("""SELECT id, password
                        FROM person
                        WHERE username = %s""", (payload["username"],))
        row = cur.fetchone()

        if row is None:
            con.close()
            response = {
                "status": 400,
                "errors": "Username does not exist",
                "results": None
            }
            return jsonify(response), 400

        user_id, stored_password = row

        # verify password
        if payload["password"] != stored_password:
            con.close()
            response = {
                "status": 400,
                "errors": "Invalid password",
                "results": None
            }
            return jsonify(response), 400

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
            response = {
                "status": 400,
                "errors": "User type not found",
                "results": None
            }
            return jsonify(response), 400

        user_id, user_type = row

        # generate a token
        token = generate_token(user_id, user_type)
        response = {
            "status": 200,
            "errors": None,
            "results": token
        }

        cur.execute("commit")
        app.logger.info(f"---- {user_type} logged in  ----")
        con.close()

        return jsonify(response)
    except Exception as e:
        app.logger.error(e)
        con.close()
        result = {
            "status": 500,
            "errors": "Internal Server Error",
            "results": None
        }
        return jsonify(result), 500

@app.route('/dbproj/song', methods=['POST'])
def add_song():
    app.logger.info("###              DEMO: POST /song              ###")

    # artist verification
    payload = verify_token(request.args['token'])
    if not payload:
        result = {
                "status": 400,
                "errors": "Invalid token or token expired",
                "results": None
            }
        return jsonify(result), 400

    user_type = payload['user_type']
    artist_id = payload['user_id']

    if user_type != 'artist':
        result = {
                "status": 400,
                "errors": "Only artists can add songs",
                "results": None
            }
        return jsonify(result), 400

    payload = request.get_json()
    app.logger.debug(f'payload: {payload}')

    con = db_connection()
    cur = con.cursor()

    # song insertion
    statement = """INSERT INTO song(title, genre, release_date, duration, record_label_label_id) 
                    VALUES (%s, %s, %s, %s, %s)"""
    values = (payload["name"], payload["genre"], payload["release_date"], payload["duration"], payload["publisher"])

    try:   
        cur.execute(statement, values)

        cur.execute("""SELECT ismn
                        FROM song 
                        WHERE title = %s""", (payload["name"],))
        song_id = cur.fetchone()
        song_id = song_id[0]

        cur.execute("""INSERT INTO artist_song (artist_person_id, song_ismn)
            VALUES (%s)""", (artist_id, song_id))
        
        for i in range (len(payload["other_artists"])):
            cur.execute("""INSERT INTO artist_song (artist_person_id, song_ismn)
            VALUES (%s)""", (payload["other_artists"][i], song_id))

        result = {
            "status": 200,
            "errors": None,
            "results": song_id
        }

        cur.execute("commit")
        app.logger.info("---- new song added  ----")
    except (Exception, psycopg2.DatabaseError) as error:
        app.logger.error(error)
        result = {
            "status": 500,
            "errors": "Internal Server Error",
            "results": None
        }
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
                    "API v1.0 online: http://localhost:8080/dbproj/\n\n")
    
    app.run(host="localhost", port="8080", debug=True, threaded=True)
