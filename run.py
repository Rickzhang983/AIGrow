
from backend import app
from backend.node_proxy import socketio
import sys,traceback

#app.config['SERVER_NAME'] ='www.aigrow.net'
#app.run('0.0.0.0', debug=True, port=8080)# , ssl_context=('SSLcertificate/2108031_www.aigrow.net.pem', 'SSLcertificate/2108031_www.aigrow.net.key'))
try:
    socketio.run(app, host='0.0.0.0',port=8080)
    #app.run('0.0.0.0', debug=True, port=8080)  #
except :
    info = sys.exc_info()
    tb_obj = info[-1]
    ss_obj = traceback.extract_tb(tb_obj)  
    traceback.print_exc()
