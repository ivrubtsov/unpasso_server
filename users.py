from flask import jsonify
import psycopg2
import os
from datetime import datetime
from dotenv import load_dotenv
from user import User

load_dotenv(".env")
DB_SERVER = os.getenv('DB_SERVER')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_DATABASE = os.getenv('DB_DATABASE')
DB_PORT = os.getenv('DB_PORT')
DB_STRING = os.getenv('DB_STRING')
if not DB_STRING:
    DB_STRING = '$$'
DB_SEARCH_LIMIT = os.getenv('DB_SEARCH_LIMIT')
if not DB_SEARCH_LIMIT:
    DB_SEARCH_LIMIT = 10
DB_FETCH_LIMIT = os.getenv('DB_FETCH_LIMIT')
if not DB_FETCH_LIMIT:
    DB_FETCH_LIMIT = 100
TMP_DIR = os.getenv('TMP_DIR')
if not TMP_DIR:
    TMP_DIR = 'tmp'
SITE_URL = os.getenv('SITE_URL')
BASE_URL = os.getenv('BASE_URL')
if not BASE_URL:
    BASE_URL = '/wp-json/wp/v2'
SERVICE_USERNAME = os.getenv('SERVICE_USERNAME')
SERVICE_PASSWORD = os.getenv('SERVICE_PASSWORD')

try:
    db = psycopg2.connect(database=DB_DATABASE,
                            host=DB_SERVER,
                            user=DB_USER,
                            password=DB_PASSWORD,
                            port=DB_PORT)
    print('Database connection established')

except:
    print("Database connection error")
    quit()

import atexit
#defining function to run on shutdown
def close_database_connection():
    db.close()
    print("Database connection closed")
#Register the function to be called on exit
atexit.register(close_database_connection)

def findUsers(request_string):
    try:
        cursor = db.cursor()
        query = "SELECT users.id, users.username, users.name, users.email, users.url, users.date, users.avatar, users.rating FROM users WHERE (users.name LIKE "+DB_STRING+str(request_string)+DB_STRING+" OR users.username LIKE "+DB_STRING+str(request_string)+DB_STRING+") AND users.status=2 LIMIT "+DB_SEARCH_LIMIT+";"
        cursor.execute(query)
        res = cursor.fetchall()
        publicUsers = []
        for (id, username, name, email, url, date, avatar, rating) in res:
            public = User(
                id=id,
                name=name,
                username=username,
                avatar=avatar,
                rating=rating,
            )
            public.getAchievements()
            publicUsers.append(public)
        return jsonify(publicUsers), 200

    except:
        print("Search users by name or username error")
        res = {
            "code": "search_users_error",
            "message": "Unknown error. Please, try again later",
            "data": ''
        }
        return jsonify(res), 500

def getPublicUserById(request_id):
    try:
        cursor = db.cursor()
        query = "SELECT users.id, users.username, users.name, users.email, users.url, users.date, users.avatar, users.rating FROM users WHERE users.id="+str(request_id)+" AND users.status=2 LIMIT 1;"
        cursor.execute(query)
        res = cursor.fetchone()
        public = User()
        for (id, username, name, email, url, date, avatar, rating) in res:
            public.id = id
            public.name = name
            public.username = username
            public.avatar = avatar
            public.rating = rating
        public.getAchievements()
        return jsonify(public), 200

    except:
        print("Get public user data by ID error")
        res = {
            "code": "get_user_public_error",
            "message": "Unknown error. Please, try again later",
            "data": ''
        }
        return jsonify(res), 500

