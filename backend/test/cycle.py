from plotapp import manager

from plotapp.base.util import *
from plotapp.base.model import *
from plotapp import app, socketio
import time
from flask import request
import os

import sqlite3
from datetime import datetime

from flask_restless.helpers import to_dict


@app.route('/api/cycle/order', methods=['POST'])
def order_steps():
    data = request.get_json()

    steps = Cycle.query.all()
    for s in steps:
        s.order = data[str(s.id)]
        db.session.add(s)
        db.session.commit()
    return ('',204)

@app.route('/api/cycle/clear', methods=['POST'])
def getBrews():
    Cycle.query.delete()
    db.session.commit()
    return ('',204)

@socketio.on('start', namespace='/plot')
def startCycle(*kwargs):
    nextCycle()

@socketio.on('next', namespace='/plot')
def nextCycle2():
    nextCycle()

def nextCycle():
    active = Cycle.query.filter_by(state='A').first()
    nextCycle = Cycle.query.filter(state='I').order_by(Cycle.order).first()

    if(nextCycle == None):
        socketio.emit('message', {"headline": "BREWING_FINISHED", "message": "BREWING_FINISHED_MESSAGE"}, namespace ='/plot')
        return

    if(active != None):
        active.state = 'D'
        active.end = datetime.utcnow()
        db.session.add(active)
        db.session.commit()
        app.plotapp_current_step  = None

    if(nextCycle != None):
        nextCycle.state = 'A'
        nextCycle.start = datetime.utcnow()
        db.session.add(nextCycle)
        db.session.commit()
        app.plotapp_current_cycle = nextCycle

    socketio.emit('step_update', getCycles(), namespace ='/plot')

## WebSocket
@socketio.on('reset', namespace='/plot')
def reset():
    pass



## Methods
@socketio.on('reset_current_step', namespace='/plot')
def resetCurrentCycles():
#    resetBeep()
    active = Cycle.query.filter_by(state='A').first()
    active.start = datetime.utcnow()
    active.end = None
    app.plotapp_current_step = active
    db.session.add(active)
    db.session.commit()
    socketio.emit('step_update', getCycles(), namespace ='/plot')


## REST POST PROCESSORS
def post_patch_many(result, **kw):
    pass
    #init()

def pre_put(data, **kw):
    pass

def post_get(result=None,**kw):
    ## SORT RESULT BY FIELD 'ORDER'
    result["objects"] = sorted(result["objects"], key=lambda k: k['order'])

    pass

@plotinit()
def init():
    ## REST API FOR STEP
    manager.create_api(Cycle, methods=['GET', 'POST', 'DELETE', 'PUT'],allow_patch_many=True, results_per_page=None, postprocessors=
    {'GET_MANY': [post_get]})
    s = Cycle.query.filter_by(state='A').first()
    if(s != None):
        app.plotapp_current_step = s


@plotjob(key="cyclejob", interval=0.1)
def cyclejob():


    ## Skip if no step is active
    if(app.plotapp_current_step == None):
        return
    ## current step
    cs = app.plotapp_current_step

    if cs.get("start") == None:
        s = Cycle.query.get(cs.get("id"))
        s.start = datetime.utcnow()
        app.plotapp_current_step = s
        db.session.add(s)
        db.session.commit()

    else:
        # check if timer elapsed
        end = cs.get("start") + cs.get("duration")*24*3600
        now = int((datetime.utcnow() - datetime(1970,1,1)).total_seconds())*1000
        ## switch to next step if timer is over
        if(end < now ):
            if(cs.get("type") == 'A'):
                nextCycle()

def getCycles():
    cycles = getAsArray(Cycle, order = "order")
    '''
    for o in steps:
        if(o["start"] != None):
            o["start"] = o["start"]  + "+00:00"
        if(o["timer_start"] != None):
            o["timer_start"] = o["timer_start"]  + "+00:00"
        if(o["end"] != None):
            o["end"] = o["end"]  + "+00:00"
    '''
    return cycles
