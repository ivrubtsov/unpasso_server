from flask import jsonify
import json
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
MASTER_USER = os.getenv('MASTER_USER')
if not MASTER_USER:
    MASTER_USER = 737

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

class Goal:
    def __init__(
            this,
            id = 0,
            author = 0,
            date = datetime.now(),
            title = '',
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
        this.link = link
        this.status = status
        this.iscompleted = iscompleted
        this.ispublic = ispublic
        this.isfriends = isfriends
        this.isprivate = isprivate
        this.likes = likes
        this.likeUsers = likeUsers
    def fromJSON(this, data):
        if not data:
            return
        # data = json.loads(data)
        if 'id' in data:
            this.id = data['id']
            this.link = SITE_URL+'/?p='+str(this.id)
        if 'author' in data:
            this.author = data['author']
        if 'date' in data:
            this.date = datetime.fromisoformat(data['date'])
        if 'date_gmt' in data:
            this.date = datetime.fromisoformat(data['date_gmt'])
        if 'title' in data:
            this.title = data['title']
        if 'tags' in data:
            tags = data['tags']
            if 8 in tags:
                this.iscompleted = True
            else:
                this.iscompleted = False
            if 26 in tags:
                this.ispublic = True
            else:
                this.ispublic = False
            if 27 in tags:
                this.isfriends = True
            else:
                this.isfriends = False
            if 28 in tags:
                this.isprivate = True
            else:
                this.isprivate = False
        if 'status' in data:
            if data['status'] == 'publish':
                this.status = 1
            if data['status'] == 'future':
                this.status = 2
            if data['status'] == 'draft':
                this.status = 3
            if data['status'] == 'pending':
                this.status = 4
            if data['status'] == 'private':
                this.status = 5
            if data['status'] == 'deleted':
                this.status = 6
        return

    def toJSON(this):
        if this.iscompleted:
            tags = [8]
        else:
            tags = []
        if this.ispublic:
            tags.append(26)
        if this.isfriends:
            tags.append(27)
        if this.isprivate:
            tags.append(28)

        user = User()
        user.getUserById(this.author)

        description = {
            'authorName': user.name,
            'authorUserName': user.username,
            'authorAvatar': user.avatar,
            'authorRating': user.rating,
            'friendsUsers': user.friends,
            'likeUsers': this.likeUsers,
        }
    
        return {
            'id': this.id,
            'title': {'rendered': this.title},
            'date': this.date.isoformat("T", "seconds"),
            'author': this.author,
            'tags': tags,
            'content': {'rendered': description},
        }

    def getLikes(this):
        try:
            cursor = db.cursor()
            query = "SELECT id_user FROM likes WHERE id_post="+this.id+";"
            cursor.execute(query)
            res = cursor.fetchall()
            likes = []
            for (id_user) in res:
                likes.append(id_user)
            this.likeUsers = likes
            this.likes = len(this.likeUsers)
            return
        except:
            print("Database get likes request error")
            return []

    def addLike(this, id_user):
        try:
            this.getLikes()
            if not id_user in this.likeUsers:
                cursor = db.cursor()
                query = "INSERT INTO likes (id_post, id_user) VALUES ("+str(this.id)+", "+str(id_user)+");"
                cursor.execute(query)
                db.commit()
                this.likeUsers.append(id_user)
                this.likes = this.likes+1
            return
        except:
            print("Database add like request error")
            return

    def removeLike(this, id_user):
        try:
            this.getLikes()
            if id_user in this.likeUsers:
                cursor = db.cursor()
                query = "DELETE FROM likes WHERE id_post="+str(this.id)+" AND id_user="+str(id_user)+";"
                cursor.execute(query)
                db.commit()
                this.likeUsers.remove(id_user)
                this.likes = this.likes-1
            return
        except:
            print("Database remove like request error")
            return

    def getGoalById(this, request_id):
        try:
            cursor = db.cursor()
            query = "SELECT posts.id, posts.author, posts.date, posts.title, posts.link, posts.status, posts.iscompleted, posts.ispublic, posts.isfriends, posts.isprivate FROM posts WHERE posts.id="+str(request_id)+" AND posts.status=1 ORDER BY posts.date DESC LIMIT 1;"
            cursor.execute(query)
            res = cursor.fetchone()
            for (id, author, date, title, link, status, iscompleted, ispublic, isfriends, isprivate) in res:
                this.id = id
                this.author = author
                #this.date = datetime.fromisoformat(date)
                this.date = date
                this.title = title
                this.link = link
                this.status = status
                this.iscompleted = iscompleted
                this.ispublic = ispublic
                this.isfriends = isfriends
                this.isprivate = isprivate
                this.getLikes()
            return
        except:
            print("Get post data by ID error")
            return        
    
    def save(this):
        #try:
            if this.iscompleted:
                iscompleted = "TRUE"
            else:
                iscompleted = "FALSE"
            if this.ispublic:
                ispublic = "TRUE"
            else:
                ispublic = "FALSE"
            if this.isfriends:
                isfriends = "TRUE"
            else:
                isfriends = "FALSE"
            if this.isprivate:
                isprivate = "TRUE"
            else:
                isprivate = "FALSE"
            cursor = db.cursor()
            if this.id == 0:
                # this.date = datetime.now()
                query = "INSERT INTO posts (author, date, title, link, status, iscompleted, ispublic, isfriends, isprivate) VALUES ("+str(this.author)+", '"+this.date.isoformat(" ", "seconds")+"', "+DB_STRING+this.title+DB_STRING+", '', "+str(this.status)+", "+iscompleted+", "+ispublic+", "+isfriends+", "+isprivate+") RETURNING id;"
                cursor.execute(query)
                this.id = cursor.fetchone()[0]
                this.link = SITE_URL+'/?p='+str(this.id)
                query = "UPDATE posts SET link='"+this.link+"' WHERE id="+str(this.id)+";"
                cursor.execute(query)
            else:
                query = "UPDATE posts SET title="+DB_STRING+this.title+DB_STRING+", link='"+this.link+"', status="+str(this.status)+", iscompleted="+iscompleted+", ispublic="+ispublic+", isfriends="+isfriends+", isprivate="+isprivate+" WHERE id="+str(this.id)+";"
                cursor.execute(query)
            db.commit()
            return jsonify(this.toJSON()), 200
        #except:
        #    print("Post save error")
        #    res = {
        #        "code": "post_save_error",
        #        "message": "Unknown error. Please, try again later",
        #        "data": ''
        #    }
        #    return jsonify(res), 500

    def delete(this):
        try:
            cursor = db.cursor()
            this.status = 6
            query = "UPDATE posts SET status="+str(this.status)+" WHERE id="+str(this.id)+";"
            cursor.execute(query)
            db.commit()
            return jsonify(this.toJSON()), 200
        except:
            print("Post delete error")
            res = {
                "code": "post_delete_error",
                "message": "Unknown error. Please, try again later",
                "data": ''
            }
            return jsonify(res), 500

def getPersonalUserGoals(user_id, page, per_page):
    #try:
        if page:
            page = int(page)
            if page < 1:
                page = 1
        else:
            page = 1
        if per_page:
            per_page = int(per_page)
            if per_page < 1:
                per_page = DB_FETCH_LIMIT
        else:
            per_page = DB_FETCH_LIMIT
        cursor = db.cursor()
        offset = per_page * (page - 1)
        query = "SELECT posts.id, posts.author, posts.date, posts.title, posts.link, posts.status, posts.iscompleted, posts.ispublic, posts.isfriends, posts.isprivate FROM posts WHERE posts.author="+str(user_id)+" AND posts.status=1 ORDER BY posts.date DESC LIMIT "+str(per_page)+" OFFSET "+str(offset)+";"
        cursor.execute(query)
        res = cursor.fetchall()
        goals = []
        if cursor.rowcount>0:
            for (id, author, date, title, link, status, iscompleted, ispublic, isfriends, isprivate) in res:
                goal = Goal(
                    id,
                    author,
                    #datetime.fromisoformat(date),
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
    #except:
    #    print("Get user's goals error")
    #    res = {
    #        "code": "get_user_goals_error",
    #        "message": "Unknown error. Please, try again later",
    #        "data": ''
    #    }
    #    return jsonify(res), 500

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
                per_page = DB_FETCH_LIMIT
        else:
            per_page = DB_FETCH_LIMIT
        offset = per_page * (page - 1)
        cursor = db.cursor()
        query = "SELECT posts.id, posts.author, posts.date, posts.title, posts.link, posts.status, posts.iscompleted, posts.ispublic, posts.isfriends, posts.isprivate FROM posts, friends WHERE ((posts.ispublic=TRUE OR (posts.author=friends.id_user AND friends.id_friend="+str(user_id)+" AND posts.isfriends=TRUE)) AND posts.status=1) ORDER BY posts.date DESC LIMIT "+str(per_page)+" OFFSET "+str(offset)+";"
        cursor.execute(query)
        res = cursor.fetchall()
        goals = []
        if cursor.rowcount>0:
            for (id, author, date, title, link, status, iscompleted, ispublic, isfriends, isprivate) in res:
                goal = Goal(
                    id,
                    author,
                    #datetime.fromisoformat(date),
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
