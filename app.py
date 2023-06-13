from flask import Flask, jsonify, request
from datetime import date
import logging
import psycopg2
import time
import jwt
from datetime import date
import random, string

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

def insert_song(cur, payload, artist_id):
    statement = """INSERT INTO song(title, genre, release_date, duration, record_label_label_id) 
                    VALUES (%s, %s, %s, %s, %s)"""
    values = (payload["name"], payload["genre"], payload["release_date"], payload["duration"], payload["publisher"])

    cur.execute(statement, values)

    cur.execute("""SELECT ismn
                    FROM song 
                    WHERE title = %s AND record_label_label_id = %s""", (payload["name"], payload["publisher"]))
    song_id = cur.fetchone()[0]

    cur.execute("""INSERT INTO artist_song (artist_person_id, song_ismn)
        VALUES (%s, %s)""", (artist_id, song_id))
    
    if payload["other_artists"]:
        for artist in payload["other_artists"]:
            cur.execute("""INSERT INTO artist_song (artist_person_id, song_ismn)
            VALUES (%s, %s)""", (artist, song_id))
    
    app.logger.info("---- new song added  ----")

    return song_id

@app.route('/dbproj/user', methods=['POST'])
def register():
    app.logger.info("###              DEMO: POST /user              ###")
    payload = request.get_json()

    con = db_connection()
    cur = con.cursor()

    app.logger.debug(f'payload: {payload}')

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
    
    cur.execute("begin transaction")
    
    # insert consumer data
    if 'label_id' not in payload or 'artistic_name' not in payload:
        statement = """INSERT INTO person(username, password, email, name, birthdate) 
                       VALUES (%s, %s, %s, %s, %s)"""
        values = (payload["username"], payload["password"], payload["email"], payload["name"], payload["birthdate"])

        try:   
            cur.execute(statement, values)
   
            cur.execute("""SELECT id
                            FROM person 
                            WHERE username = %s""", (payload["username"],))
            consumer_id = cur.fetchone()[0]

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
    else:
        token = request.headers.get('Authorization')
        if not token:
            result = {
                    "status": 400,
                    "errors": "Missing token",
                    "results": None
                }
            return jsonify(result), 400

        token = token.split('Bearer ')[-1]

        verification = verify_token(token)
        if not verification:
            result = {
                    "status": 400,
                    "errors": "Invalid token or token expired",
                    "results": None
                }
            return jsonify(result), 400

        user_type = verification['user_type']
        admin_id = verification['user_id']

        if user_type != 'administrator':
            result = {
                    "status": 400,
                    "errors": "Only admins can add artists",
                    "results": None
                }
            return jsonify(result), 400
        
        # insert artist data
        statement = """INSERT INTO person(username, password, email, name, birthdate) 
                    VALUES (%s, %s, %s, %s, %s)"""
        values = (payload["username"], payload["password"], payload["email"], payload["name"], payload["birthdate"])

        try:   
            cur.execute(statement, values)

            cur.execute("""SELECT id
                            FROM person 
                            WHERE username = %s""", (payload["username"],))
            artist_id = cur.fetchone()
            artist_id = artist_id[0]

            cur.execute("""INSERT INTO artist (artistic_name, record_label_label_id, administrator_person_id, person_id)
            VALUES (%s, %s, %s, %s)""", (payload["artistic_name"], payload["label_id"], admin_id, artist_id))

            result = {
                "status": 200,
                "errors": None,
                "results": artist_id
            }

            cur.execute("commit")
            app.logger.info("---- new artist registered  ----")
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

    try:
        # verify if the table is empty
        cur.execute("""SELECT EXISTS (SELECT 1 FROM person WHERE username = %s)""", (payload["username"],))
        person_exists = cur.fetchone()[0]

        if not person_exists:
            con.close()
            result = {
                "status": 400,
                "errors": "Username does not exist",
                "results": None
            }
            return jsonify(result), 400

        # verify if the user exists
        cur.execute("""SELECT id, password
                        FROM person
                        WHERE username = %s""", (payload["username"],))
        row = cur.fetchone()

        if row is None:
            con.close()
            result = {
                "status": 400,
                "errors": "Username does not exist",
                "results": None
            }
            return jsonify(result), 400

        user_id, stored_password = row

        # verify password
        if payload["password"] != stored_password:
            con.close()
            result = {
                "status": 400,
                "errors": "Invalid password",
                "results": None
            }
            return jsonify(result), 400

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
            result = {
                "status": 400,
                "errors": "User type not found",
                "results": None
            }
            return jsonify(result), 400

        user_id, user_type = row

        # generate a token
        token = generate_token(user_id, user_type)
        result = {
            "status": 200,
            "errors": None,
            "results": token
        }

        app.logger.info(f"---- {user_type} logged in  ----")

    except Exception as e:
        app.logger.error(e)
        con.close()
        result = {
            "status": 500,
            "errors": "Internal Server Error",
            "results": None
        }
        return jsonify(result), 500
    
    finally:
        if con is not None:
            con.close()
        
        return jsonify(result)
    
# login required operations

@app.route('/dbproj/song', methods=['POST'])
def add_song():
    app.logger.info("###              DEMO: POST /song              ###")

    # login and artist verification
    token = request.headers.get('Authorization')
    if not token:
        result = {
                "status": 400,
                "errors": "Missing token",
                "results": None
            }
        return jsonify(result), 400

    token = token.split('Bearer ')[-1]

    payload = verify_token(token)
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

    cur.execute("begin transaction")

    # song insertion
    try:   
        song_id = insert_song(cur, payload, artist_id)
        
        result = {
            "status": 200,
            "errors": None,
            "results": song_id
        }

        cur.execute("commit")
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

@app.route('/dbproj/album', methods=['POST'])
def add_album():
    app.logger.info("###              DEMO: POST /album              ###")

    # login and artist verification
    token = request.headers.get('Authorization')
    if not token:
        result = {
            "status": 400,
            "errors": "Missing token",
            "results": None
        }
        return jsonify(result), 400

    token = token.split('Bearer ')[-1]

    payload = verify_token(token)
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

    # album creation
    statement = """INSERT INTO album(name, genre, release_date, record_label_label_id, artist_person_id) 
                    VALUES (%s, %s, %s, %s, %s)"""
    values = (payload["name"], payload["genre"], payload["release_date"], payload["publisher"], artist_id)

    cur.execute("begin transaction")

    try:
        cur.execute(statement, values)

        cur.execute("""SELECT album_id
                    FROM album 
                    WHERE name = %s AND artist_person_id = %s""", (payload["name"], artist_id))
        album_id = cur.fetchone()[0]

        if payload["songs"]:
            for song in payload["songs"]:
                # verify if it's a new song
                if isinstance(song, dict):
                    song_id = insert_song(cur, song, artist_id)

                    cur.execute("""INSERT INTO song_album (song_ismn, album_album_id)
                            VALUES (%s, %s)""", (song_id, album_id))

                    result = {
                        "status": 200,
                        "errors": None,
                        "results": album_id
                    }
                # existing song id
                elif isinstance(song, int):
                    cur.execute("""SELECT artist_person_id
                        FROM artist_song 
                        WHERE song_ismn = %s""", (song,))
                    real_artist = cur.fetchone()
                    if real_artist is None:
                        result = {
                            "status": 400,
                            "errors": f'The song with id {song} does not exist',
                            "results": None
                        }
                        break
                    real_artist = real_artist[0]
                    # verify if the artist created the song
                    if artist_id == real_artist:
                        cur.execute("""INSERT INTO song_album (song_ismn, album_album_id)
                                VALUES (%s, %s)""", (song, album_id))

                        result = {
                            "status": 200,
                            "errors": None,
                            "results": album_id
                        }
                    else:
                        result = {
                            "status": 400,
                            "errors": f'The song with id {song} is not from the artist with id {artist_id}',
                            "results": None
                        }
                        break
                else:
                    result = {
                        "status": 400,
                        "errors": "Invalid song format",
                        "results": None
                    }
                    break

        else:
            result = {
                "status": 400,
                "errors": "The album needs at least one song",
                "results": None
            }

        cur.execute("commit")
        app.logger.info("---- new album added  ----")
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


@app.route('/dbproj/song/<keyword>', methods=['GET'])
def search_song(keyword):
    app.logger.info(f'###              DEMO: GET /song/{keyword}              ###')
    
    # token verification
    token = request.headers.get('Authorization')
    if not token:
        result = {
                "status": 400,
                "errors": ["Missing token"],
                "results": None
            }
        return jsonify(result), 400

    token = token.split('Bearer ')[-1]

    payload = verify_token(token)
    if not payload:
        result = {
                "status": 400,
                "errors": ["Invalid token or token expired"],
                "results": None
            }
        return jsonify(result), 400

    con = db_connection()
    cur = con.cursor()
    try:
        # Perform the song search
        cur.execute("""SELECT song.ismn, song.title,
                        array_agg(DISTINCT artist.artistic_name),
                        array_agg(DISTINCT song_album.album_album_id) FILTER (WHERE song_album.album_album_id IS NOT NULL)
                    FROM song
                    LEFT JOIN artist_song ON artist_song.song_ismn = song.ismn
                    LEFT JOIN artist ON artist.person_id = artist_song.artist_person_id
                    LEFT JOIN song_album ON song_album.song_ismn = song.ismn
                    WHERE title ILIKE %s
                    GROUP BY song.ismn, song.title, song.record_label_label_id""", ('%' + keyword + '%',))
        rows = cur.fetchall()

        if not rows:
            result = {
                "status": 400,
                "errors": "No results found",
                "results": None
            }
            con.close()
            return jsonify(result), 400

        data = []
        for row in rows:
            data.append({
            'title': row[1],
            'artists': row[2],
            'albums': row[3] 
            })

        result = {
            "status": 200,
            "errors": None,
            "results": data
        }

        app.logger.info("---- got songs  ----")
    except Exception as e:
            app.logger.error(e)
            con.close()
            result = {
                "status": 500,
                "errors": "Internal Server Error",
                "results": None
            }
            return jsonify(result), 500
    
    finally:
        if con is not None:
            con.close()
        return jsonify(result)

@app.route('/dbproj/artist_info/<artist_id>', methods=['GET'])
def artist_info(artist_id):
    app.logger.info(f'###              DEMO: GET /artist_info/{artist_id}              ###')
    # login verification
    token = request.headers.get('Authorization')
    if not token:
        result = {
                "status": 400,
                "errors": "Missing token",
                "results": None
            }
        return jsonify(result), 400

    token = token.split('Bearer ')[-1]

    payload = verify_token(token)
    if not payload:
        result = {
                "status": 400,
                "errors": "Invalid token or token expired",
                "results": None
            }
        return jsonify(result), 400

    con = db_connection()
    cur = con.cursor()

    try:
        # verify if the table is empty
        cur.execute("""SELECT EXISTS (SELECT 1 FROM artist WHERE person_id = %s)""", (artist_id,))
        person_exists = cur.fetchone()[0]

        if not person_exists:
            con.close()
            result = {
                "status": 400,
                "errors": "Artist does not exist",
                "results": None
            }
            return jsonify(result), 400

        # artist info
        query = """
            SELECT DISTINCT a.artistic_name,
              array_agg(DISTINCT s.ismn) FILTER (WHERE s.ismn IS NOT NULL) AS song_id,
              array_agg(DISTINCT al.album_id) FILTER (WHERE al.album_id IS NOT NULL),
              array_agg(DISTINCT p.playlist_id) FILTER (WHERE p.playlist_id IS NOT NULL)
            FROM artist AS a
            LEFT JOIN artist_song AS asg ON asg.artist_person_id = a.person_id
            LEFT JOIN song AS s ON s.ismn = asg.song_ismn
            LEFT JOIN song_album AS sa ON sa.song_ismn = s.ismn
            LEFT JOIN album AS al ON al.album_id = sa.album_album_id
            LEFT JOIN song_playlist AS sp ON sp.song_ismn = s.ismn
            LEFT JOIN playlist AS p ON p.playlist_id = sp.playlist_playlist_id
            WHERE a.person_id = %s
            GROUP BY a.artistic_name
        """

        cur.execute(query, (artist_id,))
        rows = cur.fetchone()

        if not rows:
            result = {
                "status": 400,
                "errors": "Artist not found",
                "results": None
            }
            con.close()
            return jsonify(result), 400

        result = {
            "status": 200,
            "errors": None,
            "results": {
                "name": rows[0],
                "songs": rows[1] if rows[1] is not None else [],
                "albums": rows[2] if rows[2] is not None else [],
                "playlists": rows[3] if rows[3] is not None else []
            }
        }

        app.logger.info("---- got artist ----")
    except Exception as e:
        app.logger.error(e)
        con.close()
        result = {
            "status": 500,
            "errors": "Internal Server Error",
            "results": None
        }
        return jsonify(result), 500
    
    finally:
        if con is not None:
            con.close()
        return jsonify(result)
    
@app.route('/dbproj/subscription', methods=['POST'])
def subscribe():
    app.logger.info("###              DEMO: POST /subscription              ###")

    # login and consumer verification
    token = request.headers.get('Authorization')
    if not token:
        result = {
                "status": 400,
                "errors": "Missing token",
                "results": None
            }
        return jsonify(result), 400

    token = token.split('Bearer ')[-1]

    payload = verify_token(token)
    if not payload:
        result = {
                "status": 400,
                "errors": "Invalid token or token expired",
                "results": None
            }
        return jsonify(result), 400

    user_type = payload['user_type']

    if user_type != 'consumer':
        result = {
                "status": 400,
                "errors": "Only consumers can subscribe to premium",
                "results": None
            }
        return jsonify(result), 400

    payload = request.get_json()
    app.logger.debug(f'payload: {payload}')

    con = db_connection()
    cur = con.cursor()

    # subscription operations

    if payload["period"] not in ["month", "quarter", "semester"]:
        result = {
                "status": 400,
                "errors": "Invalid period",
                "results": None
            }
        return jsonify(result), 400
    
    ####################################################################################################################
    #                                                                                                                  #
    #                                                  incompleto                                                      #
    #                                                                                                                  #
    ####################################################################################################################


    statement = """INSERT INTO subscription_transactions(name, genre, release_date, record_label_label_id, artist_person_id) 
                    VALUES (%s, %s, %s, %s, %s)"""
    values = (payload["name"], payload["genre"], payload["release_date"], payload["publisher"], )

    cur.execute("begin transaction")

    try:   
        cur.execute(statement, values)

        cur.execute("""SELECT album_id
                    FROM album 
                    WHERE name = %s AND artist_person_id = %s""", (payload["name"], ))
        album_id = cur.fetchone()[0]
        
        
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

@app.route('/dbproj/playlist', methods=['POST'])
def create_playlist():
    app.logger.info("###              DEMO: POST /playlist              ###")

    # login and artist verification
    token = request.headers.get('Authorization')
    if not token:
        result = {
            "status": 400,
            "errors": "Missing token",
            "results": None
        }
        return jsonify(result), 400

    token = token.split('Bearer ')[-1]

    payload = verify_token(token)
    if not payload:
        result = {
            "status": 400,
            "errors": "Invalid token or token expired",
            "results": None
        }
        return jsonify(result), 400

    user_type = payload['user_type']
    consumer_id = payload['user_id']

    if user_type != 'consumer':
        result = {
            "status": 400,
            "errors": "Only consumers can create playlists",
            "results": None
        }
        return jsonify(result), 400

    payload = request.get_json()
    app.logger.debug(f'payload: {payload}')

    con = db_connection()
    cur = con.cursor()

    cur.execute("begin transaction")

    try:
        # Find if consumer is premium
        cur.execute("SELECT consumer_person_id FROM consumer_subscription_transactions WHERE consumer_person_id = %s", (consumer_id,))
        premium = bool(cur.fetchone())

        if not premium:
            result = {
                "status": 400,
                "errors": "Only premium consumers can create playlists",
                "results": None
            }
            return jsonify(result), 400
        
        cur.execute("""SELECT date_start, date_finish
                    FROM subscription_transactions AS st
                    LEFT JOIN consumer_subscription_transactions AS cst ON cst.subscription_transactions_subs_id = st.subs_id""")
        
        subscription_data = cur.fetchone()

        # get actual data
        today = date.today()

        if subscription_data and (today < subscription_data[0] or today > subscription_data[1]):
            result = {
                "status": 400,
                "errors": "Only premium consumers can create playlists",
                "results": None
            }
            return jsonify(result), 400

        cur.execute("""SELECT name FROM person
                    WHERE id = %s""", (consumer_id,))

        name = cur.fetchone()

        if payload["visibility"] == "public":
            visib = 1
        else:
            visib = 0

        if payload["playlist_name"] != "top10":
            top = 0
        else:
            top = 1

        # Check if the consumer already has a playlist with the given name
        cur.execute("""SELECT COUNT(*) FROM playlist
                    WHERE creator = %s AND name = %s""", (name, payload["playlist_name"]))
        
        count = cur.fetchone()[0]

        if count > 0:
            result = {
                "status": 400,
                "errors": "A playlist with the given name already exists",
                "results": None
            }
            return jsonify(result), 400

        statement = """INSERT INTO playlist(name, creator, public, top_ten) 
                        VALUES (%s, %s, %s, %s)"""
        values = (payload["playlist_name"], name, bool(visib), bool(top))

        cur.execute(statement, values)

        cur.execute("""SELECT playlist_id FROM playlist
                    WHERE creator = %s AND name = %s""", (name, payload["playlist_name"]))
        
        playlist_id = cur.fetchone()[0]

        # Update song_playlist table with ISMN and playlist_id
        for ismn in payload["songs"]:
            cur.execute("""INSERT INTO song_playlist(song_ismn, playlist_playlist_id) 
                        VALUES (%s, %s)""", (ismn, playlist_id))

        cur.execute("""INSERT INTO consumer_playlist(consumer_person_id, playlist_playlist_id) 
                        VALUES (%s, %s)""", (consumer_id, playlist_id))
        
        result = {
                "status": 200,
                "errors": None,
                "results": playlist_id
            }
            
        cur.execute("commit")
        app.logger.info("---- new playlist added  ----")
  
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

# generate a 6 digit card code
def gen_code():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=6)).upper()

@app.route('/dbproj/card', methods=['POST'])
def create_card():
    app.logger.info("###              DEMO: POST /card              ###")

    # login and admin verification
    token = request.headers.get('Authorization')
    if not token:
        result = {
                "status": 400,
                "errors": "Missing token",
                "results": None
            }
        return jsonify(result), 400

    token = token.split('Bearer ')[-1]

    payload = verify_token(token)
    if not payload:
        result = {
                "status": 400,
                "errors": "Invalid token or token expired",
                "results": None
            }
        return jsonify(result), 400

    user_type = payload['user_type']
    admin_id = payload['user_id']

    if user_type != 'administrator':
        result = {
                "status": 400,
                "errors": "Only consumers can subscribe to premium",
                "results": None
            }
        return jsonify(result), 400

    payload = request.get_json()
    app.logger.debug(f'payload: {payload}')

    con = db_connection()
    cur = con.cursor()

    cur.execute("begin transaction")

    # operations
    try:
        ppc = []
        if payload["card_price"] in [10, 25, 50]:
            for i in range(payload["number_cards"]):
                cur.execute("""INSERT INTO pre_paid_card (id_card, limit_date, card_price, administrator_person_id)
                                VALUES (%s, CURRENT_DATE + INTERVAL \'1 year\', %s, %s) RETURNING id_card""", (gen_code(), payload['card_price'], admin_id))
                ppc.append(cur.fetchone()[0])
        else:
            result = {
                    "status": 400,
                    "errors": "Invalid card price",
                    "results": None
                }
            return jsonify(result), 400
        
        result = {
                "status": 200,
                "errors": None,
                "results": ppc
            }
            
        cur.execute("commit")
        app.logger.info("---- cards added ----")

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