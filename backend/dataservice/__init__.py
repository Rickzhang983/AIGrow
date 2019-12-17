from flask import Blueprint,json, request,Response
from flask_cors import cross_origin
from ..idm import userAuthenticate,Users
from backend import db
from ..util import *
from .image import *
from ..config.recipe import *
from ..shared import getUseridByNode,Datarecord
import traceback,logging

datasvc = Blueprint('dataservice', __name__, url_prefix='/api/data')
logger = logging.getLogger("datasvc")
import os


@datasvc.route('/datastream', methods=['POST'])
def receive_remote_data():
    try:
        data = json.loads(request.json.encode('utf-8'))
        print ("get post from remote MC",request.json)
        lastdata = Datarecord()
        lastdata.place = data.get("location")
        lastdata.type = "Sensor"
        lastdata.name = data.get("name")
        #lastdata.event_type = data.get("name")
        lastdata.value1 = data.get("value")
        lastdata.unit1 = data.get("unit")
        lastdata.time =  data.get("sample_time")
        lastdata.host_id = getUseridByNode(data.get("nodeid"))
        db.session.add(lastdata)
        db.session.commit()
        return return_success("Data accepted!")

    except Exception as e:
        db.session.rollback()
        logger.error("Adding data failed "+str(e) )
        return make_error(500,str(e),"")


@datasvc.route('/<placeid>/last', methods=['GET'])
@userAuthenticate()
def read_container_data(placeid,**kwargs):
    try:
        userid = kwargs['userid']

        data = request.query_string.decode()
        #print('query string', data)
        if data:
            key, value = (request.query_string.decode()).split("=")
            if key== 'owner':
                owner = value
                print ("userid &owner",userid, owner)
                allowed= Users.query.filter_by(username = owner, spectation_enable = True).first()
                if (not allowed):
                    return make_error(404,"unauthorized spectation")
                userid = allowed.id
        results=[]
        sensors = db.session.query(Datarecord).with_entities(Datarecord.name).filter_by(place=placeid, host_id = userid).distinct()
        for sensor in sensors:
            result = Datarecord.query.filter_by(place=placeid,name= sensor.name,host_id = userid).order_by(Datarecord.time.desc()).first()

            #print ("Result %s"%result.name)
            if result == None: continue
            value = {"id":result.id,"time":result.time,"place":result.place,"type":result.type,\
                "name":result.name,"value1":result.value1,"unit1":result.unit1,
                "value2":result.value2,"sensor_state":getDeviceStatus(result.time),"userid":result.host_id}
            results.append(value)
        return json.dumps(results,sort_keys=False)
    except Exception as e:
        logger.error("Query container data failed ", e)
        return not_found('No records found for %s'%placeid)


@datasvc.route('/<place>/<sensor_id>/last', methods=['GET'])
@userAuthenticate()
def read_container_sensordata(place,sensor_id,**kwargs):
    userid = kwargs['userid']
    #value = []
    if sensor_id == "data": return read_container_data()
    print ("place %s sensor %s"%(place,sensor_id))
    try:

        result = Datarecord.query.filter_by(place=place, name=sensor_id, host_id=userid).order_by(Datarecord.time.desc()).first()
        value=({"id":result.id,"time":result.time,"place":result.place,"type":result.type,\
                "name":result.name,"value1":result.value1,"unit1":result.unit1,
                "value2":result.value2, "userid":result.host_id})
        return json.dumps(value,sort_keys=False)
    except Exception as e:
        return not_found(sensor_id+" data")

@datasvc.route('/growth/<direction>/<oid>', methods=['GET'])
@userAuthenticate()
def read_image_data( oid,direction,**kwargs):
    print("read_image_data called ", direction)
    userid = kwargs['userid']
    pid =int(oid)
    results=[]
    if direction == "last": #if shall never be here
        sql = Datarecord.query.filter_by( name="growth", host_id=userid).order_by(Datarecord.time.desc())
        result = sql.first()
        #return read_container_sensordata(place,'growth',**kwargs)
        # for view : result = Datarecord.query.filter_by(place ="plot", event_type="Growth", id=pid, host_id = userid).order_by(Datarecord.id.desc()).first()
    elif direction == 'next':
        result = Datarecord.query.filter ( Datarecord.id > pid,  Datarecord.name== "growth", Datarecord.host_id == userid).order_by(Datarecord.time).first()
    else:
        result = Datarecord.query.filter(Datarecord.id<pid, Datarecord.name=="growth", Datarecord.host_id==userid).order_by(Datarecord.time.desc()).first()

    if result == None: return not_found("Not found resource")
    value = {"id":result.id,"time":result.time,"place":result.place,"type":result.type,\
            "name":result.name,"value1":result.value1,"unit1":result.unit1,
            "value2":result.value2, "sensor_state":getDeviceStatus(result.time),"userid":result.host_id}
    #print(value)
    #results.append(value)
    return json.dumps(value,sort_keys=False)



def store_growth_data(area,diameter,file_name,current_time,host_id,place):
    try:
        lastdata = Datarecord()
        lastdata.place = place
        lastdata.name = "growth"
        lastdata.type = "AI"
        lastdata.value1 = "%.3f"%area
        lastdata.unit1 = "cm^2"
        lastdata.time = current_time
        lastdata.host_id = host_id
        lastdata.value2 = file_name
        db.session.add(lastdata)
        db.session.commit()
    except Exception as e:
        print (e)
        raise (e)


@datasvc.route('/<place>/growth', methods=['POST'])
@cross_origin(allow_headers=['Content-Type'])
@userAuthenticate()
def upload_growth_record(place,**kwargs):
    userid = kwargs['userid']
    try:
        file = request.files['file']
        filename = file.filename
        r = "userfiles/"+str(userid)+"/"+ filename  #字符串，表示上传文件的文件名
        print ("uploaded file",r)
        if (os.path.exists(r)):
            return make_error(500,"Duplicated file")
        file.save(r)
        area, max_diameter, t_datetime = process_img("userfiles/"+str(userid),file.filename)
        store_growth_data(area,max_diameter,filename,t_datetime,userid,place)
        print("--------Get no Error")
        return return_success("The image is success captured and processed!")
    except Exception as e:
        traceback.print_exc()
        if (os.path.exists(r)):
            os.remove(r)
        return make_error(500,e.__str__())

@datasvc.route('/<place>/growth/<id>', methods=['DELETE'])
@userAuthenticate()
def delete_growth_record(id,place, **kwargs):
    userid = kwargs['userid']
    print("recieve deletion request, id=",id)
    filename =''
    try:
        sql_statement = "select value2 from datarecord where place ='"+ place +"' and id="+str(id) +" and host_id="+ str(userid)
        print (sql_statement)
        results = db.engine.execute(sql_statement).first()
        if results==None: return not_found("The data does not exist")
        filename="userfiles/"+str(userid)+"/"+results.value2
        print("filename",filename)
        os.remove(filename)
        os.remove(filename.replace(".jpg", "-2.jpg"))
        sql_statement ="delete from datarecord where id="+str(id) +" and host_id="+ str(userid)
        print(sql_statement)
        db.engine.execute(sql_statement)

        return return_success("Delete successed!")
    except Exception as e:
        if e is IOError:
            sql_statement = "delete from datarecord where id=" + id +" and host_id= "+ userid
            db.engine.execute(sql_statement)
            print ("File access error")
            return return_success()
        db.session.rollback()
        logger.error("Remove img failed "+str(e) )
        return make_error(500,"Remove img failed!","")

@datasvc.route('/img/<userid>/<imgfile>',methods=['GET'])
# @userAuthenticate()
def image_handler(imgfile,userid,**kwargs):
    import os
    # userid = kwargs['userid']
    imagepath="userfiles/"+ userid + "/"+ imgfile
    try:
        with open(imagepath, 'rb') as f:
             image_data = f.read()
             return Response(image_data, content_type="image/png")
    except Exception as e:
        print(e)
        return not_found(imgfile)



@datasvc.route('/chart/<place>/<id>', methods=['GET'])
@userAuthenticate()
def read_container_history_chart(place,id,**kwargs):
    userid = kwargs['userid']
    LIMIT_RECORD = "2000"
    sql = "select * from (select id, time, value1, unit1, value2 from datarecord where place ='" + place \
          + "' and name = '"+id +"' and host_id=" + str(userid) +" order by ID DESC LIMIT " + LIMIT_RECORD+ " ) as chart order by id"
    results = db.engine.execute (sql) #Datarecord.query.filter_by(place=place, name=id).order_by(Datarecord.id.desc()).limit(600).all()
    values = []
    s = {"Y": 1, "N": 0}
    for result in results:
        #v = (datetime.datetime.strptime(result.time, '%Y-%m-%d %H:%M:%S')- datetime.datetime(1970, 1,1)).total_seconds() * 1000
        value = [result.time, float(result.value1)]
        values.append(value)
    return json.dumps(values, sort_keys=False, separators=(",", ":"))