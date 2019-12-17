# _*_coding:utf-8_*_

from backend import db
from backend.util import make_error,not_found,return_create_success
from flask import json,jsonify,request,Blueprint
from .tokenservice import *
from functools import wraps
import datetime

class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, index=True)
    username = db.Column(db.String(24))
    create_time = db.Column(db.DATETIME)
    mobile = db.Column(db.String(20))
    password = db.Column(db.String(16))
    state = db.Column(db.Integer)
    spectation_enable = db.Column(db.Boolean)

idm = Blueprint('idm', __name__,url_prefix='/api/user')
import logging
applogger = logging.getLogger('idm')
logging.basicConfig(filename='log/idm.log',level=logging.INFO)

@idm.route('/query/<user>', methods=['GET'])
def check_user_existence(user):
    """
    :type username: basestring
    """
    results=[]
    user = db.session.query(Users).filter_by(username = user).first()
    if user:
        value = {"id": user.id}
        applogger.info ("user exists:", value)
        return json.dumps(results, sort_keys=False)
    else:
        return not_found()

@idm.route('/login', methods=['POST'])
def user_login():
    """ 将账号和密码 POST 到 Auth 模块后，Auth 设置一个 header，设置 Cookie 及过期时间"""
    applogger.info ("Request method: %s"%request.method)
    data = request.form #json.loads(request.json)
    username = data["username"]
    password = data["password"]
    applogger.info ("User login: %s, %s"%(username,password))
    results = []
    user = Users.query.filter_by(username = username,password = password).first()
    if user:
        #print ("------------------user found!")
        tokenString = generateToken(user.id,username)
        resp = jsonify({"token": str(tokenString,'utf-8') })
        if resp.headers:
            # resp.headers['Set-Cookie'] = 'User:' + username +'; token = '+ str(tokenString,'utf-8') +';Max-Age = 3600; path=\\'
            resp.headers.set('Authorization',str(tokenString,'utf-8'))
        return   resp
        # value = {"id": user.id,"token": token}
        # results.append(value)
        # json.dumps(results, sort_keys = False)
    else:
        applogger.debug("---No---------------user found!")
        return make_error(500, "Wrong user or password","Correct user name or password!")


@idm.route('/add', methods=['POST'])
def user_create():
    import os
    try:
        data = request.form
        user = db.session.query(Users).filter_by(username = data["username"]).first()
        if  user:
            return make_error(500, "Duplicated user name","Change a different user name")
        applogger.info("Adding user in progress")
        user = Users()
        user.username = data["username"]
        user.mobile = data["mobile"]
        user.create_time = datetime.datetime.utcnow()
        user.password = data["password"]
        user.state = 0
        user.spectation_enable = False
        db.session.add(user)
        db.session.flush()
        print (user.id)
        db.session.commit()
        to_created_path = 'userfiles/'+str(user.id)
        if not os.path.exists(to_created_path):
            os.makedirs(to_created_path)
        applogger.info("Adding user --- Done")
        return return_create_success("User created!")

    except Exception as e:
        db.session.rollback()
        applogger.error("Adding user --- failed "+str(e) )
        return make_error(500,str(e),"")


def userAuthenticate():
    from flask import request
    def real_decorator(function):
        @wraps (function)
        def wrapper(*args, **kwargs):
            # cookie = request.cookies
            # token = cookie.get("token")
            token = request.headers.get('Authorization')
            if (token == None): return rediect_to_login()
            #print ("function: %s"%function.__name__)
            user_id, msg = getUseridByToken(token)
            if( user_id):
                kwargs['userid'] = user_id
                return function(*args, **kwargs)
            else:
                # return HTTP 401
                return rediect_to_login()
        return wrapper
    return real_decorator


def rediect_to_login():
    response = jsonify({
        'status': 401,
        'message': 'Authentication is required',
        'action': 'Login'
    })
    response.status_code = 401
    return response

