
import flask
import logging
import psycopg2
import time

app = flask.Flask(__name__)

'''
def db_connection():
    db = psycopg2.connect(
        user='aulaspl',
        password='aulaspl',
        host='localhost',
        port='5432',
        database='WAVE'
    )

    return db
'''
@app.route("/")
def home():
    return "Hello, world!"

"""
@app.route("/")
def landing_page():
    return "HEllo World"
@app.route('/song', methods=['POST'])
def card(): 
    
    return



StatusCodes = {
    'success': 200,
    'api_error': 400,
    'internal_error': 500
}
# replace with your actual database URI
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/test.db'





# ENDPOINTS




@app.route('/dbproj/{song_id}', method=['PUT'])
def play_song():
    # playing deez
    return


@app.route('/dbproj/user', methods=['POST'])
def register_user():
    payload = flask.request.get_json()
"""