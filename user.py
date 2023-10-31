from flask import jsonify
import psycopg2
import os
import random
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
DB_SEARCH_LIMIT = os.getenv('DB_SEARCH_LIMIT')
if not DB_SEARCH_LIMIT:
    DB_SEARCH_LIMIT = 10
else:
    DB_SEARCH_LIMIT = int(DB_SEARCH_LIMIT)
SITE_URL = os.getenv('SITE_URL')
SERVICE_USERNAME = os.getenv('SERVICE_USERNAME')
SERVICE_PASSWORD = os.getenv('SERVICE_PASSWORD')
MASTER_USER = os.getenv('MASTER_USER')
if not MASTER_USER:
    MASTER_USER = 737
else:
    MASTER_USER = int(MASTER_USER)
AVATAR_MAX = os.getenv('AVATAR_MAX')
if not AVATAR_MAX:
    AVATAR_MAX = 50
else:
    AVATAR_MAX = int(AVATAR_MAX)

def open_database_connection():
    try:
        connection = psycopg2.connect(database=DB_DATABASE,
                                host=DB_SERVER,
                                user=DB_USER,
                                password=DB_PASSWORD,
                                port=DB_PORT)
        print('Database connection established')
        return connection
    except Exception as e:
        print("Database connection error: "+str(e))
        quit()
db = open_database_connection()

def check_db():
    global db
    if not db.closed == 0:
        db = open_database_connection()
        return
    try:
        cursor = db.cursor()
        cursor.execute('SELECT 1')
    except psycopg2.OperationalError:
        db = open_database_connection()

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
            isPaid = False,
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
        this.isPaid = isPaid
        this.status = status
        this.achievements = achievements
        this.friends = friends
        this.friendsRequestsReceived = friendsRequestsReceived
        this.friendsRequestsSent = friendsRequestsSent
    def fromJSON(this, data):
        if not data:
            return
        # data = json.loads(data)
        if 'id' in data:
            this.id = data['id']
        if 'name' in data:
            this.name = data['name']     
        if 'date' in data:
            this.date = datetime.fromisoformat(data['date'])
        if 'username' in data:
            this.username = data['username']
        if 'password' in data:
            this.password = wp_crypt.crypt_private(data['password'])
        if 'description' in data:
            description = data['description']
        if 'avatar' in data:
            this.avatar = data['avatar']
        elif 'description' in data and 'avatar' in description:
            this.avatar = description['avatar']
        
        if 'email' in data:
            this.email = data['email']
        if 'url' in data:
            this.url = data['url']
        if 'locale' in data:
            this.locale = data['locale']
        if 'rating' in data:
            this.rating = data['rating']
        elif 'description' in data and 'rating' in description:
            this.rating = description['rating']
        if 'status' in data:
            this.status = data['status']
        if 'achievements' in data:
            this.achievements = data['achievements']
        elif 'description' in data and 'achievements' in description:
            this.achievements = description['achievements']
        return

    def toJSON(this):
        friendsIds = []
        friendsRequestsReceivedIds = []
        friendsRequestsSentIds = []
        for friend in this.friends:
            friendsIds.append(friend['id'])
        for friendsRequestReceived in this.friendsRequestsReceived:
            friendsRequestsReceivedIds.append(friendsRequestReceived['id'])
        for friendsRequestSent in this.friendsRequestsSent:
            friendsRequestsSentIds.append(friendsRequestSent['id']) 
        if not this.avatar or this.avatar == 0:
            this.avatar = random.randint(1, AVATAR_MAX)
            this.save()
       
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
                    'rating': this.rating,
                    'isPaid': this.isPaid,
                    'friends': friendsIds,
                    'friendsRequestsReceived': friendsRequestsReceivedIds,
                    'friendsRequestsSent': friendsRequestsSentIds,
                    },
                'link': SITE_URL+'/author/'+this.username,
        }

    def toPublicJSON(this):
        if not this.avatar or this.avatar == 0:
            this.avatar = random.randint(1, AVATAR_MAX)
            this.save()

        return {
                'id': this.id,
                'name': this.name,
                'username': this.username,
                'url': this.url,
                'description': {
                    'achievements': this.achievements,
                    'avatar': this.avatar,
                    'rating': this.rating,
                    },
                'link': SITE_URL+'/author/'+this.username,
        }

    def toFriendsJSON(this):
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
                    'rating': this.rating,
                    'isPaid': this.isPaid,
                    'friends': this.friends,
                    'friendsRequestsReceived': this.friendsRequestsReceived,
                    'friendsRequestsSent': this.friendsRequestsSent,
                    },
                'link': SITE_URL+'/author/'+this.username,
        }

    def getAchievements(this):
        try:
            if not this.id or this.id == 0:
                return []
            check_db()
            cursor = db.cursor()
            query = "SELECT id_achievement FROM achievements WHERE id_user="+str(this.id)+";"
            cursor.execute(query)
            res = cursor.fetchall()
            achs = []
            if cursor.rowcount>0:
                for (id_achievement) in res:
                    achs.append(id_achievement[0])
            return achs
        except Exception as e:
            print("Database get achievements request error: "+str(e))
            return []

    def setAchievements(this):
        try:
            check_db()
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
            this.updateRating()
            return
        except Exception as e:
            print("Database set achievements request error: "+str(e))
            return

    def getPaid(this):
        try:
            if not this.id or this.id == 0:
                return False
            check_db()
            cursor = db.cursor()
            query = "SELECT posts.id FROM posts WHERE posts.author="+str(this.id)+" AND posts.status=1 AND posts.isgenerated=TRUE AND posts.isaccepted=TRUE ORDER BY posts.date DESC LIMIT 1;"
            cursor.execute(query)
            res = cursor.fetchall()
            if cursor.rowcount>0:
                return True
            else:
                return False
        except Exception as e:
            print("Database get paid status error: "+str(e))
            return []

    def getFriends(this):
        try:
            check_db()
            cursor = db.cursor()
            query = "SELECT friends.id_friend, users.username, users.name, users.avatar, users.rating FROM friends, users WHERE friends.id_user="+str(this.id)+" AND friends.id_friend=users.id AND users.status=2;"
            cursor.execute(query)
            res = cursor.fetchall()
            friends = []
            if cursor.rowcount>0:
                for (id, username, name, avatar, rating) in res:
                    friends.append({
                        'id': id,
                        'username': username,
                        'name': name,
                        'description': {
                            'avatar': avatar,
                            'rating': rating,
                        }
                    })
            return friends
        except Exception as e:
            print("Database get friends error: "+str(e))
            return []

    def getFriendsRequestsSent(this):
        try:
            check_db()
            cursor = db.cursor()
            query = "SELECT friends_requests.id, friends_requests.id_status, users.id, users.username, users.name, users.avatar, users.rating FROM friends_requests, users WHERE friends_requests.id_source="+str(this.id)+" AND friends_requests.id_target=users.id AND users.status=2 AND friends_requests.id_status=1 ORDER BY friends_requests DESC;"
            cursor.execute(query)
            res = cursor.fetchall()
            friendsRequestsSent = []
            if cursor.rowcount>0:
                for (requestid, status, userid, username, name, avatar, rating) in res:
                    friendsRequestsSent.append({
                        'id': userid,
                        'username': username,
                        'name': name,
                        'description': {
                            'avatar': avatar,
                            'rating': rating,
                        }
                    })
            return friendsRequestsSent
        except Exception as e:
            print("Database get friends requests sent error: "+str(e))
            return []

    def getFriendsRequestsReceived(this):
        try:
            check_db()
            cursor = db.cursor()
            query = "SELECT friends_requests.id, friends_requests.id_status, users.id, users.username, users.name, users.avatar, users.rating FROM friends_requests, users WHERE friends_requests.id_target="+str(this.id)+" AND friends_requests.id_source=users.id AND users.status=2 AND friends_requests.id_status=1 ORDER BY friends_requests DESC;"
            cursor.execute(query)
            res = cursor.fetchall()
            friendsRequestsReceived = []
            if cursor.rowcount>0:
                for (requestid, status, userid, username, name, avatar, rating) in res:
                    friendsRequestsReceived.append({
                        'id': userid,
                        'username': username,
                        'name': name,
                        'description': {
                            'avatar': avatar,
                            'rating': rating,
                        }
                    })
            return friendsRequestsReceived
        except Exception as e:
            print("Database get friends requests received error: "+str(e))
            return []

    def acceptFriendsRequest(this, friend_id):
        try:
            for friend in this.friends:
                if friend['id'] == friend_id:
                    check_db()
                    cursor = db.cursor()
                    query = "UPDATE friends_requests SET id_status=2 WHERE id_source="+str(friend_id)+" AND id_target="+str(this.id)+";"
                    cursor.execute(query)
                    db.commit()
                    this.friendsRequestsReceived = this.getFriendsRequestsReceived()
                    return jsonify(this.toFriendsJSON()), 200
            check_db()
            cursor = db.cursor()
            query = "INSERT INTO friends (id_user, id_friend) VALUES ("+str(this.id)+", "+str(friend_id)+"), ("+str(friend_id)+", "+str(this.id)+");"
            cursor.execute(query)
            query = "UPDATE friends_requests SET id_status=2 WHERE id_source="+str(friend_id)+" AND id_target="+str(this.id)+";"
            cursor.execute(query)
            db.commit()
            this.friends = this.getFriends()
            this.friendsRequestsReceived = this.getFriendsRequestsReceived()
            this.updateRating()
            return jsonify(this.toFriendsJSON()), 200
        except Exception as e:
            print("Database accept friends request error: "+str(e))
            res = {
                "code": "friends_accept_error",
                "message": "Unknown error. Please, try again later",
                "data": ''
            }
            return jsonify(res), 500

    def rejectFriendsRequest(this, friend_id):
        try:
            for friend in this.friends:
                if friend['id'] == friend_id:
                    this.removeFriend(friend_id)
            check_db()
            cursor = db.cursor()
            query = "UPDATE friends_requests SET id_status=3 WHERE id_source="+str(friend_id)+" AND id_target="+str(this.id)+";"
            cursor.execute(query)
            db.commit()
            this.friendsRequestsReceived = this.getFriendsRequestsReceived()
            return jsonify(this.toFriendsJSON()), 200
        except Exception as e:
            print("Database reject friend request error: "+str(e))
            res = {
                "code": "friends_reject_error",
                "message": "Unknown error. Please, try again later",
                "data": ''
            }
            return jsonify(res), 500

    def sendFriendsRequest(this, friend_id):
        try:
            for friendsRequest in this.friendsRequestsSent:
                if friendsRequest['id'] == friend_id:
                    return jsonify(this.toFriendsJSON()), 200
            for friend in this.friends:
                if friend['id'] == friend_id:
                    return jsonify(this.toFriendsJSON()), 200
            check_db()
            cursor = db.cursor()
            date = datetime.now()
            query = "INSERT INTO friends_requests (id_source, id_target, id_status, date) VALUES ("+str(this.id)+", "+str(friend_id)+", 1, '"+date.isoformat(" ", "seconds")+"');"
            cursor.execute(query)
            db.commit()
            this.friendsRequestsSent = this.getFriendsRequestsSent()
            this.updateRating()
            return jsonify(this.toFriendsJSON()), 200
        except Exception as e:
            print("Database send friends request error: "+str(e))
            res = {
                "code": "friends_send_error",
                "message": "Unknown error. Please, try again later",
                "data": ''
            }
            return jsonify(res), 500

    def removeFriend(this, friend_id):
        try:
            print(this.friends)
            for friend in this.friends:
                print(friend)
                if friend['id'] == friend_id:
                    check_db()
                    cursor = db.cursor()
                    query = "DELETE FROM friends WHERE id_user="+str(friend_id)+" AND id_friend="+str(this.id)+";"
                    cursor.execute(query)
                    query = "DELETE FROM friends WHERE id_user="+str(this.id)+" AND id_friend="+str(friend_id)+";"
                    cursor.execute(query)
                    db.commit()
                    this.friends = this.getFriends()
                    this.updateRating()
            return jsonify(this.toFriendsJSON()), 200
        except Exception as e:
            print("Database remove friend request error: "+str(e))
            res = {
                "code": "friends_remove_error",
                "message": "Unknown error. Please, try again later",
                "data": ''
            }
            return jsonify(res), 500


    def getUserByUsername(this, request_username):
        try:
            check_db()
            cursor = db.cursor()
            query = "SELECT users.id, users.username, users.name, users.email, users.password, users.url, users.locale, users.date, users.avatar, users.rating FROM users WHERE users.username='"+request_username+"' AND users.status=2 LIMIT 1;"
            cursor.execute(query)
            res = cursor.fetchone()
            if res:
                (id, username, name, email, password, url, locale, date, avatar, rating) = res
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
                this.isPaid = this.getPaid()
                this.achievements = this.getAchievements()
                this.friends = this.getFriends()
                this.friendsRequestsSent = this.getFriendsRequestsSent()
                this.friendsRequestsReceived = this.getFriendsRequestsReceived()
            return
        except Exception as e:
            print("Get user data by username error: "+str(e))
            return        

    def getUserById(this, request_id):
        try:
            check_db()
            cursor = db.cursor()
            query = "SELECT users.id, users.username, users.name, users.email, users.password, users.url, users.locale, users.date, users.avatar, users.rating FROM users WHERE users.id="+str(request_id)+" AND users.status=2 LIMIT 1;"
            cursor.execute(query)
            res = cursor.fetchone()
            if res:
                (id, username, name, email, password, url, locale, date, avatar, rating) = res
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
                this.isPaid = this.getPaid()
                this.achievements = this.getAchievements()
                this.friends = this.getFriends()
                this.friendsRequestsSent = this.getFriendsRequestsSent()
                this.friendsRequestsReceived = this.getFriendsRequestsReceived()
            return
        except Exception as e:
            print("Get user data by ID error: "+str(e))
            return        
    
    def save(this):
        try:
            #Check email format
            if not checkEmail(this.email):
                res = {
                    'code': 'rest_invalid_param',
                    'message': 'Invalid parameter(s): email',
                    'data': {
                        'status': 400,
                        'params': {
                            'email': "Invalid email address."
                        },
                        'details': {
                            'email': {
                                'code': 'rest_invalid_email',
                                'message': 'Invalid email address.',
                                'data': '',
                            }
                        }
                    }
                }
                return jsonify(res), 400
            # Check username
            check_db()
            cursor = db.cursor()
            query = "SELECT users.id FROM users WHERE LOWER(users.username)="+DB_STRING+this.username.lower()+DB_STRING+" AND users.status=2 AND NOT users.id="+str(this.id)+" LIMIT 1;"
            cursor.execute(query)
            if cursor.rowcount>0:
                print('user exists')
                res = {
                    'code': 'existing_user_login',
                    'message': 'Sorry, this username is already taken!',
                    'data': '',
                }
                return jsonify(res), 500
            # Check email exists

            query = "SELECT users.id FROM users WHERE LOWER(users.email)="+DB_STRING+this.email.lower()+DB_STRING+" AND users.status=2 AND NOT users.id="+str(this.id)+" LIMIT 1;"
            cursor.execute(query)
            if cursor.rowcount>0:
                print('email exists')
                res = {
                    'code': 'existing_user_email',
                    'message': 'Sorry, this email address is already used!',
                    'data': '',
                }
                return jsonify(res), 500
            this.url = SITE_URL+"/author/"+this.username
            if this.id == 0:
                this.date = datetime.now()
                query = "INSERT INTO users (username, name, email, url, locale, date, password, avatar, rating, status) VALUES ("+DB_STRING+this.username+DB_STRING+", "+DB_STRING+this.name+DB_STRING+", "+DB_STRING+this.email+DB_STRING+", "+DB_STRING+this.url+DB_STRING+", "+DB_STRING+this.locale+DB_STRING+", '"+this.date.isoformat(" ", "seconds")+"', "+DB_STRING+this.password+DB_STRING+", "+str(this.avatar)+", "+str(this.rating)+", 2) RETURNING id;"
                cursor.execute(query)
                this.id = cursor.fetchone()[0]
                this.initialInvite()
            else:
                this.rating = this.calculateRating()
                query = "UPDATE users SET username="+DB_STRING+this.username+DB_STRING+", name="+DB_STRING+this.name+DB_STRING+", email="+DB_STRING+this.email+DB_STRING+", url="+DB_STRING+this.url+DB_STRING+", password="+DB_STRING+this.password+DB_STRING+", avatar="+str(this.avatar)+", rating="+str(this.rating)+" WHERE id="+str(this.id)+";"
                cursor.execute(query)
                this.setAchievements()
            db.commit()
            print('user save successful')
            return jsonify(this.toJSON()), 200
        except Exception as e:
            print("User save error: "+str(e))
            res = {
                "code": "user_save_error",
                "message": "Unknown error. Please, try again later",
                "data": ''
            }
            return jsonify(res), 500

    def delete(this):
        try:
            check_db()
            cursor = db.cursor()
            #query = "DELETE FROM users WHERE id="+this.id+";"
            this.status = 4
            query = "UPDATE users SET status="+str(this.status)+" WHERE id="+str(this.id)+";"
            cursor.execute(query)
            query = "UPDATE posts SET status=8 WHERE author="+str(this.id)+";"
            cursor.execute(query)
            query = "UPDATE friends_requests SET status=3 WHERE id_source="+str(this.id)+" OR id_target="+str(this.id)+";"
            cursor.execute(query)
            query = "DELETE FROM friends WHERE id_user="+str(this.id)+" OR id_friend="+str(this.id)+";"
            cursor.execute(query)
            db.commit()
            return jsonify(this.toJSON()), 200
        except Exception as e:
            print("User delete error: "+str(e))
            res = {
                "code": "user_delete_error",
                "message": "Unknown error. Please, try again later",
                "data": ''
            }
            return jsonify(res), 500

    def initialInvite(this):
        try:
            check_db()
            cursor = db.cursor()
            date = datetime.now()
            query = "INSERT INTO friends_requests (id_source, id_target, id_status, date) VALUES ("+str(MASTER_USER)+", "+str(this.id)+", 1, '"+date.isoformat(" ", "seconds")+"');"
            cursor.execute(query)
            db.commit()
            this.friendsRequestsSent = this.getFriendsRequestsSent()
            return
        except Exception as e:
            print("User Initial invite error: "+str(e))
            res = {
                "code": "user_initial_error",
                "message": "Unknown error. Please, try again later",
                "data": ''
            }
            return jsonify(res), 500
        
    def updateRating(this):
        try:
            this.rating = this.calculateRating()
            if this.id != 0:
                check_db()
                cursor = db.cursor()
                query = "UPDATE users SET rating="+str(this.rating)+" WHERE id="+str(this.id)+";"
                cursor.execute(query)
                db.commit()
            print('user rating update successful')
            return
        except Exception as e:
            print("User rating update error: "+str(e))
            res = {
                "code": "user_rating_update_error",
                "message": "Unknown error. Please, try again later",
                "data": ''
            }
            return jsonify(res), 500

    def calculateRating(this):
        try:
            check_db()
            cursor = db.cursor()
            query = "SELECT count(posts.id) FROM posts WHERE posts.author="+str(this.id)+" AND posts.status=1;"
            cursor.execute(query)
            if cursor.rowcount>0:
                res = cursor.fetchone()
                goals = res[0]
            else:
                goals = 0

            query = "SELECT count(posts.id) FROM posts WHERE posts.author="+str(this.id)+" AND posts.status=1 AND posts.iscompleted=TRUE;"
            cursor.execute(query)
            if cursor.rowcount>0:
                res = cursor.fetchone()
                goalsCompleted = res[0]
            else:
                goalsCompleted = 0

            friends = len(this.friends)
            friendsRequestsSent = len(this.friendsRequestsSent)
            achievements = len(this.achievements)
            rating = goals + goalsCompleted*3 + friends*7 + achievements*37 + friendsRequestsSent
            return rating
        except Exception as e:
            print("User rating calculation error: "+str(e))
            return 0


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
    check_db()
    cursor = db.cursor()
    query = "SELECT users.id, users.username, users.password FROM users WHERE (LOWER(users.username)="+DB_STRING+username.lower()+DB_STRING+" OR LOWER(users.email)="+DB_STRING+username.lower()+DB_STRING+") AND users.status=2;"
    cursor.execute(query)
    auth = False
    if cursor.rowcount>0:
        res = cursor.fetchall()
        for (db_id, db_username, db_password) in res:
            user_password = wp_crypt.crypt_private(password, db_password)
            if db_id and db_username and db_password == user_password:
                auth = True
    return auth

def check_auth_service(username, password):
    return username == SERVICE_USERNAME and password == SERVICE_PASSWORD

def findUsers(request_string):
    try:
        check_db()
        cursor = db.cursor()
        query = "SELECT users.id, users.username, users.name, users.email, users.url, users.date, users.avatar, users.rating FROM users WHERE (LOWER(users.name) LIKE "+DB_STRING+"%"+str(request_string)+"%"+DB_STRING+" OR LOWER(users.username) LIKE "+DB_STRING+"%"+str(request_string)+"%"+DB_STRING+") AND users.status=2 LIMIT "+str(DB_SEARCH_LIMIT)+";"
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
                url=url,
            )
            # public.getAchievements()
            publicUsers.append(public.toPublicJSON())
        return jsonify(publicUsers), 200

    except Exception as e:
        print("Search users by name or username error: "+str(e))
        res = {
            "code": "search_users_error",
            "message": "Unknown error. Please, try again later",
            "data": ''
        }
        return jsonify(res), 500

def getPublicUserById(request_id):
    try:
        check_db()
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

    except Exception as e:
        print("Get public user data by ID error: "+str(e))
        res = {
            "code": "get_user_public_error",
            "message": "Unknown error. Please, try again later",
            "data": ''
        }
        return jsonify(res), 500
