from flask import Flask, request, jsonify
from functools import wraps
import os
from dotenv import load_dotenv
from user import User, check_auth, check_auth_service

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

app = Flask(__name__)

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
        if not check_auth_service(auth.username, auth.password):
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
        if user.id == 0:
            return jsonify({'message': 'User is not found'}), 404
        else:
            return jsonify(user.toJSON), 200
    except:
        print("User auth error")
        return jsonify({'message': 'Server internal error'}), 500

# Register a new user
@app.route(BASE_URL+'/users', methods=['GET', 'POST'])
@login_service
def registerUser():
    try:
        if request.method == 'POST':
            request_data = request.get_json()
            user = User()
            user.fromJSON(request_data)
            res = user.save()
            return res
        else:
            print("Incorrect request")
            return jsonify({'message': 'Incorrect request'}), 400
    except:
        print("User registration error")
        return jsonify({'message': 'Server internal error'}), 500

# Delete a user
@app.route(BASE_URL+'/users/<int:id>', methods=['DELETE'])
@login_service
def deleteUser(id):
    if (not id or id=='' or id==0):
        print("User ID is null")
        return jsonify({'message': 'User ID is null'}), 400
    try:
        user = User()
        user.getUserDataById(id)
        if user.id == 0:
            return jsonify({'message': 'User is not found'}), 404
#        elif not user.username == request.authorization.username:
#            return jsonify({'message': 'Unable to access data of other users'}), 403
        else:
            res = user.delete()
            return res
    except:
        print("User delete error")
        return jsonify({'message': 'Server internal error'}), 500

# Get a user data
@app.route(BASE_URL+'/users/<int:id>', methods=['GET'])
@login_service
def getUser(id):
    if (not id or id=='' or id==0):
        print("User ID is null")
        return jsonify({'message': 'User ID is null'}), 400
    try:
        user = User()
        user.getUserDataById(id)
        if user.id == 0:
            return jsonify({'message': 'User is not found'}), 404
#        elif not user.username == request.authorization.username:
#            return jsonify({'message': 'Unable to access data of other users'}), 403
        else:
            return jsonify(user.toJSON), 200
    except:
        print("User data error")
        return jsonify({'message': 'Server internal error'}), 500

# Update user's data
# Don't forget about achievements in the description fiels
@app.route(BASE_URL+'/users/<int:id>', methods=['POST'])
@login
def updateUser(id):
    if (not id or id=='' or id==0):
        print("User ID is null")
        return jsonify({'message': 'User ID is null'}), 400
    try:
        user = User()
        user.getUserDataById(id)
        if user.id == 0:
            return jsonify({'message': 'User is not found'}), 404
        elif not user.username == request.authorization.username:
            return jsonify({'message': 'Unable to update data of other users'}), 403
        else:
            if request.method == 'POST':
                request_data = request.get_json()
                user.fromJSON(request_data)
                res = user.save()
                return res
            else:
                print("Incorrect request")
                return jsonify({'message': 'Incorrect request'}), 400
    except:
        print("User data error")
        return jsonify({'message': 'Server internal error'}), 500

# Create a goal
@app.route(BASE_URL+'/posts', methods=['POST'])
@login
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
@login
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
@login
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
@login
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