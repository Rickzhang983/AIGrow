from flask import request
from plotapp.base import *

from model import *
from views import base
from plotapp import app
import json


@base.route('/setup')
def setup():
    return base.send_static_file("setup.html")

@app.route('/api/setup/kettle', methods=['POST'])
def setKettle():
    data =request.get_json()


    Hardware.query.delete()

    for hw in data["hardware"]:
        ks = Hardware(id=hw["id"], name=hw["name"], type=hw["type"], config=json.dumps(hw["config"]))
        db.session.add(ks)


    setConfigParameter("PLOT_NAME", data["plot_name"])
    setConfigParameter("SETUP", "No")
    return ('', 204)

@app.route('/api/setup/thermometer', methods=['POST'])
def setThermometer():
    data =request.get_json()
    thermometer = {
        '1WIRE': w1_thermometer.OneWireThermometer(),
    }
    app.plotapp_thermometer = thermometer.get(data["type"], w1_thermometer.OneWireThermometer())
    setConfigParameter("THERMOMETER_TYPE",data["type"] )
    return json.dumps(app.plotapp_thermometer.getSensors())

@app.route('/api/setup/hardware', methods=['POST'])
def setHardware():
    data =request.get_json()
    hardware= {
        'GPIO': gpio.RPIGPIO(),
    }
    setConfigParameter("SWITCH_TYPE",data["type"] )
    return json.dumps(app.plotapp_hardware.getDevices())

def setConfigParameter(name, value):
    config = Config.query.get(name)

    if(config == None):
        config = Config()
        config.name = name
        config.value = value
    else:
        config.value = value

    app.plotapp_config[name] = value

    db.session.add(config)
    db.session.commit()
