from flask import Blueprint, json, request
from ..util import *
from ..idm import userAuthenticate
from .recipe import *
from sqlalchemy.exc import InvalidRequestError
from .. import db
import time
from backend.node_proxy import socketio, Node2Socketio,buffer,asyn2syn
from ..shared import UserRecipe,UserNode
import logging

config = Blueprint('config', __name__,url_prefix='/api/config')
logger = logging.getLogger('config')

@config.route('/my_active_program/<domain>', methods=['GET'])
@userAuthenticate()
def get_program_summary(domain,**kwargs):
    userid = kwargs['userid']
    #try:
    userRecipe = UserRecipe.query.filter_by(user_id = userid,domain = domain).order_by(UserRecipe.start_time)
    for record in userRecipe:
        # for now, only hydroponics domain and general_greens template are for any user
        tm = time.strptime(str(record.start_time),"%Y-%m-%d %H:%M:%S")
        rs = RecipeInstance(record.domain,record.template, (tm[0], tm[1], tm[2], tm[3], tm[4], tm[5]), record.offset_minutes)
        try:
            first_stage, first_phase, current_stage, past_cycles, last_phase, past_duration = rs.currentState()
            result = {"template": rs.template.to_json(),"start_time": (record.start_time), "offset_hours": "%.2f"%(rs.offset / 60),
                      "first_stage":first_stage, "first_phase":first_phase,
                      "current_stage": current_stage, "past_cycles": past_cycles,
                      "latest_phase": last_phase.to_json(), "past_duration": "%.2f"%past_duration, "remaining": "%d"%(last_phase.duration - past_duration)}
            return json.dumps(result, separators=(",", ":"),cls=ComplexEncoder)
        except RuntimeError as re:
            continue
        except Exception as e:
            return make_error(500,"failed")
    return make_error(404, "No template configured")

@config.route('/my_programs/<domain>', methods=['GET'])
@userAuthenticate()
def get_my_program_list(domain,**kwargs):
    userid = kwargs['userid']
    #try:
    query_result =UserRecipe.query.filter_by(user_id = userid,domain = domain).order_by(UserRecipe.start_time).all()
    ar = []
    working_found= False
    for record in query_result:
            # for now, only hydroponics domain and general_greens template are for any user
        try:
            tm = time.strptime(str(record.start_time),"%Y-%m-%d %H:%M:%S")
            rs = RecipeInstance(record.domain,record.template, (tm[0], tm[1], tm[2], tm[3], tm[4], tm[5]), record.offset_minutes)
            first_stage, first_phase, current_stage, past_cycles, last_phase, past_duration = rs.currentState()
            if (working_found) :
                raise RuntimeError('Standby')
            result = {"id":record.id, "template": rs.template.to_json(),"status":"Busy","total_duration":rs.template.totalDuration(),\
                      "start_time": (record.start_time), "offset_hours": "%.2f"%(rs.offset / 60),
                      "first_stage":first_stage, "first_phase":first_phase,
                     "current_stage": current_stage, "past_cycles": past_cycles,
                      "latest_phase": last_phase.to_json(), "past_duration": "%.2f"%past_duration, "remaining": "%d"%(last_phase.duration - past_duration)}
            ar.append(result)
            working_found = True
        except RuntimeError as re:
            status = re.args[0]
            result = {"id":record.id,"template": rs.template.to_json(),"status":status,\
                      "total_duration":rs.template.totalDuration(),"start_time": (record.start_time), "offset_hours": "%.2f"%(rs.offset / 60)}
            ar.append(result)
        except Exception as e:
            logger.exception("exception")
            return make_error(500,"failed")
    if ar:
        return json.dumps(ar, separators=(",", ":"),cls=ComplexEncoder)
    return make_error(404, "No program configured")


@config.route('/my_programs/<domain>', methods=['POST'])
@userAuthenticate()
def create_user_program(domain,**kwargs):
    userid = kwargs['userid']
    logger.info("request content %s"%request.json)
    try:
        data = request.json
        program= data['program']
        if recipeCache[domain][program]:
            # save data
            user_recipe = UserRecipe()
            user_recipe.domain = domain
            user_recipe.template = program
            user_recipe.start_time = data['start_time']
            user_recipe.offset_minutes = float(data['offset'])*60
            # user_id = db.Column(db.Integer, db.ForeignKey('User.id'))
            user_recipe.user_id = userid
            user_recipe.expired = False
            db.session.add(user_recipe)
            db.session.commit()
            return return_create_success("user program created")
        else:
            return make_error(404,'no program matched')
    except Exception as e:
        logger.exception("fail")
        import traceback
        traceback.print_exc()
        return make_error(500, "failed")


@config.route('/my_programs/<domain>/<id>', methods=['DELETE'])
@userAuthenticate()
def delete_user_program(domain,id,**kwargs):
    userid = kwargs['userid']
    try:
        data = request.json
        program_id = id
        # delete data
        record = UserRecipe.query.filter_by(user_id=userid, id=id).first()
        db.session.delete(record)
        db.session.commit()
        return return_delete_success("user program deleted")
    except InvalidRequestError as e:
        import traceback
        traceback.print_exc()
        return make_error(404,'no program matched')
    except Exception as e:
        print (e)
        import traceback
        traceback.print_exc()
        return make_error(500, "failed")


@config.route('/all_programs/<domain>', methods=['GET'])
@userAuthenticate()
def get_all_program(domain,**kwargs):
    ar=[]
    for key in recipeCache.get(domain,''):
        if key:
            ar.append(recipeCache[domain][key].to_json())
    if ar:
        return json.dumps(ar, separators=(",", ":"))
    return make_error(500, "failed")



@socketio.on("/calibration/all/result")
def recv_calibration_list(data):
    buffer[request.sid] =data  #produce data

@socketio.on("/calibration/execute/result")
def recv_calibration_result(data):
    #global buffer
    buffer[request.sid] =data #produce data


@config.route('/calibration/<domain>', methods=['GET'])
@userAuthenticate()
def get_all_calibration(domain,**kwargs):
    userid = kwargs['userid']
    sid = Node2Socketio.getSocketioByUserID(userid)
    #remove the previous data
    from flask import jsonify
    if sid:
        if sid in buffer: buffer.pop(sid)
        socketio.emit("/calibration/all",room=sid)
        socketio.sleep(1)
        result = asyn2syn(sid,10)
        #print ("--------------",result)
        if result:
            if "failure" in result:
                return make_error(500, result["failure"])
            return json.dumps(result)
        return make_error(500, "No repsonse got from your device")
    else:
       return make_error(500, "Your device is not connected")

@config.route('/calibration_execution', methods=['POST'])
@userAuthenticate()
def calibration_execution( **kwargs):
    userid = kwargs['userid']
    sid = Node2Socketio.getSocketioByUserID(userid)
    data = request.json
    if sid:
        logger.info("data to send to node for execution %s" % data)
        if sid in buffer: buffer.pop(sid)
        socketio.emit("/calibration/execute",data,room=sid)
        socketio.sleep(0.1)
        result = asyn2syn(sid,15)
        if result:
            if "failure" in result:
                return make_error(500, result["failure"])
            return json.dumps(result)
        return make_error(500, "No repsonse got from your device")
    else:
       return make_error(500, "Your device is not connected")



@config.route('/hardware', methods=['GET'])
@userAuthenticate()
def query_myhardware(**kwargs):
    userid = kwargs['userid']
    node =UserNode.query.filter_by(host_id = userid).first()
    if node:
        result = {"node_id": node.node_id, "id":node.host_id, "ip_address":node.ip_address,"alias":node.alias,"interval_sec":node.interval}
        ar=[]
        ar.append(result)
        return json.dumps(ar)
    else:
        return make_error(404,'no node configured')



@config.route('/hardware', methods=['POST'])
@userAuthenticate()
def configure_my_hardware(**kwargs):
    userid = kwargs['userid']
    data = request.json
    query_result = UserNode.query.filter(UserNode.host_id==userid, UserNode.node_id!=data["node_id"],
                                         UserNode.alias==data['alias']).first()
    if query_result:
        return make_error(409,"Duplicated memorable alias under your user name")

    query_result = UserNode.query.filter(UserNode.host_id != userid , UserNode.node_id==data['node_id']).first()
    if query_result:
        return make_error(409,"The device id has been used by someone else")


    query_result = UserNode.query.filter_by(host_id=userid).first()
    if query_result:
        user_node = query_result
    else:
        user_node =UserNode()
        user_node.ip_address=''
    user_node.node_id = data["node_id"]
    user_node.host_id = userid
    user_node.alias = data['alias']
    user_node.interval = data["interval_sec"]
    try:
        if query_result:
            pass #flask will update the record
        else:
            db.session.add(user_node)
        db.session.commit()
        return query_myhardware(**kwargs)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return make_error(500,e)


@config.route('/<path:path>')
def default_config(path):
    return make_error(404,"the requested API %s is not existed"%path)


