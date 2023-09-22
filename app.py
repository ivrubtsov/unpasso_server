from flask import Flask, request
from functools import wraps
from flask import jsonify
#from flask_sqlalchemy import SQLAlchemy
#from sqlalchemy.sql import func
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
            description = {},
            locale = '',
            rating = 0,
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
        this.description = description
        this.achievements = achievements
        this.friends = friends
        this.friendsRequestsReceived = friendsRequestsReceived
        this.friendsRequestsSent = friendsRequestsSent
    def fromJSON(this, json):
        if not json:
            return
        if json['id']:
            this.id = json['id']
        if json['name']:
            this.name = json['name']
        if json['date']:
            this.date = datetime.fromisoformat(json['date'])
        if json['username']:
            this.username = json['username']
        if json['password']:
            this.password = wp_crypt.crypt_private(json['password'])
        if json['avatar']:
            this.avatar = json['avatar']
        elif json['description'] and json['description']['avatar']:
            this.avatar = json['description']['avatar']
        if json['email']:
            this.email = json['email']
        if json['url']:
            this.url = json['url']
        if json['locale']:
            this.locale = json['locale']
        if json['rating']:
            this.rating = json['rating']
        if json['description']:
            this.description = json['description']
        if json['achievements']:
            this.achievements = json['achievements']
        elif json['description'] and json['description']['achievements']:
            this.achievements = json['description']['achievements']
        this.setAchievements()
#        if json['friends']:
#            this.friends = json['friends']
#        elif json['description'] and json['description']['friends']:
#            this.friends = json['description']['friends']
#        if json['friendsRequests']:
#            this.friendsRequests = json['friendsRequests']
#        elif json['description'] and json['description']['friendsRequests']:
#            this.friendsRequests = json['description']['friendsRequests']

    def toJSON(this):
        return {
                'id': this.id,
                'name': this.name,
                'username': this.username,
                'date': this.date.isoformat(),
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

    def toSQL(this):
        return ''

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
            query = "DELETE FROM achievements WHERE id_user="+this.id+"';"
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
            query = "SELECT friends.id_friend, users.username, users.name, users.avatar, users.rating FROM friends, users WHERE friends.id_user="+this.id+" AND friends.id_friend=users.id;"
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
            query = "SELECT friends_requests.id, friends_requests.id_status, users.id, users.username, users.name, users.avatar, users.rating FROM friends_requests, users WHERE friends_requests.id_source="+this.id+" AND friends_requests.id_target=users.id;"
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
            query = "SELECT friends_requests.id, friends_requests.id_status, users.id, users.username, users.name, users.avatar, users.rating FROM friends_requests, users WHERE friends_requests.id_target="+this.id+" AND friends_requests.id_source=users.id;"
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

    def getUserDataByUsername(this, username):
        cursor = db.cursor()
        query = "SELECT users.id, users.username, users.name, users.email, users.url, users.description, users.locale, users.date, users.avatar, users.rating FROM users WHERE users.username='"+username+"' ORDER BY users.date DESC LIMIT 1;"
        cursor.execute(query)
        res = cursor.fetchone()
        for (id, username, name, email, url, description, locale, date, avatar, rating) in res:
            this.id = id
            this.name = name
            this.date = date
            this.username = username
            this.avatar = avatar
            this.email = email
            this.url = url
            this.locale = locale
            this.rating = rating
            this.description = description
            this.achievements = this.getAchievements()
            this.friends = this.getFriends()
            this.friendsRequestsSent = this.getFriendsRequestsSent()
            this.friendsRequestsReceived = this.getFriendsRequestsReceived()
        return

app = Flask(__name__)
#app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://username:password@host:port/database_name'
#app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
#db = SQLAlchemy(app)
#
#class User(db.Model):
#    id = db.Column(db.Integer, primary_key=True)
#    firstname = db.Column(db.String(100), nullable=False)
#    lastname = db.Column(db.String(100), nullable=False)
#    email = db.Column(db.String(80), unique=True, nullable=False)
#    age = db.Column(db.Integer)
#    created_at = db.Column(db.DateTime(timezone=True),
#                           server_default=func.now())
#    bio = db.Column(db.Text)
#
#    def __repr__(self):
#        return f'<User {self.id}>'

# Check WP passwords:
# from passlib.hash import phpass
# phpass.verify("password", "wordpress hash")

def check_auth(username, password):
    cursor = db.cursor()
    query = "SELECT users.id, users.username, users.password FROM users WHERE users.username='"+username+"' OR users.email='"+username+"';"
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

def login(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth = request.authorization
        if not auth:
            return jsonify({'message': 'Authentication required'}), 401
        if not check_auth(auth.username, auth.password):
            return jsonify({'message': 'User not found'}), 403
        return f(*args, **kwargs)
    return decorated_function

def login_service(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth = request.authorization
        if not auth:
            return jsonify({'message': 'Authentication required'}), 401
        if not check_auth(auth.username, auth.password):
            return jsonify({'message': 'User not found'}), 403
        return f(*args, **kwargs)
    return decorated_function

# Server responce if a user didn't request anything
@app.route("/", methods=["GET"])
@login_service
def hello():
    return "Hello World!"

# Server responce if a user didn't request anything
@app.route("/auth", methods=["GET"])
@login
def hello():
    return "User is authorized!"

# Compatibility with the Wordpress site:
#
#  static const authUser = '$_baseUrl/users/me';
#  static String registerUser(
#    String email,
#    String password,
#    String username,
#    String name,
#    String description,
#  ) =>
#      '$_baseUrl/users?username=$username&name=$name&email=$email&password=$password&description=$description';
#
#  static String deleteUser(int id) =>
#      '$_baseUrl/users/$id?force=True&reassign=111';
#
#  static String getAchievements(int id) => '$_baseUrl/users/$id';
#
#  static String setAchievements(String description, int id) =>
#      '$_baseUrl/users/$id?description=$description';
#
#  static String getUser(int id) => '$_baseUrl/users/$id';
#
#  static String createGoal(String title, int authorId, String date) =>
#      '$_baseUrl/posts?status=publish&title=$title&author=$authorId&categories=6&date_gmt=$date';
#
#  static String getUserGoals(int authorId) =>
#      '$_baseUrl/posts?per_page=100&status=publish,future&categories=6&author=$authorId';
#
#  static String completeGoal(int postId) => '$_baseUrl/posts/$postId?tags=8';
#
#
# New v3.0 functions:
#  static String updateUser(
#          int id, String name, String userName, String description) =>
#      '$_baseUrl/users/$id?name=$name&username=$userName&description=$description';
#
#  static String getFriends(int id) => '$_baseUrl/users/$id';
#
#  static String setFriends(int id, String description) =>
#      '$_baseUrl/users/$id?description=$description';
#
#  static String inviteFriends(int id, String description) =>
#      '$_baseUrl/users/$id?description=$description';
#
#  static String createGoal() => '$_baseUrl/posts';
#
#  static String getPublicGoals() =>
#      '$_baseUrl/posts?per_page=100&status=publish,future&tags=26&categories=6';
#
#  static String getFriendsGoals() =>
#      '$_baseUrl/posts?per_page=100&status=publish,future&tags=27&categories=6';
#
#  static String getGoalById(int id) => '$_baseUrl/posts/$id';
#
#  static String updateGoal(int id) => '$_baseUrl/posts/$id';
#

# Authenticate user
@app.route(BASE_URL+'/users/me', methods=['GET'])
@login
def authUser():
    if request.method == 'GET':
        username = request.authorization.username
    else:
        print("Incorrect request")
        return jsonify({'message': 'Incorrect request'}), 400
    if (not username or username==''):
        print("Username is null")
        return jsonify({'message': 'Username is null'}), 400
    try:
        username = request.authorization.username
        user = User()
        user.getUserDataByUsername(username)
        return jsonify(user.toJSON), 200
    except:
        print("User auth error")
        return jsonify({'message': 'Server internal error'}), 500

# Register a new user
@app.route(BASE_URL+'/users', methods=['POST'])
@login_service
def registerUser():
    try:
        conn = psycopg2.connect(database=DB_DATABASE,
                                host=DB_SERVER,
                                user=DB_USER,
                                password=DB_PASSWORD,
                                port=DB_PORT)

    except:
        print("Не могу установить соединение с базой данных")
        return 500
    if request.method == 'POST':
        request_data = request.get_json()
        id_product = request_data['id_product']
        quantity = request_data['quantity']
        id_productname = request_data['id_productname']

    elif request.method == 'GET':
        id_product = request.args.get('id_product')
        quantity = request.args.get('quantity')
        id_productname = request.args.get('id_productname')
    else:
        print("Некорректный запрос")
        return 500
    if not id_product:
        print("Не указан продукт")
        return 500

    if id_productname and quantity:
        query = "UPDATE products SET id_productname="+str(id_productname)+", quantity="+str(quantity)+" WHERE id_product="+str(id_product)+""
    elif not id_productname:
        query = "UPDATE products SET quantity="+str(quantity)+" WHERE id_product="+str(id_product)+""
    elif not quantity:
        query = "UPDATE products SET id_productname="+str(id_productname)+" WHERE id_product="+str(id_product)+""

    cursor = conn.cursor()
    cursor.execute(query)
    conn.commit()
    conn.close()
    print('Продукт изменен, его номер: ',id_product)
    return {'id_product':id_product, 'operation':'update'}


# Delete a user
@app.route(BASE_URL+'/users/<int:id>', methods=['DELETE'])
def deleteUser(id):
    try:
        conn = psycopg2.connect(database=DB_DATABASE,
                                host=DB_SERVER,
                                user=DB_USER,
                                password=DB_PASSWORD,
                                port=DB_PORT)
    except:
        print("Не могу установить соединение с базой данных")
        return 500

    if request.method == 'POST':
        request_data = request.get_json()
        id_product = request_data['id_product']

    elif request.method == 'GET':
        id_product = request.args.get('id_product')
    else:
        print("Некорректный запрос")
        return 500
    if not id_product:
        print("Не указан продукт")
        return 500

    cursor = conn.cursor()
    query = "UPDATE products SET id_status=2 WHERE id_product="+str(id_product)+""
    cursor.execute(query)
    conn.commit()
    conn.close()
    print('Продукт удален, его номер: ',id_product)
    return {'id_product':id_product, 'operation':'delete'}

# Get a user data
@app.route(BASE_URL+'/users/<int:id>', methods=['GET'])
def getUser(id):
    # здесь мы обращаемся к базе данных и показываем список продуктов
    try:
        conn = psycopg2.connect(database=DB_DATABASE,
                                host=DB_SERVER,
                                user=DB_USER,
                                password=DB_PASSWORD,
                                port=DB_PORT)

    except:
        print("Не могу установить соединение с базой данных")
        return 500
    cursor = conn.cursor()
    query = ("SELECT products.id_product, product_names.name FROM products, product_names WHERE products.id_productname=product_names.id_productname AND products.id_status=1")
    cursor.execute(query)
    res = cursor.fetchall()
    products = []
    for (productID, productName) in res:
        print("Продукт номер "+str(productID)+", название: "+productName)
        products.append({'id_product':productID, 'name':productName})
    conn.close()
    return jsonify(products)


# Update user's data
# Don't forget about achievements in the description fiels
@app.route(BASE_URL+'/users/<int:id>', methods=['POST'])
def updateUser(id):
    try:
        conn = psycopg2.connect(database=DB_DATABASE,
                                host=DB_SERVER,
                                user=DB_USER,
                                password=DB_PASSWORD,
                                port=DB_PORT)
    except:
        print("Не могу установить соединение с базой данных")
        return 500
    if request.method == 'POST':
        request_data = request.get_json()
        id_user = request.args.get('id_user')

    elif request.method == 'GET':
        id_user = request.ards.get('id_user')

    # получение последнего номера чек-листа пользователя чтобы увеличить его на 1
    cursor = conn.cursor()
    query = "SELECT number FROM lists WHERE id_user="+str(id_user)+" ORDER BY number DESC LIMIT 1"
    cursor.execute(query)
    if cursor.rowcount>0:
        number = cursor.fetchone()[0]+1
    else:
        number = 1
    query = "INSERT INTO lists (id_user, number) VALUES ("+str(id_user)+", "+str(number)+") RETURNING id_list;"
    cursor.execute(query)
    id_list = cursor.fetchone()[0]
    conn.commit()
    conn.close()
    print('Добавлен чек-лист, его ид: ',id_list, ', номер чек-листа пользователя: ', number)
    return {'id_list':id_list, 'number':number}


# Create a goal
@app.route(BASE_URL+'/posts', methods=['POST'])
def createGoal():
    # здесь мы обращаемся к базе данных и показываем список продуктов
    try:
        conn = psycopg2.connect(database=DB_DATABASE,
                                host=DB_SERVER,
                                user=DB_USER,
                                password=DB_PASSWORD,
                                port=DB_PORT)

    except:
        print("Не могу установить соединение с базой данных")
        return 500

    if request.method == 'POST':
        request_data = request.get_json()
        id_user = request_data['id_user']

    elif request.method == 'GET':
        id_user = request.args.get('id_user')
    else:
        print("Некорректный запрос")
        return 500
    if not id_user:
        print("Не указан пользователь")
        return 500

    cursor = conn.cursor()
    query = ("SELECT users.id_user, users.name, users.nickname, lists.id_list, products.id_product, product_names.name, products.quantity FROM products, lists, users, product_names WHERE products.id_productname=product_names.id_productname AND products.id_status=1 AND products.id_list=lists.id_list AND lists.id_user=users.id_user AND users.id_user="+str(id_user))
    cursor.execute(query)
    res = cursor.fetchall()
    products = []
    for (userID, userName, userNickname, listID, productID, productName, productQuantity) in res:
        print("Имя: "+userName+", ник: "+userNickname+", номер чек-листа: ", listID, ", номер продукта: ", productID, ", название: ", productName, ", количество: "+str(productQuantity))
        products.append({'id_user':userID, 'userName':userName , 'userNickname:':userNickname, 'id_list':listID, 'id_product':productID, 'name':productName, 'quantity':productQuantity})
    conn.close()
    return jsonify(products)


# Get user's goals
@app.route(BASE_URL+'/posts', methods=['GET'])
def getUserGoals():
    try:
        conn = psycopg2.connect(database=DB_DATABASE,
                                host=DB_SERVER,
                                user=DB_USER,
                                password=DB_PASSWORD,
                                port=DB_PORT)

    except:
        print("Не могу установить соединение с базой данных")
        return 500
    if request.method == 'POST':
        request_data = request.get_json()
        email = request_data('email')
        name = request_data('name')
        nickname = request_data('nickname')
        password = request_data('password')

    elif request.method == 'GET':
        email = request.args.get('email')
        name = request.args.get('name')
        nickname = request.args.get('nickname')
        password = request.args.get('password')
    else:
        print("Некорректный запрос")
        return 500
    if not email:
        print("Не указан email")
        return 500
    if not name:
        print("Не указано имя")
        return 500
    if not nickname:
        print("Не указан ник")
        return 500
    if not password:
        print("Не указан пароль")
        return 500

    cursor = conn.cursor()
    query = "INSERT INTO users (email, name, nickname, password) VALUES ('"+email+"', '"+name+"' , '"+nickname+"', '"+password+"') RETURNING id_user;"
    cursor.execute(query)
    id_user = cursor.fetchone()[0]
    conn.commit()
    conn.close()
    print('Добавлен пользователь, имя: ',name,', ник: ',nickname,', его номер: ',id_user)
    return {'id_user':id_user, 'operation':'add'}


# Complete the goal
@app.route(BASE_URL+'/posts/<int:id>', methods=['POST'])
def completeGoal(id):
    try:
        conn = psycopg2.connect(database=DB_DATABASE,
                                host=DB_SERVER,
                                user=DB_USER,
                                password=DB_PASSWORD,
                                port=DB_PORT)
    except:
        print("Не могу установить соединение с базой данных")
        return 500
    if request.method == 'POST':
        request_data = request.get_json()
        id_user = request_data('id_user')
        email = request_data('email')
        name = request_data('name')
        nickname = request_data('nickname')
        password = request_data('password')

    elif request.method == 'GET':
        id_user = request.ards.get('id_user')
        email = request.args.get('email')
        name = request.args.get('name')
        nickname = request.args.get('nickname')
        password = request.args.get('password')
    else:
        print("Некорректный запрос")
        return 500
    if not id_user:
        print("Не указан идентификатор пользователя")
        return 500

    cursor = conn.cursor()
    query = "UPDATE users SET email='"+email+"', name='"+name+"', nickname='"+nickname+"', password='"+password+"' WHERE id_user="+str(id_user)+""
    cursor.execute(query)
    conn.commit()
    conn.close()
    return {'id_user':id_user, 'operation':'update'}


#  static String getFriends(int id) => '$_baseUrl/users/$id';
#
#  static String setFriends(int id, String description) =>
#      '$_baseUrl/users/$id?description=$description';
#
#  static String inviteFriends(int id, String description) =>
#      '$_baseUrl/users/$id?description=$description';
#
#  static String createGoal() => '$_baseUrl/posts';
#
#  static String getFriendsGoals(int userId) =>
#      '$_baseUrl/posts?per_page=100&status=publish,future&tags=27&categories=6&user=$userId';
#
#  static String getGoalById(int id) => '$_baseUrl/posts/$id';
#
#  static String updateGoal(int id) => '$_baseUrl/posts/$id';
#
@app.route(BASE_URL+'/friends/<int:id>', methods=['GET', 'POST'])
def friendsList(id):
    # здесь мы обращаемся к базе данных и показываем список пользователей
    try:
        conn = psycopg2.connect(database=DB_DATABASE,
                                host=DB_SERVER,
                                user=DB_USER,
                                password=DB_PASSWORD,
                                port=DB_PORT)
    except:
        print("Не могу установить соединение с базой данных")
        return 500
    cursor = conn.cursor()
    query = ("SELECT id_user,name,nickname,email FROM users")
    cursor.execute(query)
    res = cursor.fetchall()
    users = []
    for (userID, userName, userNickname, userEmail) in res:
        users.append({'id_user':userID, 'name':userName, 'nickname':userNickname, 'email':userEmail})
        print("Пользователь номер ", userID, ' имя: ', userName, ' ник: ', userNickname, ", почта: ",userEmail)
    conn.close()
    return jsonify(users)

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8000)