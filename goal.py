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

class Goal:
    def __init__(
            this,
            id = 0,
            author = 0,
            date = datetime.now(),
            title = '',
            content = '',
            link = '',
            status = 1, 
            iscompleted = False,
            ispublic = True,
            isfriends = False,
            isprivate = False,
            likes = 0,
            likeUsers = [],
        ):
        this.id = id
        this.author = author
        this.date = date
        this.title = title
        this.content = content
        this.link = link
        this.status = status
        this.iscompleted = iscompleted
        this.ispublic = ispublic
        this.isfriends = isfriends
        this.isprivate = isprivate
        this.likes = likes
        this.likeUsers = likeUsers
    def fromJSON(this, jsonData):
        if not jsonData:
            return
        data = json.loads(jsonData)
        if 'id' in data:
            this.id = data['id']
        if 'author' in data:
            this.author = data['author']
        if 'date' in data:
            this.date = datetime.fromisoformat(data['date'])
        if 'date_gmt' in data:
            this.date = datetime.fromisoformat(data['date_gmt'])
        if 'title' in data:
            this.title = data['title']
    final List<int> tags = isCompleted ? [8] : [];
    if (isPublic) tags.add(26);
    if (isFriends) tags.add(27);
    if (isPrivate) tags.add(28);
    final createdDate = createdAt.toUtc();
    final Map<String, dynamic> description = {
      'authorName': authorName,
      'authorUserName': authorUserName,
      'authorAvatar': authorAvatar,
      'authorRating': authorRating,
      'friendsUsers': friendsUsers,
      'likeUsers': likeUsers,
      'likes': likeUsers.length + 1,
    };

        if 'rating' in data:
            this.rating = data['rating']
        if 'status' in data:
            this.status = data['status']

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
            query = "DELETE FROM achievements WHERE id_user="+this.id+";"
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

    def getPostDataById(this, request_id):
        try:
            cursor = db.cursor()
            query = "SELECT users.id, users.username, users.name, users.email, users.url, users.locale, users.date, users.avatar, users.rating FROM users WHERE users.id="+request_id+" AND users.status=2 ORDER BY users.date DESC LIMIT 1;"
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
                INSERT INTO public.posts(
	id, author, date, date_gmt, title, content, link, status, iscompleted, ispublic, isfriends, isprivate)
	VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                query = "INSERT INTO users (username, name, email, url, locale, date, password, avatar, rating, status) VALUES ('"+this.username+"', '"+this.name+"', '"+this.email+"', '"+this.url+"', '"+this.locale+"', '"+this.date.isoformat(" ", "seconds")+"', '"+this.password+"', "+str(this.avatar)+", "+str(this.rating)+", 2) RETURNING id;"
                cursor.execute(query)
                this.id = cursor.fetchone()[0]
            else:
                query = "UPDATE users SET username='"+this.username+"', name='"+this.name+"', email='"+this.email+"', url='"+this.url+"', password='"+this.password+"', avatar="+str(this.avatar)+" WHERE id="+str(this.id)+";"
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
