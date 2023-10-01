from flask import jsonify
import json
import psycopg2
import os
from datetime import datetime
from dotenv import load_dotenv
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

import wp_crypt
# Check WP passwords:
# from passlib.hash import phpass
# phpass.verify("password", "wordpress hash")

class User:
    def __init__(
            this,
            id = 0,
            name = '',
            date = datetime.now(),
            username = '',
            password = '',
            avatar = 0,
            achievements = [],
            friends = [],
            friendsRequestsReceived = [],
            friendsRequestsSent = [],
            email = '',
            url = '',
            locale = '',
            rating = 0,
            status = 2,
        ):
        this.id = id
        this.name = name
        this.date = date
        this.username = username
        this.password = password
        this.avatar = avatar
        this.email = email
        this.url = url
        this.locale = locale
        this.rating = rating
        this.status = status
        this.achievements = achievements
        this.friends = friends
        this.friendsRequestsReceived = friendsRequestsReceived
        this.friendsRequestsSent = friendsRequestsSent
    def fromJSON(this, jsonData):
        if not jsonData:
            return
        data = json.loads(jsonData)
        if 'id' in data:
            this.id = data['id']
        if json['name']:
            this.name = data['name']
        if json['date']:
            this.date = datetime.fromisoformat(data['date'])
        if json['username']:
            this.username = data['username']
        if json['password']:
            this.password = wp_crypt.crypt_private(data['password'])
        if json['avatar']:
            this.avatar = data['avatar']
        elif json['description'] and data['description']['avatar']:
            this.avatar = data['description']['avatar']
        if json['email']:
            this.email = data['email']
        if json['url']:
            this.url = data['url']
        if json['locale']:
            this.locale = data['locale']
        if json['rating']:
            this.rating = data['rating']
        if json['status']:
            this.status = data['status']
        if json['achievements']:
            this.achievements = data['achievements']
        elif json['description'] and json['description']['achievements']:
            this.achievements = data['description']['achievements']
#        this.setAchievements()
#        if json['friends']:
#            this.friends = json['friends']
#        elif json['description'] and json['description']['friends']:
#            this.friends = data['description']['friends']
#        if json['friendsRequests']:
#            this.friendsRequests = data['friendsRequests']
#        elif json['description'] and json['description']['friendsRequests']:
#            this.friendsRequests = data['description']['friendsRequests']
        return

    def toJSON(this):
        return {
                'id': this.id,
                'name': this.name,
                'username': this.username,
                'date': this.date.isoformat("T", "seconds"),
                'url': this.url,
                'email': this.email,
                'description': {
                    'achievements': this.achievements,
                    'avatar': this.avatar,
                    'friends': this.friends,
                    'friendsRequestsReceived': this.friendsRequestsReceived,
                    'friendsRequestsSent': this.friendsRequestsSent,
                    },
                'link': SITE_URL+'/author/'+this.username,
        }

    def getAchievements(this):
        try:
            cursor = db.cursor()
            query = "SELECT id_achievement FROM achievements WHERE id_user="+this.id+";"
            cursor.execute(query)
            res = cursor.fetchall()
            achs = []
            for (id_achievement) in res:
                achs.append(id_achievement)
            return achs
        except:
            print("Database get achievements request error")
            return []

    def setAchievements(this):
        try:
            cursor = db.cursor()
            query = "DELETE FROM achievements WHERE id_user="+str(this.id)+";"
            cursor.execute(query)
            if not this.achievements == []:
                first = True
                query = "INSERT INTO achievements (id_user, id_achievement) VALUES "
                for id_achievement in this.achievements:
                    if not first:
                        query = query + ', '
                    query = query + '('+str(this.id)+', '+str(id_achievement)+')'
                    first = False
                query = query + ';'
                cursor.execute(query)
            db.commit()
            return
        except:
            print("Database set achievements request error")
            return

    def getFriends(this):
        try:
            cursor = db.cursor()
            query = "SELECT friends.id_friend, users.username, users.name, users.avatar, users.rating FROM friends, users WHERE friends.id_user="+this.id+" AND friends.id_friend=users.id AND users.status=2;"
            cursor.execute(query)
            res = cursor.fetchall()
            friends = []
            for (id, username, name, avatar, rating) in res:
                friends.append({
                    'id': id,
                    'username': username,
                    'name': name,
                    'avatar': avatar,
                    'rating': rating,
                })
            return friends
        except:
            print("Database get friends request error")
            return []

    def getFriendsRequestsSent(this):
        try:
            cursor = db.cursor()
            query = "SELECT friends_requests.id, friends_requests.id_status, users.id, users.username, users.name, users.avatar, users.rating FROM friends_requests, users WHERE friends_requests.id_source="+this.id+" AND friends_requests.id_target=users.id AND users.status=2;"
            cursor.execute(query)
            res = cursor.fetchall()
            friendsRequestsSent = []
            for (requestid, status, userid, username, name, avatar, rating) in res:
                friendsRequestsSent.append({
                    'requestId': requestid,
                    'status': status,
                    'userId': userid,
                    'username': username,
                    'name': name,
                    'avatar': avatar,
                    'rating': rating,
                })
            return friendsRequestsSent
        except:
            print("Database get friends request error")
            return []

    def getFriendsRequestsReceived(this):
        try:
            cursor = db.cursor()
            query = "SELECT friends_requests.id, friends_requests.id_status, users.id, users.username, users.name, users.avatar, users.rating FROM friends_requests, users WHERE friends_requests.id_target="+this.id+" AND friends_requests.id_source=users.id AND users.status;"
            cursor.execute(query)
            res = cursor.fetchall()
            friendsRequestsReceived = []
            for (requestid, status, userid, username, name, avatar, rating) in res:
                friendsRequestsReceived.append({
                    'requestId': requestid,
                    'status': status,
                    'userId': userid,
                    'username': username,
                    'name': name,
                    'avatar': avatar,
                    'rating': rating,
                })
            return friendsRequestsReceived
        except:
            print("Database get friends request error")
            return []

    def getUserByUsername(this, request_username):
        try:
            cursor = db.cursor()
            query = "SELECT users.id, users.username, users.name, users.email, users.url, users.locale, users.date, users.avatar, users.rating FROM users WHERE users.username='"+request_username+"' AND users.status=2 ORDER BY users.date DESC LIMIT 1;"
            cursor.execute(query)
            res = cursor.fetchone()
            for (id, username, name, email, url, locale, date, avatar, rating) in res:
                this.id = id
                this.name = name
                this.date = date
                this.username = username
                this.avatar = avatar
                this.email = email
                this.url = url
                this.locale = locale
                this.rating = rating
                this.achievements = this.getAchievements()
                this.friends = this.getFriends()
                this.friendsRequestsSent = this.getFriendsRequestsSent()
                this.friendsRequestsReceived = this.getFriendsRequestsReceived()
            return
        except:
            print("Get user data by username error")
            return        

    def getUserById(this, request_id):
        try:
            cursor = db.cursor()
            query = "SELECT users.id, users.username, users.name, users.email, users.url, users.locale, users.date, users.avatar, users.rating FROM users WHERE users.id="+str(request_id)+" AND users.status=2 ORDER BY users.date DESC LIMIT 1;"
            cursor.execute(query)
            res = cursor.fetchone()
            for (id, username, name, email, url, locale, date, avatar, rating) in res:
                this.id = id
                this.name = name
                this.date = date
                this.username = username
                this.avatar = avatar
                this.email = email
                this.url = url
                this.locale = locale
                this.rating = rating
                this.achievements = this.getAchievements()
                this.friends = this.getFriends()
                this.friendsRequestsSent = this.getFriendsRequestsSent()
                this.friendsRequestsReceived = this.getFriendsRequestsReceived()
            return
        except:
            print("Get user data by ID error")
            return        
    
    def save(this):
        try:
            #Check email format
            if not checkEmail(this.email):
                res = {
                    "code": "rest_invalid_param",
                    "message": "Invalid parameter(s): email",
                    "data": {
                        "status": 400,
                        "params": {
                            "email": "Invalid email address."
                        },
                        "details": {
                            "email": {
                                "code": "rest_invalid_email",
                                "message": "Invalid email address.",
                                "data": ''
                            }
                        }
                    }
                }
                return jsonify(res), 400
            # Check username
            cursor = db.cursor()
            query = "SELECT users.id FROM users WHERE users.username='"+this.username+"' AND users.status=2 ORDER BY users.date DESC LIMIT 1;"
            cursor.execute(query)
            if cursor.rowcount>0:
                res = {
                    "code": "existing_user_login",
                    "message": "Sorry, that username already exists!",
                    "data": ''
                }
                return jsonify(res), 400
            # Check email exists
            query = "SELECT users.id FROM users WHERE users.email='"+this.email+"' AND users.status=2 ORDER BY users.date DESC LIMIT 1;"
            cursor.execute(query)
            if cursor.rowcount>0:
                res = {
                    "code": "existing_user_email",
                    "message": "Sorry, that email address is already used!",
                    "data": ''
                }
                return jsonify(res), 400
            this.url = SITE_URL+"/author/"+this.username
            if this.id == 0:
                this.date = datetime.now()
                query = "INSERT INTO users (username, name, email, url, locale, date, password, avatar, rating, status) VALUES ("+DB_STRING+this.username+DB_STRING+", "+DB_STRING+this.name+DB_STRING+", "+DB_STRING+this.email+DB_STRING+", "+DB_STRING+this.url+DB_STRING+", "+DB_STRING+this.locale+DB_STRING+", '"+this.date.isoformat(" ", "seconds")+"', "+DB_STRING+this.password+DB_STRING+", "+str(this.avatar)+", "+str(this.rating)+", 2) RETURNING id;"
                cursor.execute(query)
                this.id = cursor.fetchone()[0]
            else:
                query = "UPDATE users SET username="+DB_STRING+this.username+DB_STRING+", name="+DB_STRING+this.name+DB_STRING+", email="+DB_STRING+this.email+DB_STRING+", url="+DB_STRING+this.url+DB_STRING+", password="+DB_STRING+this.password+DB_STRING+", avatar="+str(this.avatar)+" WHERE id="+str(this.id)+";"
                cursor.execute(query)
                this.setAchievements()
            db.commit()
            return jsonify(this.toJSON()), 200
        except:
            print("User save error")
            res = {
                "code": "user_save_error",
                "message": "Unknown error. Please, try again later",
                "data": ''
            }
            return jsonify(res), 500

    def delete(this):
        try:
            cursor = db.cursor()
            #query = "DELETE FROM users WHERE id="+this.id+";"
            this.status = 4
            query = "UPDATE users SET status="+str(this.status)+" WHERE id="+str(this.id)+";"
            cursor.execute(query)
            db.commit()
            return jsonify(this.toJSON()), 200
        except:
            print("User delete error")
            res = {
                "code": "user_delete_error",
                "message": "Unknown error. Please, try again later",
                "data": ''
            }
            return jsonify(res), 500


# Check emails
import re
# Make a regular expression
# for validating an Email
regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b'
# Define a function for
# for validating an Email
def checkEmail(email):
    # pass the regular expression
    # and the string into the fullmatch() method
    if(re.fullmatch(regex, email)):
        return True
    else:
        return False

def check_auth(username, password):
    cursor = db.cursor()
    query = "SELECT users.id, users.username, users.password FROM users WHERE (users.username='"+username+"' OR users.email='"+username+"') AND users.status=2;"
    cursor.execute(query)
    auth = False
    if cursor.rowcount>0:
        res = cursor.fetchall()
        for (db_id, db_username, db_password) in res:
            if db_id and db_username and db_password == wp_crypt.crypt_private(password):
                auth = True
    return auth

def check_auth_service(username, password):
    return username == SERVICE_USERNAME and password == SERVICE_PASSWORD
