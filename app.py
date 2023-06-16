## =============================================
## ============== Bases de Dados ===============
## ============== LEI  2022/2023 ===============
## =============================================
## =============================================
## === Department of Informatics Engineering ===
## =========== University of Coimbra ===========
## =============================================
##
## Authors: 
##   Marcelo Gomes nº2021222994
##   Pedro Brites nº2021226319
##   University of Coimbra

from flask import Flask, jsonify, request
from datetime import date
import logging
import psycopg2
import time
import jwt
from datetime import date, timedelta
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
    
    # insert consumer data
    if 'label_id' not in payload or 'artistic_name' not in payload:
        statement = """INSERT INTO person(username, password, email, name, birthdate) 
                       VALUES (%s, %s, %s, %s, %s)"""
        values = (payload["username"], payload["password"], payload["email"], payload["name"], payload["birthdate"])

        try:
            cur.execute("begin transaction")
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
            cur.execute("begin transaction")
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

    # song insertion
    try:   
        cur.execute("begin transaction")
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


    try:
        cur.execute("begin transaction")
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
                        cur.execute("rollback")
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
                        cur.execute("rollback")
                        break
                else:
                    result = {
                        "status": 400,
                        "errors": "Invalid song format",
                        "results": None
                    }
                    cur.execute("rollback")
                    break

        else:
            result = {
                "status": 400,
                "errors": "The album needs at least one song",
                "results": None
            }
            cur.execute("rollback")

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

    user_type = payload["user_type"]
    user_id = payload["user_id"]

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

    period = {
        "month": [30, 7], # days, price
        "quarter": [90, 21],
        "semester": [105, 42]
    }

    # subscription operations

    if payload["period"] not in period:
        result = {
                "status": 400,
                "errors": "Invalid period",
                "results": None
            }
        return jsonify(result), 400

    try:
        cur.execute("begin transaction")
        cur.execute('''
            SELECT subs_id, date_finish
            FROM subscription_transactions
            LEFT JOIN consumer_subscription_transactions ON subs_id = subscription_transactions_subs_id
            WHERE consumer_person_id = %s AND date_finish > CURRENT_DATE''', (user_id, ))

        row = cur.fetchone()

        start_date = None
        # has active subscription
        if row is not None:
            query = '''
            SELECT date_finish
            FROM subscription_transactions
            LEFT JOIN consumer_subscription_transactions ON subs_id = subscription_transactions_subs_id
            WHERE consumer_person_id = %s
            ORDER BY date_finish DESC
            '''
            cur.execute(query, (user_id, ))

            start_date = cur.fetchone()[0] + timedelta(days=1)
        else:
            start_date = date.today()
        end_date = start_date + timedelta(days=period[payload["period"]][0])
        cur.execute("""INSERT INTO subscription_transactions (plan, date_start, date_finish, transactions_transaction_date)
                        VALUES (%s, %s, %s, %s)""", (payload["period"], start_date, end_date, start_date))
        
        cur.execute('SELECT subs_id FROM subscription_transactions ORDER BY subs_id DESC LIMIT 1')
        subs_id = cur.fetchone()[0]

        if subs_id is None:
            result = {
                "status": 400,
                "errors": "Failed to retrieve subscription ID",
                "results": None
            }
            cur.execute("rollback")
            return jsonify(result), 400

        cur.execute("""SELECT id_card 
                    FROM pre_paid_card
                    WHERE id_card = ANY(%s) FOR UPDATE""", (payload["cards"], ))
        
        price = period[payload["period"]][1]
        for card in payload["cards"]:
            cur.execute("SELECT limit_date, card_price FROM pre_paid_card WHERE id_card = %s", (card, ))
            expire, amount = cur.fetchone()

            if expire < date.today() or amount <= 0 or expire is None:
                result = {
                    "status": 400,
                    "errors": f'card {card} expired or doesnt exist',
                    "results": None
                }
                cur.execute("rollback")
                return jsonify(result), 400
  
            cur.execute("SELECT consumer_person_id FROM consumer_pre_paid_card WHERE pre_paid_card_id_card = %s", (card,))
            owner = cur.fetchone()

            if owner is None:
                cur.execute("""INSERT INTO consumer_pre_paid_card (consumer_person_id, pre_paid_card_id_card)
                                VALUES (%s, %s)""", (user_id, card))
                
            elif owner[0] != user_id:
                result = {
                    "status": 400,
                    "errors": f'card {card} already owned',
                    "results": None
                }
                cur.execute("rollback")
                return jsonify(result), 400
            
            
            while True:
                amount-=1
                price-=1
                if price == 0 or amount == 0:
                    cur.execute("INSERT INTO subscription_transactions_pre_paid_card (subscription_transactions_subs_id, pre_paid_card_id_card) VALUES (%s, %s)", (subs_id, card))
                    break
            
            cur.execute('UPDATE pre_paid_card SET card_price = %s WHERE id_card = %s', (amount, card))
            if price == 0:
                break

        cur.execute("INSERT INTO consumer_subscription_transactions (consumer_person_id, subscription_transactions_subs_id) VALUES (%s, %s)", (user_id, subs_id))

        if price > 0:
            result = {
                "status": 400,
                "errors": "insuficient funds",
                "results": None
            }
            cur.execute("rollback")
            app.logger.info("---- insuficient funds ----")
            return jsonify(result), 400
        
        result = {
            "status": 200,
            "errors": None,
            "results": subs_id
        }
        
        cur.execute("commit")
        app.logger.info("---- subscribed premium ----")
        
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

    try:
        cur.execute("begin transaction")
        # Find if consumer is premium
        cur.execute("SELECT consumer_person_id FROM consumer_subscription_transactions WHERE consumer_person_id = %s", (consumer_id,))
        premium = cur.fetchone()

        if premium is None:
            result = {
                "status": 400,
                "errors": "Only premium consumers can create playlists",
                "results": None
            }
            return jsonify(result), 400
        
        cur.execute("""SELECT date_finish
                    FROM subscription_transactions
                    LEFT JOIN consumer_subscription_transactions ON subscription_transactions_subs_id = subs_id
                    WHERE consumer_person_id = %s AND date_finish > CURRENT_DATE""", (consumer_id,))
        
        subscription_data = cur.fetchone()

        if subscription_data is None:
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

# generate a 16 digit card code
def gen_code():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=16)).upper()

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

    # operations
    try:
        cur.execute("begin transaction")
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
            cur.execute("rollback")
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
    
@app.route('/dbproj/comments/<int:song_id>', methods=['POST'])
def create_comment(song_id):
    app.logger.info("###              DEMO: POST /comments              ###")

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

    user_id = payload['user_id']

    payload = request.get_json()
    app.logger.debug(f'payload: {payload}')

    comment = payload.get("comment")

    if not comment:
        result = {
            "status": 400,
            "errors": "Missing comment",
            "results": None
        }
        return jsonify(result), 400

    con = db_connection()
    cur = con.cursor()

    # Check if the song exists
    cur.execute("SELECT COUNT(*) FROM song WHERE ismn = %s", (song_id,))
    count = cur.fetchone()[0]

    if count == 0:
        result = {
            "status": 400,
            "errors": "Song does not exist",
            "results": None
        }
        return jsonify(result), 400

    today = date.today()
    d1 = today.strftime("%d/%m/%Y")

    # Insert the comment
    statement = """INSERT INTO comment(content, comment_date, consumer_person_id, song_ismn)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id"""
    values = (comment, d1, user_id, song_id)

    try:
        cur.execute("begin transaction")
        cur.execute(statement, values)
        comment_id = cur.fetchone()[0]

        result = {
            "status": 200,
            "errors": None,
            "results": comment_id
        }

        con.commit()
        app.logger.info("---- new comment added ----")
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

@app.route('/dbproj/comments/<int:song_id>/<int:parent_comment_id>', methods=['POST'])
def create_reply(song_id, parent_comment_id):
    app.logger.info("###              DEMO: POST /comments/reply              ###")

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

    user_id = payload['user_id']

    payload = request.get_json()
    app.logger.debug(f'payload: {payload}')

    comment = payload.get("comment")

    if not comment:
        result = {
            "status": 400,
            "errors": "Missing comment",
            "results": None
        }
        return jsonify(result), 400

    con = db_connection()
    cur = con.cursor()

    # Check if the song exists
    cur.execute("SELECT COUNT(*) FROM song WHERE ismn = %s", (song_id,))
    count = cur.fetchone()[0]

    if count == 0:
        result = {
            "status": 400,
            "errors": "Song does not exist",
            "results": None
        }
        return jsonify(result), 400

    cur.execute('SELECT person_id FROM consumer WHERE person_id = %s', (user_id, ))

    # Check if the parent comment exists
    cur.execute("SELECT consumer_person_id FROM comment WHERE comment_id = %s", (parent_comment_id,))
    person_id = cur.fetchone()[0]

    if count == 0:
        result = {
            "status": 400,
            "errors": "Parent comment does not exist",
            "results": None
        }
        return jsonify(result), 400
    
    today = date.today()
    d1 = today.strftime("%d/%m/%Y")
    
    try:
        cur.execute("begin transaction")

        cur.execute("""SELECT comment_id 
                    FROM comment
                    WHERE comment_id = %s FOR UPDATE""", (parent_comment_id, ))
        
        # Insert the reply comment
        statement = """INSERT INTO comment(content, comment_date, consumer_person_id, comment_comment_id, comment_consumer_person_id, song_ismn)
                        VALUES (%s, %s, %s, %s, %s, %s)"""
        values = (comment, today, user_id, parent_comment_id, person_id, song_id)

        cur.execute(statement, values)
        comment_id = cur.lastrowid

        result = {
            "status": 200,
            "errors": None,
            "results": comment_id
        }

        con.commit()
        app.logger.info("---- new reply comment added ----")
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


@app.route('/dbproj/report/<year_month>', methods=['GET'])
def generate_monthly_report(year_month):
    app.logger.info(f'###              DEMO: GET /report/{year_month}              ###')
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
    
    user_type = payload['user_type']
    consumer_id = payload['user_id']

    if user_type != 'consumer':
        result = {
            "status": 400,
            "errors": "Only consumers can create reports",
            "results": None
        }
        return jsonify(result), 400

    # Parse the year and month from the URL parameter
    try:
        year, month = year_month.split('-')
        year = int(year)
        month = int(month)
    except ValueError:
        result = {
            "status": 400,
            "errors": "Invalid year-month format",
            "results": None
        }
        return jsonify(result), 400
    

    con = db_connection()
    cur = con.cursor()

    try:
        result = {
            "status": 200,
            "errors": None,
            "results": []
        }

        for i in range(12):
            # Execute the query with the specified year and month
            cur.execute("""
                SELECT TO_CHAR(a.listen_date, 'YYYY-MM') AS month, s.genre,COUNT(*) AS playbacks, a.n_listens
                FROM activity AS a INNER JOIN song AS s ON a.song_ismn = s.ismn
                WHERE EXTRACT(YEAR FROM a.listen_date) = %s
                AND EXTRACT(MONTH FROM a.listen_date) = %s
                AND a.consumer_person_id = %s
                GROUP BY TO_CHAR(a.listen_date, 'YYYY-MM'), s.genre, a.n_listens
                ORDER BY TO_CHAR(a.listen_date, 'YYYY-MM') ASC, s.genre ASC""", (year, month, consumer_id))

            rows = cur.fetchall()

            # Format the results as required
            for row in rows:
                result["results"].append({
                    "month": row[0],
                    "genre": row[1],
                    "playbacks": row[2] * row[3]
                })
            
            # Decrement the month and adjust the year if necessary
            month -= 1
            if month == 0:
                month = 12
                year -= 1

        app.logger.info("---- generated 12 month report ----")
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