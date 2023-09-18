from flask import Flask, request
from flask import jsonify
import psycopg2
import os
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
BASE_URL = os.getenv('BASE_URL')
if not BASE_URL:
    BASE_URL = '/wp-json/wp/v2'

app = Flask(__name__)

# Server responce if a user didn't request anything
@app.route("/", methods=["GET"])
def hello():
    return "Hello World!"

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
def authUser():
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
        id_productname = request_data['id_productname']
        quantity = request_data['quantity']
        id_list = request_data['id_list']

    elif request.method == 'GET':
        id_productname = request.args.get('id_productname')
        quantity = request.args.get('quantity')
        id_list = request.args.get('id_list')
    else:
        print("Некорректный запрос")
        return 500
    if (not id_productname):
        print("Не указано название продукта")
        return 500
    if not quantity:
        quantity = 1
    if not id_list:
        id_list = 1

    cursor = conn.cursor()
    query = "INSERT INTO products (id_list, id_status, id_productname, quantity) VALUES ("+str(id_list)+", 1, "+str(id_productname)+", "+str(quantity)+") RETURNING id_product;"
    cursor.execute(query)
    id_product = cursor.fetchone()[0]
    conn.commit()
    conn.close()
    print('Добавлен продукт, его номер: ',id_product)
    return {'id_product':id_product, 'operation':'add'}


# Register a new user
@app.route(BASE_URL+'/users', methods=['POST'])
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
@app.route(BASE_URL+'/users/$id', methods=['DELETE'])
def deleteUser():
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
@app.route(BASE_URL+'/users/$id', methods=['GET'])
def getUser():
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
@app.route(BASE_URL+'/posts/$postId', methods=['POST'])
def completeGoal():
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


# Update user's data
@app.route(BASE_URL+'/users/$id', methods=['POST'])
def updateUser():
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
@app.route(BASE_URL+'/users/listall', methods=['GET', 'POST'])
def usersList():
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