from flask_socketio.test_client import SocketIOTestClient
from flask_socketio import SocketIO
from flask import Flask
import time
import logging,sys

def on_aaa_response(args):
    print('on_aaa_response', args)

def echo(args):
    print ("server message",args)

app =  Flask("test")
logging.basicConfig(stream =sys.stdout,level=logging.INFO,format ='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
socket = SocketIO(app)
client = SocketIOTestClient(app, socket)


socket.on('message', on_aaa_response)
socket.on('connect',echo)
socket.on('disconnect',echo)
client.connect('http://192.168.0.100:8080')
print (socket.transports)
print ("sending")
client.send('aaa')
print ("waiting")
time.sleep(3)
client.wait()
