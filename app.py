from flask import Flask, request, jsonify
from functools import wraps
import os
import random
from datetime import datetime
import wp_crypt
from dotenv import load_dotenv
from user import User, check_auth, check_auth_service, getPublicUserById, findUsers
from goal import Goal, getPersonalUserGoals, getAvailableGoals
from ai import generateGoal

load_dotenv(".env")
TMP_DIR = os.getenv('TMP_DIR')
if not TMP_DIR:
    TMP_DIR = 'tmp'
BASE_URL = os.getenv('BASE_URL')
if not BASE_URL:
    BASE_URL = '/wp-json/wp/v2'
SERVICE_IMPORT_PASSWORD = os.getenv('SERVICE_IMPORT_PASSWORD')
if not SERVICE_IMPORT_PASSWORD:
    SERVICE_IMPORT_PASSWORD = 'password'
AVATAR_MAX = os.getenv('AVATAR_MAX')
if not AVATAR_MAX:
    AVATAR_MAX = 50
else:
    AVATAR_MAX = int(AVATAR_MAX)
LOG_LEVEL = os.getenv('LOG_LEVEL')
if not LOG_LEVEL:
    LOG_LEVEL = 'debug'

app = Flask(__name__)

def login(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth = request.authorization
        if not auth:
            return jsonify({'error_description': 'Authentication required'}), 401
        if not check_auth(auth.username, auth.password):
            return jsonify({'error_description': 'Incorrect password.'}), 403
        return f(*args, **kwargs)
    return decorated_function

def login_service(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth = request.authorization
        if not auth:
            return jsonify({'error_description': 'Authentication required'}), 401
        if not check_auth_service(auth.username, auth.password):
            return jsonify({'error_description': 'Incorrect password.'}), 403
        return f(*args, **kwargs)
    return decorated_function

# Server responce if a user didn't request anything
@app.route("/hello", methods=["GET"], endpoint='hello')
def hello():
    return "Hello World!"

# Server responce if a user didn't request anything
@app.route("/auth", methods=["GET"], endpoint='helloAuth')
@login
def helloAuth():
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
@app.route(BASE_URL+'/users/me', methods=['GET'], endpoint='authUser')
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
            return jsonify({'message': 'User does not exist.'}), 404
        else:
            return jsonify(user.toJSON()), 200
    except Exception as e:
        print("User auth error: "+str(e))
        return jsonify({'message': 'Server internal error'}), 500

# Register a new user
@app.route(BASE_URL+'/users', methods=['GET', 'POST'], endpoint='registerUser')
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
    except Exception as e:
        print("User registration error: "+str(e))
        return jsonify({'message': 'Server internal error'}), 500

# Delete a user
@app.route(BASE_URL+'/users/<int:id>', methods=['DELETE'], endpoint='deleteUser')
@login_service
def deleteUser(id):
    if (not id or id=='' or id==0):
        print("User ID is null")
        return jsonify({'message': 'User ID is null'}), 400
    try:
        user = User()
        user.getUserById(id)
        if user.id == 0:
            return jsonify({'message': 'User does not exist.'}), 404
#        elif not user.username == request.authorization.username:
#            return jsonify({'message': 'Unable to access data of other users'}), 403
        else:
            res = user.delete()
            return res
    except Exception as e:
        print("User delete error: "+str(e))
        return jsonify({'message': 'Server internal error'}), 500

# Get a user data
@app.route(BASE_URL+'/users/<int:id>', methods=['GET'], endpoint='getUser')
@login
def getUser(id):
    if (not id or id=='' or id==0):
        print("User ID is null")
        return jsonify({'message': 'User ID is null'}), 400
    try:
        user = User()
        user.getUserById(id)
        if user.id == 0:
            return jsonify({'message': 'User does not exist.'}), 404
        elif not user.username == request.authorization.username:
            return jsonify(user.toPublicJSON()), 200
        else:
            return jsonify(user.toJSON()), 200
    except Exception as e:
        print("User data error: "+str(e))
        return jsonify({'message': 'Server internal error'}), 500

# Update user's data
# Don't forget about achievements in the description fiels
@app.route(BASE_URL+'/users/<int:id>', methods=['POST'], endpoint='updateUser')
@login
def updateUser(id):
    if (not id or id=='' or id==0):
        print("User ID is null")
        return jsonify({'message': 'User ID is null'}), 400
    try:
        user = User()
        user.getUserById(id)
        if user.id == 0:
            return jsonify({'message': 'User does not exist.'}), 404
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
    except Exception as e:
        print("User data error: "+str(e))
        return jsonify({'message': 'Server internal error'}), 500

# Create a goal
@app.route(BASE_URL+'/posts', methods=['POST'], endpoint='createGoal')
@login
def createGoal():
    try:
        if request.method == 'POST':
            request_data = request.get_json()
            goal = Goal()
            goal.fromJSON(request_data)
            res = goal.save()
            user = User()
            user.getUserById(goal.author)
            user.updateRating()
            return res
        else:
            print("Incorrect request")
            return jsonify({'message': 'Incorrect request'}), 400
    except Exception as e:
        print("Goal save error: "+str(e))
        return jsonify({'message': 'Server internal error'}), 500

# Get user's goals - personal and available
@app.route(BASE_URL+'/posts', methods=['GET'], endpoint='getUserGoals')
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
                return getPersonalUserGoals(author, page, per_page)
        else:
            user.getUserByUsername(username)
            return getAvailableGoals(user.id, page, per_page)
    except Exception as e:
        print("Get user's goals error: "+str(e))
        return jsonify({'message': 'Server internal error'}), 500

# Complete or update the goal
@app.route(BASE_URL+'/posts/<int:id>', methods=['POST'], endpoint='updateGoal')
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
            res = goal.save()
            user.updateRating()
            return res
    except Exception as e:
        print("Goal data error: "+str(e))
        return jsonify({'message': 'Server internal error'}), 500

# Get the goal by ID
@app.route(BASE_URL+'/posts/<int:id>', methods=['GET'], endpoint='getGoal')
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
    except Exception as e:
        print("Get goal data error: "+str(e))
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

# Like the goal
@app.route(BASE_URL+'/posts/like/<int:id>', methods=['POST'], endpoint='likeGoal')
@login
def likeGoal(id):
    try:
        if request.method == 'POST':
            username = request.authorization.username
            if (not username or username==''):
                print("Username is null")
                return jsonify({'message': 'Username is null'}), 400
            if (not id or id=='' or id==0):
                print("Goal ID is null")
                return jsonify({'message': 'Goal ID is null'}), 400
            goal = Goal()
            goal.getGoalById(id)
            user = User()
            user.getUserByUsername(username)
            goal.addLike(user.id)
            return jsonify(goal.toJSON()), 200
        else:
            print("Incorrect request")
            return jsonify({'message': 'Incorrect request'}), 400
    except Exception as e:
        print("Goal like error: "+str(e))
        return jsonify({'message': 'Server internal error'}), 500

# Unlike the goal
@app.route(BASE_URL+'/posts/unlike/<int:id>', methods=['POST'], endpoint='unLikeGoal')
@login
def unLikeGoal(id):
    try:
        if request.method == 'POST':
            username = request.authorization.username
            if (not username or username==''):
                print("Username is null")
                return jsonify({'message': 'Username is null'}), 400
            if (not id or id=='' or id==0):
                print("Goal ID is null")
                return jsonify({'message': 'Goal ID is null'}), 400
            goal = Goal()
            goal.getGoalById(id)
            user = User()
            user.getUserByUsername(username)
            goal.removeLike(user.id)
            return jsonify(goal.toJSON()), 200
        else:
            print("Incorrect request")
            return jsonify({'message': 'Incorrect request'}), 400
    except Exception as e:
        print("Goal unlike error: "+str(e))
        return jsonify({'message': 'Server internal error'}), 500

# Generate a new goal by AI
@app.route(BASE_URL+'/posts/generate', methods=['GET'], endpoint='genGoal')
@login
def genGoal():
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
        title = generateGoal(user, mode='run')
        return jsonify({'title': title}), 200
    except Exception as e:
        print("Generate new goal error: "+str(e))
        return jsonify({'message': 'Server internal error'}), 500

# Generate a new test goal by AI for a user
@app.route(BASE_URL+'/posts/generate/test/<int:id>', methods=['GET'], endpoint='genTestGoal')
@login_service
def genTestGoal(id):
    user = User()
    user.getUserById(id)
    response = generateGoal(user, mode='test')
    return jsonify(response), 200

# Get user's friends
@app.route(BASE_URL+'/friends', methods=['GET'], endpoint='getFriends')
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
    except Exception as e:
        print("Get user's friends error: "+str(e))
        return jsonify({'message': 'Server internal error'}), 500

# Get user's friends received requests
@app.route(BASE_URL+'/friends/requests/received', methods=['GET'], endpoint='getFriendsRequestsReceived')
@login
def getFriendsRequestsReceived():
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
        return jsonify(user.friendsRequestsReceived), 200
    except Exception as e:
        print("Get user's friends received error: "+str(e))
        return jsonify({'message': 'Server internal error'}), 500

# Get user's friends sent requests
@app.route(BASE_URL+'/friends/requests/sent', methods=['GET'], endpoint='getFriendsRequestsSent')
@login
def getFriendsRequestsSent():
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
        return jsonify(user.friendsRequestsSent), 200
    except Exception as e:
        print("Get user's friends sent error: "+str(e))
        return jsonify({'message': 'Server internal error'}), 500

# Get user's friends and requests data
@app.route(BASE_URL+'/friends/<int:id>', methods=['GET'], endpoint='getFriendsData')
@login
def getFriendsData(id):
    if (not id or id=='' or id==0):
        print("User ID is null")
        return jsonify({'message': 'User ID is null'}), 400
    try:
        user = User()
        user.getUserById(id)
        if user.id == 0:
            return jsonify({'message': 'User does not exist.'}), 404
        elif not user.username == request.authorization.username:
            return jsonify(user.toPublicJSON()), 200
        else:
            return jsonify(user.toFriendsJSON()), 200
    except Exception as e:
        print("User data error: "+str(e))
        return jsonify({'message': 'Server internal error'}), 500

# Search for friends
@app.route(BASE_URL+'/friends/search', methods=['GET'], endpoint='searchFriends')
@login
def searchFriends():
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
    except Exception as e:
        print("Search users error: "+str(e))
        return jsonify({'message': 'Server internal error'}), 500

# Process friends requests
@app.route(BASE_URL+'/friends/requests/<int:id>', methods=['POST'], endpoint='friendsRequest')
@login
def friendsRequest(id):
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
            if 'action' in request_data:
                action = request_data['action']
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
    except Exception as e:
        print("Goal save error: "+str(e))
        return jsonify({'message': 'Server internal error'}), 500

# Import users
@app.route(BASE_URL+'/users/import', methods=['POST'], endpoint='importUsers')
@login_service
def importUsers():
    try:
        request_data = request.get_json()
        if not request_data:
            return jsonify({'message': 'Incorrect request'}), 400
        result = []
        if 'people' in request_data:
            users = request_data['people']
            for userJSON in users:
                if ('name' in userJSON) and ('username' in userJSON) and ('email' in userJSON):
                    print('Importing:')
                    print(userJSON)
                    user = User(
                        date=datetime.now(),
                        name=userJSON['name'],
                        username=userJSON['username'],
                        email=userJSON['email'],
                        avatar=random.randint(1, AVATAR_MAX),
                        status=2,
                    )
                    if (not 'password' in userJSON) or (userJSON['password'] == ''):
                        user.password = wp_crypt.crypt_private(SERVICE_IMPORT_PASSWORD)
                    res = user.save()
                    result.append(res[0])
        return jsonify({'result': result}), 200
    except Exception as e:
        print("Users import error: "+str(e))
        return jsonify({'message': 'Server internal error'}), 500

# Import goals
@app.route(BASE_URL+'/posts/import', methods=['POST'], endpoint='importPosts')
@login_service
def importPosts():
    try:
        request_data = request.get_json()
        if not request_data:
            return jsonify({'message': 'Incorrect request'}), 400
        result = []
        if 'posts' in request_data:
            posts = request_data['posts']
            for postJSON in posts:
                if ('author' in postJSON) and ('title' in postJSON):
                    print('Importing:')
                    print(postJSON)
                    goal = Goal(
                        author=int(postJSON['author']),
                        date=datetime.now(),
                        title=postJSON['title'],
                        isprivate=False,
                        isfriends=False,
                        ispublic=True,
                        isgenerated=True,
                        isaccepted=True,
                        status=1,
                    )
                    # goal.fromJSON(postJSON)
                    res = goal.save()
                    user = User()
                    user.getUserById(goal.author)
                    user.updateRating()
                    result.append(res[0])
        return jsonify({'result': result}), 200
    except Exception as e:
        print("Goals import error: "+str(e))
        return jsonify({'message': 'Server internal error'}), 500

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8000)