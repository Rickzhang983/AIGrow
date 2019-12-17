# _*_coding:utf-8_*_
#!usr/bin/python3

import datetime
from flask import Blueprint, Flask,jsonify, json, request
from .. import db
from ..util import *
from ..shared import getUseridByNode,UserNode
from .. import app
from ..idm import userAuthenticate

msgSvc = Blueprint('message', __name__,url_prefix='/api/message')

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, index=True)
    host_id = db.Column(db.Integer)  # ,db.ForeignKey('user.id'))
    node_id = db.Column(db.String(20))
    session = db.Column(db.String(20))
    time = db.Column(db.TIMESTAMP)
    source = db.Column(db.String(40))  # type: String;
    type = db.Column(db.String(12)) # notification or alarm
    message = db.Column(db.String(128))



@msgSvc.route('/notification', methods=['POST'])
def receive_notification0():
    try:
        message = json.loads(request.json)
        node_id = getUseridByNode(message.get("nodeid"))
        session = message.get('session','No SID')
        if session !='No SID': #to supress the messages for one session
            session_old = Notification.query.filter(Notification.node_id == node_id, Notification.session == session).first()
            if session_old: #exist a same session in the table, so merge the messages
                session.message =  session.message+chr(10)+ message["time"]+"--"+ message["content"]
                db.session.commit()
                return return_success("the notification accepted")
        else:
            note = Notification()
            note.type = message.get("type")
            note.session = message.get('session','No SID')
            note.node_id = message.get("nodeid")
            note.source = message["source"]
            note.time =  message["time"]
            note.message =  message["content"]
            note.host_id = node_id
            db.session.add(note)
            db.session.commit()
            return return_success("Notification accepted!")

    except Exception as e:
        app.logger.error("Adding notification failed "+str(e) )
        return make_error(500,str(e),"")


def get_notifications(**kwargs):
    userid = kwargs['userid']
    _,duration = (request.query_string.decode()).split("=")
    print (duration)
    if (duration == "day"):
        today = datetime.date.strftime(datetime.datetime.now(),'%Y-%m-%d')
        results = Notification.query.filter(Notification.host_id == userid , Notification.time >=today).\
            order_by(Notification.type,  Notification.time.desc(),Notification.source)
    else:
        t1 = datetime.datetime.date(datetime.datetime.now())
        t2 = t1-datetime.timedelta(7)
        today = datetime.date.strftime(t1, '%Y-%m-%d')
        weekago = datetime.date.strftime(t2, '%Y-%m-%d')
        print ("today, weekago",today, weekago)
        results = Notification.query.filter(Notification.host_id == userid , Notification.time.between(weekago, today)).\
            order_by(Notification.type,Notification.time.desc(),Notification.source)
        print ("today", today, "week ago", weekago)
    values = []
    for result in results:
        values.append({"id":result.id,"time":result.time,"node_id":result.node_id,"type":result.type, "source":result.source,"message":result.message})
    return json.dumps(values, sort_keys=False, separators=(",", ":"),cls=ComplexEncoder)

@msgSvc.route('/notification', methods=['GET'])
@userAuthenticate()
def get_notification_json(**kwargs):
    userid = kwargs['userid']
    _, duration = (request.query_string.decode()).split("=")
    if (duration == "day"):
        today = datetime.date.strftime(datetime.datetime.now(), '%Y-%m-%d')  #add_columns(UserNode.alias). \
        results = db.session.query(Notification,UserNode.alias).join(UserNode,Notification.node_id==UserNode.node_id). \
            filter(Notification.host_id == userid, Notification.time >=today).\
            order_by( Notification.type,Notification.time.desc(),Notification.type,Notification.source)
    else:
        t1 = datetime.datetime.date(datetime.datetime.now())
        t2 = t1 - datetime.timedelta(7)
        today = datetime.date.strftime(t1, '%Y-%m-%d')
        weekago = datetime.date.strftime(t2, '%Y-%m-%d')
        results = db.session.query(Notification,UserNode.alias).join(UserNode, Notification.node_id == UserNode.node_id). \
            filter(Notification.host_id == userid,Notification.time.between(weekago, today)).\
            order_by(Notification.type,Notification.time.desc(),Notification.type,Notification.source)
    alarms={}
    notifications={}

    values = []
    for result,alias in results:
        values.append({"id":result.id,"time":result.time,"node_id":alias,"type":result.type, "source":result.source,"message":result.message})
    return json.dumps(values, sort_keys=False, separators=(",", ":"),cls=ComplexEncoder)

    # for (result,alias) in results:
    #     print (result, alias)
    #
    #     if result.type == 'alarm':
    #         #build a json data following hierachy of result_type, source. the node_id is ignored since it  is always the same.
    #         if not (alarms.get(result.source)):
    #             alarms[result.source]=[]
    #         alarms[result.source].append({"id":result.id,"time":result.time,"node_id":alias, "message":result.message})
    #     else:
    #         if not (notifications.get(result.source)):
    #             notifications[result.source]=[]
    #         notifications[result.source].append({"id":result.id,"time":result.time,"node_id":alias, "message":result.message})
    # return json.dumps({'alarms':alarms,'notifications':notifications}, sort_keys=False, separators=(",", ":"),cls=ComplexEncoder)