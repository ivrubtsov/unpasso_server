from flask import Flask, request, jsonify
import json
from functools import wraps
import os
from dotenv import load_dotenv
from user import User, check_auth, check_auth_service
from goal import Goal
from goals import getUserGoals, getAvailableGoals
from users import getPublicUserById, findUsers

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
#  static String getFriends() => '$_baseUrl/friends';
#
#  static String inviteFriend(int id) => '$_baseUrl/friends/$id?action=invite';
#
#  static String acceptFriend(int id) => '$_baseUrl/friends/$id?action=accept';
#
#  static String rejectFriend(int id) => '$_baseUrl/friends/$id?action=reject';
#
#  static String removeFriend(int id) => '$_baseUrl/friends/$id?action=remove';
#
#  static String createGoal() => '$_baseUrl/posts';
#
#  static String getAvailableGoals(int page) =>
#      '$_baseUrl/posts?per_page=$fetchPageLimit&page=$page&status=publish,future&categories=6';
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
        user = User()
        user.getUserByUsername(username)
        if user.id == 0:
            return jsonify({'message': 'User is not found'}), 404
        else:
            return jsonify(user.toJSON()), 200
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
        user.getUserById(id)
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
        user.getUserById(id)
        if user.id == 0:
            return jsonify({'message': 'User is not found'}), 404
        elif not user.username == request.authorization.username:
            return jsonify(user.toPublicJSON()), 200
        else:
            return jsonify(user.toJSON()), 200
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
        user.getUserById(id)
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
    try:
        if request.method == 'POST':
            request_data = request.get_json()
            goal = Goal()
            goal.fromJSON(request_data)
            res = goal.save()
            return res
        else:
            print("Incorrect request")
            return jsonify({'message': 'Incorrect request'}), 400
    except:
        print("Goal save error")
        return jsonify({'message': 'Server internal error'}), 500

# Get user's goals - personal and available
@app.route(BASE_URL+'/posts', methods=['GET'])
@login
def getUserGoals():
    if request.method == 'GET':
        username = request.authorization.username
    else:
        print("Incorrect request")
        return jsonify({'message': 'Incorrect request'}), 400
    if (not username or username==''):
        print("Username is null")
        return jsonify({'message': 'Username is null'}), 400
    try:
        if 'page' in request.args:
            page = request.args.get('page')
        else:
            page = 1
        if 'per_page' in request.args:
            per_page = request.args.get('per_page')
        else:
            per_page = 100
        user = User()
        if 'author' in request.args:
            author = request.args.get('author')
            user.getUserById(author)
            if not user.username == username:
                print("Wrong request to get other user's goals")
                return jsonify({'message': 'Unable to update data of other users'}), 403
            else:
                return getUserGoals(author, page, per_page)
        else:
            user.getUserByUsername(username)
            return getAvailableGoals(user.id, page, per_page)
    except:
        print("Get user's goals error")
        return jsonify({'message': 'Server internal error'}), 500

# Complete or update the goal
@app.route(BASE_URL+'/posts/<int:id>', methods=['POST'])
@login
def updateGoal(id):
    if request.method == 'POST':
        username = request.authorization.username
    else:
        print("Incorrect request")
        return jsonify({'message': 'Incorrect request'}), 400
    if (not username or username==''):
        print("Username is null")
        return jsonify({'message': 'Username is null'}), 400
    if (not id or id=='' or id==0):
        print("Goal ID is null")
        return jsonify({'message': 'Goal ID is null'}), 400
    try:
        goal = Goal()
        goal.getGoalById(id)
        user = User()
        user.getUserByUsername(username)
        if goal.id == 0:
            return jsonify({'message': 'Goal is not found'}), 404
        elif not user.id == goal.author:
            return jsonify({'message': 'Unable to update data of other users'}), 403
        else:
            request_data = request.get_json()
            goal.fromJSON(request_data)
            return goal.save()
    except:
        print("Goal data error")
        return jsonify({'message': 'Server internal error'}), 500

# Get the goal by ID
@app.route(BASE_URL+'/posts/<int:id>', methods=['GET'])
@login
def getGoal(id):
    if request.method == 'GET':
        username = request.authorization.username
    else:
        print("Incorrect request")
        return jsonify({'message': 'Incorrect request'}), 400
    if (not username or username==''):
        print("Username is null")
        return jsonify({'message': 'Username is null'}), 400
    if (not id or id=='' or id==0):
        print("Goal ID is null")
        return jsonify({'message': 'Goal ID is null'}), 400
    try:
        goal = Goal()
        goal.getGoalById(id)
        user = User()
        user.getUserByUsername(username)
        if goal.id == 0:
            return jsonify({'message': 'Goal is not found'}), 404
        elif (goal.isprivate and not user.id == goal.author) or (goal.isfriends and not goal.author in user.friends):
            return jsonify({'message': 'Unable to get hidden data of other users'}), 403
        else:
            return jsonify(goal.toJSON()), 200
    except:
        print("Get goal data error")
        return jsonify({'message': 'Server internal error'}), 500

#  static String getFriends() => '$_baseUrl/friends';
#
#  static String searchFriends(String text) =>
#      '$_baseUrl/friends/search?text=$text';
#
#  static String inviteFriend(int id) => '$_baseUrl/friends/$id?action=invite';
#
#  static String acceptFriend(int id) => '$_baseUrl/friends/$id?action=accept';
#
#  static String rejectFriend(int id) => '$_baseUrl/friends/$id?action=reject';
#
#  static String removeFriend(int id) => '$_baseUrl/friends/$id?action=remove';

# Get user's friends
@app.route(BASE_URL+'/friends', methods=['GET'])
@login
def getFriends():
    if request.method == 'GET':
        username = request.authorization.username
    else:
        print("Incorrect request")
        return jsonify({'message': 'Incorrect request'}), 400
    if (not username or username==''):
        print("Username is null")
        return jsonify({'message': 'Username is null'}), 400
    try:
        user = User()
        user.getUserByUsername(username)
        return jsonify(user.friends), 200
    except:
        print("Get user's goals error")
        return jsonify({'message': 'Server internal error'}), 500

# Search for friends
@app.route(BASE_URL+'/friends/search', methods=['GET'])
@login
def getFriends():
    if request.method == 'GET':
        username = request.authorization.username
    else:
        print("Incorrect request")
        return jsonify({'message': 'Incorrect request'}), 400
    if (not username or username==''):
        print("Username is null")
        return jsonify({'message': 'Username is null'}), 400
    if 'text' in request.args:
        text = request.args.get('text')
    else:
        print("Search string is null")
        return jsonify([]), 200
    try:
        return findUsers(text)
    except:
        print("Search users error")
        return jsonify({'message': 'Server internal error'}), 500

@app.route(BASE_URL+'/friends/requests/<int:id>', methods=['POST'])
@login
def friendsRequests(id):
    try:
        if request.method == 'POST':
            username = request.authorization.username
            if (not username or username==''):
                print("Username is null")
                return jsonify({'message': 'Username is null'}), 400
            if (not id or id=='' or id==0):
                print("Friend ID is null")
                return jsonify({'message': 'Friend ID is null'}), 400
            user = User()
            user.getUserByUsername(username)
            request_data = request.get_json()
            data = json.loads(request_data)
            if 'action' in data:
                action = data['action']
                if action == 'invite':
                    return user.sendFriendsRequest(id)
                elif action == 'accept':
                    return user.acceptFriendsRequest(id)
                elif action == 'reject':
                    return user.rejectFriendsRequest(id)
                elif action == 'remove':
                    return user.removeFriend(id)
                else:
                    print("Incorrect request wrong action")
                    return jsonify({'message': 'Incorrect request'}), 400
            else:
                print("Incorrect request no action")
                return jsonify({'message': 'Incorrect request'}), 400
        else:
            print("Incorrect request")
            return jsonify({'message': 'Incorrect request'}), 400
    except:
        print("Goal save error")
        return jsonify({'message': 'Server internal error'}), 500

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8000)