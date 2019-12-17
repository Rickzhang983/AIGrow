#!usr/bin/python3

from flask_restless.helpers import to_dict
import datetime,json
import os.path


from flask import jsonify
import time


class ComplexEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.strftime('%Y-%m-%d %H:%M:%S')
        elif isinstance(obj, datetime.date):
            return obj.strftime('%Y-%m-%d')
        else:
            return json.JSONEncoder.default(self, obj)

def getSessionID(user_id,device_id):
    import random
    s1= str(hex(int(time.time()))).split('0x')[1][2:]+device_id+'%02d'%random.getrandbits(4)
    return s1


def not_found(resource_name=''):
    msg = {
        'status': 404,
        'message': 'not found resource ' + resource_name
    }
    resp = jsonify(msg)
    resp.status_code = 404
    return resp


def make_error(status_code, message, action=""):
    response = jsonify({
        'status': status_code,
        'message': message,
        'action': action
    })
    response.status_code = status_code
    return response


def return_success(message):
    response = jsonify({
        'status': 200,
        'message': message,
        'action': ""
    })
    response.status_code = 200
    return response

def return_create_success(message):
    response = jsonify({
        'status': 201,
        'message': message,
        'action': ""
    })
    response.status_code = 201
    return response

def return_delete_success(message):
    response = jsonify({
        'status': 202,
        'message': message,
        'action': ""
    })
    response.status_code = 202
    return response


def getAsArray(obj,order = None):
    if order is not None :
        result =obj.query.order_by(order).all()
    else:
        result =obj.query.all()
    ar = []
    for t in result:
        ar.append(to_dict(t))
    return ar


def getAsDict(obj, key, deep=None, order = None):
    if order is not None :
        result = obj.query.order_by(order).all()
    else:
        result =obj.query.all()
    ar = {}
    for t in result:
        ar[getattr(t, key)] = to_dict(t, deep=deep)
    return ar



# Job Annotaiton
# key = uniquie key as string
# interval = interval in which the method is invoked
def plotjob(key, interval, config_parameter = None):
    from backend import app
    import traceback
    traceback.print_stack()
    def real_decorator(function):
        #app = commondata["app"]
        d={"function": function, "key": key, "interval": interval, "config_parameter": config_parameter}
        if key not in app.myplot_jobs:
 #           app.myplot_jobs.append(d)
            app.myplot_jobs[key]=d
        def wrapper(*args, **kwargs):
            function(*args, **kwargs)
        return wrapper
    return real_decorator


# Init Annotaiton
def plotinit(order = 0, config_parameter = None):
    from backend import app
    def real_decorator(function):
        #app = commondata["app"]
        d = {"function": function, "order": order, "config_parameter": config_parameter}
        app.myplot_init.append(d)
        def wrapper(*args, **kwargs):
            function(*args, **kwargs)
        return wrapper

    return real_decorator


def delete_file(file):
    if os.path.isfile(file) == True:
        os.remove(file)

import traceback
def getDeviceStatus(last_record_time):
    try:
        last_time = datetime.datetime.strptime(last_record_time,"%Y-%m-%d %H:%M:%S")
        if (datetime.datetime.now()-last_time).total_seconds()<1800:
                return "Alive"
        return "Unknown"
    except Exception:
        traceback.print_exc()
        return 'Unknown'


