from flask import jsonify
import psycopg2
import os
import atexit
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
DB_FETCH_LIMIT = os.getenv('DB_FETCH_LIMIT')
if not DB_FETCH_LIMIT:
    DB_FETCH_LIMIT = 100
else:
    DB_FETCH_LIMIT = int(DB_FETCH_LIMIT)
OPENAI_GOALS_LIMIT_PERSONAL = os.getenv('OPENAI_GOALS_LIMIT_PERSONAL')
if not OPENAI_GOALS_LIMIT_PERSONAL:
    OPENAI_GOALS_LIMIT_PERSONAL = 300
else:
    OPENAI_GOALS_LIMIT_PERSONAL = int(OPENAI_GOALS_LIMIT_PERSONAL)
OPENAI_GOALS_LIMIT_ALL = os.getenv('OPENAI_GOALS_LIMIT_ALL')
if not OPENAI_GOALS_LIMIT_ALL:
    OPENAI_GOALS_LIMIT_ALL = 1000
else:
    OPENAI_GOALS_LIMIT_ALL = int(OPENAI_GOALS_LIMIT_ALL)
SITE_URL = os.getenv('SITE_URL')
LOG_LEVEL = os.getenv('LOG_LEVEL')
if not LOG_LEVEL:
    LOG_LEVEL = 'debug'


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


# defining function to run on shutdown
def close_database_connection():
    db.close()
    print("Database connection closed")


# Register the function to be called on exit
atexit.register(close_database_connection)


class Goal:
    def __init__(
            this,
            id=0,
            user=User(),
            date=datetime.now(),
            title='',
            link='',
            status=1,
            iscompleted=False,
            ispublic=True,
            isfriends=False,
            isprivate=False,
            likes=0,
            likeUsers=[],
            isgenerated=False,
            isaccepted=False,
    ):
        this.id = id
        this.user = user
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
        this.isgenerated = isgenerated
        this.isaccepted = isaccepted

    def fromJSON(this, data):
        if not data:
            return
        # data = json.loads(data)
        if 'id' in data:
            this.id = data['id']
            this.link = SITE_URL+'/?p='+str(this.id)
        if 'author' in data:
            user = User()
            user.getUserById(data['author'])
            this.user = user
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
            if 29 in tags:
                this.isgenerated = True
            else:
                this.isgenerated = False
            if 30 in tags:
                this.isaccepted = True
            else:
                this.isaccepted = False
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
        if this.isgenerated:
            tags.append(29)
        if this.isaccepted:
            tags.append(30)

        this.date = this.date.replace(tzinfo=None)

        description = {
            'authorName': this.user.name,
            'authorUserName': this.user.username,
            'authorAvatar': this.user.avatar,
            'authorRating': this.user.rating,
            'friendsUsers': [],  # For the compatibility with the previous version
            'likeUsers': this.likeUsers,
        }

        return {
            'id': this.id,
            'title': {'rendered': this.title},
            'date': this.date.isoformat("T", "seconds"),
            'author': this.user.id,
            'tags': tags,
            'content': {'rendered': description},
        }

    def getLikes(this):
        try:
            if LOG_LEVEL == 'debug':
                print('Getting likes for a goal')
                print('Author: '+str(this.user.id))
                print('Goal: '+str(this.id))
            check_db()
            cursor = db.cursor()
            query = "SELECT id_user FROM likes WHERE id_post="+str(this.id)+";"
            cursor.execute(query)
            res = cursor.fetchall()
            likes = []
            if cursor.rowcount > 0:
                for (id_user) in res:
                    likes.append(id_user[0])
            this.likeUsers = likes
            this.likes = len(this.likeUsers)
            return
        except Exception as e:
            print("Database get likes request error: "+str(e))
            return []

    def addLike(this, id_user):
        try:
            if LOG_LEVEL == 'debug':
                print('Adding a like for a goal')
                print('Author: '+str(this.user.id))
                print('Goal: '+str(this.id))
                print('User: '+str(id_user))
            this.getLikes()
            if id_user not in this.likeUsers:
                check_db()
                cursor = db.cursor()
                query = "INSERT INTO likes (id_post, id_user) VALUES ("+str(this.id)+", "+str(id_user)+");"
                cursor.execute(query)
                db.commit()
                this.likeUsers.append(id_user)
                this.likes = this.likes+1
            return
        except Exception as e:
            print("Database add like request error: "+str(e))
            cursor = db.cursor()
            cursor.execute("ROLLBACK")
            db.commit()
            return

    def removeLike(this, id_user):
        try:
            if LOG_LEVEL == 'debug':
                print('Removing a like for a goal')
                print('Author: '+str(this.user.id))
                print('Goal: '+str(this.id))
                print('User: '+str(id_user))
            this.getLikes()
            if id_user in this.likeUsers:
                check_db()
                cursor = db.cursor()
                query = "DELETE FROM likes WHERE id_post="+str(this.id)+" AND id_user="+str(id_user)+";"
                cursor.execute(query)
                db.commit()
                this.likeUsers.remove(id_user)
                this.likes = this.likes-1
            return
        except Exception as e:
            print("Database remove like request error: "+str(e))
            cursor = db.cursor()
            cursor.execute("ROLLBACK")
            db.commit()
            return

    def getGoalById(this, request_id):
        try:
            if LOG_LEVEL == 'debug':
                print('Looking for a goal by id')
                print('Goal: '+str(request_id))
            check_db()
            cursor = db.cursor()
            query = "SELECT DISTINCT posts.id, posts.date, posts.title, posts.link, posts.status, posts.iscompleted, posts.ispublic, posts.isfriends, posts.isprivate, posts.isgenerated, posts.isaccepted, users.id, users.username, users.name, users.avatar, users.rating FROM posts,users WHERE posts.id="+str(request_id)+" AND posts.status=1 AND posts.author=users.id ORDER BY posts.date DESC LIMIT 1;"
            cursor.execute(query)
            res = cursor.fetchone()
            if cursor.rowcount > 0:
                (id, date, title, link, status, iscompleted, ispublic, isfriends, isprivate, isgenerated, isaccepted, userid, userUsername, userName, userAvatar, userRating) = res
                this.id = id
                this.user = User(
                    id=userid,
                    name=userName,
                    username=userUsername,
                    avatar=userAvatar,
                    rating=userRating
                    )
                # this.date = datetime.fromisoformat(date)
                this.date = date
                this.title = title
                this.link = link
                this.status = status
                this.iscompleted = iscompleted
                this.ispublic = ispublic
                this.isfriends = isfriends
                this.isprivate = isprivate
                this.isgenerated = isgenerated
                this.isaccepted = isaccepted
                this.getLikes()
            return
        except Exception as e:
            print("Get post data by ID error: "+str(e))
            return

    def save(this):
        try:
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
            if this.isgenerated:
                isgenerated = "TRUE"
            else:
                isgenerated = "FALSE"
            if this.isaccepted:
                isaccepted = "TRUE"
            else:
                isaccepted = "FALSE"
            check_db()
            cursor = db.cursor()
            if this.id == 0:
                if LOG_LEVEL == 'debug':
                    print('Creating a goal')
                    print('Author: '+str(this.user.id))
                # this.date = datetime.now()
                query = "INSERT INTO posts (author, date, title, link, status, iscompleted, ispublic, isfriends, isprivate, isgenerated, isaccepted) VALUES ("+str(this.user.id)+", '"+this.date.isoformat(" ", "seconds")+"', "+DB_STRING+this.title+DB_STRING+", '', "+str(this.status)+", "+iscompleted+", "+ispublic+", "+isfriends+", "+isprivate+", "+isgenerated+", "+isaccepted+") RETURNING id;"
                cursor.execute(query)
                this.id = cursor.fetchone()[0]
                if LOG_LEVEL == 'debug':
                    print('Goal: '+str(this.id))
                this.link = SITE_URL+'/?p='+str(this.id)
                query = "UPDATE posts SET link='"+this.link+"' WHERE id="+str(this.id)+";"
                cursor.execute(query)
                if this.isgenerated and this.isaccepted:
                    query = "UPDATE posts SET status=9 WHERE title="+DB_STRING+this.title+DB_STRING+" AND status=7;"
                    cursor.execute(query)
            else:
                if LOG_LEVEL == 'debug':
                    print('Updating a goal')
                    print('Author: '+str(this.user.id))
                    print('Goal: '+str(this.id))
                query = "UPDATE posts SET title="+DB_STRING+this.title+DB_STRING+", link='"+this.link+"', status="+str(this.status)+", iscompleted="+iscompleted+", ispublic="+ispublic+", isfriends="+isfriends+", isprivate="+isprivate+" WHERE id="+str(this.id)+";"
                cursor.execute(query)
            db.commit()
            if LOG_LEVEL == 'debug':
                print('Goal is saved')
            return jsonify(this.toJSON()), 200
        except Exception as e:
            print("Post save error: "+str(e))
            cursor = db.cursor()
            cursor.execute("ROLLBACK")
            db.commit()
            res = {
                "code": "post_save_error",
                "message": "Unknown error. Please, try again later",
                "data": ''
            }
            return jsonify(res), 500

    def delete(this):
        try:
            if LOG_LEVEL == 'debug':
                print('Deleting a goal')
                print('Author: '+str(this.user.id))
                print('Goal: '+str(this.id))
            check_db()
            cursor = db.cursor()
            this.status = 6
            query = "UPDATE posts SET status="+str(this.status)+" WHERE id="+str(this.id)+";"
            cursor.execute(query)
            db.commit()
            return jsonify(this.toJSON()), 200
        except Exception as e:
            print("Post delete error: "+str(e))
            cursor = db.cursor()
            cursor.execute("ROLLBACK")
            db.commit()
            res = {
                "code": "post_delete_error",
                "message": "Unknown error. Please, try again later",
                "data": ''
            }
            return jsonify(res), 500


def getPersonalUserGoals(user, page, per_page):
    try:
        if LOG_LEVEL == 'debug':
            print('Getting personal goals for a user')
            print('User: '+str(user.id))
            print('Page/per page: '+str(page)+'/'+str(per_page))
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
        check_db()
        cursor = db.cursor()
        offset = per_page * (page - 1)
        query = "SELECT DISTINCT posts.id, posts.date, posts.title, posts.link, posts.status, posts.iscompleted, posts.ispublic, posts.isfriends, posts.isprivate, posts.isgenerated, posts.isaccepted FROM posts WHERE posts.author="+str(user.id)+" AND posts.status=1 ORDER BY posts.date DESC LIMIT "+str(per_page)+" OFFSET "+str(offset)+";"
        cursor.execute(query)
        res = cursor.fetchall()
        goals = []
        if cursor.rowcount > 0:
            for (id, date, title, link, status, iscompleted, ispublic, isfriends, isprivate, isgenerated, isaccepted) in res:
                goal = Goal(
                    id=id,
                    user=user,
                    # datetime.fromisoformat(date),
                    date=date,
                    title=title,
                    link=link,
                    status=status,
                    iscompleted=iscompleted,
                    ispublic=ispublic,
                    isfriends=isfriends,
                    isprivate=isprivate,
                    isgenerated=isgenerated,
                    isaccepted=isaccepted,
                )
                goal.getLikes()
                goals.append(goal.toJSON())
        return jsonify(goals), 200
    except Exception as e:
        print("Get user's goals error: "+str(e))
        res = {
            "code": "get_user_goals_error",
            "message": "Unknown error. Please, try again later",
            "data": ''
        }
        return jsonify(res), 500


def getAvailableGoals(user, page, per_page):
    try:
        if LOG_LEVEL == 'debug':
            print('Getting available goals for a user')
            print('User: '+str(user.id))
            print('Page/per page: '+str(page)+'/'+str(per_page))
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
        check_db()
        cursor = db.cursor()
        query = "SELECT DISTINCT posts.id, posts.date, posts.title, posts.link, posts.status, posts.iscompleted, posts.ispublic, posts.isfriends, posts.isprivate, users.id, users.username, users.name, users.avatar, users.rating FROM posts, friends, users WHERE ((posts.ispublic=TRUE OR (posts.author=friends.id_user AND friends.id_friend="+str(user.id)+" AND posts.isfriends=TRUE)) AND posts.status=1 AND NOT posts.author="+str(user.id)+" AND posts.author=users.id) ORDER BY posts.date DESC LIMIT "+str(per_page)+" OFFSET "+str(offset)+";"
        cursor.execute(query)
        res = cursor.fetchall()
        goals = []
        if cursor.rowcount > 0:
            for (id, date, title, link, status, iscompleted, ispublic, isfriends, isprivate, userid, userUsername, userName, userAvatar, userRating) in res:
                goal = Goal(
                    id=id,
                    user=User(
                        id=userid,
                        name=userName,
                        username=userUsername,
                        avatar=userAvatar,
                        rating=userRating
                    ),
                    # datetime.fromisoformat(date),
                    date=date,
                    title=title,
                    link=link,
                    status=status,
                    iscompleted=iscompleted,
                    ispublic=ispublic,
                    isfriends=isfriends,
                    isprivate=isprivate,
                )
                goal.getLikes()
                goals.append(goal.toJSON())
        return jsonify(goals), 200
    except Exception as e:
        print("Get available goals error: "+str(e))
        res = {
            "code": "get_available_goals_error",
            "message": "Unknown error. Please, try again later",
            "data": ''
        }
        return jsonify(res), 500


def aiGetUserGoals(user_id):
    try:
        if LOG_LEVEL == 'debug':
            print('Getting goals for a user to use in the AI generator')
            print('User: '+str(user_id))
        check_db()
        cursor = db.cursor()
        # query = "SELECT posts.date, posts.title, posts.iscompleted, posts.isgenerated, posts.isaccepted FROM posts WHERE posts.author="+str(user_id)+" AND (posts.status=1 OR posts.status=7) ORDER BY posts.date DESC LIMIT "+str(OPENAI_GOALS_LIMIT_PERSONAL)+";"
        query = "SELECT DISTINCT posts.date, posts.title, posts.iscompleted, posts.isgenerated, posts.isaccepted FROM posts WHERE posts.author="+str(user_id)+" AND (posts.status=1) ORDER BY posts.date DESC LIMIT "+str(OPENAI_GOALS_LIMIT_PERSONAL)+";"
        cursor.execute(query)
        res = cursor.fetchall()
        goals = []
        if cursor.rowcount > 0:
            for (date, title, iscompleted, isgenerated, isaccepted) in res:
                goal = {
                    'date': date,
                    'title': title,
                    'iscompleted': iscompleted,
                    'isgenerated': isgenerated,
                    'isaccepted': isaccepted,
                }
                goals.append(goal)
        if LOG_LEVEL == 'debug':
            print(goals)
        return goals
    except Exception as e:
        print("Get user's goals for AI error: "+str(e))
        return []


def aiGetAllGoals():
    try:
        if LOG_LEVEL == 'debug':
            print('Getting all available goals for AI generator')
        check_db()
        cursor = db.cursor()
        query = "SELECT posts.date, posts.title, posts.iscompleted, posts.isgenerated, posts.isaccepted FROM posts WHERE (posts.status=1 OR posts.status=7) ORDER BY posts.date DESC LIMIT "+str(OPENAI_GOALS_LIMIT_ALL)+";"
        cursor.execute(query)
        res = cursor.fetchall()
        goals = []
        if cursor.rowcount > 0:
            for (date, title, iscompleted, isgenerated, isaccepted) in res:
                goal = {
                    'date': date,
                    'title': title,
                    'iscompleted': iscompleted,
                    'isgenerated': isgenerated,
                    'isaccepted': isaccepted,
                }
                goals.append(goal)
        if LOG_LEVEL == 'debug':
            print(goals)
        return goals
    except Exception as e:
        print("Get all users' goals for AI error: "+str(e))
        return []
