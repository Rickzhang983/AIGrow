import logging

from backend.test.usocketio import client

logging.basicConfig(level=logging.DEBUG)

def hello():
    with client.connect('http://127.0.0.1:8080/') as socketio:
        @socketio.on('message')
        def on_message(self, message):
            print("message", message)

        @socketio.on('alert')
        def on_alert(self, message):
            print("alert", message)

        socketio.run_forever()

hello()
