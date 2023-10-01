from flask import jsonify
import json
import psycopg2
import os
from datetime import datetime
from dotenv import load_dotenv
from user import User
from goal import Goal

load_dotenv(".env")
DB_SERVER = os.getenv('DB_SERVER')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_DATABASE = os.getenv('DB_DATABASE')
DB_PORT = os.getenv('DB_PORT')
DB_STRING = os.getenv('DB_STRING')
if not DB_STRING:
    DB_STRING = '$$'
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

def getUserGoals(user_id, page, per_page):
    try:
        if page:
            page = int(page)
            if page < 1:
                page = 1
        else:
            page = 1
        if per_page:
            per_page = int(per_page)
            if per_page < 1:
                per_page = 100
        else:
            per_page = 100
        cursor = db.cursor()
        offset = per_page * (page - 1)
        query = "SELECT posts.id, posts.author, posts.date, posts.title, posts.link, posts.status, posts.iscompleted, posts.ispublic, posts.isfriends, posts.isprivate FROM posts WHERE posts.author="+str(user_id)+" AND posts.status=1 ORDER BY posts.date DESC LIMIT "+str(per_page)+" OFFSET "+str(offset)+";"
        cursor.execute(query)
        res = cursor.fetchone()
        goals = []
        for (id, author, date, title, link, status, iscompleted, ispublic, isfriends, isprivate) in res:
            goal = Goal(
                id,
                author,
                date,
                title,
                link,
                status,
                iscompleted,
                ispublic,
                isfriends,
                isprivate,
            )
            goal.getLikes()
            goals.append(goal.toJSON())
        return jsonify(goals), 200
    except:
        print("Get user's goals error")
        res = {
            "code": "get_user_goals_error",
            "message": "Unknown error. Please, try again later",
            "data": ''
        }
        return jsonify(res), 500

def getAvailableGoals(user_id, page, per_page):
    try:
        if page:
            page = int(page)
            if page < 1:
                page = 1
        else:
            page = 1
        if per_page:
            per_page = int(per_page)
            if per_page < 1:
                per_page = 100
        else:
            per_page = 100
        offset = per_page * (page - 1)
        cursor = db.cursor()
        query = "SELECT posts.id, posts.author, posts.date, posts.title, posts.link, posts.status, posts.iscompleted, posts.ispublic, posts.isfriends, posts.isprivate FROM posts, friends WHERE ((posts.ispublic=TRUE OR (posts.author=friends.id_user AND friends.id_friend="+str(user_id)+" AND posts.isfriends=TRUE)) AND posts.status=1) ORDER BY posts.date DESC LIMIT "+str(per_page)+" OFFSET "+str(offset)+";"
        cursor.execute(query)
        res = cursor.fetchone()
        goals = []
        for (id, author, date, title, link, status, iscompleted, ispublic, isfriends, isprivate) in res:
            goal = Goal(
                id,
                author,
                date,
                title,
                link,
                status,
                iscompleted,
                ispublic,
                isfriends,
                isprivate,
            )
            goal.getLikes()
            goals.append(goal.toJSON())
        return jsonify(goals), 200
    except:
        print("Get available goals error")
        res = {
            "code": "get_available_goals_error",
            "message": "Unknown error. Please, try again later",
            "data": ''
        }
        return jsonify(res), 500
